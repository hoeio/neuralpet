# Experiment 006 — Real odours (DoOR 2.0): does real wiring help with natural odour statistics? (plan, 2026-11-06)

Written and committed before any learning run with DoOR odours. Not edited afterwards.

## Why
001–005 used random odours. Real PN→KC wiring is biased towards particular glomeruli (Zheng et al.
2022; MacKenzie et al. 2025), and random odours average that away. If real wiring has an advantage,
odours with natural statistics are the most likely place to see it.

## Odours (adapter v4, docs/ADAPTERS.md)
- **Source:** DoOR 2.0 (Münch & Galizia 2016, Sci Rep 6:21841), response matrix from
  ropensci/DoOR.data (CC BY-SA 4.0), fetched by `scripts/fetch_door.py`.
- **Glomeruli:** 47 of our 55 PN glomeruli have DoOR data.
- **Odorants:** kept if measured for ≥ 60% of those 47 → **60 odorants**.
- **Values:** response − the receptor's spontaneous rate, clipped at 0. Missing values → 0.
  Glomeruli without data and multiglomerular PNs → 0.
- **Scale:** one global factor (4.89) so the mean input-unit value is 0.2, the same as v1 random
  odours.
- **Measured before this plan, no learning run:**

  | | DoOR | random v1 |
  |---|---|---|
  | input units active | 29% | 20% |
  | mean pairwise odour correlation | 0.30 | 0.00 |

## Conditions
Odour source {random v1, DoOR} × wiring {random, shuffle, real} × sparsity {sparse 0.10, literal
0.552}. 30 seeds per cell, paired by seed.
- Each seed draws set A = 18 odours and set B = 18 different odours (DoOR: from the 60; random: new
  v1 odours), 9 CS+ / 9 CS− per set.
- Everything else is as in 001: η = 0.02, σ_train 0.2, 20 blocks, snapshot at 10, 10 blocks of B,
  metrics M1 (cap 360 + 10 = 370), M2 (AUC at σ = 1), M3.
- **Primary readout: ratio** (004). The pooled readout (001) is recorded on the same runs as
  secondary.

## Questions and falsifiers
- **Q1.** With DoOR odours, does real wiring beat shuffle? Not supported if the CI of real − shuffle
  includes 0 or favours shuffle (each of M1–M3, ratio readout).
- **Q2 (interaction).** Is real wiring relatively better with DoOR odours than with random odours?
  Statistic: [(real − shuffle) under DoOR] − [(real − shuffle) under random], paired by seed, for M1
  and M2. Not supported if the CI includes 0 or goes the other way.
- My expectation, stated in advance: no advantage for real (the earlier experiments never showed
  one). The DoOR task will be harder for every wiring because odours are correlated.

## Limits
DoOR covers 47/55 glomeruli and no multiglomerular PNs. Missing values become 0, which may make odours
look sparser along some glomeruli. Odorant concentrations are not modelled. Single global scale.
