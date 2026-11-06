# Experiment 008 — Does it matter *which* PNs get the high out-degree? (plan, 2026-11-06)

Written and committed before running. Not edited afterwards.

## Why
In 007, keeping each PN's out-degree (`pn_out`) beat random PN→KC wiring with DoOR odours but hurt
with random odours. Two explanations:
- **Assignment:** the connectome gives many KC partners to the PNs whose glomeruli carry the most
  DoOR signal (007 exploratory: r ≈ 0.38). Then the benefit needs the real PN ↔ out-degree pairing.
- **Skew alone:** any uneven out-degree distribution helps with DoOR odours, whatever PN has it.

## Conditions (PN→KC only; KC→MBON real everywhere; 10,505 edges and the real weight multiset)
- `random`, `pn_out`, `shuffle`, `real`: as in 007.
- `pn_out_perm`: `pn_out`, then the PN rows are randomly permuted. Same out-degree values, assigned to
  random PNs; partners uniform.
- `shuffle_perm`: `shuffle`, then PN rows permuted. Keeps KC in-degree and the out-degree values, breaks
  the PN ↔ degree pairing.
- `real_perm`: real matrix with PN rows permuted. Keeps every KC's set-size and which KCs share inputs,
  but PN identities are scrambled.
Rows are permuted across all 149 PNs, including multiglomerular PNs (which get no DoOR input), so a
permuted high-degree row can land on an uninformative PN. That is part of what is being tested.

Odours: DoOR (adapter v4) primary, random (v1) reference. Sparsity 0.10 and literal (0.552). 30 seeds,
paired by seed. Task, η, noise, readouts exactly as in 006/007. No adapter changes.

## Metric
Primary: M2_ratio (AUC at σ = 1 after training, ratio readout). Secondary: plateau_ratio, M3_ratio.

## Questions and falsifiers (DoOR; each in both sparsity settings)
- **Q1.** pn_out − pn_out_perm. "The real PN ↔ out-degree pairing matters" is supported if the CI is
  above 0. If it includes 0, the assignment idea is not supported (skew alone, or nothing).
- **Q2.** pn_out_perm − random. If above 0, skew alone helps.
- **Q3.** shuffle − shuffle_perm: same as Q1 with KC in-degree also kept.
- **Q4.** real_perm − real: does scrambling PN identities on the real matrix change robustness?
  (Above 0 would mean the specific real PN assignment hurts.) Reported both directions, no prediction.
- Reference (random odours): Q1–Q3 should be ≈ 0, since no glomerulus is more informative there.
- Prediction stated in advance: Q1 > 0 and Q3 > 0 with DoOR; Q2 ≈ 0 or < 0.
