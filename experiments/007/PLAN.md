# Experiment 007 — Which degree property helps with real odours? (plan, 2026-11-06)

Written and committed before running. Not edited afterwards.

## Why
In 006 (DoOR odours), wirings that keep the connectome's degrees (real, shuffle) beat random wiring
on noise robustness, and real never beat the shuffle. So the degree distribution, not the specific
partners, carried the benefit. The PN→KC degree structure has two parts:
- PN out-degree: how many KCs each PN, and so each glomerulus, reaches. Some PN types reach many
  more KCs than others (MacKenzie et al. 2025).
- KC in-degree: how many PNs each KC samples (0–9 here).

## Conditions (PN→KC only; KC→MBON is real in every condition)
Edges always total 10,505 and carry the real weight multiset, randomly permuted:
- `real`: FlyWire.
- `shuffle`: both degrees kept (curveball, as before).
- `pn_out`: each PN keeps its number of KC partners; partners drawn uniformly without replacement.
- `kc_in`: each KC keeps its number of PN inputs; inputs drawn uniformly without replacement.
- `random`: neither kept (as before).

Odours: DoOR (adapter v4, 18 per set) as primary, random v1 as reference. Sparsity: sparse 0.10 and
literal 0.552. 30 seeds per cell, paired by seed. Task, η and noise as in 006.

## Metric
- **Primary: M2_ratio**, AUC at σ = 1 after 180 trials, ratio readout.
- Also AUC at σ = 0.2 at the end of training (the plateau; 006 showed the ratio readout plateaus
  after one block), M3_ratio, and the pooled-readout versions.

## Questions and falsifiers (DoOR, sparse and literal)
- **Q1.** Does keeping PN out-degree alone beat random wiring? Not supported if the CI of
  pn_out − random includes 0.
- **Q2.** Does keeping KC in-degree alone beat random wiring? Same test.
- **Q3.** Is pn_out as good as the full shuffle? Statistic: shuffle − pn_out. "PN out-degree explains
  the degree benefit" is supported if this CI includes 0 and Q1 holds.
- **Q4 (replication).** Real − shuffle as in 006.
- Prediction stated in advance: PN out-degree carries most of the benefit (Q1 yes, Q3 ≈ 0); KC
  in-degree carries little.
