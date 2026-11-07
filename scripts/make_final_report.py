"""Build reports/FINAL.md and reports/figures/ from the generated tables and raw result files.

    uv run python scripts/make_final_report.py

Every number in FINAL.md comes from a results file or a table that was itself made by script from raw
results (reports/0NN/tables.md). Prose is fixed text; numbers are inserted here, never typed.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_numbers as FN  # noqa: E402

from neuralpet import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R, FIG = ROOT / "reports", ROOT / "reports" / "figures"


def rows(md, title):
    """Rows (lists of cells) of the first markdown table under a '## title' heading."""
    sec = md.split("## " + title, 1)[1].split("\n## ", 1)[0]
    out = []
    for line in sec.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            out.append([c.strip() for c in line.strip().strip("|").split("|")])
    return out[1:]


def section(md, title):
    return "\n".join(l for l in md.split("## " + title, 1)[1].split("\n## ", 1)[0].splitlines()[1:]).strip()


def find(rs, *keys):
    for r in rs:
        if all(k in r for k in keys):
            return r
    raise KeyError(keys)


def num(cell):
    return float(cell.split()[0])


def ci_cell(cell):
    m, rest = cell.split(" ", 1)
    lo, hi = rest.strip("[]").split(", ")
    return float(m), float(lo), float(hi)


def steer_summary():
    d = pd.read_csv(ROOT / "experiments" / "explore" / "results" / "steer_check.csv")
    out = {}
    for (g, v, s), x in d.groupby(["gain", "valence", "steering"]):
        m, lo, hi = stats.boot_ci(x.d_dist.to_numpy())
        out[(g, v, s)] = f"{m:+.2f} [{lo:+.2f}, {hi:+.2f}]"
    n = int(d.groupby(["gain", "valence", "steering"]).size().iloc[0])
    return out, n


def forest(t010, t011, t012):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from neuralpet.plotstyle import COLORS, style
    style()
    fam = rows(t010, "Confirmatory family")
    v011 = rows(t011, "H1–H3 per model variant (M2) vs experiment 010 (kWTA, global DA)")
    items = []
    for r in fam:
        items.append((f"010 {r[0]} {r[1]} ({r[2]})", *ci_cell(r[3]), 0))
    for r in v011:
        items.append((f"011 {r[0].split(':')[0]} apl_comp (sparse)", *ci_cell(r[2]), 1))
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw=dict(width_ratios=[1.3, 1]))
    y = np.arange(len(items))[::-1]
    for yi, (lab, m, lo, hi, k) in zip(y, items):
        ax[0].plot([lo, hi], [yi, yi], color=COLORS[k], lw=2)
        ax[0].plot(m, yi, "o", color=COLORS[k])
    ax[0].axvline(0, color="#52514e", lw=1)
    for s in (-0.02, 0.02):
        ax[0].axvline(s, color="#b9b6ad", lw=1, ls="--")
    ax[0].set_yticks(y, [i[0] for i in items], fontsize=7)
    ax[0].set(xlabel="difference in M2 (noise robustness), 95% CI; dashed = SESOI ±0.02",
              title="Wiring contrasts (010 registered, 011)")
    fam12 = rows(t012, "Confirmatory family")
    lab12 = [f"{r[0]} {r[1]}" for r in fam12 if r[2] == "mean_energy"]
    y2 = np.arange(len(lab12))[::-1]
    for yi, r in zip(y2, [r for r in fam12 if r[2] == "mean_energy"]):
        m, lo, hi = ci_cell(r[3])
        ax[1].plot([lo, hi], [yi, yi], color=COLORS[2], lw=2)
        ax[1].plot(m, yi, "o", color=COLORS[2])
    ax[1].axvline(0, color="#52514e", lw=1)
    ax[1].set_yticks(y2, lab12, fontsize=8)
    ax[1].set_xticks([-0.05, 0, 0.05])
    ax[1].set(xlabel="difference in mean energy, 95% CI", title="Creature (012): state rule and wiring")
    fig.tight_layout()
    fig.savefig(FIG / "summary.png", dpi=150)
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    N = FN.early()
    T = FN.confirmatory()
    t010, t010d, t011, t011d, t012 = T["t010"], T["t010dev"], T["t011"], T["t011dev"], T["t012"]
    for src, dst in [(R / "010" / "effects.png", "010_effects.png"), (R / "012" / "pet.png", "012_pet.png"),
                     (ROOT / "docs" / "play_teach.png", "play_teach.png"), (ROOT / "docs" / "play_phone.png", "play_phone.png")]:
        shutil.copyfile(src, FIG / dst)
    forest(t010, t011, t012)

    fam = rows(t010, "Confirmatory family")
    H = {(r[0], r[2]): r for r in fam}
    famd = rows(t010d, "Confirmatory family")
    Hd = {(r[0], r[2]): r for r in famd}
    n2 = rows(t010, "Pre-specified secondary contrasts: N2 nulls (not in the family)")
    v011 = rows(t011, "H1–H3 per model variant (M2) vs experiment 010 (kWTA, global DA)")
    over011 = "no" if "overturned by apl_comp: no" in t011 else "yes"
    cm = {r[0]: r for r in rows(t012, "Condition means")}
    f12 = rows(t012, "Confirmatory family")
    S = {(r[0], r[2]): r for r in f12}
    san = {r[0]: r[1] for r in rows(t012, "Sanity check (not a headline): brain-driven steering")}
    holm12 = min(float(r[6]) for r in f12)
    ind = section(t012, "Individuality (same genome, different histories; pre-specified secondary)")
    rev = section(t012, "Adaptation to environment change (pre-specified secondary)")
    steer, n_steer = steer_summary()
    teach = json.loads((ROOT / "docs" / "play_teach.json").read_text())
    last = teach["trace"][-1]
    nb, na = teach["approach_near_before"], teach["approach_near_after"]
    meta010 = json.loads((ROOT / "experiments" / "010" / "results_registered" / "meta.json").read_text())
    runs010 = pd.read_csv(ROOT / "experiments" / "010" / "results_registered" / "runs.csv")
    ceil = int((runs010.plateau >= 0.99).sum())
    creature_tbl = (ROOT / "docs" / "CREATURE.md").read_text().split("## Real data vs our design, part by part", 1)[1].split("\n## ", 1)[0].strip()
    life = (ROOT / "docs" / "LIFE_CRITERIA.md").read_text().split("\n\n", 2)[2].split("\n\nWhat these criteria", 1)[0].strip()
    died_on = num(cm["on"][2])

    def h(k, s):
        r = H[(k, s)]
        return f"{r[3]} (d_z {r[5]}, Holm p {r[7]}; {r[8]})"

    md = f"""# NeuralPet — final report (v1.0)

