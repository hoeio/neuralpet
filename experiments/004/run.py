"""Experiment 004: experiment 001 with the ratio readout. See PLAN.md.

    uv run python experiments/004/run.py [--seeds 30] [--procs 10]
"""
import argparse
import importlib.util
import json
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


run001 = _load("run001", ROOT / "experiments" / "001" / "run.py")


def init():
    run001.READOUT = "ratio"


def job(args):
    return run001.run_one(args)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--seeds", type=int, default=30)
    a.add_argument("--procs", type=int, default=10)
    a = a.parse_args()
    W_pk, _, glom = run001.load()
    fr = {"sparse": 0.10, "literal": run001.literal_fraction(W_pk, glom)}
    jobs = [(s, c, sp, fr[sp]) for s in range(a.seeds) for c in run001.CONDS for sp in run001.SPARSITIES]
    with Pool(a.procs, initializer=init) as pool:
        rows = pool.map(job, jobs, chunksize=1)
    res = HERE / "results"
    res.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(res / "runs.csv", index=False)
    (res / "meta.json").write_text(json.dumps(dict(seeds=a.seeds, fractions=fr, readout="ratio",
                                                   eta=run001.ETA, n_odors=run001.N_ODORS)))
    _load("report001", ROOT / "experiments" / "001" / "report.py").main(
        res, ROOT / "reports" / "004", "Experiment 004 (ratio readout)")


if __name__ == "__main__":
    main()
