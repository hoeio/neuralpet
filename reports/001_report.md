# Report: does real mushroom-body wiring help dopamine-gated learning? (experiments 001, 003, 004)

2026-11-06. All numbers come from the script-generated tables `reports/001/tables.md`,
`reports/003/tables.md`, `reports/004/tables.md` and `experiments/003/results/explore.txt`.
Cells are mean [95% bootstrap CI]; n = 30 seeds per condition; paired by seed.

## Short answer

**No. In this model, real FlyWire MB wiring did not learn better than matched fake wiring on any
metric.**
- **001 (as planned):** real wiring learned *slower* and was *less* noise-robust than both a
  degree-preserving shuffle and a random network.
- **003:** almost all of that deficit came from the PN→KC layer.
- **004:** most of the learning-speed deficit was an artifact of our pooled MBON readout, which mixes
  KC types that differ a lot in output weight. With a readout that only uses what was learned, real
  and shuffle are close in learning speed. Real is still slightly worse on noise robustness and
  interference, and never better.

The pre-registered idea "real wiring helps" is **not supported**.

## Setup (fixed in advance: PLAN.md files, docs/ADAPTERS.md v1)

- **Circuit:** right-hemisphere MB from FlyWire v783 — 2,597 KCs, 48 MBONs, 149 olfactory PNs in 84
  input units, connections with ≥5 synapses (docs/MB_EXTRACTION.md).
- **Odours:** random (20% of glomeruli active, Exp(1) amplitudes); per-PN noise.
- **KC code:** binary k-winners-take-all — an idealised APL — at f = 0.10 ("sparse") or f = 0.552
  ("literal" = share of KCs with any input).
- **Plasticity:** KC→MBON depression on punishment (after Hige et al. 2015), η = 0.02.
- **Choice:** the odour with the lower pooled MBON drive is avoided.
- **Task:** 20 odours (10 CS+); 20 blocks of training; a noise test after 200 trials; then 200
  trials on a second set B.
- **Controls** (same neurons, same edge count, same weight multiset):
  - random edges;
  - degree-preserving curveball shuffle.

The task difficulty was set on a synthetic circuit before any FlyWire run, because the first
draft was at ceiling.

## Results

### 001: wiring as planned (pooled readout)

| sparse (f = 0.10) | random | shuffle | real |
|---|---|---|---|
| M1 trials to AUC ≥ 0.9 | 143 [121, 169] | 154 [133, 176] | 368 [344, 389] |
| M2 AUC at test noise σ = 1 | 0.80 [0.775, 0.823] | 0.779 [0.759, 0.799] | 0.619 [0.596, 0.642] |
| M3 interference (AUC drop) | 0.058 [0.043, 0.072] | 0.059 [0.045, 0.073] | 0.018 [−0.005, 0.041] |
| not learned by 400 trials | 1/30 | 0/30 | 18/30 |

Paired real − shuffle (sparse):
- M1: +214 trials [187, 241], d_z 2.76.
- M2: −0.16 [−0.188, −0.132].
- M3: −0.041 [−0.061, −0.021].

Literal code (f = 0.552), real − shuffle:
- M1: +79 trials [42, 118].
- M2: −0.041 [−0.058, −0.024].
- M3: −0.030 [−0.057, −0.002].

All conditions learn worse with the literal code than with the sparse code. This matches the idea
that sparseness helps (Lin et al. 2014).

**About the "better" interference for real wiring:** it is not a benefit. Real wiring had learned
set A less well before set B (lower AUC), so it had less to lose. Scaled by how much was learned,
real (0.064 [−0.053, 0.181]) is not distinguishable from shuffle (0.136 [0.103, 0.170]).

### 003: which layer? (hybrids, pre-registered prediction: PN→KC)

| sparse, M1 trials | KC→MBON real | KC→MBON shuffle |
|---|---|---|
| PN→KC real | 368 [344, 389] | 357 [331, 381] |
| PN→KC shuffle | 181 [153, 210] | 170 [145, 196] |

- **Real PN→KC adds about 187 trials** (+187 [159, 215] with shuffled KC→MBON).
- **Real KC→MBON adds about 11** (+11 [4.7, 18.3] with real PN→KC; +11 [−18, 41] with shuffled
  PN→KC).
- The prediction held.

