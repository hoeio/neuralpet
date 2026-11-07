"""WP3 difficulty pilot on SYNTHETIC wiring only (no FlyWire connectivity is used).

    uv run python experiments/010/pilot.py [--seeds 8]

Uses from the real data only the PN -> glomerulus labels (to map DoOR/Hallem odours onto PNs) and the
layer sizes. W_pk, W_km are random. Two synthetic circuits:
  synth_random   : each KC samples ~4 PNs uniformly (real mean in-degree 4.05)
  synth_random2  : (grid 3) a second independent synth_random draw; synth_random - synth_random2 per
                   seed estimates the SD of a paired difference between two equivalent wirings (power)
  synth_degraded : each KC samples ~4 PNs from a fixed random 15% of PNs (a deliberately worse
                   circuit, used only to show that the metrics can separate circuits)
Writes experiments/010/pilot_results/pilot_grid<N>.csv and prints a summary per parameter set.
"""
import argparse
import itertools
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from neuralpet import mb, task
from neuralpet.odors import door_odors, hallem_odors

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = np.load(ROOT / "data" / "mb" / "mb.npz")
GLOM, NAMES = D["glom_of_pn"], D["glom_names"]
N_PN, N_KC, N_MB = len(GLOM), 2597, 48
DOOR, KEYS, _ = door_odors(NAMES, GLOM)
HALL = hallem_odors(NAMES, GLOM, exclude=KEYS)[0]


def synth(kind, seed):
    r = np.random.default_rng([seed, 556 if kind == "synth_random2" else 555])
    allowed = np.arange(N_PN) if kind != "synth_degraded" else r.choice(N_PN, int(0.15 * N_PN), replace=False)
    W_pk = np.zeros((N_PN, N_KC), np.float32)
    for k in range(N_KC):
        d = max(1, r.poisson(4.05))
        W_pk[r.choice(allowed, min(d, len(allowed)), replace=False), k] = r.integers(5, 30, min(d, len(allowed)))
    W_km = ((r.random((N_KC, N_MB)) < 7485 / (N_KC * N_MB)) * r.integers(5, 12, (N_KC, N_MB))).astype(np.float32)
    return W_pk, W_km


def job(a):
    seed, kind, source, sp, prm = a
    W_pk, W_km = synth(kind, seed)
    r = np.random.default_rng([seed, 11])
    n = prm["n"]
    pool = {"random": lambda: mb.make_odors(2 * n, GLOM, r), "door": lambda: DOOR, "hallem": lambda: HALL}[source]()
    A, B = task.pick_sets(pool, n, r)
    frac = 0.10 if sp == "sparse" else float(((mb.make_odors(300, GLOM, np.random.default_rng(1)) @ W_pk) > 0).mean())
    out = task.run(W_pk, W_km, A, B, seed, frac, prm)
    c = out.pop("curve")
    return dict(seed=seed, kind=kind, source=source, sparsity=sp, **{k: v for k, v in prm.items()},
                **out, auc_b1=c[1], auc_b0=c[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--grid", type=int, default=1)
    a = ap.parse_args()
    grids = {1: itertools.product([0.005, 0.01, 0.02], [0.02, 0.05, 0.1], [12], [1.0]),        # round 1
             2: itertools.product([0.02, 0.04], [0.01, 0.02], [6, 8], [0.5, 1.0]),             # round 2
             3: itertools.product([0.02], [0.01], [8], [1.0])}                                 # chosen, 24 seeds
    grid = [dict(task.P, eta=e, sig_out=s, n=n, sig_test=t) for e, s, n, t in grids[a.grid]]
    jobs = [(s, k, so, sp, g) for g in grid for s in range(a.seeds) for k in ["synth_random", "synth_degraded"] + (["synth_random2"] if a.grid == 3 else [])
            for so in (["random", "door", "hallem"] if a.grid < 3 else ["door", "hallem"]) for sp in ["sparse", "literal"]]
    with Pool(10) as p:
        df = pd.DataFrame(p.map(job, jobs, chunksize=4))
    (HERE / "pilot_results").mkdir(exist_ok=True)
    df.to_csv(HERE / "pilot_results" / f"pilot_grid{a.grid}.csv", index=False)
    g = df.groupby(["eta", "sig_out", "n", "sig_test", "kind", "source", "sparsity"])[["auc_b1", "aulc", "plateau", "m2", "m3"]].mean().round(3)
    pd.set_option("display.width", 200)
    print(g.to_string())


if __name__ == "__main__":
    main()
