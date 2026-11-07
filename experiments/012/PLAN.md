# Experiment 012 — A pet whose state rule can be tested (plan, 2026-11-07)

Written and committed before any run on connectome wiring. Not edited afterwards.

## Why
Experiment 002 tested the energy-dependent reward dopamine in a world where the pet starved ~75–77% of
the time, so the test was at the floor (review item 6). This experiment uses the WP5a body
(docs/CREATURE.md) in a world fixed beforehand on synthetic wiring with reward modulation off
(`experiments/012/pilot.py`, rounds 1–7; docs/ADAPTERS.md v5 and v8). The run asserts that the creature
constants equal the registered v8 values.

## Setup
FlyWire v783 right MB (real PN→KC and KC→MBON), WP5a body, 6 × 6 BL torus, 4 food + 2 toxic sources
with random DoOR odorants, life of 2400 s simulated time, mortality on (120 s at zero energy ends the
life). **Seeds 2000–2039 (40)** for the main comparison. A seed fixes the world and the noise; the same
seed is used for every condition (paired).

## Conditions (main)
- `on`: reward DA = homeostatic drive reduction (Keramati & Gutkin 2014 form).
- `const`: reward DA = the per-seed mean reward DA of the `on` run (modulation off, matched size).
- `generic`: a size-matched generic substitute for the state module: same input (energy before the
  meal), a random quadratic max(0, a + b·e + c·e²) with (a, b, c) ~ N(0, 1) per seed, rescaled so its mean
  over the `on` run's pre-meal energies equals the `on` mean reward DA (rule 6 control).
- `shuffle_on`: `on` with degree-preserving shuffled PN→KC wiring (real vs shuffled inside the pet).
- `steer_off`: `on` with brain steering switched off (sanity check of the body–brain loop; **not a
  headline**).

## Confirmatory family (6 tests, Holm)
Primary metrics: **survival time** (s, capped at 2400) and **mean energy** over the life.
S1 on − const, S2 on − generic, S3 on − shuffle_on; each on both metrics. Paired t-test across the 40
seeds, Holm across the 6 tests; 95% bootstrap CIs; d_z.
- The state rule "matters" if S1 and S2 are Holm-significant on at least one primary metric with the
  same sign. If S1 is significant but S2 is not, the effect is not specific to the homeostatic form
  (a generic state-dependent signal does as well). If neither, the null is reported.
- Real wiring "helps the pet" if S3 is Holm-significant and positive.
- **Risk written now:** the pilot world keeps energy well above zero (mean ≈ 0.6 on synthetic wiring),
  so deaths may be rare and survival may be at its ceiling for all conditions; then mean energy carries
  the comparison and the survival result is reported as uninformative, not as "no effect".
- **What would show the state rule does nothing here:** all S1/S2 CIs within ±0.02 mean energy and
  ±60 s survival.

## Sanity check (reported, not a headline)
on − steer_off on meals and mean energy. Expected: steering helps (more meals). On the synthetic pilot
circuit it did not (round 7: 12.9 vs 13.3 meals), so a null here is possible and will be reported as
"brain-driven steering did not measurably help foraging".

## Pre-specified secondary analyses
- **Individuality.** One genome (real wiring, fixed constants), 20 individuals (seeds 3000–3019) with
  different histories: each lives 2400 s (no mortality) in its own world drawn from a panel of 8 DoOR
  odorants (3 food, 2 toxic roles at random). For 5 of those histories, 4 extra individuals share the
  world but use other noise streams. Preference vector = learned valence of the 8 panel odorants at the
  end. Measures: mean pairwise distance between individuals with different histories vs the same
  history; correlation of each individual's preferences with its own history (food +1, toxic −1,
  absent 0) vs with other individuals' histories (seed-shuffled baseline). Individuality is "met" if
  own-history correlation exceeds the shuffled baseline (CI of the difference above 0) and
  different-history distance exceeds same-history distance.
- **Adaptation to environment change.** 20 seeds (4000–4019), food and toxic sources swap roles at
  1200 s; paired with the same seeds without the swap. Gap = valence(new food odours) − valence(new
  toxic odours). Adaptation is "met" if the gap rises from the swap to the end (CI above 0).

## Run
`uv run python experiments/012/run.py` → `experiments/012/results/{main,indiv,reversal}.csv`,
`reports/012/tables.md`, `reports/012/pet.png`. Operational life criteria are summarised in
docs/LIFE_CRITERIA.md afterwards.
