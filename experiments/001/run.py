"""Experiment 001: real vs degree-shuffled vs random MB wiring. See PLAN.md.

    uv run python experiments/001/run.py [--seeds 30] [--procs 10]

Writes raw results to experiments/001/results/ (never edited by hand), then runs report.py.
"""
import argparse
import json
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from neuralpet import mb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"
CONDS = ["random", "shuffle", "real"]
SPARSITIES = ["sparse", "literal"]
ETA, SIG, N_ODORS, BLOCKS, SNAP, BLOCKS_B, CRIT = 0.02, 0.2, 20, 20, 10, 10, 0.9
TEST_SIGMAS = [0.0, 0.5, 1.0, 2.0]
READOUT = "pooled"   # "ratio" = R(W_t)/R(W_0) on the same KC code (experiment 004)
W_INIT = {}          # per-process initial KC->MBON weights, set in run_one


def cond_id(cond):
    """Stable id for the wiring rng. 001 strings keep their original ids (0, 1, 2)."""
    if isinstance(cond, str):
        return CONDS.index(cond)
    return 10 + 3 * CONDS.index(cond[0]) + CONDS.index(cond[1])


def load():
    d = np.load(ROOT / "data" / "mb" / "mb.npz")
    return d["W_pnkc"], d["W_kcmbon"], d["glom_of_pn"]


def literal_fraction(W_pk, glom, n=500):
    odors = mb.make_odors(n, glom, np.random.default_rng(12345))
    return float(((odors @ W_pk) > 0).mean())


def evaluate(odors, val, W_pk, W_km, frac, sigma, reps, rng):
    X, y = np.repeat(odors, reps, 0), np.repeat(val, reps)
    kc = mb.kc_code(mb.pn_rates(X, sigma, rng), W_pk, frac)
    R = mb.mbon_out(kc, W_km)
    if READOUT == "ratio":
        R = R / np.maximum(mb.mbon_out(kc, W_INIT["W"]), 1e-9)
    return mb.auc(R[y == 1], R[y == 0]), float(kc.mean())


def train_block(odors, val, W_pk, W_km, frac, rng):
    for i in rng.permutation(len(odors)):
        kc = mb.kc_code(mb.pn_rates(odors[i:i + 1], SIG, rng), W_pk, frac)[0]
        mb.learn(W_km, kc, float(val[i]), ETA)


def task_set(rng, glom):
    odors = mb.make_odors(N_ODORS, glom, rng)
    val = rng.permutation(np.r_[np.ones(N_ODORS // 2), np.zeros(N_ODORS - N_ODORS // 2)])
    return odors, val


def run_one(args):
    seed, cond, sparsity, frac = args
    W_pk0, W_km0, glom = load()
    W_pk, W_km = mb.make_wiring(cond, W_pk0, W_km0, np.random.default_rng([seed, cond_id(cond)]))
    W_km = W_km.astype(np.float64).copy()
    W_INIT["W"] = W_km.copy()
    task = np.random.default_rng([seed, 99])          # same odours/valences in every condition
    noise = np.random.default_rng([seed, 7])          # same noise stream in every condition
    A, vA = task_set(task, glom)
    B, vB = task_set(task, glom)

    curve = [evaluate(A, vA, W_pk, W_km, frac, SIG, 10, noise)[0]]
    for b in range(BLOCKS):
        train_block(A, vA, W_pk, W_km, frac, noise)
        curve.append(evaluate(A, vA, W_pk, W_km, frac, SIG, 10, noise)[0])
        if b + 1 == SNAP:
            W_snap = W_km.copy()
    hit = [i for i, a in enumerate(curve) if a >= CRIT]
    m1 = hit[0] * N_ODORS if hit else (BLOCKS * N_ODORS + 10)

    row = dict(seed=seed, wiring=cond, sparsity=sparsity, frac=frac, M1_trials=m1, M1_censored=not hit,
               edge_overlap_pk=float(((W_pk > 0) & (W_pk0 > 0)).sum() / (W_pk0 > 0).sum()),
               edge_overlap_km=float(((W_km > 0) & (W_km0 > 0)).sum() / (W_km0 > 0).sum()))
    for s in TEST_SIGMAS:
        a, act = evaluate(A, vA, W_pk, W_snap, frac, s, 10, noise)
        row[f"auc_sigma{s}"] = a
        row[f"kc_active_sigma{s}"] = act
    row["M2_auc_sigma1.0"] = row["auc_sigma1.0"]

    W = W_snap.copy()
    before = evaluate(A, vA, W_pk, W, frac, SIG, 10, noise)[0]
    for _ in range(BLOCKS_B):
        train_block(B, vB, W_pk, W, frac, noise)
    after = evaluate(A, vA, W_pk, W, frac, SIG, 10, noise)[0]
    row.update(aucA_before=before, aucA_after=after, M3_interference=before - after,
               aucB=evaluate(B, vB, W_pk, W, frac, SIG, 10, noise)[0], curve=json.dumps(curve))
    return row


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=30)
    p.add_argument("--procs", type=int, default=10)
    a = p.parse_args()
    W_pk, _, glom = load()
    fr = {"sparse": 0.10, "literal": literal_fraction(W_pk, glom)}
    print("KC fractions:", fr)
    jobs = [(s, c, sp, fr[sp]) for s in range(a.seeds) for c in CONDS for sp in SPARSITIES]
    t = time.time()
    with Pool(a.procs) as pool:
        rows = pool.map(run_one, jobs, chunksize=1)
    print(f"{len(jobs)} runs in {time.time() - t:.1f}s")
    OUT.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "runs.csv", index=False)
    (OUT / "meta.json").write_text(json.dumps(dict(
        seeds=a.seeds, fractions=fr, eta=ETA, sigma_train=SIG, n_odors=N_ODORS, blocks=BLOCKS,
        snap=SNAP, blocks_B=BLOCKS_B, criterion=CRIT, wall_s=round(time.time() - t, 1)), indent=1))
    subprocess.run([sys.executable, str(HERE / "report.py")], check=True)


if __name__ == "__main__":
    main()
