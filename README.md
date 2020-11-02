Dataset containing all data available from the UNFCCC API at https://di.unfccc.int as of 2020-10-28. Additionally, includes a small library to query the UNFCCC API for a subset of the data, and a script to refresh the data in case newer data is available.

Due to the large size of the full dataset, the dataset is shared using [datalad](https://www.datalad.org/), which is based on git. To download the data, see the dataset page on [gin](https://gin.g-node.org/mikapfl/read_di_unfccc) to download individual files from the data/ directory, or clone the whole dataset using datalad:
```shell
$ datalad clone https://github.com/mikapfl/read_di_unfccc.git
```
Then you can fetch the data using datalad:
```shell
$ cd read_di_unfccc
$ datalad get -r .
```
You can learn more about datalad in the [datalad handbook](http://handbook.datalad.org).

References:
All the data included in this dataset is available from the UNFCC API, which sources the data from:
* GHG inventory data: UNFCCC: Greenhouse Gas Inventory Data, available at https://unfccc.int/process/transparency-and-reporting/greenhouse-gas-data/what-is-greenhouse-gas-data
* Population data: UNSD Demographic Statistics, available at http://data.un.org
* GDP data: The World Bank GDP data, available at https://data.worldbank.org/ and shared by The World Bank under the [CC-BY 4.0 License](https://creativecommons.org/licenses/by/4.0/) and pusuant to their [terms of use](https://data.worldbank.org/summary-terms-of-use).

If you want to use the library to download data from the UNFCCC API, check out the `example.ipynb` notebook for a simple usage example. To re-download all of the data, use the `download_all.py` script.

License: the python scripts are provided under the Apache License, Version 2.0.
