# Wiring nulls (PN→KC)

All nulls keep the node sets, the number of edges and the multiset of synapse weights. KC→MBON stays
real in experiments 007–011. Code: `src/neuralpet/mb.py` (N0/N1 and degree components),
`src/neuralpet/nulls.py` (N2). Verification: `experiments/010/verify_nulls.py` →
`reports/010/nulls.md` (10 draws per null, every connectome sample; wiring seeds 900–909, never used
for learning runs).

| name | keeps | destroys |
|---|---|---|
| `random` (N0) | edge count, weights | all degree structure |
| `shuffle` (N1, curveball) | every PN out-degree, every KC in-degree | partner identity, class-specific input, co-convergence beyond degrees |
| `pn_out` | every PN out-degree | KC in-degree, partners |
| `pn_out_perm_live` | the multiset of out-degrees among PNs with DoOR input (silent PNs keep theirs) | which live PN has which out-degree |
| `n2a_coconv` (N2a) | every KC's complete input vector (PNs, so glomeruli, with weights) as a unit, therefore all glomerulus-pair co-convergence counts exactly, every PN out-degree, the KC in-degree multiset | which KC (class, KC→MBON outputs) receives which input set |
| `n2b_subtype` (N2b) | every KC in-degree, every PN out-degree, every PN × KC-class (αβ, α′β′, γ, other) edge count | co-convergence beyond what those counts imply, partner identity within class |
| `real` | everything | nothing |

## Design choices (logged in docs/DECISIONS.md, 2026-11-07)
- **N2a** is a column permutation among KCs that have PN input (KCs with no PN input stay silent, as
  in N1). It preserves co-convergence at the PN level, which implies the glomerulus level (Zheng et al.
  2022 measured it at the glomerulus level). Because it is exact, it isolates one thing: the pairing
  between an input set and the KC that carries it (and so that KC's MBON outputs). Experiment 004
  suggested that this pairing is what makes real worse than shuffle with a pooled readout.
- **N2b** runs the curveball inside each KC class. KC classes come from cell types: `KCab*` → αβ,
  `KCapbp*`/`KCa'b'*` → α′β′, `KCg*` → γ (FlyWire and hemibrain names).
- Together with `shuffle` and `real` they span a 2 × 2 (co-convergence kept? × class/pairing kept?).

## Measured (from reports/010/nulls.md)
- N2a: `coconv_exact` True in all three samples; `kc_input_identical` ≤ 0.001 (pairing destroyed);
  class counts kept only at chance level (0.06–0.10).
- N2b: `class_counts_kept` = 1.0 in all samples; excess co-convergence correlation with real
  0.30 (FW right), 0.29 (FW left), 0.43 (hemibrain): class-level bias carries part, not all, of the
  co-convergence structure; plain shuffle 0.03–0.05.
- N1 (shuffle): degrees exact, class counts kept 0.09–0.13, excess co-convergence r ≤ 0.05.
