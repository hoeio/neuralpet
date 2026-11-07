"""Associative-learning task v6 (experiments 010, 011). Rules in docs/ADAPTERS.md v6.

Differences to the 001-009 task: the choice readout has fixed output noise, so a learned change
must outgrow that noise and the learning curve rises over blocks instead of jumping after one block;
learning speed is the area under the learning curve (AULC), not trials-to-criterion (no censoring).
"""
import numpy as np

from neuralpet import mb

# fixed by the synthetic pilot (experiments/010/pilot.py), registered in docs/ADAPTERS.md v6
P = dict(n=8, eta=0.02, sig_train=0.2, sig_test=1.0, sig_out=0.01, blocks=12, blocks_b=6, reps=12)


def apl_kwta(drive, frac):
    k = max(1, int(round(frac * drive.shape[1])))
    thr = np.partition(drive, -k, axis=1)[:, -k][:, None]
    return ((drive >= thr) & (drive > 0)).astype(np.float32)


def run(W_pk, W_km, A, B, seed, frac, p=P, kc_fn=None, da_mask=None):
    """One learning run. A, B: (2n, n_pn) odour sets (first half CS+ after a seeded permutation).
    kc_fn(pn_rates) -> KC code; default kWTA. da_mask: (n_mbon,) 0/1, MBONs the punishment DA reaches
    and that are read out (compartment model, experiment 011); default all.
    Returns dict of metrics; curve = AUC after each block (block 0 = before training)."""
    n = p["n"]
    kc_fn = kc_fn or (lambda x: apl_kwta(x @ W_pk, frac))
    m = np.ones(W_km.shape[1]) if da_mask is None else np.asarray(da_mask, float)
    W0 = W_km.astype(np.float64)
    W = W0.copy()
    task = np.random.default_rng([seed, 99])
    noise = np.random.default_rng([seed, 7])
    vA = task.permutation(np.r_[np.ones(n // 2), np.zeros(n - n // 2)])
    vB = task.permutation(np.r_[np.ones(n // 2), np.zeros(n - n // 2)])

    def score(odors, val, Wt, sigma):
        X, y = np.repeat(odors, p["reps"], 0), np.repeat(val, p["reps"])
        kc = kc_fn(mb.pn_rates(X, sigma, noise))
        r = (kc @ (Wt * m)).sum(1) / np.maximum((kc @ (W0 * m)).sum(1), 1e-9)
        r = r + p["sig_out"] * noise.standard_normal(len(r))
        return mb.auc(r[y == 1], r[y == 0])

    def block(odors, val, Wt):
        for i in noise.permutation(len(odors)):
            kc = kc_fn(mb.pn_rates(odors[i:i + 1], p["sig_train"], noise))[0]
            Wt *= 1 - p["eta"] * val[i] * np.outer(kc, m)

    curve = [score(A, vA, W, p["sig_train"])]
    for _ in range(p["blocks"]):
        block(A, vA, W)
        curve.append(score(A, vA, W, p["sig_train"]))
    c = np.array(curve)
    out = dict(aulc=float(c[1:].mean()), plateau=float(c[-3:].mean()),
               m2=score(A, vA, W, p["sig_test"]), curve=c.round(4).tolist())
    before = score(A, vA, W, p["sig_train"])
    Wb = W.copy()
    for _ in range(p["blocks_b"]):
        block(B, vB, Wb)
    out["m3"] = before - score(A, vA, Wb, p["sig_train"])
    out["kc_active"] = float(kc_fn(mb.pn_rates(A, 0.0, noise)).mean())
    return out


def pick_sets(pool, n, rng):
    """Two disjoint odour sets of n from an odour pool (rows)."""
    i = rng.permutation(len(pool))
    return pool[i[:n]], pool[i[n:2 * n]]


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    W_pk = ((rng.random((40, 500)) < 0.1) * 10).astype(np.float32)
    W_km = ((rng.random((500, 6)) < 0.5) * 5).astype(np.float32)
    pool = mb.make_odors(40, np.arange(40), rng)
    A, B = pick_sets(pool, P["n"], rng)
    r1, r2 = run(W_pk, W_km, A, B, 1, 0.1), run(W_pk, W_km, A, B, 1, 0.1)
    assert r1 == r2, "not deterministic"
    assert abs(r1["curve"][0] - 0.5) < 0.15 and r1["plateau"] > r1["curve"][0]
    print("task self-check ok", {k: v for k, v in r1.items() if k != "curve"})
