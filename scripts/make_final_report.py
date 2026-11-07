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


def fmt(x, d=4):
    m, lo, hi = stats.boot_ci(np.asarray(x, float))
    return f"{m:+.{d}f} [{lo:+.{d}f}, {hi:+.{d}f}]"


def excl0(x):
    _, lo, hi = stats.boot_ci(np.asarray(x, float))
    return lo > 0 or hi < 0


def audit_numbers():
    """Numbers added after the independent audit (reviews/final.md), computed from raw results."""
    A = {}
    d = pd.read_csv(ROOT / "experiments" / "010" / "results_registered" / "runs.csv")
    for sp in ("sparse", "literal"):
        p = d[d.sparsity == sp].groupby(["seed", "cond"]).m2.mean().unstack()
        A[f"real_random_{sp}"] = fmt(p.real - p.random)
        A[f"shuffle_random_{sp}"] = fmt(p.shuffle - p.random)
        A[f"real_random_{sp}_pos"] = excl0(p.real - p.random) and (p.real - p.random).mean() > 0
    q = d[d.sparsity == "sparse"].pivot_table(index="seed", columns=["sample", "source", "cond"], values="m2")
    cells = {}
    for smp in d["sample"].unique():
        for src in d.source.unique():
            cells[(smp, src)] = q[(smp, src, "real")] - q[(smp, src, "shuffle")]
    A["h1_cells_total"] = len(cells)
    A["h1_cells_incl0"] = sum(not excl0(v) for v in cells.values())
    worst = min(cells, key=lambda k: cells[k].mean())
    A["h1_worst_cell"] = f"{worst[0]} × {worst[1]}: {fmt(cells[worst])}"
    for smp in ("fw_right", "fw_left"):
        A[f"h1_{smp}_incl0"] = not excl0(q.xs(smp, axis=1, level=0).xs("real", axis=1, level=1).mean(axis=1)
                                         - q.xs(smp, axis=1, level=0).xs("shuffle", axis=1, level=1).mean(axis=1))
    m = pd.read_csv(ROOT / "experiments" / "012" / "results" / "main.csv")
    da = m.pivot(index="seed", columns="cond", values="mean_da_r")
    meals = m.pivot(index="seed", columns="cond", values="meals")
    ok = meals["on"] > 0
    ratio = (da["generic"] / da["on"])[ok & (da["on"] > 0)]
    A["gen_n"] = int(len(ratio))
    A["gen_zero"] = int(((da["generic"] == 0) & ok).sum())
    A["gen_half"] = int((ratio < 0.5).sum())
    A["gen_median"] = f"{ratio.median():.2f}"
    A["const_ratio"] = f"{(da['const'] / da['on'])[ok & (da['on'] > 0)].median():.3f}"
    # individuality: cluster bootstrap (resample individuals / histories), CI of the difference
    ind = pd.read_csv(ROOT / "experiments" / "012" / "results" / "indiv.csv")
    ind["P"] = ind.pref.map(lambda x: np.array(json.loads(x)))
    own = np.stack(ind[ind.rep == 0].sort_values("hist").P)
    groups = [np.stack(g.P) for _, g in ind.groupby("hist") if len(g) > 1]
    D = np.linalg.norm(own[:, None] - own[None], axis=2)
    rng = np.random.default_rng(0)
    diffs, dh, dn = [], [], []
    for _ in range(5000):
        i = rng.integers(0, len(own), len(own))
        sub = D[np.ix_(i, i)]
        mask = i[:, None] < i[None]                       # distinct individuals only
        a = sub[mask].mean()
        gs = [groups[k] for k in rng.integers(0, len(groups), len(groups))]
        b = np.mean([np.linalg.norm(G[x] - G[y]) for G in gs for x in range(len(G)) for y in range(x + 1, len(G))])
        dh.append(a); dn.append(b); diffs.append(a - b)
    pc = lambda v: f"[{np.percentile(v, 2.5):.3f}, {np.percentile(v, 97.5):.3f}]"
    A["ind_cluster_hist"], A["ind_cluster_noise"] = pc(dh), pc(dn)
    A["ind_cluster_diff"] = f"{np.mean(diffs):+.3f} {pc(diffs)}"
    A["ind_cluster_diff_pos"] = np.percentile(diffs, 2.5) > 0
    # steering check, paired with steering off (same seed and odorant)
    sc = pd.read_csv(ROOT / "experiments" / "explore" / "results" / "steer_check.csv")
    off = sc[(sc.gain == 25.0) & (~sc.steering) & (sc.valence > 0)].set_index(["odor", "run"]).d_dist
    for g in (25.0, 100.0):
        for v in (0.3, -0.3):
            on = sc[(sc.gain == g) & sc.steering & (np.isclose(sc.valence, v))].set_index(["odor", "run"]).d_dist
            A[f"steer_paired_{g:.0f}_{v:+.1f}"] = fmt(on - off.loc[on.index], 2)
    return A


