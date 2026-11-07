"""Experiment 012: does the state rule matter in a pet that can survive? See PLAN.md.

    uv run python experiments/012/run.py [--seeds 40] [--procs 10] [--report-only]

Raw: experiments/012/results/{main,indiv,reversal}.csv. Report: reports/012/tables.md + figures.
"""
import argparse
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from neuralpet import creature as C
from neuralpet import mb, stats
from neuralpet.odors import door_odors

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "reports" / "012"
LIFE = 2400.0
SEED_MAIN, SEED_IND, SEED_REV = 2000, 3000, 4000
CONDS = ["on", "const", "generic", "shuffle_on", "steer_off"]
FAMILY = [("S1", "on", "const"), ("S2", "on", "generic"), ("S3", "on", "shuffle_on")]
METRICS = ["survival_s", "mean_energy"]
PANEL = 8                       # odorants in the individuality worlds
_D = {}


def data():
    if not _D:
        d = np.load(ROOT / "data" / "mb" / "mb.npz")
        odors, keys, _ = door_odors(d["glom_names"], d["glom_of_pn"])
        _D.update(W_pk=d["W_pnkc"], W_km=d["W_kcmbon"], odors=odors)
    return _D


def life(seed, cond, da_const=0.5, coef=None, mortal=True, roles=None, odors=None, noise_seed=None, swap_at=None, T=LIFE):
    D = data()
    W_pk = D["W_pk"]
    if cond == "shuffle_on":
        W_pk = mb.degree_shuffle(W_pk, np.random.default_rng([seed, 77]))
    mode = {"on": "on", "shuffle_on": "on", "steer_off": "on", "const": "const", "generic": "generic"}[cond]
    c = C.Creature(W_pk, D["W_km"], D["odors"] if odors is None else odors, seed=seed, da_mode=mode, da_const=da_const,
                   generic_coef=coef, steering=cond != "steer_off", mortal=mortal, roles=roles, noise_seed=noise_seed)
    eat_e = []                                                  # energy before each meal (for matching)
    n_ev = 0
    pre = {}
    for _ in range(int(round(T / C.TICK))):
        if not c.alive:
            break
        e = c.energy
        c.tick()
        for ev in c.events[n_ev:]:
            if ev[1] == "eat":
                eat_e.append(e)
        n_ev = len(c.events)
        if swap_at is not None and abs(c.t - swap_at) < C.TICK / 2:
            pre = dict(pref=c.preferences())
            for s in c.sources:
                s.kind = {"food": "toxic", "toxic": "food"}[s.kind]
    E = np.array(c.energy_log)
    ev = [x[1] for x in c.events]
    food = [o for k, o in c.roles if k == "food"]
    tox = [o for k, o in c.roles if k == "toxic"]
    out = dict(seed=seed, cond=cond, survival_s=round(c.t, 1), died=not c.alive, mean_energy=float(E.mean()),
               frac_pos=float((E > 0).mean()), meals=ev.count("eat"), toxic=ev.count("toxic"),
               mean_da_r=float(np.mean(c.da_r_log)) if c.da_r_log else None, eat_energy=json.dumps(eat_e))
    out["valence_gap"] = float(c.preferences(food).mean() - c.preferences(tox).mean())
    return out, c, pre


def generic_coef(seed, eat_e, target):
    """Size-matched generic substitute for the state module (same input e, a quadratic like H(e)):
    random coefficients, rescaled so its mean over the 'on' run's pre-meal energies equals the 'on'
    mean reward DA. Drawn once per seed before the run, never tuned."""
    r = np.random.default_rng([seed, 55])
    a, b, c = r.standard_normal(3)
    e = np.asarray(eat_e) if len(eat_e) else np.array([0.5])
    m = np.mean(np.maximum(0, a + b * e + c * e ** 2))
    k = target / m if m > 0 else 0.0
    return (a * k, b * k, c * k)


def job_main(seed):
    on, _, _ = life(seed, "on")
    target = on["mean_da_r"] if on["mean_da_r"] is not None else 0.5
    rows = [on]
    for cond in CONDS[1:]:
        coef = generic_coef(seed, json.loads(on["eat_energy"]), target) if cond == "generic" else None
        r, _, _ = life(seed, cond, da_const=target, coef=coef)
        r["da_const"] = target
        rows.append(r)
    return rows


def roles_for(seed):
    r = np.random.default_rng([seed, 5])
    idx = r.permutation(PANEL)
    return [("food", int(i)) for i in idx[:3]] + [("toxic", int(i)) for i in idx[3:5]]


