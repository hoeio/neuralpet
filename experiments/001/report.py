"""Make tables + figures for experiment 001 from results/runs.csv (never edited by hand).
Outputs: reports/001/tables.md, reports/001/*.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "reports" / "001"
CONDS = ["random", "shuffle", "real"]
COLOR = {"random": "#2a78d6", "shuffle": "#eb6834", "real": "#1baf7a"}  # dataviz slots 1-3
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
METRICS = [("M1_trials", "trials to AUC≥0.9, σ=0.2 (lower better)"),
           ("M2_auc_sigma1.0", "AUC at test noise σ=1 (higher better)"),
           ("M3_interference", "AUC drop on set A after set B (lower better)")]
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "font.size": 9})


def boot_ci(x, n=10000, seed=0):
    x = np.asarray(x, float)
    m = np.random.default_rng(seed).choice(x, (n, len(x))).mean(1)
    return x.mean(), *np.percentile(m, [2.5, 97.5])


def fmt(m, lo, hi):
    return f"{m:.3g} [{lo:.3g}, {hi:.3g}]"


def tables(df):
    lines = []
    for sp in df.sparsity.unique():
        d = df[df.sparsity == sp]
        lines += [f"\n### sparsity = {sp} (KC fraction f = {d.frac.iloc[0]:.3f}, "
                  f"n = {d.seed.nunique()} seeds)\n",
                  "| metric | " + " | ".join(CONDS) + " |", "|---|" + "---|" * len(CONDS)]
        for m, lab in METRICS + [("aucB", "AUC on set B"), ("auc_sigma0.0", "AUC at σ=0"),
                                 ("kc_active_sigma0.0", "measured KC active fraction (σ=0)")]:
            lines.append(f"| {lab} | " + " | ".join(fmt(*boot_ci(d[d.wiring == c][m])) for c in CONDS) + " |")
        cens = {c: int(d[d.wiring == c].M1_censored.sum()) for c in CONDS}
        lines.append(f"\nM1 censored (not learned by 400 trials): {cens}\n")
        lines += ["| paired contrast | metric | mean diff [95% CI] | d_z |", "|---|---|---|---|"]
        p = d.pivot(index="seed", columns="wiring")
        for other in ["shuffle", "random"]:
            for m, lab in METRICS:
                diff = p[m]["real"] - p[m][other]
                sd = diff.std(ddof=1)
                dz = diff.mean() / sd if sd > 0 else float("nan")
                lines.append(f"| real − {other} | {m} | {fmt(*boot_ci(diff))} | {dz:.2f} |")
        lines.append(f"\nedge overlap with real (mean): PN→KC "
                     + ", ".join(f"{c} {d[d.wiring == c].edge_overlap_pk.mean():.3f}" for c in CONDS)
                     + "; KC→MBON "
                     + ", ".join(f"{c} {d[d.wiring == c].edge_overlap_km.mean():.3f}" for c in CONDS))
    return "\n".join(lines)


def label_ends(ax, items, gap=0.035):
    """Direct end labels, nudged apart so they never overlap. items: [(x, y, text)]."""
    items = sorted(items, key=lambda t: t[1])
    ys = [items[0][1]]
    for _, y, _ in items[1:]:
        ys.append(max(y, ys[-1] + gap))
    for (x, _, c), y in zip(items, ys):
        ax.annotate(c, (x, y), xytext=(4, 0), textcoords="offset points", color=INK2, va="center")


def fig_curves(df):
    sps = list(df.sparsity.unique())
    fig, axes = plt.subplots(1, len(sps), figsize=(4.2 * len(sps), 3.2), sharey=True)
    for ax, sp in zip(np.atleast_1d(axes), sps):
        ends = []
        for c in CONDS:
            cur = np.array([json.loads(s) for s in df[(df.sparsity == sp) & (df.wiring == c)].curve])
            x = np.arange(cur.shape[1]) * 20
            m = cur.mean(0)
            lo, hi = np.array([boot_ci(cur[:, j])[1:] for j in range(cur.shape[1])]).T
            ax.fill_between(x, lo, hi, color=COLOR[c], alpha=0.18, lw=0)
            ax.plot(x, m, color=COLOR[c], lw=2, label=c)
            ends.append((x[-1], m[-1], c))
        label_ends(ax, ends)
        ax.axhline(0.9, color=INK2, lw=1, ls=":")
        ax.set(title=f"{sp} KC code", xlabel="training trials (set A)", xlim=(0, 460))
    np.atleast_1d(axes)[0].set_ylabel("AUC (CS− vs CS+), σ=0.2")
    np.atleast_1d(axes)[0].legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "learning_curves.png", dpi=150)


def fig_noise(df):
    sig = sorted(float(c.removeprefix("auc_sigma")) for c in df.columns if c.startswith("auc_sigma"))
    sps = list(df.sparsity.unique())
    fig, axes = plt.subplots(1, len(sps), figsize=(4.2 * len(sps), 3.2), sharey=True)
    for ax, sp in zip(np.atleast_1d(axes), sps):
        ends = []
        for c in CONDS:
            d = df[(df.sparsity == sp) & (df.wiring == c)]
            st = np.array([boot_ci(d[f"auc_sigma{s}"]) for s in sig])
            ax.errorbar(sig, st[:, 0], yerr=[st[:, 0] - st[:, 1], st[:, 2] - st[:, 0]], color=COLOR[c],
                        lw=2, marker="o", ms=5, capsize=0, label=c)
            ends.append((sig[-1], st[-1, 0], c))
        label_ends(ax, ends)
        ax.set(title=f"{sp} KC code", xlabel="test noise σ", xlim=(-0.1, 2.5))
    np.atleast_1d(axes)[0].set_ylabel("AUC after 200 training trials")
    np.atleast_1d(axes)[0].legend(frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "noise.png", dpi=150)


def fig_metrics(df):
    sps = list(df.sparsity.unique())
    fig, axes = plt.subplots(len(sps), 3, figsize=(10, 3 * len(sps)), squeeze=False)
    rng = np.random.default_rng(0)
    for i, sp in enumerate(sps):
        for j, (m, lab) in enumerate(METRICS):
            ax = axes[i, j]
            for k, c in enumerate(CONDS):
                v = df[(df.sparsity == sp) & (df.wiring == c)][m].to_numpy()
                ax.scatter(k + rng.uniform(-0.15, 0.15, len(v)), v, s=14, color=COLOR[c], alpha=0.6,
                           edgecolor=SURF, lw=0.5)
                mm, lo, hi = boot_ci(v)
                ax.plot([k - 0.28, k + 0.28], [mm, mm], color=INK, lw=2)
                ax.plot([k, k], [lo, hi], color=INK, lw=1)
            ax.set_xticks(range(3), CONDS)
            ax.grid(axis="x", visible=False)
            ax.set_title(f"{sp}: {lab}", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "metrics_by_seed.png", dpi=150)


def main():
    df = pd.read_csv(HERE / "results" / "runs.csv")
    meta = json.loads((HERE / "results" / "meta.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    t = tables(df)
    (OUT / "tables.md").write_text(f"# Experiment 001 tables (generated by experiments/001/report.py)\n\n"
                                   f"meta: `{json.dumps(meta)}`\n\nCells: mean [95% bootstrap CI].\n{t}\n")
    fig_curves(df), fig_noise(df), fig_metrics(df)
    print(t)


if __name__ == "__main__":
    main()
