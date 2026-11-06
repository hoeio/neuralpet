# Experiment 001 — Does real MB wiring help DA-gated associative learning? (plan, 2026-11-06)

Written and committed before any learning run. Not edited afterwards. Changes go in a new note.

## Question
In a minimal binary KC model with Hige-style dopamine-gated KC→MBON depression, does the real
FlyWire right-hemisphere MB wiring (PN→KC and KC→MBON) learn faster, resist noise better, or suffer
less interference than matched fake wiring?

## Conditions
Wiring (applied to both PN→KC and KC→MBON; same neurons, same edge count, same multiset of synapse
weights in every condition):
- **random**: edges placed uniformly at random among all pairs, real weights randomly permuted onto them.
- **shuffle**: degree-preserving (every PN, KC, MBON keeps its degree; curveball algorithm, 5×n_KC
  trades), real weights randomly permuted onto the edges.
- **real**: FlyWire v783 (≥5 synapses per connection).
Sparsity (rule 7): `sparse` f = 0.10, `literal` f = measured fraction with "any input fires"
(docs/ADAPTERS.md v1 item 4). Full design: 3 wiring × 2 sparsity.

Seeds: 30 per cell. Seed s fixes odours, valences, and noise and is shared across conditions (paired
design). Control wirings are re-sampled per seed. Real wiring is the same in every seed.

## Task (all rules in docs/ADAPTERS.md v1; η = 0.02, training noise σ = 0.2)
1. Set A: 20 independent random odours, 10 punished (CS+), 10 not (CS−). A block = each odour once,
   random order. Train 20 blocks (400 trials). After every block, test (no learning): 10 presentations
   per odour at σ = 0.2 → AUC.
2. Noise test on the weights after 10 blocks (200 trials): AUC at σ_test ∈ {0, 0.5, 1, 2},
   10 presentations per odour.
3. Interference: from the 10-block weights, train a new set B (20 new odours, 10/10) for 10 blocks.
   Measure AUC on set A before and after (σ = 0.2).

Difficulty was set before this plan was committed, by a pilot on a **synthetic** random circuit of the
same size (no FlyWire data; scratch script, see docs/DECISIONS.md). The first draft (η = 0.1,
10 odours) was at ceiling (AUC = 1 after 10 trials) for every wiring, so it could not separate
conditions. Odour mixtures (shared base, ρ = 0.5–0.7) were tried and were too hard; they were dropped.

## Metrics (pre-specified primaries)
- **M1 trials to learn**: training trials until set-A AUC ≥ 0.9 (checked after each block of 20).
  Not reached within 400 trials → recorded as 410 (censored; the number censored is reported).
- **M2 noise robustness**: set-A AUC at σ_test = 1.0 after 10 blocks.
- **M3 interference**: AUC_A(before B) − AUC_A(after B). Lower is better.
Secondary: full learning curves, AUC vs σ_test, AUC_B, measured KC active fraction.

## Analysis
For each sparsity, each metric: paired mean difference real − shuffle and real − random over seeds,
95% bootstrap CI (10,000 resamples, percentile), and d_z = mean/sd of the paired differences. Also
condition means with bootstrap CIs. 12 primary contrasts (3 metrics × 2 contrasts × 2 sparsities);
CIs are uncorrected and a single isolated "hit" is weak evidence.

## What would prove the idea wrong
"Real wiring helps learning" is **not supported** if, for a metric, the CI of real − shuffle includes
0 or favours shuffle. If real beats random but not shuffle, the benefit is explained by degree
distribution, not specific wiring. If real is worse than the controls, report that real is worse.

## Known limitations (decided in advance)
Random odours (no receptor data); APL as idealised kWTA; pooled MBONs and a single global DA signal,
so DAN and compartment wiring are not tested; depression-only rule; η and odour statistics not varied.
Real wiring's known bias towards some glomeruli (Zheng 2022) is averaged away by random odours.