def plan012_verdict(S):
    """Apply experiments/012/PLAN.md's decision rules to the confirmatory family."""
    sig = {k: float(r[6]) < 0.05 for k, r in S.items()}
    sign = {k: np.sign(ci_cell(r[3])[0]) for k, r in S.items()}
    matters = any(sig[("S1", m)] and sig[("S2", m)] and sign[("S1", m)] == sign[("S2", m)] for m in ("survival_s", "mean_energy"))
    s1_only = any(sig[("S1", m)] for m in ("survival_s", "mean_energy")) and not matters
    wiring = any(sig[("S3", m)] and sign[("S3", m)] > 0 for m in ("survival_s", "mean_energy"))
    bound = {"mean_energy": 0.02, "survival_s": 60.0}
    equiv = all(-bound[m] < ci_cell(S[(t, m)][3])[1] and ci_cell(S[(t, m)][3])[2] < bound[m]
                for t in ("S1", "S2") for m in bound)
    widest = {m: max(ci_cell(S[(t, m)][3])[2] - ci_cell(S[(t, m)][3])[1] for t in ("S1", "S2")) / (2 * bound[m]) for m in bound}
    return dict(matters=matters, s1_only=s1_only, wiring=wiring, equiv=equiv, widest=widest)


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

    A = audit_numbers()
    cm011 = {r[1]: r for r in rows(t011, "Condition means") if r[0] == "apl_comp"}
    kc011 = {k: cm011[k][5].split()[0] for k in cm011}
    aulc011_h2 = find(rows(t011, "Secondary: AULC per variant"), "H2")[1]
    ps = rows(t010, "Per connectome sample and per odour source (M2; descriptive, not in the family)")
    h2_cells = [ci_cell(c) for r in ps if r[0] == "H2" for c in r[2:]]
    h2_every = ("It held (CI above 0) in every sample and both odour sources, in both code settings."
                if all(lo > 0 for _, lo, _ in h2_cells) else "It did not hold in every sample and odour source (see per-sample table).")
    rep = {k: H[k][8].startswith("replicated") for k in H}
    repl_text = "; ".join(f"{hh}: " + ", ".join(f"{sp} {'replicated' if rep[(hh, sp)] else 'not replicated'}" for sp in ("sparse", "literal"))
                          for hh in ("H1", "H2", "H3"))
    V = plan012_verdict(S)
    v12_text = (("all S1/S2 CIs are within ±0.02 mean energy and ±60 s survival" if V["equiv"] else
                 f"the S1/S2 CIs are up to {V['widest']['mean_energy']:.1f}× (energy) and {V['widest']['survival_s']:.1f}× (survival) "
                 "wider than the ±0.02 / ±60 s equivalence bounds")
                + ("; the plan's rule for \"the state rule matters\" (S1 and S2 significant, same sign) is met" if V["matters"]
                   else "; the plan's rule for \"the state rule matters\" (S1 and S2 significant, same sign) is not met")
                + ("; real wiring helps the pet (S3)" if V["wiring"] else "; nor is the rule for \"real wiring helps the pet\" (S3)"))
    lit_text = ", ".join(f"{k} {v:.2f}" for k, v in meta010["literal"].items())

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

1. **Real mushroom-body partners did not beat a degree-preserving shuffle; they were slightly worse.**
   Registered experiment 010 (64 seeds × 3 connectome samples × 2 odour sources): real − shuffle on
   noise robustness (M2) = {h("H1", "sparse")} with a sparse Kenyon-cell code, {h("H1", "literal")}
   with the literal (dense) code. Both are below the smallest effect we said would matter (±0.02). With
   the sparse code the deficit is carried mostly by one cell ({A["h1_worst_cell"]}):
   {A["h1_cells_incl0"]} of {A["h1_cells_total"]} sample × source cells have CIs that include 0,
   {"both FlyWire hemispheres are indistinguishable from 0" if A["h1_fw_right_incl0"] and A["h1_fw_left_incl0"] else "the FlyWire hemispheres differ from 0"},
   and at the harder (deviation) task setting it was {Hd[("H1", "sparse")][3]}.
