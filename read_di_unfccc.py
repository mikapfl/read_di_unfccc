import requests
import pandas as pd
import treelib
import typing
import logging


class UNFCCCApiReader:
    """Provides simplified unified access to the Flexible Query API of the UNFCCC data access for all parties.
    Essentially encapsulates https://di.unfccc.int/flex_non_annex1 and https://di.unfccc.int/flex_annex1 ."""
    def __init__(self, *, base_url="https://di.unfccc.int/api/"):
        self.annex_one_reader = UNFCCCSingleCategoryApiReader(party_category='annexOne', base_url=base_url)
        self.non_annex_one_reader = UNFCCCSingleCategoryApiReader(party_category='nonAnnexOne', base_url=base_url)

        self.parties = pd.concat([self.annex_one_reader.parties, self.non_annex_one_reader.parties]).sort_index()
        self.gases = pd.concat([self.annex_one_reader.gases, self.non_annex_one_reader.gases]).sort_index()
        self.gases = self.gases[~self.gases.index.duplicated(keep="first")]  # drop duplicated gases

    def query(self, *, party_code, gases=None):
        """Query the UNFCCC for data.
        :param party_code:       ISO codes of a party for which to query.
                                 For possible values, see .parties .
        :param gases:            list of gases to query for. For possible values, see .gases .
                                 Default: query for all gases.

        If you need more fine-grained control over which variables to query for, including restricting the query
        to specific measures, categories, or classifications or to query for multiple parties at once, please see the
        corresponding methods .annex_one_reader.query and .non_annex_one_reader.query .
        """
        if party_code in self.annex_one_reader.parties['code'].values:
            reader = self.annex_one_reader
        elif party_code in self.non_annex_one_reader.parties['code'].values:
            reader = self.non_annex_one_reader
        else:
            raise KeyError(party_code)

        return reader.query(party_codes=[party_code], gases=gases)