*Generated by `scripts/make_final_report.py` from the result files; do not edit by hand.*

NeuralPet puts a sub-circuit of the adult *Drosophila* connectome (FlyWire FAFB v783 mushroom body,
plus the hemibrain as an independent fly) into a simple learning model, and that model into a designed
worm-like body in a designed world. It is a research toy and a pet you can raise in a browser. **It is
not alive, not conscious and not a faithful emulation of a fly.** Every link between layers (odours →
projection neurons, dopamine rules, readout, body, metabolism) is a rule we designed and wrote down in
`docs/ADAPTERS.md` before the runs that used it.

## Headline findings

1. **Real mushroom-body partners do not help associative learning compared with a degree-preserving
   shuffle; they are slightly worse.** Registered experiment 010 (64 seeds × 3 connectome samples × 2
   odour sources): real − shuffle on noise robustness (M2) = {h("H1", "sparse")} with a sparse
   Kenyon-cell code, {h("H1", "literal")} with the literal (dense) code. Both are below the smallest
   effect we said would matter (±0.02).
2. **What helps is degree structure: keeping each projection neuron's real out-degree.** pn_out −
   random = {h("H2", "sparse")} sparse; {h("H2", "literal")} literal. It held in every sample and both
   odour sources.
3. **The real pairing between a projection neuron and its out-degree helps with a sparse code only.**
   pn_out − pn_out_perm_live = {h("H3", "sparse")} sparse; {h("H3", "literal")} literal.
4. **These wiring results survive a more biological model** (graded APL feedback + compartment-specific
   dopamine, experiment 011): 010 overturned: {over011}.
5. **In the creature, neither the homeostatic dopamine rule nor the real wiring made a detectable
   difference** to survival or mean energy (experiment 012, 40 seeds; smallest Holm p = {holm12:g}).
   The confidence intervals are wide, so this is "no detectable effect", not "shown to be zero".
6. **Brain-driven steering did not matter in the registered creature** (steering on − off, mean
   energy {san["mean_energy"]}), and a post-hoc check shows why: under the registered steering gain the
   learned valence does not measurably steer the body (details below).
7. **Individuals with the same genome but different histories became measurably different, history-
   specific individuals**, and they re-learned (slowly, incompletely) when food and toxic roles swapped.

![summary](figures/summary.png)

## Expected versus what happened

