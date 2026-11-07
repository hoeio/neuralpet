# Operational "life-like" criteria (WP5)

These are **operational tests of a simulation** (of behaviour or of internal learned state, as marked), not a claim that anything here is alive.
Each criterion is defined so that it can fail. The numbers are in `reports/012/tables.md` (made by
`experiments/012/run.py`) and are quoted in `reports/FINAL.md` by script; this page holds no numbers.

**When the criteria were set.** The 012 plan pre-specified "met" rules only for individual divergence and
adaptation. The self-maintenance and precariousness verdicts below were defined after the 012 results
(this page was first committed after them) and should be read as post hoc descriptions.

| criterion | operational test (experiment 012, PLAN.md) | verdict |
|---|---|---|
| **Self-maintenance**: keeps its internal variable away from the lethal bound by its own actions | fraction of life with energy > 0 and mean energy in a world where energy drains with effort; compared across state rules (S1, S2) | **met, but not specific (post hoc).** Pets keep energy above zero most of the time, yet the homeostatic dopamine rule did no detectably better than a constant rule or a generic substitute (S1, S2 inconclusive; the generic substitute was matched in expectation, not in realisation). What maintains energy here is the fixed body/world rules; no learning-off condition was run, so the role of learning is untested. |
| **Precariousness / mortality**: can die, and dying depends on what it does | deaths within 2400 s with mortality on; survival time | **met in the weak sense (post hoc).** About half or more of the pets die within the life, so survival is not at ceiling. Whether dying depends on the brain is open: no condition (state rule, wiring, steering off) changed survival detectably. |
| **Individual divergence**: one genome, different histories → different, history-specific learned preferences | preference vectors of 20 individuals with different histories vs individuals sharing a history but not noise; correlation with own history vs a seed-shuffled baseline | **met for internal valences (pre-specified rule).** Learned preferences track the individual's own history far above the shuffled baseline, and different histories give more different preference vectors than same history with different noise (still true, with much wider CIs, when individuals rather than pairs are resampled). These are internal valences: under the registered steering gain they barely reach behaviour, so behavioural individuality is not shown. |
| **Adaptation**: its learned preferences change when the world changes | food and toxic roles swap halfway; does the learned gap move towards the new roles? | **met for internal valences, partly (pre-specified rule).** The gap moves towards the new roles (CI of the change above 0) but only reaches about zero by the end of the life: re-learning is slow and incomplete. Not shown in behaviour, for the same reason as above. |
| Brain-driven behaviour (sanity, not a life criterion) | steering on vs off | **not met.** Steering off made no detectable difference to meals, energy or survival. Under the registered steering gain the learned valence hardly steers the body (see the OPEN_QUESTIONS entry of 2026-11-08). |
| Reproduction | — | **untested** (future work). |
| Evolution / heredity | — | **untested** (future work). |

What these criteria do **not** say: nothing about experience, consciousness or biological fidelity.
The body, world, metabolism and every link between layers are designed rules (docs/ADAPTERS.md,
docs/CREATURE.md).
