"""Exploratory (not pre-registered): how much of the PN->KC edge mass sits on PNs that get DoOR input,
real vs PN-row-permuted?    uv run python experiments/008/explore.py -> results/explore.txt"""
from pathlib import Path

import numpy as np

from neuralpet.odors import door_odors

ROOT = Path(__file__).resolve().parents[2]
d = np.load(ROOT / "data" / "mb" / "mb.npz")
glom, names, W = d["glom_of_pn"], d["glom_names"], d["W_pnkc"]
O, _, _ = door_odors(names, glom)
live = O.sum(0) > 0                                   # PNs with any DoOR input
deg = (W > 0).sum(1)
rng = np.random.default_rng(0)
perm = np.array([deg[rng.permutation(len(deg))][live].sum() for _ in range(10000)]) / deg.sum()
L = [f"PNs with DoOR input: {live.sum()} of {len(live)}",
     f"fraction of KC edges from those PNs: real {deg[live].sum() / deg.sum():.3f}; "
     f"row-permuted mean {perm.mean():.3f} [2.5-97.5%: {np.percentile(perm, 2.5):.3f}, {np.percentile(perm, 97.5):.3f}]",
     f"mean out-degree: live PNs {deg[live].mean():.1f}, silent PNs {deg[~live].mean():.1f}"]
t = "\n".join(L)
(ROOT / "experiments" / "008" / "results" / "explore.txt").write_text(t + "\n")
print(t)
