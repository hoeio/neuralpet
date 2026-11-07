# Experiment 010 — Confirmatory replication of the wiring question (plan, 2026-11-07)

Written and committed before any learning run on connectome wiring. Not edited afterwards.
Everything not listed under "Confirmatory family" is secondary or exploratory.

## Why
The only positive finding so far (PN out-degree helps noise robustness with DoOR odours, 006–009)
came from a chain of follow-ups each designed after seeing the previous result, with borderline CIs,
no multiplicity correction, one connectome sample, one odour dataset and re-used seeds (review, items
1–3). This experiment tests the three key claims once, on fresh seeds, more data, a task off the floor,
with a fixed family and Holm correction.

## Units of replication
- **Connectome samples (3):** FlyWire v783 right MB (`data/mb/mb.npz`), FlyWire v783 left MB
  (`mb_left.npz`, same extraction rules, `scripts/extract_mb.py --side left`), and the **hemibrain v1.2**
  right MB, an independent fly (`mb_hemibrain.npz`, `scripts/fetch_hemibrain.py` +
  `scripts/extract_hemibrain.py`, CC BY 4.0). Counts: `data/mb/counts*.json`, docs/MB_EXTRACTION.md.
- **Odour sources (2):** DoOR 2.0 consensus (60 odorants, adapter v4) and Hallem & Carlson 2006
  single-study responses restricted to the 57 odorants not in the DoOR panel (adapter v6). They share no
  odorant, but they are not independent labs (DoOR includes Hallem 2006). This is weaker than a fully
  independent dataset; no public PN/glomerulus response table from another lab with download and
  licence could be verified in the time available (docs/DECISIONS.md).
- **Seeds:** 1000–1063 (64), never used before. Seed s fixes odour sets (per source), CS+ labels,
  noise streams and wiring draws (per sample and condition).

## Task and metrics (adapter v6, docs/ADAPTERS.md; set on synthetic wiring only)
Task in `src/neuralpet/task.py`, parameters `task.P` (n = 8 odours per set, η = 0.02, σ_train 0.2,
σ_test 1.0, readout noise 0.01, 12 + 6 blocks). PN→KC wiring varies; KC→MBON is the sample's real
wiring in every condition. Sparse (f = 0.10) and literal (f measured per sample) KC codes.
- **Primary: M2** = AUC at test noise σ = 1 after training (noise robustness).
- Secondary: AULC (area under the learning curve), plateau, M3 (interference).

**Synthetic pilot** (`experiments/010/pilot.py`, `pilot_results/pilot_grid{1,2,3}.csv`; random wiring
with the real PN → glomerulus labels, no connectome edges). Grid 1 (n = 12) left natural odours near
the floor; grid 2 varied η, readout noise, n, σ_test; grid 3 = the chosen setting, 24 seeds. On the
synthetic random circuit (grid 3): AULC 0.84–0.88 (sparse) / 0.66–0.70 (literal), plateau 0.87–0.91 /
0.70–0.76, M2 0.66–0.76 / 0.57–0.63, M3 0.03–0.08; no run hit a ceiling of 1.0 on average and none was
censored (AULC cannot be). A deliberately degraded synthetic circuit (KCs sample only 15% of PNs) was
lower on every metric (sparse AULC −0.12 to −0.15, M2 −0.06 to −0.12), so the task separates circuits in
principle. Random v1 odours were at ceiling under every setting that lifted natural odours off the
floor, so they are not used here.

One smoke test of the final code was run before this commit to measure run time (seed 7, not in the
confirmatory range: `n2b_subtype` on FW right and `real` on hemibrain). Its numbers were seen
(sparse M2 ≈ 0.57, literal ≈ 0.49–0.53): connectome circuits are harder than the synthetic one, and
the literal code may sit near chance. **No parameter was changed after it.**

## Conditions (PN→KC; docs/NULLS.md; verified in reports/010/nulls.md)
`random`, `shuffle` (N1), `pn_out`, `pn_out_perm_live`, `n2a_coconv` (N2a), `n2b_subtype` (N2b), `real`.
Live PNs = any non-zero DoOR value (as in 009), per sample.

## Confirmatory family (6 tests, Holm-adjusted together)
Statistic per seed: M2(a) − M2(b), averaged over the 3 samples × 2 odour sources. Paired two-sided
t-test across the 64 seeds; 95% bootstrap CI; Holm across the 6 tests (3 hypotheses × 2 sparsities).
Smallest effect size of interest (SESOI): **|Δ M2| = 0.02**.

| | contrast | earlier finding (predicted sign) |
|---|---|---|
| H1 | real − shuffle | real < shuffle (001, 004, 007: −0.014 sparse DoOR) → negative |
| H2 | pn_out − random (natural odours) | +0.025 sparse (007) → positive |
| H3 | pn_out − pn_out_perm_live | +0.022 sparse, +0.031 literal (009) → positive |

**Verdict rules (per test):**
- *replicated*: Holm p < 0.05 and the mean has the predicted sign (flagged "smaller than SESOI" if
  |mean| < 0.02).
- *not replicated, equivalent to 0*: not replicated and the 90% CI lies within ±0.02.
- *not replicated, inconclusive*: otherwise; *opposite direction* if Holm p < 0.05 with the other sign.
- A hypothesis counts as replicated if it is replicated with the sparse code (the setting where the
  earlier effects were found); the literal result is reported next to it either way (rule 7).
- **What proves the earlier claims wrong:** H2 or H3 sparse not replicated means the "out-degree
  helps / real PN ↔ degree pairing helps" story does not survive and is reported as a failed
  replication in the final report. H1 not replicated means "real is worse than shuffle" is not robust.
- Per-sample and per-source estimates are reported for every family contrast (descriptive). A
  replicated effect whose sign differs between connectome samples is reported as sample-dependent.

## Power
Pilot (grid 3): SD of the per-seed M2 difference between two *equivalent* synthetic random wirings,
averaged over the two odour sources, was 0.021 (sparse) / 0.017 (literal). Real-vs-null differences
varied more in 009 (d_z = 0.44 for +0.022, SD ≈ 0.05, one sample, one source). With 64 seeds and the
worst Holm level α = 0.05/6: power to detect Δ = 0.02 is ≈ 0.99 if SD = 0.03 and ≈ 0.7 if SD = 0.05
(normal approximation). 30 seeds would give ≈ 0.25 at SD = 0.05, so 64 are used.

## Pre-specified secondary contrasts (not in the family; 95% CIs, no p-values)
- real − n2a_coconv (does the pairing of input sets with KCs matter?);
- n2a_coconv − shuffle (does co-convergence beyond degrees matter?);
- n2b_subtype − shuffle and real − n2b_subtype (does class-specific input explain real vs shuffle?).
Interpretation rule written now: if real ≈ n2a (CI within ±0.02) and n2a < shuffle, the real-vs-shuffle
deficit is carried by co-convergence, not by which KC gets which input; if real < n2a, the pairing
matters (as 004 suggested for the pooled readout).

## Run
`uv run python experiments/010/run.py` (64 seeds × 3 samples × 7 conditions × 2 sources × 2 sparsities
= 5,376 learning runs, ~5 min on 10 cores). Raw: `experiments/010/results/runs.csv`. Tables and figure
by script: `reports/010/tables.md`, `reports/010/effects.png`.
