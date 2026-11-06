# Experiment 003 — Why does real wiring learn slower in 001? (plan, 2026-11-06)

Written and committed before running. Not edited afterwards. Follows from experiment 001, where real
FlyWire MB wiring needed more trials, was less noise-robust, and (as a by-product) showed less
interference than degree-preserving shuffle and random wiring.

## Question
Which layer causes the 001 deficit: PN→KC wiring, KC→MBON wiring, or both? And what property of the
KC code goes with it?

## Part A — hybrid wirings (learning)
Same task, adapters (v1), metrics M1–M3, seeds (30) and analysis as experiment 001. Conditions are
(PN→KC, KC→MBON):
- (real, real), (real, shuffle), (shuffle, real), (shuffle, shuffle). Both sparsities.
Predictions stated in advance: the deficit comes mainly from PN→KC (real, ·) because the pooled
readout only sees each KC's total output weight.
- **The prediction is wrong if** (shuffle, real) is as slow as (real, real), or (real, shuffle) is
  as fast as (shuffle, shuffle). Measured by M1, with CIs of paired differences.

## Part B — KC code diagnostics (no learning)
For real / shuffle / random PN→KC, sparse and literal f, 200 random v1 odours, noise-free:
- mean pairwise Jaccard overlap of KC codes;
- participation-ratio dimension of the KC code matrix;
- fraction of KCs that fire for at least one odour;
- Gini coefficient of per-KC firing probability.
- Input concentration: Gini of total PN→KC synapses per input unit (glomerulus or mPN). Degree-
  preserving shuffle keeps each PN's edge count but permutes weights, so per-PN synapse totals can
  differ from real. Reported as a check.
Shuffle/random: 30 wiring samples, mean and 95% bootstrap CI.

## Also check
M3 interference in 001 depends on how much was learned. Report interference relative to what was
learned: (AUC_A before − AUC_A after) / (AUC_A before − 0.5). Secondary, exploratory.
