# Experiment 009 — Out-degree matching within DoOR-input PNs (plan, 2026-11-06)

Written and committed before running. Not edited afterwards.

## Why
In 008, permuting PN rows across all 149 PNs removed the pn_out benefit with DoOR odours. But real wiring
puts 82% of KC edges on the 95 PNs with DoOR input versus 64% after permutation (008 explore.py), so the
loss could just be edges moved onto silent PNs (multiglomerular, or glomeruli without DoOR data).

## Conditions (PN→KC only; KC→MBON real; 10,505 edges, real weight multiset)
- `pn_out`, `pn_out_perm` (all PNs), `random`: as in 008.
- `pn_out_perm_live`: `pn_out`, then rows permuted only among the 95 PNs with any DoOR input; silent
  PNs keep their rows. Edge mass on live PNs is unchanged (82.2%).
- `pn_out_perm_silent`: rows permuted only among the 54 silent PNs.
"Live" = the PN gets a non-zero value for at least one of the 60 DoOR odorants (adapter v4), decided
from the odour table only. DoOR odours only (with random odours no PN is silent, so the split is
undefined). Sparsity 0.10 and literal. 30 seeds, paired. Task, η, noise, readout as in 006–008.

## Metric
Primary M2_ratio; secondary plateau_ratio.

## Questions and falsifiers (both sparsity settings)
- **Q1.** pn_out − pn_out_perm_live. "Coverage is matched to informative channels *within measured
  glomeruli*" is supported if the CI is above 0. If it includes 0, the 008 effect is explained by
  edges on silent PNs, not by matching among live PNs.
- **Q2.** pn_out − pn_out_perm_silent. Predicted ≈ 0 (silent PNs give no input, so their rows should
  not matter). A non-zero value would point to a bug or a side effect of the code.
- **Q3 (replication).** pn_out − pn_out_perm as in 008.
- No prediction stated for Q1.
