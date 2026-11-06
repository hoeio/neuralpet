# Report: does the internal-state → dopamine rule matter for the pet? (experiment 002)

2026-11-06. Numbers from `reports/002/tables.md` (generated) and `experiments/002/results/runs.csv`.
n = 30 seeds per condition, paired by seed, 6,000 steps each, real FlyWire MB wiring, sparse
f = 0.10. All rules are in docs/ADAPTERS.md v2.

## Short answer

**Not supported: no detectable effect.** Making reward dopamine depend on energy (drive reduction,
after Keramati & Gutkin 2014) did not change how well the pet kept its energy up, compared with a
constant reward dopamine matched per seed in average size. Mean energy, on − off: −0.006
[−0.018, 0.005], d_z −0.19.

**But the test ran at the floor.** In both conditions the pet is a poor forager. Its energy is 0 for
78% (on) and 75% (off) of steps, with about 11–12 meals in 6,000 steps (~3 energy units gained
against 12 drained). In this regime a small rule change has little room to show.

## Results

| metric | on | off (matched) | on − off (paired) |
|---|---|---|---|
| mean energy (steps 1,001–6,000) | 0.042 [0.033, 0.052] | 0.048 [0.036, 0.062] | −0.006 [−0.018, 0.005] |
| meals | 11.1 [9.3, 13.0] | 12.3 [10.0, 14.8] | −1.2 [−3.0, 0.5] |
| toxic contacts | 19.9 [8.0, 39.7] | 9.2 [6.7, 12.2] | 10.7 [−1.3, 30.7] |
| learned valence gap (food − toxic) | 0.302 [0.237, 0.367] | 0.297 [0.228, 0.371] | 0.005 [−0.045, 0.058] |
| fraction of steps at energy 0 | 0.78 [0.74, 0.82] | 0.75 [0.70, 0.80] | 0.03 [−0.01, 0.07] |

- **Matched constant.** The constant reward DA was 0.79 on average across seeds (range 0.62–0.88).
  Because the pet is nearly always hungry, the "on" rule gives close to its maximum on most meals.
  So on and off deliver almost the same dopamine, which is another reason for the null.
- **Toxic contacts.** The "on" mean is driven by one seed (seed 21: 267 contacts, apparently stuck
  near a toxic source). Medians are 6.5 (on) and 7 (off).
- **Learning works in both conditions.** Food odours end up with higher learned valence than toxic
  odours (gap ≈ 0.30). That learning does not translate into enough food.

## What this means

The state → dopamine rule as designed makes no measurable difference in this world. The experiment
cannot tell "the rule never matters" apart from "the rule cannot matter when the pet is always
starving". This is a null under weak conditions, not evidence of absence.

## Recommended next step

Pre-register a new pet experiment (005) in a world where foraging is feasible:
- lower drain or more food, so energy varies over its range;
- fix the stuck-at-toxic behaviour, e.g. a stronger escape reflex.

Set the world parameters on a run with the modulation switched off, not on the comparison. Also
compare real vs shuffled wiring in the pet (rule 6) before claiming anything about the connectome
there.
