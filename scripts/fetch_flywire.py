"""Download FlyWire FAFB v783 connectivity + annotations into data/ (gitignored).

Sources (checked 2026-11-06, see docs/DATA.md):
- Zenodo record 10676866 "FlyWire Whole-brain Connectome Connectivity Data", v783.
  Codex's own download page needs a Google sign-in, so we use this public mirror.
- flyconnectome/flywire_annotations (Schlegel et al. 2024) supplemental neuron annotations.

Licence: treat everything as CC BY-NC 4.0 (the strictest of what the sources state).
Never commit anything under data/.
"""
import hashlib
import json
import ssl
import sys
import urllib.request
from pathlib import Path

import certifi

CTX = ssl.create_default_context(cafile=certifi.where())

DATA = Path(__file__).resolve().parents[1] / "data" / "flywire"
ZENODO = "https://zenodo.org/api/records/10676866"
ZENODO_FILES = ["proofread_connections_783.feather", "proofread_root_ids_783.npy"]
ANNOT = ("https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/"
         "supplemental_files/Supplemental_file1_neuron_annotations.tsv")


def fetch(url, dest, md5=None):
    if dest.exists() and (md5 is None or _md5(dest) == md5):
        print("ok  ", dest.name)
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    print("get ", url)
    with urllib.request.urlopen(url, context=CTX) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    if md5 and _md5(tmp) != md5:
        sys.exit(f"md5 mismatch for {dest.name}")
    tmp.rename(dest)


def _md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while chunk := f.read(1 << 22):
            h.update(chunk)
    return h.hexdigest()


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    rec = json.load(urllib.request.urlopen(ZENODO, context=CTX))
    (DATA / "zenodo_record.json").write_text(json.dumps(rec, indent=1))
    files = {f["key"]: f for f in rec["files"]}
    for name in ZENODO_FILES:
        f = files[name]
        fetch(f["links"]["self"], DATA / name, f["checksum"].removeprefix("md5:"))
    fetch(ANNOT, DATA / "neuron_annotations.tsv")
    print("done:", sorted(p.name for p in DATA.iterdir()))


if __name__ == "__main__":
    main()
