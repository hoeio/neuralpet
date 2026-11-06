"""Extract the right-hemisphere mushroom-body sub-circuit from FlyWire v783 into data/mb/.

Selection (docs/MB_EXTRACTION.md): annotations from Schlegel et al. 2024 (cell_class column).
  KC   = cell_class 'Kenyon_Cell', side right
  MBON = cell_class 'MBON', side right
  DAN  = cell_class 'DAN', side right
  APL  = cell_type 'APL', side right
  PN   = cell_class 'ALPN' (either soma side) with >= 1 thresholded edge onto a selected KC
Edges: proofread_connections_783 summed over neuropils, kept if syn_count >= SYN_THRESHOLD.
Writes data/mb/mb.npz (gitignored) and prints counts (copied into docs/MB_EXTRACTION.md).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "data" / "flywire"
OUT = ROOT / "data" / "mb"
SYN_THRESHOLD = 5


def main():
    a = pd.read_csv(FW / "neuron_annotations.tsv", sep="\t", low_memory=False)
    r = a[a.side == "right"]
    groups = {
        "kc": r[r.cell_class == "Kenyon_Cell"],
        "mbon": r[r.cell_class == "MBON"],
        "dan": r[r.cell_class == "DAN"],
        "apl": r[r.cell_type == "APL"],
    }
    pn_all = a[a.cell_class == "ALPN"]
    ids = {k: v.root_id.to_numpy() for k, v in groups.items()}

    c = pd.read_feather(FW / "proofread_connections_783.feather")
    print("connection columns:", list(c.columns), len(c))
    pre, post = "pre_pt_root_id", "post_pt_root_id"
    c = c.groupby([pre, post], as_index=False).syn_count.sum()
    c = c[c.syn_count >= SYN_THRESHOLD]

    kc_set = set(ids["kc"])
    to_kc = c[c[post].isin(kc_set)]
    pn_ids = np.array(sorted(set(to_kc[pre]) & set(pn_all.root_id)))
    ids["pn"] = pn_ids

    def mat(src, dst):
        si = {x: i for i, x in enumerate(ids[src])}
        di = {x: i for i, x in enumerate(ids[dst])}
        e = c[c[pre].isin(si) & c[post].isin(di)]
        M = np.zeros((len(si), len(di)), np.float32)
        M[e[pre].map(si), e[post].map(di)] = e.syn_count
        return M

    M = {f"W_{s}{d}": mat(s, d) for s, d in [
        ("pn", "kc"), ("kc", "mbon"), ("dan", "kc"), ("kc", "apl"), ("apl", "kc"), ("kc", "kc")]}

    # glomerulus label per PN: uniglomerular 'DA1_lPN' -> 'DA1'; others keep their own cell_type id
    pt = pn_all.set_index("root_id").loc[pn_ids]
    glom = np.where(pt.cell_sub_class == "uniglomerular",
                    pt.cell_type.str.split("_").str[0], "m:" + pt.index.astype(str))
    glom_names, glom_of_pn = np.unique(glom, return_inverse=True)

    # how much of all KC input comes from the selected PNs?
    kc_in_total = to_kc.syn_count.sum()
    kc_in_pn = to_kc[to_kc[pre].isin(set(pn_ids))].syn_count.sum()

    counts = {k: int(len(v)) for k, v in ids.items()}
    counts["n_glomeruli_or_mPN"] = int(len(glom_names))
    counts["n_uniglomerular_pn"] = int((pt.cell_sub_class == "uniglomerular").sum())
    for k, W in M.items():
        counts[f"{k}_edges"] = int((W > 0).sum())
        counts[f"{k}_synapses"] = int(W.sum())
    counts["frac_kc_input_syn_from_ALPN"] = round(float(kc_in_pn / kc_in_total), 3)
    counts["kc_with_no_pn_input"] = int((M["W_pnkc"].sum(0) == 0).sum())
    counts["kc_with_no_mbon_output"] = int((M["W_kcmbon"].sum(1) == 0).sum())
    counts["pn_inputs_per_kc_mean"] = round(float((M["W_pnkc"] > 0).sum(0).mean()), 2)
    counts["syn_threshold"] = SYN_THRESHOLD
    counts["kc_types"] = groups["kc"].cell_type.value_counts().to_dict()

    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "mb.npz", glom_of_pn=glom_of_pn, glom_names=glom_names,
                        kc_type=groups["kc"].cell_type.fillna("").to_numpy().astype(str),
                        **{f"id_{k}": v for k, v in ids.items()}, **M)
    (OUT / "counts.json").write_text(json.dumps(counts, indent=1))
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