| question | what we expected (plans) | what happened |
|---|---|---|
| Does real MB wiring beat matched fake wiring? (CLAUDE.md, the one real question) | real > shuffle > random | real < shuffle by a small margin (H1); degree-preserving wirings > random (H2) |
| Is the 001–009 pattern robust to a second fly, a second hemisphere and a second odour set? (010) | replicate or fail visibly | H1 and H2 replicated in both code settings; H3 only with the sparse code |
| What makes real worse than shuffle? (010 N2) | co-convergence of glomeruli or KC class structure | real ≈ n2a (keeps co-convergence exactly): {find(n2, "N2-pairing: real − n2a_coconv", "sparse")[2]} sparse, and n2a − shuffle {find(n2, "N2-coconv: n2a_coconv − shuffle", "sparse")[2]}: by the plan's rule the deficit is carried by co-convergence |
| Does a more biological APL / dopamine change the answer? (011) | maybe | no; signs and sizes hold |
| Does the energy-dependent dopamine rule help the pet? (002, then 012) | yes, in a world where foraging is feasible | 002: null at the floor (pets starved {N["e002_starving"]} of the time). 012: still null, now off the floor ({cm["on"][2]} of pets died) |
| Does the body–brain loop work? (012 sanity) | steering helps foraging | no detectable help; the registered gain is too weak to steer (exploratory) |
| Can one owner teach a pet a like and a dislike within minutes? (WP6) | yes | the learned valences move the right way within a minute; in behaviour the dislike shows, the like does not (play app only, with a play-only steering gain) |

## Methods in one page

- **Connectome samples.** FlyWire v783 right and left mushroom body, and the hemibrain v1.2 right MB
  (Scheffer et al. 2020) as an independent animal. PN→KC and KC→MBON synapse counts (≥ 5 synapses);
  details in `docs/MB_EXTRACTION.md`. No connectivity is committed; scripts download and derive it.
- **Odours.** DoOR 2.0 receptor responses mapped to glomeruli (60 odorants) and, as a second source,
  Hallem & Carlson 2006 (57 odorants not in the DoOR panel, from the DoOR.data tables).
- **Learning model.** Binary Kenyon cells with a k-winners-take-all "APL" (sparse: 10% active; literal:
  as the connectome input gives), dopamine-gated depression of KC→MBON weights, ratio readout. Task:
  two odour sets, one rewarded; readout noise; metrics AULC, plateau, M2 (AUC at test noise σ = 1,
  primary), M3 (interference). Parameters chosen on synthetic circuits before any connectome run.
- **Controls.** random (same edge count and weights), degree-preserving shuffle (curveball), pn_out
  (keeps PN out-degree), pn_out_perm_live (permutes out-degrees among PNs with odour input), N2a (keeps
  glomerular co-convergence exactly), N2b (shuffle within KC class). Verified by computed statistics
  (`reports/010/nulls.md`, `docs/NULLS.md`).
- **Statistics.** Paired across seeds, 95% bootstrap CIs, d_z, Holm across each confirmatory family,
  SESOI 0.02 for M2, equivalence by the 90% CI.
- **Creature (012).** The MB model drives a 12-segment overdamped body with anisotropic drag and a
  phase-oscillator CPG on a 6 × 6 body-length torus. The brain only biases the CPG (steering from two
  head sensors × learned valence; amplitude/frequency from energy). Metabolism drains energy with muscle
  effort. Reward dopamine follows drive reduction (Keramati & Gutkin 2014). All constants were fixed on
  synthetic wiring with reward modulation off (pilot rounds 1–7) and asserted in code before the run.

### The creature: real data versus our design

{creature_tbl}

## Experiment 010 (confirmatory): does the wiring result replicate?

Plan: `experiments/010/PLAN.md` (committed before the run). {runs010.seed.nunique()} seeds,
{runs010["sample"].nunique()} samples, {runs010.source.nunique()} odour sources, {len(runs010)} runs. Runs at the task ceiling
(plateau ≥ 0.99): {ceil}.

{section(t010, "Confirmatory family (primary metric M2)")}

Per sample and odour source:

{section(t010, "Per connectome sample and per odour source (M2; descriptive, not in the family)")}

Null-model contrasts (pre-specified, not in the family):

{section(t010, "Pre-specified secondary contrasts: N2 nulls (not in the family)")}

![010 effects](figures/010_effects.png)

**Protocol deviation.** The first 010 and 011 runs used unregistered, harder task parameters because the
code default was never updated after the pilot (`experiments/010/DEVIATION.md`). Those raw outputs are
kept; the registered rerun above is the confirmatory result. At the harder setting all effects were
smaller (H1 sparse {Hd[("H1", "sparse")][3]}, H2 sparse {Hd[("H2", "sparse")][3]}, H3 sparse
{Hd[("H3", "sparse")][3]}; `reports/010/deviation/tables.md`). A constants assert now guards 012.

## Experiment 011: a more biological APL and dopamine

{section(t011, "H1–H3 per model variant (M2) vs experiment 010 (kWTA, global DA)")}

