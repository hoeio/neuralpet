"""Exploratory (not pre-registered): do glomeruli with more KC partners respond more to / vary more
across DoOR odorants?    uv run python experiments/007/explore.py -> results/explore.txt"""
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from neuralpet.odors import door_odors

ROOT = Path(__file__).resolve().parents[2]
d = np.load(ROOT / "data" / "mb" / "mb.npz")
glom, names, W = d["glom_of_pn"], d["glom_names"], d["W_pnkc"]
O, _, _ = door_odors(names, glom)
units = [u for u in range(len(names)) if not names[u].startswith("m:")]
kc_edges = np.array([(W[glom == u] > 0).sum() for u in units])            # KC partners per glomerulus
n_pn = np.array([(glom == u).sum() for u in units])
resp = np.array([O[:, np.flatnonzero(glom == u)[0]] for u in units]).T    # odorants x glomeruli
has = resp.sum(0) > 0
L = [f"glomeruli with DoOR data: {has.sum()} of {len(units)}"]
for lab, x in [("mean response", resp.mean(0)), ("sd across odorants", resp.std(0)),
               ("fraction of odorants activating", (resp > 0).mean(0))]:
    r, p = spearmanr(kc_edges[has], x[has])
    r2, p2 = spearmanr((kc_edges / n_pn)[has], x[has])
    L.append(f"{lab}: Spearman vs KC edges per glomerulus r={r:.2f} (p={p:.3f}); "
             f"vs KC edges per PN r={r2:.2f} (p={p2:.3f})")
t = "\n".join(L)
(ROOT / "experiments" / "007" / "results" / "explore.txt").write_text(t + "\n")
print(t)