2. **Real wiring did beat random wiring with the sparse code, by about the SESOI:** real − random
   {A["real_random_sparse"]} sparse, {A["real_random_literal"]} literal (descriptive, not in the
   registered family). A degree-preserving shuffle did at least as well (shuffle − random
   {A["shuffle_random_sparse"]} sparse, {A["shuffle_random_literal"]} literal), so the benefit comes from
   degree structure, not from which projection neuron contacts which Kenyon cell.
3. **Keeping each projection neuron's real out-degree helps.** pn_out − random = {h("H2", "sparse")}
   sparse; {h("H2", "literal")} literal. {h2_every}
4. **The real pairing of a projection neuron with its out-degree helps with the sparse code only.**
   pn_out − pn_out_perm_live = {h("H3", "sparse")} sparse; {h("H3", "literal")} literal (the point
   estimate is negative; the exploratory 009 literal effect, {N["e009_pnout_permlive_lit"]}, did not replicate).
5. **The sparse-code wiring results held with graded APL feedback + compartment-specific dopamine**
   (experiment 011, sparse code only; 010 overturned: {over011}). Caveats under the 011 table.
6. **In the creature, neither the homeostatic dopamine rule nor the real wiring made a detectable
   difference** to survival or mean energy (experiment 012, 40 seeds; smallest Holm p = {holm12:g}).
   By the plan's own equivalence bounds the result is **inconclusive**, not null: {v12_text}. And since
   learned valence barely reaches behaviour under the registered constants (next point), 012 could
   hardly have detected a state-rule effect.
7. **Brain-driven steering did not matter in the registered creature** (steering on − off, mean
   energy {san["mean_energy"]}); a post-hoc check shows that under the registered steering gain the
   learned valence does not measurably steer the body (details below). We missed this before registering.
8. **Learned odour preferences (internal valences) diverged between individuals with the same genome and
   different histories, and re-adapted (slowly, incompletely) when food and toxic roles swapped.** Under
   the registered constants these internal differences do not show in behaviour.

![summary](figures/summary.png)

## Expected versus what happened

| question | expectation | what happened |
|---|---|---|
| Does real MB wiring beat matched fake wiring? (CLAUDE.md, the one real question) | the project's starting hope: real > shuffle > random; the 010 plan, after 001–009, predicted real < shuffle | real < shuffle by a small margin (H1); real > random with the sparse code only; pn_out > random (H2) |
| Is the 001–009 pattern robust to a second fly, a second hemisphere and a second odour set? (010) | replicate or fail visibly | {repl_text} |
| What makes real worse than shuffle? (010 N2) | co-convergence of glomeruli or KC class structure | sparse: real − n2a (keeps co-convergence exactly) {find(n2, "N2-pairing: real − n2a_coconv", "sparse")[2]} and n2a − shuffle {find(n2, "N2-coconv: n2a_coconv − shuffle", "sparse")[2]}, so by the plan's rule co-convergence carries the deficit; literal: real − n2a {find(n2, "N2-pairing: real − n2a_coconv", "literal")[2]}, so there the pairing also matters. The co-convergence account holds for the pooled sparse code only |
| Does a more biological APL / dopamine change the answer? (011) | maybe | {"no" if over011 == "no" else "yes"}, for the sparse code (see caveats) |
| Does the energy-dependent dopamine rule help the pet? (002, then 012) | yes, in a world where foraging is feasible | 002: null at the floor (pets starved {N["e002_starving"]} of the time). 012: inconclusive, now off the floor ({cm["on"][2]} of pets died) |
| Does the body–brain loop work? (012 sanity) | steering helps foraging | no detectable help; the registered gain is too weak to steer (exploratory) |
| Can one owner teach a pet a like and a dislike within minutes? (WP6) | yes | the learned valences move the right way within a minute; in behaviour the dislike shows, the like does not (play app only, play-only steering gain) |

## Methods in one page

- **Connectome samples.** FlyWire v783 right and left mushroom body, and the hemibrain v1.2 right MB
  (Scheffer et al. 2020) as an independent animal. PN→KC and KC→MBON synapse counts (≥ 5 synapses);
  details in `docs/MB_EXTRACTION.md`. No connectivity is committed; scripts download and derive it.
