"""Exploratory checks after 003 (not pre-registered; they motivated experiment 004).

    uv run python experiments/003/explore.py   -> experiments/003/results/explore.txt

One wiring sample per control (rng [0, 500]), 100-200 v1 odours, sparse f = 0.10.
"""
import importlib.util
from pathlib import Path

import numpy as np

from neuralpet import mb

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("run001", ROOT / "experiments" / "001" / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def main():
    W_pk, W_km, glom = run.load()
    kc_type = np.load(ROOT / "data" / "mb" / "mb.npz")["kc_type"]
    odors = mb.make_odors(200, glom, np.random.default_rng(777))
    G = np.zeros((glom.max() + 1, len(glom)))
    G[glom, np.arange(len(glom))] = 1
    L = ["## 1. Input heterogeneity, promiscuous KCs, code reliability (PN->KC only)"]
    for c in ["real", "shuffle", "random"]:
        W, _ = mb.make_wiring(c, W_pk, W_km, np.random.default_rng([0, 500]))
        tot = W.sum(0)[W.sum(0) > 0]
        B = W > 0
        m = B.sum(0) > 0
        units = (G @ B > 0).sum(0)[m].mean()
        out = [f"{c}: KC total-input CV {tot.std() / tot.mean():.2f}; distinct input units/KC {units:.2f}"]
        for s in [0.0, 0.2]:
            kc = mb.kc_code(mb.pn_rates(odors, s, np.random.default_rng(1)), W, 0.1)
            p = kc.mean(0)
            out.append(f"sigma {s}: KCs firing for >30% of odours {(p > 0.3).mean():.3f}")
        for s in [0.2, 1.0]:
            a = mb.kc_code(mb.pn_rates(odors[:100], s, np.random.default_rng(1)), W, 0.1)
            b = mb.kc_code(mb.pn_rates(odors[:100], s, np.random.default_rng(2)), W, 0.1)
            j = ((a * b).sum(1) / np.maximum(((a + b) > 0).sum(1), 1)).mean()
            out.append(f"same-odour Jaccard at sigma {s}: {j:.3f}")
        L.append("; ".join(out))
    L.append("\n## 2. KC type: mean KC->MBON output synapses and PN input synapses (real)")
    for k in ["KCg-m", "KCab", "KCapbp-m", "KCapbp-ap1", "KCapbp-ap2", "KCg-d", "KCab-p"]:
        sel = kc_type == k
        L.append(f"{k} (n={sel.sum()}): MBON out {W_km.sum(1)[sel].mean():.1f}, PN in {W_pk.sum(0)[sel].mean():.1f}")
    L.append("\n## 3. Spread of naive pooled MBON drive R0 across odours (CV), noise-free")
    for pk in ["real", "shuffle"]:
        for km in ["real", "shuffle"]:
            W, K = mb.make_wiring((pk, km), W_pk, W_km, np.random.default_rng([0, 500]))
            R = mb.mbon_out(mb.kc_code(odors, W, 0.1), K)
            L.append(f"PN->KC {pk}, KC->MBON {km}: R0 CV = {R.std() / R.mean():.3f}")
    t = "\n".join(L)
    (ROOT / "experiments" / "003" / "results" / "explore.txt").write_text(t + "\n")
    print(t)


if __name__ == "__main__":
    main()
