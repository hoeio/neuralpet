# Experiment 002 — Does the internal-state → dopamine rule matter for the pet? (plan, 2026-11-06)

Written and committed before any run. Not edited afterwards.

## Question
In the pet (docs/ADAPTERS.md v2, real FlyWire MB wiring, sparse f = 0.10), does making reward
dopamine depend on energy (drive reduction, Keramati & Gutkin 2014) change how well the pet keeps
its energy up, compared with a matched constant reward dopamine?

## Conditions
- **on**: DA_r = drive reduction (v2 item 6).
- **off (matched)**: DA_r = constant = mean DA_r per meal in the *on* run of the same seed (if the on
  run ate nothing: 0.5). Same average reward magnitude; only its dependence on state is removed.
Same seed → same odours, starting positions and noise stream at the start (paths diverge afterwards).
30 seeds per condition, 6,000 steps each.

## Metrics
- **Primary: mean energy over steps 1,001–6,000.**
- Secondary: meals eaten, toxic contacts, final learned valence gap (mean food V − mean toxic V),
  fraction of steps at energy 0.

## Analysis
Paired difference on − off, 95% bootstrap CI (10,000 resamples), d_z.

## What would prove the idea wrong
"The internal-state modulation matters" is **not supported** if the CI of on − off for mean energy
includes 0. Expectation stated in advance: the rule only reshapes when reward is large, so a null is
plausible. A null will be reported as such.

## Limits
One wiring (no wiring control here; 002 makes no claim about wiring). Curiosity does not touch
dopamine. Learning rate and world fixed, not explored.