def panel_odors():
    D = data()
    return D["odors"][np.random.default_rng(321).choice(len(D["odors"]), PANEL, replace=False)]


def job_indiv(a):
    hist, rep = a                     # rep 0 = own noise; rep 1..4 = same history, other noise streams
    roles = roles_for(hist)
    r, c, _ = life(hist, "on", mortal=False, roles=roles, odors=panel_odors(), noise_seed=None if rep == 0 else 90000 + 10 * hist + rep)
    role = np.zeros(PANEL)
    for k, o in roles:
        role[o] = 1 if k == "food" else -1
    return dict(r, hist=hist, rep=rep, pref=json.dumps(c.preferences().round(5).tolist()), role=json.dumps(role.tolist()))


def job_rev(a):
    seed, swap = a
    r, c, pre = life(seed, "on", mortal=False, swap_at=LIFE / 2 if swap else None)
    food0 = [o for k, o in c.roles if k == "food"]
    tox0 = [o for k, o in c.roles if k == "toxic"]
    post = c.preferences()
    gap = lambda p: float(np.mean(p[tox0]) - np.mean(p[food0])) if p is not None else None   # new food − new toxic after swap
    return dict(seed=seed, swap=swap, gap_at_swap=gap(pre.get("pref")), gap_end=gap(post), meals=r["meals"], toxic=r["toxic"],
                mean_energy=r["mean_energy"])


def tables(m, ind, rev):
    L = ["# Experiment 012 tables (generated by experiments/012/run.py)\n",
         f"Life {LIFE:.0f} s (simulated), FlyWire right MB, WP5a body. {m.seed.nunique()} seeds ({m.seed.min()}–{m.seed.max()}). "
         "95% bootstrap CIs over seeds; paired t, Holm across the 6-test family.\n",
         "## Condition means\n", "| cond | survival s | died | mean energy | frac time E>0 | meals | toxic hits | valence gap food−toxic |",
         "|---|---|---|---|---|---|---|---|"]
    for c in CONDS:
        d = m[m.cond == c]
        L.append(f"| {c} | " + " | ".join(stats.fmt(stats.boot_ci(d[k].astype(float)), 3) for k in
                                          ["survival_s", "died", "mean_energy", "frac_pos", "meals", "toxic", "valence_gap"]) + " |")
    p = m.pivot(index="seed", columns="cond")
    fam = [(h, a, b, k, p[k][a] - p[k][b]) for h, a, b in FAMILY for k in METRICS]
    adj = stats.holm([stats.ttest_p(x) for *_, x in fam])
    L += ["\n## Confirmatory family\n", "| test | contrast | metric | mean diff [95% CI] | d_z | p | p Holm |", "|---|---|---|---|---|---|---|"]
    for (h, a, b, k, x), pa in zip(fam, adj):
        L.append(f"| {h} | {a} − {b} | {k} | {stats.fmt(stats.boot_ci(x), 4)} | {stats.dz(x):.2f} | {stats.ttest_p(x):.2g} | {pa:.2g} |")
    L += ["\n## Sanity check (not a headline): brain-driven steering\n", "| metric | on − steer_off |", "|---|---|"]
    for k in ["meals", "mean_energy", "survival_s", "valence_gap"]:
        L.append(f"| {k} | {stats.fmt(stats.boot_ci(p[k]['on'] - p[k]['steer_off']), 3)} |")
    # individuality
    ind = ind.assign(P=ind.pref.map(lambda s: np.array(json.loads(s))), R=ind.role.map(lambda s: np.array(json.loads(s))))
    own = ind[ind.rep == 0].reset_index(drop=True)
    H = np.stack(own.P)
    d_hist = [np.linalg.norm(H[i] - H[j]) for i in range(len(H)) for j in range(i + 1, len(H))]
    d_noise = []
    for h, g in ind.groupby("hist"):
        if len(g) > 1:
            Q = np.stack(g.P)
            d_noise += [np.linalg.norm(Q[i] - Q[j]) for i in range(len(Q)) for j in range(i + 1, len(Q))]
    r_own = np.array([np.corrcoef(a, b)[0, 1] for a, b in zip(own.P, own.R)])
    rng = np.random.default_rng(0)
    r_sh = np.array([np.mean([np.corrcoef(own.P[i], own.R[j])[0, 1] for j in rng.choice([j for j in range(len(own)) if j != i], 10, replace=False)])
                     for i in range(len(own))])
    L += ["\n## Individuality (same genome, different histories; pre-specified secondary)\n",
          f"- {len(own)} individuals with different histories; {int((ind.rep > 0).sum())} extra individuals sharing 5 histories but with other noise streams.",
          f"- Mean pairwise distance of preference vectors: different histories {stats.fmt(stats.boot_ci(d_hist), 4)}; same history, other noise {stats.fmt(stats.boot_ci(d_noise), 4)}.",
          f"- Correlation of an individual's preferences with its own history (food +1, toxic −1, absent 0): {stats.fmt(stats.boot_ci(r_own), 3)}; "
          f"with other individuals' histories (seed-shuffled baseline): {stats.fmt(stats.boot_ci(r_sh), 3)}; difference {stats.fmt(stats.boot_ci(r_own - r_sh), 3)}."]
    # adaptation
    s, ns = rev[rev.swap], rev[~rev.swap]
    L += ["\n## Adaptation to environment change (pre-specified secondary)\n",
          "Food and toxic sources swap roles halfway. Gap = valence(new food odours) − valence(new toxic odours).",
          f"- at the swap: {stats.fmt(stats.boot_ci(s.gap_at_swap), 3)}; at the end: {stats.fmt(stats.boot_ci(s.gap_end), 3)}; "
          f"change {stats.fmt(stats.boot_ci(s.gap_end.to_numpy() - s.gap_at_swap.to_numpy()), 3)}.",
          f"- no-swap control, same gap measured at the end: {stats.fmt(stats.boot_ci(ns.gap_end), 3)}.",
          f"- mean energy, swap vs no swap (paired): {stats.fmt(stats.boot_ci(s.mean_energy.to_numpy() - ns.mean_energy.to_numpy()), 3)}."]
    return "\n".join(L), dict(d_hist=d_hist, d_noise=d_noise, r_own=r_own, r_sh=r_sh)


