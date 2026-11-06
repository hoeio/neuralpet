"""Download DoOR 2.0 odorant-response data into data/door/ (gitignored).

Source: github.com/ropensci/DoOR.data (data/door_response_matrix.csv, door_mappings.csv, odor.csv).
Licence: CC BY-SA 4.0 (DoOR.data DESCRIPTION, checked 2026-11-06).
Cite: Münch D, Galizia CG (2016) DoOR 2.0 - Comprehensive Mapping of Drosophila melanogaster
Odorant Responses. Sci Rep 6:21841. doi:10.1038/srep21841
"""
import ssl
import urllib.request
from pathlib import Path

import certifi

CTX = ssl.create_default_context(cafile=certifi.where())
BASE = "https://raw.githubusercontent.com/ropensci/DoOR.data/master/data/"
OUT = Path(__file__).resolve().parents[1] / "data" / "door"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in ["door_response_matrix.csv", "door_mappings.csv", "odor.csv"]:
        with urllib.request.urlopen(BASE + f, context=CTX) as r:
            (OUT / f).write_bytes(r.read())
        print("ok", f)


if __name__ == "__main__":
    main()
