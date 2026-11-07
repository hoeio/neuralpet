"""Shared statistics for confirmatory experiments (010-012): bootstrap CIs, paired t, Holm, verdicts."""
import numpy as np
from scipy import stats as st


def boot_ci(x, n=10000, seed=0, level=95):
    x = np.asarray(x, float)
    m = np.random.default_rng(seed).choice(x, (n, len(x))).mean(1)
    a = (100 - level) / 2
    return float(x.mean()), *map(float, np.percentile(m, [a, 100 - a]))


def fmt(t, d=4):
    return f"{t[0]:.{d}f} [{t[1]:.{d}f}, {t[2]:.{d}f}]"


def ttest_p(x):
    """Two-sided paired (one-sample on differences) t-test p-value."""
    x = np.asarray(x, float)
    return float(st.ttest_1samp(x, 0.0).pvalue) if x.std() > 0 else 1.0


def dz(x):
    x = np.asarray(x, float)
    sd = x.std(ddof=1)
    return float(x.mean() / sd) if sd > 0 else float("nan")


def holm(p):
    """Holm-Bonferroni adjusted p-values, same order as the input."""
    p = np.asarray(p, float)
    o = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for i, j in enumerate(o):
        run = max(run, min(1.0, (len(p) - i) * p[j]))
        adj[j] = run
    return adj.tolist()


def verdict(mean, p_holm, lo90, hi90, sign, sesoi, alpha=0.05):
    """Rejection rules written in experiments/010/PLAN.md."""
    if p_holm < alpha and np.sign(mean) == sign:
        return "replicated" + ("" if abs(mean) >= sesoi else " (smaller than SESOI)")
    if p_holm < alpha:
        return "not replicated: significant in the opposite direction"
    if -sesoi < lo90 and hi90 < sesoi:
        return "not replicated: equivalent to 0 (90% CI within ±SESOI)"
    return "not replicated: inconclusive"


if __name__ == "__main__":
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert verdict(0.03, 0.01, 0.02, 0.04, 1, 0.02) == "replicated"
    assert verdict(0.0, 0.5, -0.01, 0.01, 1, 0.02).startswith("not replicated: equivalent")
    assert verdict(-0.03, 0.01, -0.04, -0.02, 1, 0.02).endswith("opposite direction")
    print("stats self-check ok")
