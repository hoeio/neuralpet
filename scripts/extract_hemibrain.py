"""Extract the mushroom-body sub-circuit of the hemibrain v1.2 (an independent fly) into data/mb/.

    uv run python scripts/fetch_hemibrain.py && uv run python scripts/extract_hemibrain.py

Same selection rules as scripts/extract_mb.py, translated to hemibrain type names (docs/MB_EXTRACTION.md):
  KC   = type 'KC*' (all are right-hemisphere, instance '*_R')
  MBON = type 'MBON*', instance '*_R';  DAN = type 'PAM*' or 'PPL1*', instance '*_R';  APL = type 'APL', '*_R'
  PN   = type containing 'PN' with >= 1 thresholded edge onto a selected KC
  glomerulus = type prefix before '_' for uniglomerular PNs; types starting 'M_' or with '+' in the
  prefix are multiglomerular and each such PN is its own input unit (as for FlyWire).
Edges: traced-total-connections (synapse counts), kept if weight >= 5 (same threshold as FlyWire).
No positions (the adjacency export has none). Writes data/mb/mb_hemibrain.npz (gitignored).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HB = ROOT / "data" / "hemibrain" / "exported-traced-adjacencies-v1.2"
OUT = ROOT / "data" / "mb"
SYN_THRESHOLD = 5


def main():
    n = pd.read_csv(HB / "traced-neurons.csv").fillna({"type": "", "instance": ""})
    R = n[n.instance.str.endswith("_R")]
    ids = {"kc": R[R.type.str.startswith("KC")], "mbon": R[R.type.str.startswith("MBON")],
           "dan": R[R.type.str.startswith(("PAM", "PPL1"))], "apl": R[R.type == "APL"]}
    ids = {k: v.sort_values("bodyId") for k, v in ids.items()}
    c = pd.read_csv(HB / "traced-total-connections.csv")
    c = c[c.weight >= SYN_THRESHOLD]
    kc_set = set(ids["kc"].bodyId)
    to_kc = c[c.bodyId_post.isin(kc_set)]
    typ = n.set_index("bodyId").type
    pre = pd.Index(sorted(set(to_kc.bodyId_pre)))
    ids["pn"] = n[n.bodyId.isin(pre[typ.reindex(pre).str.contains("PN").to_numpy()])].sort_values("bodyId")
    idx = {k: {b: i for i, b in enumerate(v.bodyId)} for k, v in ids.items()}

    def mat(s, d):
        e = c[c.bodyId_pre.isin(idx[s]) & c.bodyId_post.isin(idx[d])]
        M = np.zeros((len(idx[s]), len(idx[d])), np.float32)
        M[e.bodyId_pre.map(idx[s]), e.bodyId_post.map(idx[d])] = e.weight
        return M

    M = {f"W_{s}{d}": mat(s, d) for s, d in [
        ("pn", "kc"), ("kc", "mbon"), ("dan", "kc"), ("kc", "apl"), ("apl", "kc"), ("kc", "kc"),
        ("kc", "dan"), ("dan", "mbon")]}
    pt = ids["pn"].type.to_numpy()
    prefix = np.array([t.split("_")[0] for t in pt])
    multi = np.array([t.startswith("M_") or "+" in p for t, p in zip(pt, prefix)])
    glom = np.where(multi, "m:" + ids["pn"].bodyId.astype(str).to_numpy(), prefix)
    glom_names, glom_of_pn = np.unique(glom, return_inverse=True)

    counts = {k: int(len(v)) for k, v in ids.items()}
    counts["n_glomeruli_or_mPN"] = int(len(glom_names))
    counts["n_uniglomerular_pn"] = int((~multi).sum())
    for k, W in M.items():
        counts[f"{k}_edges"] = int((W > 0).sum())
        counts[f"{k}_synapses"] = int(W.sum())
    kc_in_total = to_kc.weight.sum()
    counts["frac_kc_input_syn_from_PN"] = round(float(to_kc[to_kc.bodyId_pre.isin(idx["pn"])].weight.sum() / kc_in_total), 3)
    counts["kc_with_no_pn_input"] = int((M["W_pnkc"].sum(0) == 0).sum())
    counts["kc_with_no_mbon_output"] = int((M["W_kcmbon"].sum(1) == 0).sum())
    counts["pn_inputs_per_kc_mean"] = round(float((M["W_pnkc"] > 0).sum(0).mean()), 2)
    counts["syn_threshold"] = SYN_THRESHOLD
    counts["kc_types"] = ids["kc"].type.value_counts().to_dict()
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "mb_hemibrain.npz", glom_of_pn=glom_of_pn, glom_names=glom_names.astype(str),
                        kc_type=ids["kc"].type.to_numpy().astype(str), dan_type=ids["dan"].type.to_numpy().astype(str),
                        mbon_type=ids["mbon"].type.to_numpy().astype(str), pn_type=pt.astype(str),
                        **{f"id_{k}": v.bodyId.to_numpy() for k, v in ids.items()}, **M)
    (OUT / "counts_hemibrain.json").write_text(json.dumps(counts, indent=1))
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
