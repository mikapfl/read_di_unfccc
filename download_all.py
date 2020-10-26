import tqdm
import os
import pathlib

from read_di_unfccc import UNFCCCApiReader

ROOT_DIR = pathlib.Path(os.path.abspath(os.curdir))  # This is your Project Root


def main():
    r = UNFCCCApiReader()
    for party in tqdm.tqdm(r.parties["code"], desc="parties"):
        df = r.query(party_code=party, progress=True)

        annexI = party in r.annex_one_reader.parties["code"]
        subdir = "annexI" if annexI else "non-annexI"
        df.to_csv(ROOT_DIR / "data" / subdir / f"{party}.csv.gz", compression="gzip")
        df.to_parquet(ROOT_DIR / "data" / subdir / f"{party}.parquet")


if __name__ == "__main__":
    main()