def figure(m, ind_stats):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from neuralpet.plotstyle import COLORS, INK, style
    style()
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.2))
    for i, k in enumerate(["survival_s", "mean_energy"]):
        for j, c in enumerate(CONDS):
            v = m[m.cond == c][k].to_numpy(float)
            ax[i].scatter(j + np.random.default_rng(j).uniform(-.15, .15, len(v)), v, s=10, color=COLORS[j % len(COLORS)], alpha=.6)
            mm, lo, hi = stats.boot_ci(v)
            ax[i].plot([j - .25, j + .25], [mm, mm], color=INK, lw=2)
            ax[i].plot([j, j], [lo, hi], color=INK, lw=1)
        ax[i].set_xticks(range(len(CONDS)), CONDS, rotation=20)
        ax[i].set_title(k)
    ax[2].boxplot([ind_stats["d_noise"], ind_stats["d_hist"]], tick_labels=["same history", "different history"])
    ax[2].set_title("preference-vector distance")
    fig.tight_layout()
    fig.savefig(OUT / "pet.png", dpi=150)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--procs", type=int, default=10)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    res = HERE / "results"
    if not a.report_only:
        t = time.time()
        with Pool(a.procs) as pool:
            main_rows = [r for rs in pool.map(job_main, range(SEED_MAIN, SEED_MAIN + a.seeds), chunksize=1) for r in rs]
            ind = pool.map(job_indiv, [(SEED_IND + h, 0) for h in range(20)] + [(SEED_IND + h, k) for h in range(5) for k in range(1, 5)], chunksize=1)
            rev = pool.map(job_rev, [(SEED_REV + s, sw) for s in range(20) for sw in (True, False)], chunksize=1)
        res.mkdir(exist_ok=True)
        pd.DataFrame(main_rows).to_csv(res / "main.csv", index=False)
        pd.DataFrame(ind).to_csv(res / "indiv.csv", index=False)
        pd.DataFrame(rev).to_csv(res / "reversal.csv", index=False)
        (res / "meta.json").write_text(json.dumps(dict(seeds=a.seeds, life_s=LIFE, wall_s=round(time.time() - t, 1)), indent=1))
    m, ind, rev = (pd.read_csv(res / f) for f in ["main.csv", "indiv.csv", "reversal.csv"])
    t, ist = tables(m, ind, rev)
    (OUT / "tables.md").write_text(t + "\n")
    figure(m, ist)
    print(t)


if __name__ == "__main__":
    main()
