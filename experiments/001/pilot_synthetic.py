# Run from repo root: uv run python experiments/001/pilot_synthetic.py
# Difficulty pilot on SYNTHETIC random wiring only (no FlyWire data).
import sys, numpy as np
sys.path.insert(0, "experiments/001")
import run
from neuralpet import mb
rng = np.random.default_rng(0)
npk, nkc, nm = 340, 2597, 48
W_pk = ((rng.random((npk, nkc)) < 7/npk) * rng.integers(5, 30, (npk, nkc))).astype(np.float32)
W_km = ((rng.random((nkc, nm)) < 0.3) * rng.integers(5, 15, (nkc, nm))).astype(np.float32)
glom = np.minimum(np.arange(npk) // 2, 150)
run.load = lambda: (W_pk, W_km, glom)
def mix_sets(rng_, glom_, rho):
    base = mb.make_odors(1, glom_, rng_)
    o = rho * base + (1 - rho) * mb.make_odors(run.N_ODORS, glom_, rng_)
    v = rng_.permutation(np.r_[np.ones(run.N_ODORS//2), np.zeros(run.N_ODORS//2)])
    return o.astype(np.float32), v
fr = run.literal_fraction(W_pk, glom)
for eta, n, rho in [(0.02, 20, 0.0), (0.02, 20, 0.5), (0.02, 20, 0.7), (0.05, 20, 0.7)]:
    run.ETA, run.N_ODORS = eta, n
    run.task_set = lambda r, g, rho=rho: mix_sets(r, g, rho)
    res = {}
    for sp, f in [("sparse", .1), ("literal", fr)]:
        rows = [run.run_one((s, "random", sp, f)) for s in range(4)]
        res[sp] = {k: round(float(np.mean([r[k] for r in rows])), 3) for k in ["M1_trials", "auc_sigma0.5", "auc_sigma1.0", "M3_interference", "aucB"]}
    print(eta, n, rho, res)