class UNFCCCSingleCategoryApiReader:
    """Provides access to the Flexible Query API of the UNFCCC data access for a single category like nonAnnexOne.
    Essentially encapsulates https://di.unfccc.int/flex_non_annex1 or https://di.unfccc.int/flex_annex1 ."""

    def __init__(self, *, party_category: str, base_url="https://di.unfccc.int/api/"):
        """
        :param party_category: either 'nonAnnexOne' or 'annexOne'.
        :param base_url: URL where the API is accessible (default: https://di.unfccc.int/api/).
        """
        self.base_url = base_url

        parties_raw = self._get(f"parties/{party_category}")
        parties_entry = None
        for entry in parties_raw:
            if entry["categoryCode"] == party_category:
                parties_entry = entry
        if parties_entry is None:
            raise ValueError(f"Could not find parties for the party_category {party_category!r}.")

        self.parties = pd.DataFrame(parties_entry["parties"]).set_index("id").sort_index()
        self.years = pd.DataFrame(self._get("years/single")[party_category]).set_index("id").sort_index()

        # note that category names are not unique!
        category_hierarchy = self._get("dimension-instances/category")[party_category][0]
        self.category_tree = self._walk(category_hierarchy)

        self.classifications = (
            pd.DataFrame(self._get("dimension-instances/classification")[party_category]).set_index("id").sort_index()
        )

        measure_hierarchy = self._get("dimension-instances/measure")[party_category]
        self.measure_tree = treelib.Tree()
        sr = self.measure_tree.create_node("__root__")
        for i in range(len(measure_hierarchy)):
            self._walk(measure_hierarchy[i], tree=self.measure_tree, parent=sr)

        self.gases = pd.DataFrame(self._get("dimension-instances/gas")[party_category]).set_index("id").sort_index()

        unit_info = self._get("conversion/fq")
        self.units = pd.DataFrame(unit_info["units"]).set_index("id").sort_index()
        self.conversion_factors = pd.DataFrame(unit_info[party_category])

        # variable IDs are not unique, because category names are not unique
        # just give up and delete the duplicated ones
        self.variables = pd.DataFrame(self._get(f"variables/fq/{party_category}")).set_index("variableId").sort_index()
        self.variables = self.variables[~self.variables.index.duplicated(keep="first")]

    def _flexible_query(
        self, *, variable_ids: typing.List[int], party_ids: typing.List[int], year_ids: typing.List[int]
    ) -> typing.List[dict]:

        if len(variable_ids) > 5000:
            logging.warning(
                "Your query parameters lead to a lot of variables selected at once. "
                "If the query fails, try restricting your query more."
            )

        return self._post(
            "records/flexible-queries", json={"variableIds": variable_ids, "partyIds": party_ids, "yearIds": year_ids}
        )

    def query(
        self,
        *,
        party_codes: typing.List[str],
        category_ids: typing.Union[None, typing.List[int]] = None,
        classifications: typing.Union[None, typing.List[str]] = None,
        measure_ids: typing.Union[None, typing.List[int]] = None,
        gases: typing.Union[None, typing.List[str]] = None,
    ) -> pd.DataFrame:
        """Query the UNFCCC for data.
        :param party_codes:      list of ISO codes of the parties to query.
                                 For possible values, see .parties .
        :param category_ids:     list of category IDs to query. For possible values, see .show_category_hierarchy().
                                 Default: query for all categories.
        :param classifications:  list of classifications to query. For possible values, see .classifications .
                                 Default: query for all classifications.
        :param measure_ids:      list of measure IDs to query. For possible values, see .show_measure_hierarchy().
                                 Default: query for all measures.
        :param gases:            list of gases to query. For possible values, see .gases .
                                 Default: query for all gases.
        """
        party_ids = []
        for code in party_codes:
            party_ids.append(self._name_id(self.parties, code, key="code"))

        variable_ids = self._select_variable_ids(classifications, category_ids, measure_ids, gases)

        # always query all years
        year_ids = list(self.years.index)

        raw = self._flexible_query(variable_ids=variable_ids, party_ids=party_ids, year_ids=year_ids)

        return self._parse_raw_answer(raw)

    def _parse_raw_answer(self, raw: typing.List[dict]) -> pd.DataFrame:
        data = []
        for dp in raw:
            variable = self.variables.loc[dp["variableId"]]

            try:
                category = self.category_tree[variable["categoryId"]].tag
            except treelib.tree.NodeIDAbsentError:
                category = f'unknown category nr. {variable["categoryId"]}'

            row = {
                "party": self.parties.loc[dp["partyId"]]["code"],
                "year": self.years.loc[dp["yearId"]]["name"],
                "category": category,
                "classification": self.classifications.loc[variable["classificationId"]]["name"],
                "measure": self.measure_tree[variable["measureId"]].tag,
                "gas": self.gases.loc[variable["gasId"]]["name"],
                "unit": self.units.loc[variable["unitId"]]["name"],
                "numberValue": dp["numberValue"],
                "stringValue": dp["stringValue"],
            }
            data.append(row)

        return pd.DataFrame(data)

    def _select_variable_ids(self, classifications, category_ids, measure_ids, gases) -> typing.List[int]:
        # select variables from classification
        if classifications is None:
            classification_mask = pd.Series(data=[True] * len(self.variables), index=self.variables.index)
        else:
            classification_mask = pd.Series(data=[False] * len(self.variables), index=self.variables.index)
            for classification in classifications:
                cid = self._name_id(self.classifications, classification)
                classification_mask[self.variables["classificationId"] == cid] = True

        # select variables from categories
        if category_ids is None:
            category_mask = pd.Series(data=[True] * len(self.variables), index=self.variables.index)
        else:
            category_mask = pd.Series(data=[False] * len(self.variables), index=self.variables.index)
            for cid in category_ids:
                category_mask[self.variables["categoryId"] == cid] = True

        # select variables from measures
        if measure_ids is None:
            measure_mask = pd.Series(data=[True] * len(self.variables), index=self.variables.index)
        else:
            measure_mask = pd.Series(data=[False] * len(self.variables), index=self.variables.index)
            for mid in measure_ids:
                measure_mask[self.variables["measureId"] == mid] = True

        # select variables from gases
        if gases is None:
            gas_mask = pd.Series(data=[True] * len(self.variables), index=self.variables.index)
        else:
            gas_mask = pd.Series(data=[False] * len(self.variables), index=self.variables.index)
            for gas in gases:
                gid = self._name_id(self.gases, gas)
                gas_mask[self.variables["gasId"] == gid] = True

        selected_variables = self.variables[classification_mask & category_mask & measure_mask & gas_mask]
        return [int(x) for x in selected_variables.index]

    @staticmethod
    def _name_id(df, name, key="name"):
        try:
            return int(df[df[key] == name].index[0])
        except IndexError:
            raise KeyError(name)

    def show_category_hierarchy(self):
        return self.category_tree.show(idhidden=False)

    def show_measure_hierarchy(self):
        return self.measure_tree.show(idhidden=False)

    @classmethod
    def _walk(cls, node: dict, tree: treelib.Tree = None, parent=None) -> treelib.Tree:
        if tree is None:
            tree = treelib.Tree()

        tree.create_node(tag=node["name"], identifier=node["id"], parent=parent)

        if "children" in node:
            for child in node["children"]:
                cls._walk(child, tree=tree, parent=node["id"])

        return tree

    def _get(self, component: str) -> typing.Union[dict, list]:
        resp = requests.get(self.base_url + component)
        resp.raise_for_status()
        return resp.json()

    def _post(self, component: str, json: dict) -> typing.List[dict]:
        resp = requests.post(self.base_url + component, json=json)
        resp.raise_for_status()
        return resp.json()


def _smoketest_non_annex_one():
    r = UNFCCCSingleCategoryApiReader(party_category='nonAnnexOne')
    ans = r.query(party_codes=["AFG"])


def _smoketest_annex_one():
    r = UNFCCCSingleCategoryApiReader(party_category="annexOne")
    ans = r.query(party_codes=["DEU"], gases=["N₂O"])


def _smoketest_unified():
    r = UNFCCCApiReader()
    ans = r.query(party_code='AFG')


if __name__ == "__main__":
    _smoketest_annex_one()
