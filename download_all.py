import tqdm
import pandas as pd

from read_di_unfccc import UNFCCCApiReader


def main():
    r = UNFCCCApiReader()
    for party in tqdm.tqdm(r.parties["code"], desc="parties"):
        df = r.query(party_code=party, progress=True)
        df.to_csv(f"outputs/{party}.csv.gz", compression="gzip")
        df.to_parquet(f"outputs/{party}.parquet")


if __name__ == "__main__":
    main()
