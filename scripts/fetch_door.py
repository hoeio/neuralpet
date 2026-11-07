"""Download DoOR 2.0 odorant-response data into data/door/ (gitignored).

Source: github.com/ropensci/DoOR.data (data/door_response_matrix.csv, door_mappings.csv, odor.csv,
and the per-receptor study tables data/<receptor>.csv, used for the Hallem & Carlson 2006 single-study
matrix in experiment 010).
Licence: CC BY-SA 4.0 (DoOR.data DESCRIPTION, checked 2026-11-06).
Cite: Münch D, Galizia CG (2016) DoOR 2.0 - Comprehensive Mapping of Drosophila melanogaster
Odorant Responses. Sci Rep 6:21841. doi:10.1038/srep21841
Hallem EA, Carlson JR (2006) Coding of odors by a receptor repertoire. Cell 125:143-160.
doi:10.1016/j.cell.2006.01.050
"""
import json
import ssl
import urllib.request
from pathlib import Path

import certifi

CTX = ssl.create_default_context(cafile=certifi.where())
REPO = "ropensci/DoOR.data"
COMMIT = "master"
BASE = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/data/"
OUT = Path(__file__).resolve().parents[1] / "data" / "door"
NOT_RECEPTOR = ("door_", "odor.csv", "ORs.csv")


def get(url):
    with urllib.request.urlopen(url, context=CTX) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in ["door_response_matrix.csv", "door_mappings.csv", "odor.csv"]:
        (OUT / f).write_bytes(get(BASE + f))
        print("ok", f)
    tree = json.loads(get(f"https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1"))["tree"]
    rec = [t["path"].split("/")[1] for t in tree if t["path"].startswith("data/") and t["path"].endswith(".csv")
           and not t["path"].split("/")[1].startswith(NOT_RECEPTOR)]
    (OUT / "receptors").mkdir(exist_ok=True)
    for f in rec:
        (OUT / "receptors" / f).write_bytes(get(BASE + f))
    print("ok", len(rec), "receptor study tables")


if __name__ == "__main__":
    main()
