"""Type-preserving (N2) nulls for PN->KC wiring and the statistics that verify them. docs/NULLS.md.

All nulls keep the node sets, the edge count and the weight multiset of W_pk (n_pn x n_kc).
"""
import numpy as np

from neuralpet import mb


def kc_class(kc_type):
    """Map cell-type strings (FlyWire or hemibrain) to the three main KC classes."""
    t = np.asarray(kc_type).astype(str)
    out = np.full(len(t), "other", dtype=object)
    out[np.char.startswith(t, "KCab")] = "ab"
    out[np.char.startswith(t, "KCapbp") | np.char.startswith(t, "KCa'b'")] = "apbp"
    out[np.char.startswith(t, "KCg")] = "g"
    return out.astype(str)


def n2a_coconv(W, rng):
    """N2a: every KC input vector (its whole set of PN, hence glomerulus, inputs with weights) is kept
    intact but moved to a random other KC that also has input. Keeps all co-convergence counts, PN
    out-degree and the KC in-degree multiset exactly; destroys which KC (class, KC->MBON output) gets
    which input set."""
    live = np.flatnonzero(W.sum(0) > 0)
    out = W.copy()
    out[:, live] = W[:, rng.permutation(live)]
    return out


def n2b_subtype(W, rng, cls):
    """N2b: degree-preserving curveball shuffle run separately inside each KC class. Keeps every KC's
    in-degree, every PN's out-degree, and every PN x class edge count; destroys co-convergence beyond
    what those counts imply. Weights permuted within class."""
    out = np.zeros_like(W)
    for c in np.unique(cls):
        cols = np.flatnonzero(cls == c)
        sub = W[:, cols]
        B = mb.curveball((sub > 0).T, rng).T
        blk = np.zeros_like(sub)
        blk[B] = rng.permutation(sub[sub > 0])
        out[:, cols] = blk
    return out


CONDS = ["random", "shuffle", "pn_out", "pn_out_perm_live", "n2a_coconv", "n2b_subtype", "real"]


def make_pk(cond, W, rng, cls, live):
    """PN->KC wiring for experiment 010. live: bool per PN (any DoOR input)."""
    if cond == "real":
        return W
    if cond == "random":
        return mb.random_bipartite(W, rng)
    if cond == "shuffle":
        return mb.degree_shuffle(W, rng)
    if cond == "pn_out":
        return mb.keep_row_degree(W, rng)
    if cond == "pn_out_perm_live":
        return mb.permute_rows(mb.keep_row_degree(W, rng), rng, np.flatnonzero(live))
    if cond == "n2a_coconv":
        return n2a_coconv(W, rng)
    if cond == "n2b_subtype":
        return n2b_subtype(W, rng, cls)
    raise ValueError(cond)


# ---------- verification statistics ----------

def glom_by_kc(W, glom):
    G = np.zeros((glom.max() + 1, W.shape[1]))
    np.add.at(G, glom, (W > 0).astype(float))
    return G


def coconv(W, glom):
    """Glomerulus x glomerulus co-convergence counts (# KCs receiving from both), off-diagonal."""
    G = (glom_by_kc(W, glom) > 0).astype(float)
    C = G @ G.T
    np.fill_diagonal(C, 0)
    return C


def class_counts(W, cls):
    """PN x KC-class edge counts."""
    return np.stack([(W[:, cls == c] > 0).sum(1) for c in np.unique(cls)], 1)


def stats(W, W_real, glom, cls, C_exp):
    """What a null keeps (1 = exact) and destroys. C_exp = mean co-convergence under the plain
    degree-preserving shuffle, so 'excess' co-convergence is the structure beyond degrees."""
    iu = np.triu_indices(glom.max() + 1, 1)
    ex_r = (coconv(W_real, glom) - C_exp)[iu]
    ex_n = (coconv(W, glom) - C_exp)[iu]
    B, Br = W > 0, W_real > 0
    live = Br.sum(0) > 0
    return dict(
        pn_out_kept=float(((B.sum(1)) == Br.sum(1)).mean()),
        kc_in_kept=float((B.sum(0) == Br.sum(0)).mean()),
        kc_in_multiset_kept=bool((np.sort(B.sum(0)) == np.sort(Br.sum(0))).all()),
        class_counts_kept=float((class_counts(W, cls) == class_counts(W_real, cls)).mean()),
        coconv_exact=bool((coconv(W, glom) == coconv(W_real, glom)).all()),
        excess_coconv_r=float(np.corrcoef(ex_r, ex_n)[0, 1]),
        kc_input_identical=float((B[:, live] == Br[:, live]).all(0).mean()),
        edge_overlap=float((B & Br).sum() / Br.sum()),
        weights_kept=bool(np.allclose(np.sort(W[B]), np.sort(W_real[Br]))))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    W = ((rng.random((30, 300)) < 0.12) * rng.integers(5, 20, (30, 300))).astype(np.float32)
    W[:, :20] = 0
    cls = np.array(["ab", "g", "apbp"])[rng.integers(0, 3, 300)]
    glom = np.arange(30) // 2
    a = n2a_coconv(W, rng)
    assert (coconv(a, glom) == coconv(W, glom)).all() and (a[:, :20] == 0).all()
    b = n2b_subtype(W, rng, cls)
    assert (class_counts(b, cls) == class_counts(W, cls)).all() and ((b > 0).sum(0) == (W > 0).sum(0)).all()
    assert (b > 0).sum() == (W > 0).sum() and np.allclose(np.sort(b[b > 0]), np.sort(W[W > 0]))
    assert list(kc_class(["KCab-p", "KCapbp-m", "KCa'b'-ap1", "KCg-d", ""])) == ["ab", "apbp", "apbp", "g", "other"]
    print("nulls self-check ok")
