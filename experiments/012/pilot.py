"""WP5 world pilot on SYNTHETIC wiring with reward modulation OFF (constant reward DA 0.5).

    uv run python experiments/012/pilot.py [--seeds 10]

Chooses arena size, food count and energy drain so that the creature keeps energy above zero most
of the time (criterion in experiments/012/PLAN.md). Synthetic wiring = experiments/010/pilot.py
`synth_random` (no connectome edges); odours = DoOR panel. Seeds 0-9, never used in 012's main run.
Writes experiments/012/pilot_results/pilot.csv.
"""
import argparse
import importlib.util
import itertools
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from neuralpet import creature as C

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("p010", HERE.parent / "010" / "pilot.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
LIFE = 1800.0


def job(a):
    seed, arena, n_food, base, eff, steer, r_eat, sigma, noise = a
    C.ARENA, C.N_FOOD, C.E_BASE, C.E_EFFORT, C.R_EAT, C.ODOR_SIGMA, C.STEER_NOISE = arena, n_food, base, eff, r_eat, sigma, noise
    W_pk, W_km = P.synth("synth_random", seed)
    c = C.Creature(W_pk, W_km, P.DOOR, seed=seed, da_mode="const", da_const=0.5, steering=steer)
    c.run(LIFE)
    E = np.array(c.energy_log)
    ev = [e for _, e, _ in c.events]
    food = [o for k, o in c.roles if k == "food"]
    tox = [o for k, o in c.roles if k == "toxic"]
    return dict(seed=seed, arena=arena, n_food=n_food, e_base=base, e_effort=eff, steering=steer, r_eat=r_eat, odor_sigma=sigma, steer_noise=str(noise),
                frac_pos=float((E > 0).mean()), mean_e=float(E.mean()), meals=ev.count("eat"), toxic=ev.count("toxic"),
                v_food=float(c.preferences(food).mean()), v_toxic=float(c.preferences(tox).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--procs", type=int, default=10)
    ap.add_argument("--round", type=int, default=2)
    a = ap.parse_args()
    grids = {1: itertools.product([6.0, 8.0], [3, 4], [0.001, 0.0015], [0.002], [True, False], [0.25], [2.0], [(0.1, 0.3)]),   # too harsh
             2: itertools.product([5.0, 6.0], [4, 6], [0.0003, 0.0005], [0.0006], [True, False], [0.4], [2.0], [(0.1, 0.3)]),   # food ~ toxic valence: plumes too wide
             3: itertools.product([5.0], [4], [0.0003, 0.0005], [0.0006], [True, False], [0.4], [0.8, 1.2], [(0.1, 0.3)]),   # still: circling (steer noise)
             4: itertools.product([5.0], [4], [0.0005], [0.0006], [True, False], [0.4], [0.8, 1.2], [(0.02, 0.05), (0.04, 0.1)]),   # wall-trapped 79% of the time
             5: itertools.product([5.0, 6.0], [4], [0.0005], [0.0006], [True, False], [0.4], [0.8, 1.2], [(0.04, 0.1)]),   # torus; repeated toxic hits per contact
             6: itertools.product([5.0, 6.0], [4], [0.0005], [0.0006], [True, False], [0.4], [0.8, 1.2], [(0.04, 0.1)]),   # one hit per episode; energy near ceiling
             7: itertools.product([6.0], [4], [0.001, 0.0015], [0.0012], [True, False], [0.4], [0.8], [(0.04, 0.1)])}   # final candidates
    grid = list(grids[a.round])
    jobs = [(s, *g) for g in grid for s in range(a.seeds)]
    with Pool(a.procs) as p:
        df = pd.DataFrame(p.map(job, jobs, chunksize=1))
    (HERE / "pilot_results").mkdir(exist_ok=True)
    df.to_csv(HERE / "pilot_results" / f"pilot_round{a.round}.csv", index=False)
    g = df.groupby(["arena", "n_food", "e_base", "e_effort", "r_eat", "odor_sigma", "steer_noise", "steering"]).agg(
        frac_pos_med=("frac_pos", "median"), mean_e=("mean_e", "mean"), meals=("meals", "mean"), toxic=("toxic", "mean"),
        v_food=("v_food", "mean"), v_toxic=("v_toxic", "mean")).round(3)
    pd.set_option("display.width", 200)
    print(g.to_string())


if __name__ == "__main__":
    main()
