# Experiment 004 — Is the 001 deficit an innate-bias artifact of the pooled readout? (plan, 2026-11-06)

Written and committed before running. Not edited afterwards.

## Background (exploratory, after 001 and 003)
003 located the 001 deficit in PN→KC wiring. Code statistics (overlap, dimension, reliability under
noise) differ only slightly between real and shuffled PN→KC. But the naive pooled MBON drive R0
varies ~3× more across odours with real PN→KC (CV 0.14 vs 0.045; one wiring sample, 200 odours).
Likely cause: real PN→KC routes glomeruli to particular KC types, and types differ in KC→MBON output
(αβ ≈ 37 synapses/KC, γm ≈ 10). With random valence, CS+ odours that start with high R0 need many
depressions to fall below CS− odours. The real fly has separate MBONs per compartment, so this may be
an artifact of our adapter v1 item 5 (all MBONs pooled), not a property of learning.

## Question
If the choice uses only what was *learned*, does real wiring still learn slower than matched controls?

## Change (adapter v1 → v1r, only item 8)
Choice and AUC use the ratio ρ = R(W_t)/R(W_0) for the same KC code of the same presentation, i.e. the
fraction of initial KC→MBON weight that remains on the active KCs. Everything else is exactly as 001
(same seeds, odours, noise streams, conditions, metrics M1–M3, analysis).

## Prediction and falsifier
Prediction: the real − shuffle gap in M1 and M2 shrinks a lot (to under half the 001 gap).
- **Wrong if** real − shuffle M1 (sparse) stays ≥ 50% of the 001 value (214 trials) with CI excluding
  that range, i.e. the CI lower bound stays above 107. Then the deficit is not mainly innate bias.
- Separately, "real wiring helps learning" is supported only if real beats shuffle (CI excludes 0).
