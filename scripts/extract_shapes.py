"""Sample synapse positions per MB neuron, for drawing neuron shapes in the viewer only.

    uv run python scripts/extract_shapes.py      # needs fetch_flywire.py --synapses and extract_mb.py

Streams data/flywire/flywire_synapses_783.feather (9.5 GB). A synapse point belongs to a neuron if the
neuron is its pre (pre_pt position) or post (post_pt position) partner. Each point is kept with a fixed
probability, then capped per neuron. Output data/mb/shapes.npz (gitignored, derived FlyWire data):
{group}_owner (index into the group's order in mb.npz) and {group}_xyz (nm). Not used by any experiment.
"""
from pathlib import Path

import numpy as np
import pyarrow.ipc as ipc

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "flywire" / "flywire_synapses_783.feather"
GROUPS = ["pn", "kc", "mbon", "dan", "apl"]
KEEP = dict(pn=0.04, kc=0.04, mbon=0.05, dan=0.08, apl=0.01)    # sampling probability per synapse end
CAP = dict(pn=120, kc=16, mbon=200, dan=60, apl=3000)           # max points per neuron
COLS = ["pre_pt_root_id", "post_pt_root_id"] + [f"{e}_pt_position_{a}" for e in ("pre", "post") for a in "xyz"]


def main():
    d = np.load(ROOT / "data" / "mb" / "mb.npz")
    ids = np.concatenate([d[f"id_{g}"] for g in GROUPS])
    gidx = np.concatenate([np.full(len(d[f"id_{g}"]), i) for i, g in enumerate(GROUPS)])
    nidx = np.concatenate([np.arange(len(d[f"id_{g}"])) for g in GROUPS])
    order = np.argsort(ids)
    ids, gidx, nidx = ids[order], gidx[order], nidx[order]
    keep_p = np.array([KEEP[g] for g in GROUPS])
    rng = np.random.default_rng(783)
    got = {g: [] for g in GROUPS}             # lists of (owner, xyz) arrays
    f = ipc.open_file(SRC)
    for b in range(f.num_record_batches):
        t = f.get_batch(b).select(COLS)
        for end in ("pre", "post"):
            rid = t.column(f"{end}_pt_root_id").to_numpy()
            j = np.clip(np.searchsorted(ids, rid), 0, len(ids) - 1)
            hit = ids[j] == rid
            hit &= rng.random(len(rid)) < keep_p[gidx[j]]
            if not hit.any():
                continue
            xyz = np.stack([t.column(f"{end}_pt_position_{a}").to_numpy()[hit] for a in "xyz"], 1)
            for gi in np.unique(gidx[j[hit]]):
                m = gidx[j[hit]] == gi
                got[GROUPS[gi]].append((nidx[j[hit]][m], xyz[m]))
        if b % 200 == 0:
            print(f"batch {b}/{f.num_record_batches}", flush=True)
    out = {}
    for g in GROUPS:
        own = np.concatenate([o for o, _ in got[g]])
        xyz = np.concatenate([x for _, x in got[g]]).astype(np.float32)
        sel = np.concatenate([rng.permutation(np.flatnonzero(own == n))[:CAP[g]] for n in np.unique(own)])
        out[f"{g}_owner"], out[f"{g}_xyz"] = own[sel].astype(np.int32), xyz[sel]
        n = len(d[f"id_{g}"])
        print(f"{g}: {len(sel):,} points, {len(np.unique(own))}/{n} neurons covered")
    np.savez_compressed(ROOT / "data" / "mb" / "shapes.npz", **out)
    # sanity: synapse cloud of KCs should sit near the KC annotation points (both nm)
    print("KC synapse mean (um):", (out["kc_xyz"].mean(0) / 1000).round(1),
          " KC annotation mean (um):", (d["pos_kc"].mean(0) / 1000).round(1))


if __name__ == "__main__":
    main()