Code statistics differ only a little between real and shuffled PN→KC (sparse, 200 noise-free odours):

| measure | real | shuffle |
|---|---|---|
| mean code overlap (Jaccard) | 0.088 | 0.083 |
| dimension (participation ratio) | 60.7 | 66.4 |
| KCs that ever fire | 85% | 88% |

The real code is somewhat lower-dimensional, as Li et al. 2020 found for the hemibrain. Two other
exploratory checks found no difference: same-odour reliability under noise, and the number of
promiscuous KCs. Those two candidate explanations are ruled out.

**What does differ:** the naive pooled MBON drive R0 varies about 3× more across odours with real
PN→KC (exploratory, one wiring sample):

| PN→KC | R0 coefficient of variation |
|---|---|
| real | 0.14 |
| shuffle | 0.045 |

KC types differ a lot in output: αβ KCs average 37 KC→MBON synapses, γm KCs 10. So which KCs an
odour recruits sets its starting R0. With random valences, a punished odour that starts high needs
many depressions.

### 004: remove that innate bias (pre-registered; only the choice rule changed)

The choice used R(W_t)/R(W_0) on the same KC code, i.e. only the learned change.

| sparse (f = 0.10) | random | shuffle | real |
|---|---|---|---|
| M1 trials | 24 [20, 32] | 24 [20, 32] | 51 [22, 90] |
| M2 AUC at σ = 1 | 0.886 [0.868, 0.903] | 0.849 [0.830, 0.866] | 0.816 [0.796, 0.835] |
| M3 interference | 0.063 [0.050, 0.076] | 0.072 [0.058, 0.088] | 0.093 [0.076, 0.111] |

Paired real − shuffle:

| contrast | sparse | literal |
|---|---|---|
| M1 trials | +27 [−3, 68] | +99 [27, 171] |
| M2 AUC | −0.032 [−0.041, −0.022] | −0.040 [−0.052, −0.027] |
| M3 interference | +0.020 [0.005, 0.036] | −0.007 [−0.026, 0.013] |

- The pre-registered falsifier was a CI lower bound above 107 trials. It was not met, so the
  innate-bias explanation stands for M1.
- Even so, real wiring is not better than shuffle on any metric, under either sparsity.
- Random wiring is best or tied-best on M1 and M2 in every analysis. This is in line with
  random-expansion theory (Litwin-Kumar et al. 2017).

## What this means and what it does not

**Means.** In a minimal model with random odours, the real PN→KC wiring gives no learning advantage
over a degree-matched shuffle. Because the shuffle keeps every node's degree, the real − shuffle gap
is about which PN connects to which KC, not about degree distributions. The large slowdown in 001 came from how real wiring
interacts with our pooled readout — odour identity is coupled to KC types with very different
output weights.

**Does not mean.** That the fly's wiring is "bad". This model is missing several things the fly
has. The two that matter most:
- **Odour statistics.** Real odours are not random. Zheng et al. 2022 and MacKenzie et al. 2025
  report that real PN→KC is biased towards specific (e.g. food-related) glomeruli. Random odours
  average that away.
- **Compartment structure.** The fly has separate MBONs per compartment, with separate DANs and
  valences. Pooling all MBONs is our simplification, and 004 shows it matters.

The model also leaves out spiking, KC–KC and APL wiring, non-olfactory KC input, and potentiation.

**Adapter artifact.** In literal mode, AUC at test noise σ = 0 is *lower* than at σ = 0.5 for every
wiring (reports/001/noise.png). Training used σ = 0.2. Without noise, fewer KCs have positive drive
(0.51 vs 0.55), so test codes differ from training codes. M2 (σ = 1) is not affected.

**Multiple comparisons.** 001 had 12 primary contrasts, so isolated CIs are weak evidence. The main
pattern — real ≥ shuffle never true — is consistent across metrics, sparsities and readouts.

## Recommended next steps

1. **Compartment readout.** Use the real DAN→compartment and MBON grouping in place of pooling,
   with a matched random grouping as control (rule 6).
2. **Structured odours.** Use odours with real receptor/glomerulus statistics (e.g. Hallem & Carlson
   2006 data — verify before citing), and odours targeting the over-represented glomeruli.
3. **A ≥1-synapse variant.** Test whether the ≥5-synapse threshold matters.
