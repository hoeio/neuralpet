"""Download the hemibrain v1.2 traced adjacency export (an independent fly) into data/hemibrain/ (gitignored).

Source: https://storage.googleapis.com/hemibrain/v1.2/exported-traced-adjacencies-v1.2.tar.gz
(46 MB, exported from neuprint.janelia.org with neuprint-python; see its README). md5 checked.
Licence: CC BY 4.0 ("Hemibrain is licensed under CC-BY", janelia.org hemibrain page, checked 2026-11-07).
Cite: Scheffer LK et al. (2020) A connectome and analysis of the adult Drosophila central brain.
eLife 9:e57443. doi:10.7554/eLife.57443
"""
import base64
import hashlib
import ssl
import tarfile
import urllib.request
from pathlib import Path

import certifi

URL = "https://storage.googleapis.com/hemibrain/v1.2/exported-traced-adjacencies-v1.2.tar.gz"
MD5_B64 = "7B4HbRVELzaPpZeLAPSmHA=="          # x-goog-hash md5 of the object
OUT = Path(__file__).resolve().parents[1] / "data" / "hemibrain"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "adj.tar.gz"
    if not f.exists():
        with urllib.request.urlopen(URL, context=ssl.create_default_context(cafile=certifi.where())) as r:
            f.write_bytes(r.read())
    got = base64.b64encode(hashlib.md5(f.read_bytes()).digest()).decode()
    assert got == MD5_B64, f"md5 mismatch {got}"
    with tarfile.open(f) as t:
        t.extractall(OUT, filter="data")
    print("ok", OUT)


if __name__ == "__main__":
    main()
