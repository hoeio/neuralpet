"""Graded KC layer with APL feedback inhibition from the real APL<->KC connectivity (experiment 011;
docs/ADAPTERS.md v7). A documented abstraction, not a biophysical APL model.

  d_k   = sum_p W_pk[p, k] * pn_p                       (PN drive, as in v1)
  I     = sum_k B_k r_k / sum_k B_k                      (APL activity; B_k = KC->APL synapses)
  r_k   = clip((d_k - g * A_k * I) / D, 0, 1)            (KC rate; A_k = APL->KC synapses / mean)
Solved by damped fixed-point iteration (30 steps, step 0.5) and one undamped final step. D = mean drive of a KC with positive
drive for reference odours (per sample, real wiring). g is set per sample on the real wiring with
500 random v1 odours so that the mean fraction of KCs with r > 0 is 0.10 (bisection); the same g is
used for every wiring condition, so a wiring that drives KCs differently gets a different sparseness.
"""
import numpy as np

from neuralpet import mb


def make(W_pk_real, A, B, glom, target=0.10, iters=30):
    A = A / A[A > 0].mean()
    Bn = B / B.sum()
    ref = mb.make_odors(500, glom, np.random.default_rng(12345))
    d_ref = ref @ W_pk_real
    D = float(d_ref[d_ref > 0].mean())

    def rates(drive, g):
        r = np.clip(drive / D, 0, 1)
        for _ in range(iters):
            I = r @ Bn
            r = 0.5 * r + 0.5 * np.clip((drive - g * A[None, :] * (I[:, None] * D)) / D, 0, 1)
        return np.clip((drive - g * A[None, :] * ((r @ Bn)[:, None] * D)) / D, 0, 1)   # undamped final step

    lo, hi = 0.0, 50.0
    for _ in range(30):
        g = 0.5 * (lo + hi)
        if (rates(d_ref, g) > 0).mean() > target:
            lo = g
        else:
            hi = g
    g = 0.5 * (lo + hi)
    return g, D, (lambda W_pk: (lambda pn: rates(pn @ W_pk, g).astype(np.float32)))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    W = ((rng.random((40, 600)) < 0.1) * rng.integers(5, 20, (40, 600))).astype(np.float32)
    A, B = rng.integers(1, 10, 600).astype(float), rng.integers(1, 10, 600).astype(float)
    g, D, f = make(W, A, B, np.arange(40))
    r = f(W)(mb.make_odors(200, np.arange(40), np.random.default_rng(1)))
    assert 0.06 < (r > 0).mean() < 0.14 and r.max() <= 1 and r.min() >= 0, (r > 0).mean()
    print("apl self-check ok, g =", round(g, 3), "active", round(float((r > 0).mean()), 3))
