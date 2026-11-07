"""EXPLORATORY (post hoc, after experiment 012; not pre-registered): does learned valence steer the
creature towards or away from a smell under the registered steering gain?

The KC->MBON weights are scaled by (1 + 0.3*sign) so the learned valence is exactly +-0.3 for every odour;
a toy of one DoOR odorant sits 1 BL to the left or right of the head; 16 runs of 90 s per cell; outcome =
change in head distance to the toy (BL, torus minimum image; negative = moved closer). Gains: the
registered K_CONTRAST = 25 and 4x (100, the play app's value). Steering off as reference.

    uv run python experiments/explore/steer_check.py   ->  experiments/explore/results/steer_check.csv
"""
import copy
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from neuralpet import creature as C

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("r012", ROOT / "experiments" / "012" / "run.py")
r012 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r012)
RUNS, SECS, DIST = 16, 90.0, 1.0
# isopentyl acetate, benzaldehyde, linalool (InChIKeys as in the DoOR tables); the first version of this
# script used odour index 0, which is water (no receptor response), and was discarded before reporting.
ODORS = {"isopentyl acetate": "MLFHJEHSLIIPHL-UHFFFAOYSA-N", "benzaldehyde": "HUMNYLRZRPPJDN-UHFFFAOYSA-N",
         "linalool": "CDOSHBSSFJOMGT-UHFFFAOYSA-N"}


def one(gain, sign, steering, r, odor):
    C.K_CONTRAST = gain
    D = r012.data()
    p = C.Creature(D["W_pk"], D["W_km"], D["odors"], seed=5000 + r, mortal=False, steering=steering)
    p.W = p.W * (1 + 0.3 * sign)
    p.energy = 0.8
    h, hd = p.body.head.copy(), p.body.heading
    side = np.array([-np.sin(hd), np.cos(hd)]) * (1 if r % 2 else -1)
    pos = (h + DIST * side) % C.ARENA
    p.sources = [C.Source(pos, "toy", odor)]
    d0 = np.sqrt(C.Creature.dist2(p.body.head, pos))
    p.run(SECS)
    return np.sqrt(C.Creature.dist2(p.body.head, pos)) - d0


def main():
    k0 = C.K_CONTRAST
    from neuralpet.odors import door_odors
    d = np.load(ROOT / "data" / "mb" / "mb.npz")
    keys = list(door_odors(d["glom_names"], d["glom_of_pn"])[1])
    idx = {n: keys.index(k) for n, k in ODORS.items()}
    rows = []
    for gain in (25.0, 100.0):
        for sign in (+1, -1):
            for steering in (True, False):
                if not steering and gain != 25.0:
                    continue
                for name, i in idx.items():
                    for r in range(RUNS):
                        rows.append(dict(gain=gain, valence=0.3 * sign, steering=steering, odor=name, run=r,
                                         d_dist=one(gain, sign, steering, r, i)))
    C.K_CONTRAST = k0
    out = ROOT / "experiments" / "explore" / "results"
    out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / "steer_check.csv", index=False)
    print(df.groupby(["gain", "valence", "steering"]).d_dist.agg(["mean", "sem"]).round(3))


if __name__ == "__main__":
    main()