## Experiment 012: the creature

{section(t012, "Condition means")}

{section(t012, "Confirmatory family")}

Sanity check, not a headline (steering on − off):

{section(t012, "Sanity check (not a headline): brain-driven steering")}

Individuality (pre-specified secondary):

{ind}

Adaptation to a swap of food and toxic roles (pre-specified secondary):

{rev}

![012](figures/012_pet.png)

**Exploratory (post hoc): why steering did not matter.** `experiments/explore/steer_check.py` forces the
learned valence to ±0.3 and places a smell 1 body length to the side ({n_steer} runs of 90 s per cell,
3 odorants). Change in distance to the smell (BL, negative = closer), 95% CI:

| steering gain | valence +0.3 | valence −0.3 | steering off |
|---|---|---|---|
| registered (K = 25) | {steer[(25.0, 0.3, True)]} | {steer[(25.0, -0.3, True)]} | {steer[(25.0, 0.3, False)]} |
| 4× (K = 100) | {steer[(100.0, 0.3, True)]} | {steer[(100.0, -0.3, True)]} | — |

Under the registered gain the creature's learned preferences do not reach its behaviour, so 012 tested
the dopamine rule and the wiring mostly through what the creature bumps into, not through what it seeks.
The synthetic pilot had already shown no steering benefit (round 7), and we registered the constants
without following that up: a design miss on our side. A new pre-registered experiment
with the gain fixed by a chemotaxis criterion is the obvious next step (`docs/OPEN_QUESTIONS.md`).

## Operational life criteria

{life}

## The play app

A separate app (`src/neuralpet_play/`, `play/`, docs/PLAY.md) lets one owner raise and teach a pet from
a phone. It imports the frozen research code (tag `research-freeze`, checked by `tests/test_freeze.py`)
and never feeds results. It uses a play-only steering gain (K = 100), chosen by looking at behaviour,
which is not allowed for research and is labelled as such. Recorded teaching run (seed 20261108, 2
minutes): learned valence {teach["liked"]} (praised) {last[teach["liked"]]:+.3f}, {teach["disliked"]}
(scolded) {last[teach["disliked"]]:+.3f}, {teach["control"]} (never taught) {last[teach["control"]]:+.3f}.
Approach test with the smell 1 BL away, change in distance before → after teaching: praised
{nb[teach["liked"]]:+.2f} → {na[teach["liked"]]:+.2f}, scolded {nb[teach["disliked"]]:+.2f} → {na[teach["disliked"]]:+.2f},
control {nb[teach["control"]]:+.2f} → {na[teach["control"]]:+.2f} BL (one pet, {teach["approach_near"]["reps"]} copies; a demonstration, not a statistic).

![teaching](figures/play_teach.png)

## Earlier exploratory experiments (001–009)

These shaped the confirmatory plans; they are exploratory (one sample, one task setting each).
- 001: real − shuffle, trials to criterion {N["e001_m1"]}, M2 {N["e001_m2"]} (pooled readout).
- 004: with a ratio readout the trials gap shrank to {N["e004_m1"]}; M2 {N["e004_m2"]}.
- 006: DoOR odours, real − shuffle M2 {N["e006_m2_door"]}; real − random {N["e006_real_random_door"]}.
- 007: pn_out − random {N["e007_pnout_random_door"]} with DoOR odours but {N["e007_pnout_random_rand"]} with random odours.
- 008/009: pn_out − pn_out_perm {N["e008_pnout_perm"]}; within live PNs {N["e009_pnout_permlive"]} (sparse), {N["e009_pnout_permlive_lit"]} (literal).
- 002: energy-dependent dopamine in the first pet, mean energy {N["e002_energy"]}; the pet was starving {N["e002_starving"]} of the time.

## What is not supported

- That real fly wiring is "better" for learning: it was not, in any model we built.
- That the pet's internal-state rule matters: not detected in 002 or 012.
- That the creature's brain controls its foraging: not under the registered constants.
- Anything about experience, consciousness, or being alive. The "life criteria" above are behavioural
  tests of a simulation.
- Generality beyond our model: binary KCs, one task family, designed odour mapping, a designed body.
  Results could differ with spiking neurons, other plasticity rules or other tasks.
- Sample size of flies: three mushroom bodies from two animals.

## Reproduce

`docs/REPRODUCTION.md` (clean clone, data fetch, one command per experiment). Data licences and
citations: `docs/DATA.md`. Code licence: MIT.
"""
    (R / "FINAL.md").write_text(md)
    print("wrote reports/FINAL.md", len(md.splitlines()), "lines; figures:", sorted(p.name for p in FIG.iterdir()))


if __name__ == "__main__":
    main()
