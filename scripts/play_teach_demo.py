"""Recorded teaching run for docs/PLAY.md: can the pet be taught to like one smell and dislike another
within a few minutes of interaction? Uses the play Game (same code path the server calls after
validation) on a temporary save dir, with the real FlyWire genome if present.

    uv run python scripts/play_teach_demo.py      # -> docs/play_teach.json, docs/play_teach.png

Protocol (fixed before running): 6 teaching rounds, each = offer A, wait 3 s, praise; wait 7 s;
offer B, wait 3 s, scold; wait 7 s (20 s of pet time per round, 2 min in total, ~24 actions).
Before and after: approach test for each smell = a toy of that smell is put 2.5 body lengths
to the pet's side; we record the change in the head's distance to it over 40 s (fresh copies of the
pet, so the test itself teaches nothing). A second test (1 BL, 90 s, 8 copies) was added after the
first showed nothing; see docs/PLAY.md. Pet time runs faster than wall time here; in the app it is real time.
"""
import copy
import types
import json
import tempfile
from pathlib import Path

import numpy as np

from neuralpet import creature as C
from neuralpet_play.game import Game

ROOT = Path(__file__).resolve().parents[1]
A, B, CTRL = "isopentyl acetate", "benzaldehyde", "linalool"


def approach(game, odor, secs=40.0, reps=4, dist=2.5):
    """Mean final head distance to a toy of `odor` placed 2.5 BL to the side (copies; no learning kept)."""
    d = []
    for r in range(reps):
        p = copy.deepcopy(game.pet)
        p.noise = np.random.default_rng([99, r])
        h, hd = p.body.head.copy(), p.body.heading
        side = np.array([-np.sin(hd), np.cos(hd)]) * (1 if r % 2 else -1)
        pos = (h + dist * side) % C.ARENA
        p.sources = [C.Source(pos, "toy", game.names.index(odor))]
        start = np.sqrt(C.Creature.dist2(p.body.head, pos))
        p.run(secs)
        d.append(np.sqrt(C.Creature.dist2(p.body.head, pos)) - start)
    return float(np.mean(d))


def main():
    g = Game(tempfile.mkdtemp(), cfg=dict(port=0, seed=20261108))
    g.pet.energy = 0.8
    trace, t0 = [], g.pet.t

    def rec(label):
        v = {o: g.pet.valence_of(g.odors[g.names.index(o)], n=10) for o in (A, B, CTRL)}
        trace.append(dict(t=round(g.pet.t - t0, 1), label=label, **v))

    before = {o: approach(g, o) for o in (A, B, CTRL)}
    g0 = types.SimpleNamespace(pet=copy.deepcopy(g.pet), names=g.names)   # the naive pet, for the second test
    rec("start")
    for r in range(6):
        g.act({"action": "offer_odor", "odor": A}); g.advance(3); g.act({"action": "praise"}); g.advance(7)
        rec(f"round {r + 1}: praised {A}")
        g.act({"action": "offer_odor", "odor": B}); g.advance(3); g.act({"action": "scold"}); g.advance(7)
        rec(f"round {r + 1}: scolded {B}")
    after = {o: approach(g, o) for o in (A, B, CTRL)}
    # second test, fixed before it was run (2026-11-08) after the first showed no difference: toy inside the plume
    near = dict(secs=90.0, reps=8, dist=1.0)
    before_near = {o: approach(g0, o, **near) for o in (A, B, CTRL)}
    after_near = {o: approach(g, o, **near) for o in (A, B, CTRL)}
    out = dict(genome=g.genome_label, liked=A, disliked=B, control=CTRL, trace=trace,
               approach_before=before, approach_after=after, approach_near=near,
               approach_near_before=before_near, approach_near_after=after_near, pet_time_s=round(g.pet.t - t0, 1),
               note="approach_* = change in head distance to a toy of that smell (negative = moved closer); approach_before/after: 2.5 BL, 40 s, mean of 4 copies; approach_near_*: settings in approach_near")
    (ROOT / "docs" / "play_teach.json").write_text(json.dumps(out, indent=1))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from neuralpet.plotstyle import COLORS, style
    style()
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    t = [x["t"] for x in trace]
    for i, (o, lab) in enumerate([(A, "praised"), (B, "scolded"), (CTRL, "never taught")]):
        ax[0].plot(t, [x[o] for x in trace], color=COLORS[i], lw=2, marker="o", ms=3, label=f"{o} ({lab})")
    ax[0].axhline(0, color="#52514e", lw=1)
    ax[0].set(xlabel="pet time (s)", ylabel="learned valence", title="Teaching: valence")
    ax[0].legend(frameon=False, fontsize=7)
    x = np.arange(3)
    ax[1].bar(x - 0.2, [before[o] for o in (A, B, CTRL)], 0.4, color="#b9b6ad", label="before")
    ax[1].bar(x + 0.2, [after[o] for o in (A, B, CTRL)], 0.4, color=COLORS[:3], label="after")
    ax[1].set_xticks(x, ["praised", "scolded", "control"])
    ax[1].axhline(0, color="#52514e", lw=1)
    ax[1].set(ylabel="Δ distance to the smell (BL, <0 = closer)", title="Behaviour: approach test")
    ax[1].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(ROOT / "docs" / "play_teach.png", dpi=150)
    print(json.dumps({k: v for k, v in out.items() if k != "trace"}, indent=1))
    print("final valence", trace[-1])




def table():
    """Markdown table for docs/PLAY.md from docs/play_teach.json (so PLAY.md never holds hand-typed numbers)."""
    d = json.loads((ROOT / "docs" / "play_teach.json").read_text())
    last = d["trace"][-1]
    rows = ["| smell | taught | valence after | Δ distance, 2.5 BL test before → after | Δ distance, 1 BL test before → after |",
            "|---|---|---|---|---|"]
    for o, lab in ((d["liked"], "praised"), (d["disliked"], "scolded"), (d["control"], "never")):
        rows.append(f"| {o} | {lab} | {last[o]:+.3f} | {d['approach_before'][o]:+.2f} → {d['approach_after'][o]:+.2f} | "
                    f"{d['approach_near_before'][o]:+.2f} → {d['approach_near_after'][o]:+.2f} |")
    rows.append("\nΔ distance = change in head distance to a toy of that smell (BL; negative = moved closer); "
                f"2.5 BL test: 40 s, 4 copies; 1 BL test: {d['approach_near']['secs']:.0f} s, {d['approach_near']['reps']} copies. "
                "\"before\" = the same pet before any teaching.")
    return "\n".join(rows)


if __name__ == "__main__":
    main()
    md = ROOT / "docs" / "PLAY.md"
    t = md.read_text()
    a, b = "<!-- teach-table -->", "<!-- /teach-table -->"
    t = t.replace("PLAY_TEACH_TABLE", a + b) if a not in t else t
    md.write_text(t.split(a)[0] + a + "\n" + table() + "\n" + b + t.split(b)[1])
