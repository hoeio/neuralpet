# Experiment 005 — Compartment readout (plan, 2026-11-06)

Written and committed before any learning run with this readout. Not edited afterwards.

## Why
004 showed that most of the 001 learning-speed deficit came from pooling all 48 MBONs. That pool
mixes KC types whose output weights differ a lot (αβ ≈ 37 synapses/KC vs γm ≈ 10). In the fly,
punishment dopamine acts in specific compartments, each read by its own MBONs. This experiment puts
that structure in, derived from the connectome, and repeats the main question.

## Compartment rule (adapter v3, derived from data before any run; see docs/ADAPTERS.md)
- Punishment DANs = the 8 right-hemisphere `PPL1*` DANs.
- A PPL1 DAN gates an MBON if it makes **≥ 20 synapses** onto it (direct DAN→MBON). The threshold
  was chosen from the DAN→MBON table only: each PPL1 DAN has 1–3 strong targets (21–263 synapses)
  and scattered weak ones (5–16). Result: **P = 15 MBONs** (14 with KC input). Most get input from
  one KC class, e.g. two MBON14 cells and MBON18 receive only αβ KCs; MBON16, 28 and 31 receive
  only α′β′.
- Plasticity (v1 item 7) applies **only to KC→MBON synapses onto MBONs in P**.
- **Readout (primary): S = Σ_{m∈P} R_m / μ_m.** R_m = Σ_i W_im·KC_i. μ_m = the MBON's mean naive
  response to 100 fixed reference odours (noise-free, the condition's own wiring and sparsity,
  computed before training; MBONs with μ_m = 0 are left out). Each compartment MBON gets equal
  weight. The odour with lower S is avoided.
- Secondary readout: ratio Σ_P R_m(W_t) / Σ_P R_m(W_0) on the same code (as in 004, restricted to P).

## Conditions
Wiring {random, shuffle, real} (both layers, exactly as 001) × grouping × sparsity {sparse 0.10,
literal 0.552}. Grouping:
- `real`: the connectome-derived P.
- `random`: 15 MBONs drawn uniformly from all 48 (new draw per seed). Size-matched control for the
  "biological" grouping (rule 6).

30 seeds per cell. Same seeds, odours, noise streams, task, η and metrics M1–M3 as 001.

## Questions, predictions, falsifiers
- **Q1 (main question).** With the real grouping, does real wiring beat shuffle and random?
  "Real wiring helps" is not supported if the CI of real − shuffle includes 0 or favours shuffle,
  for each of M1–M3. My prediction: it will not beat shuffle.
- **Q2 (rule 6).** With real wiring, does the real grouping learn better than a random grouping of
  the same size? "Compartment structure matters" is not supported if the CI of real − random grouping
  includes 0 for M1 and M2.
- **Q3 (artifact).** With real grouping, the real − shuffle M1 gap (sparse) is smaller than in 001
  (214 trials). Wrong if the CI lower bound stays above 107.

## Analysis
As in 001: paired mean differences with 95% bootstrap CIs (10,000 resamples) and d_z. Contrasts:
real − shuffle and real − random wiring (real grouping); real − random grouping (real wiring); both
sparsities. CIs uncorrected.

## Known limits
Only aversive (PPL1) learning; PAM/reward compartments not used. MBON valence and output pathways not
modelled: the readout sums punishment compartments with equal weight. μ_m normalisation is an
adapter choice. Random odours as before.
