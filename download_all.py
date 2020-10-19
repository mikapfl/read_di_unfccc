import tqdm
import os
import pandas as pd

from read_di_unfccc import UNFCCCApiReader

ROOT_DIR = os.path.abspath(os.curdir) # This is your Project Root

def main():
    r = UNFCCCApiReader()
    for party in tqdm.tqdm(r.parties["code"], desc="parties"):
        df = r.query(party_code=party, progress=True)
        df.to_csv(ROOT_DIR + '//' + f"outputs/{party}.csv.gz", compression="gzip")
        df.to_parquet(ROOT_DIR + '//' + f"outputs/{party}.parquet")


if __name__ == "__main__":
    main()
