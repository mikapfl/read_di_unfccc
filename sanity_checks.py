import pandas as pd
import tqdm

from read_di_unfccc import UNFCCCApiReader


def main():
    reader = UNFCCCApiReader()
    assert len(reader.parties) >= 190
    for party in tqdm.tqdm(reader.parties["code"]):
        try:
            df = pd.read_parquet(f"data/annexI/{party}.parquet")
        except FileNotFoundError:
            df = pd.read_parquet(f"data/non-annexI/{party}.parquet")

        assert not df.duplicated(
            ["party", "category", "classification", "measure", "gas", "unit", "year"]
        ).any()

    print("no obvious problems")


if __name__ == "__main__":
    main()
