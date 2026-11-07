# Operational "life-like" criteria (WP5)

These are **operational tests of behaviour in a simulation**, not a claim that anything here is alive.
Each criterion is defined so that it can fail. The numbers are in `reports/012/tables.md` (made by
`experiments/012/run.py`) and are quoted in `reports/FINAL.md` by script; this page holds no numbers.

| criterion | operational test (experiment 012, PLAN.md) | verdict |
|---|---|---|
| **Self-maintenance**: keeps its internal variable away from the lethal bound by its own actions | fraction of life with energy > 0 and mean energy in a world where energy drains with effort; compared across state rules (S1, S2) | **met, but not specific.** Pets forage and keep energy above zero most of the time, yet the homeostatic dopamine rule did no better than a constant or a size-matched generic rule (S1, S2 null). Self-maintenance comes from the fixed body/world rules plus learning, not from the state rule we built. |
| **Precariousness / mortality**: can die, and dying depends on what it does | deaths within 2400 s with mortality on; survival time | **met (in the weak sense).** About half or more of the pets die within the life, so survival is not at ceiling. Whether dying depends on the brain is open: no condition (state rule, wiring, steering off) changed survival detectably. |
| **Individual divergence**: one genome, different histories → different, history-specific individuals | preference vectors of 20 individuals with different histories vs individuals sharing a history but not noise; correlation with own history vs a seed-shuffled baseline | **met.** Preferences track the individual's own history far above the shuffled baseline, and different histories give more different individuals than same history with different noise. |
| **Adaptation**: changes its learned behaviour when the world changes | food and toxic roles swap halfway; does the learned gap move towards the new roles? | **met, partly.** The gap moves towards the new roles (CI of the change above 0) but only reaches about zero by the end of the life: re-learning is slow and incomplete. |
| Brain-driven behaviour (sanity, not a life criterion) | steering on vs off | **not met.** Steering off made no detectable difference to meals, energy or survival. Under the registered steering gain the learned valence hardly steers the body (see the OPEN_QUESTIONS entry of 2026-11-08). |
| Reproduction | — | **untested** (future work). |
| Evolution / heredity | — | **untested** (future work). |

What these criteria do **not** say: nothing about experience, consciousness or biological fidelity.
The body, world, metabolism and every link between layers are designed rules (docs/ADAPTERS.md,
docs/CREATURE.md).
