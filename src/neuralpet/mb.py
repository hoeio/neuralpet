"""Minimal rate/binary mushroom-body model. All layer-to-layer rules are in docs/ADAPTERS.md.

Matrices are dense float32: W_pk (n_pn x n_kc), W_km (n_kc x n_mbon), entries = synapse counts.
"""
import numpy as np


# ---------- wiring controls (same node sets, same edge count, same weight multiset) ----------

def random_bipartite(W, rng):
    """(a) Random: same number of edges placed uniformly among all pairs; real weights permuted."""
    w = W[W > 0]
    out = np.zeros_like(W)
    idx = rng.choice(W.size, size=w.size, replace=False)
    out.flat[idx] = rng.permutation(w)
    return out


def curveball(A, rng, n_trades=None):
    """Uniform-ish sample of a binary matrix with the same row and column sums (Strona et al. 2014)."""
    rows = [set(np.flatnonzero(r)) for r in A]
    n = len(rows)
    for _ in range(n_trades or 5 * n):
        a, b = rng.choice(n, 2, replace=False)
        ra, rb = rows[a], rows[b]
        only_a, only_b = list(ra - rb), list(rb - ra)
        if not only_a or not only_b:
            continue
        pool = only_a + only_b
        rng.shuffle(pool)
        k = len(only_a)
        rows[a] = (ra & rb) | set(pool[:k])
        rows[b] = (ra & rb) | set(pool[k:])
    out = np.zeros_like(A, dtype=bool)
    for i, r in enumerate(rows):
        out[i, list(r)] = True
    return out


def degree_shuffle(W, rng):
    """(b) Degree-preserving: every node keeps its in- and out-degree; real weights permuted.
    Curveball runs over rows of the larger dimension (the KCs), 5 x n_KC trades."""
    B = curveball(W > 0, rng) if W.shape[0] >= W.shape[1] else curveball((W > 0).T, rng).T
    out = np.zeros_like(W)
    out[B] = rng.permutation(W[W > 0])
    return out


def make_wiring(cond, W_pk, W_km, rng):
    """cond: 'real' | 'random' | 'shuffle' for both layers, or a (pn_kc, kc_mbon) tuple."""
    pk, km = cond if isinstance(cond, tuple) else (cond, cond)
    f = {"real": lambda W, r: W, "random": random_bipartite, "shuffle": degree_shuffle}
    return f[pk](W_pk, rng), f[km](W_km, rng)


# ---------- adapters ----------

def make_odors(n_odors, glom_of_pn, rng, p_active=0.2):
    """Odor -> glomerulus pattern: each glomerulus active w.p. p_active, amplitude Exp(1).
    PNs of one glomerulus share its value. Returns (n_odors, n_pn)."""
    n_glom = glom_of_pn.max() + 1
    g = (rng.random((n_odors, n_glom)) < p_active) * rng.exponential(1.0, (n_odors, n_glom))
    return g[:, glom_of_pn].astype(np.float32)


def pn_rates(odor, sigma, rng):
    """Independent Gaussian noise per PN, rectified."""
    return np.maximum(0, odor + sigma * rng.standard_normal(odor.shape).astype(np.float32))


def kc_code(pn, W_pk, frac):
    """APL as global inhibition = k-winners-take-all: the top `frac` of KCs by drive fire (binary).
    Only KCs with positive drive can fire. pn: (n, n_pn) -> (n, n_kc) float32 in {0,1}."""
    drive = pn @ W_pk
    k = max(1, int(round(frac * W_pk.shape[1])))
    thr = np.partition(drive, -k, axis=1)[:, -k][:, None]
    return ((drive >= thr) & (drive > 0)).astype(np.float32)


def mbon_out(kc, W_km):
    """Pooled MBON drive (sum over all MBONs). (n, n_kc) -> (n,)"""
    return kc @ W_km.sum(1)


def learn(W_km, kc, da, eta):
    """Three-factor depression (Hige et al. 2015): KC->MBON weights of active KCs shrink when DA
    arrives. dW_im = -eta * DA * KC_i * W_im. In place."""
    W_km *= (1 - eta * da * kc)[:, None]


def auc(pos, neg):
    """P(score of a random CS- presentation > random CS+ presentation); ties count 1/2."""
    pos, neg = np.asarray(pos), np.asarray(neg)
    d = neg[:, None] - pos[None, :]
    return float(((d > 0) + 0.5 * (d == 0)).mean())


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    W = (rng.random((30, 200)) < 0.1) * rng.integers(1, 20, (30, 200)).astype(np.float32)
    for f in (random_bipartite, degree_shuffle):
        S = f(W, rng)
        assert (S > 0).sum() == (W > 0).sum()
        assert np.allclose(np.sort(S[S > 0]), np.sort(W[W > 0]))
    S = degree_shuffle(W, rng)
    assert ((S > 0).sum(0) == (W > 0).sum(0)).all() and ((S > 0).sum(1) == (W > 0).sum(1)).all()
    assert (S > 0).astype(int).ravel() @ (W > 0).astype(int).ravel() < (W > 0).sum()  # actually moved
    kc = kc_code(rng.random((4, 30)).astype(np.float32), W, 0.1)
    assert (kc.sum(1) <= 20 + 5).all()
    assert auc([0, 0], [1, 1]) == 1 and auc([1], [1]) == 0.5
    print("mb self-check ok")
