# Experiment 010 — deviation note (2026-11-07, written after the first run, before the rerun)

**What went wrong.** PLAN.md registers the task parameters chosen by the synthetic pilot (grid 3):
n = 8 odours per set, η = 0.02, readout noise σ_out = 0.01 (also in docs/ADAPTERS.md v6). The code's
default `task.P` in `src/neuralpet/task.py` was never updated from its pre-pilot placeholder
(n = 12, η = 0.01, σ_out = 0.05; the pilot passed its own parameters, so the pilot was correct). The
first 010 run therefore used **unregistered, harder parameters** — close to pilot grid 1, where the
literal code sat near the floor. This was found only after seeing the 010 and 011 results, when reading
`results/meta.json`.

**What is done about it (decided before any rerun):**
1. The first run's raw outputs stay untouched in `experiments/010/results/` (and 011's in
   `experiments/011/results/`). Their tables move to `reports/010/deviation/` and `reports/011/deviation/`.
2. `task.P` is set to the registered values. 010 is rerun **exactly as PLAN.md registers it** (same
   seeds 1000–1063, same conditions, family, SESOI and verdict rules) into
   `experiments/010/results_registered/`; its tables go to `reports/010/`. 011 likewise into
   `experiments/011/results_registered/`.
3. The registered run is the confirmatory result. The deviation run is reported next to it as a
   robustness check at a harder setting, labelled as such, never as the headline.
4. Nothing else changes. Whatever the registered run shows is reported, including if it differs from
   the deviation run.