- **Odours.** DoOR 2.0 receptor responses mapped to glomeruli (60 odorants) and, as a second source,
  Hallem & Carlson 2006 (57 odorants not in the DoOR panel, from the DoOR.data tables).
- **Learning model.** Binary Kenyon cells with a k-winners-take-all "APL" (sparse: 10% active; literal:
  a fixed active fraction per sample measured once from the connectome input with random odours —
  {lit_text}; cf. ~68% in CLAUDE.md and 5–10% in real flies), dopamine-gated depression of KC→MBON weights, ratio readout. Task:
  two odour sets, one rewarded; readout noise; metrics AULC, plateau, M2 (AUC at test noise σ = 1,
  primary), M3 (interference). Parameters chosen on synthetic circuits; one connectome smoke run (seed 7, outside the
  confirmatory range) was seen before the 010 plan was committed, as the plan states. Secondary metrics
  (AULC, plateau, M3 interference) for every contrast are in `reports/010/tables.md`.
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

Caveats (from the audit, reviews/final.md): 011 used the sparse code only, so it says nothing about the
literal results. Its H1 "sign holds" rule is an equivalence test written when the 010 run it checked
was the deviation run (H1 ≈ 0); with the registered H1 negative, "yes" there means "within ±0.02", not
"negative". The graded APL does not equalise KC activity across wirings (apl_comp KC mean rate:
random {kc011["random"]}, pn_out {kc011["pn_out"]}, pn_out_perm_live {kc011["pn_out_perm_live"]}), so H2/H3 there
are partly confounded with activity level. The secondary AULC for H2 under apl_comp is
{aulc011_h2}.

## Experiment 012: the creature

{section(t012, "Condition means")}

{section(t012, "Confirmatory family")}

The S2 control was matched to the `on` run's mean reward dopamine **in expectation, not in
realisation**: its quadratic was rescaled at the `on` run's pre-meal energies, but the generic run
meets other energies and is clipped at 0. Of {A["gen_n"]} seeds with meals, the generic rule gave exactly
zero reward dopamine in {A["gen_zero"]} and less than half of the `on` amount in {A["gen_half"]} (median
ratio {A["gen_median"]}; the `const` control matched exactly, median ratio {A["const_ratio"]}). So S2 is a
weaker rule-6 control than intended. This is the plan as registered; a better match would need a new plan.

Sanity check, not a headline (steering on − off):

{section(t012, "Sanity check (not a headline): brain-driven steering")}

Individuality (pre-specified secondary):

{ind}

The CIs above resample pairs of individuals, which are not independent. Resampling individuals (and
whole same-history groups) instead gives different histories {A["ind_cluster_hist"]}, same history
{A["ind_cluster_noise"]}, difference {A["ind_cluster_diff"]}: {"still above 0, but much less precise" if A["ind_cluster_diff_pos"] else "no longer clearly above 0"}.
These are internal valences; the steering results below mean they barely reach behaviour.

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

Paired with steering off (same seed and odorant), the change in distance is: registered gain, valence
+0.3 {A["steer_paired_25_+0.3"]}, −0.3 {A["steer_paired_25_-0.3"]}; 4× gain, +0.3 {A["steer_paired_100_+0.3"]},
−0.3 {A["steer_paired_100_-0.3"]}. So at 4× a positive valence reduces the drift away from the smell
(the creature still ends farther away than it started), while avoidance is not distinguishable from
steering off. A first version of the script used odour index 0, which is water (no receptor response);
it was discarded and the three odorants above were chosen by name before the rerun.

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
A first test with the smell 2.5 BL away (outside most of the plume) showed no difference for any smell
(after teaching: {", ".join(f"{teach['approach_after'][o]:+.2f}" for o in (teach["liked"], teach["disliked"], teach["control"]))} BL); the 1 BL test was chosen after
seeing it. Note the pattern differs from the forced-valence check above (there attraction showed and
avoidance did not); with one pet and 8 copies neither pattern is established.

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

- That the real fly's specific PN→KC partners help learning: they did not beat a degree-preserving
  shuffle in any model we built. (Real did beat random wiring with the sparse code, but no more than the
  shuffle did.)
- That the pet's internal-state rule matters: not detected in 002 or 012, and 012 was underpowered for it.
- That the creature's brain controls its foraging: not under the registered constants.
- That individuals differ in behaviour: their learned valences differ; their behaviour was not shown to.
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
