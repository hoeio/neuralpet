# Experiment 011 — Do the 010 conclusions survive a more realistic model? (plan, 2026-11-07)

Written after experiment 010's results were known (they set what is being checked) and before any 011
run. Not edited afterwards. Robustness experiment; not part of 010's confirmatory family.

## What 010 found (reports/010/tables.md, sparse code, M2)
H1 real − shuffle −0.0007 [−0.0033, 0.0020]; H2 pn_out − random +0.0083 [0.0045, 0.0121];
H3 pn_out − pn_out_perm_live +0.0068 [0.0022, 0.0113]. All below the SESOI of 0.02.
Conclusion to test: "PN→KC wiring structure changes noise robustness by less than 0.02 AUC; out-degree
effects are positive but small; real ≈ shuffle".

## Model variants (docs/ADAPTERS.md v7)
1. **apl_comp (primary):** graded KC rates with APL feedback inhibition built from the real APL↔KC
   synapse counts of each sample (`src/neuralpet/apl.py`; gain set on real wiring with random v1
   odours to 10% active KCs, then fixed for all wiring conditions), **and** compartment-specific
   dopamine: punishment DA (PPL1) depresses KC→MBON synapses only onto MBONs that receive ≥ 20
   synapses from any PPL1 DAN (the experiment-005 rule, applied per sample: 15 / 12 / 26 MBONs for
   FW right / FW left / hemibrain), and the choice score reads only those MBONs.
2. **apl_global:** graded APL KCs, global DA, all MBONs (isolates the APL change).
3. **kwta_comp:** binary kWTA f = 0.10, compartment DA (isolates the DA change).
A leaky integrate-and-fire KC variant is **not** run (would need its own time constants and a new
pilot; listed as future work).

## Everything else as 010
Task v6 (`src/neuralpet/task.py`, same `task.P`), 3 connectome samples, DoOR + Hallem-disjoint odours,
PN→KC conditions `random`, `shuffle`, `pn_out`, `pn_out_perm_live`, `real` (KC→MBON real). New seeds
**1100–1163** (64). Sparse only: a "literal" APL variant (gain 0) is not run.

## Metrics and decision rule
Primary M2; secondary AULC. For H1–H3 in each variant: mean per-seed difference averaged over samples ×
sources, 95% bootstrap CI (no new p-value family).
- **The 010 conclusion is overturned** if, in apl_comp, any of H1–H3 has a 95% CI entirely outside
  ±0.02, or H2/H3 has a CI entirely below 0 (sign reversal).
- **Sign holds** for H2/H3 if the point estimate is positive and the CI excludes 0; for H1 if the
  90% CI is within ±0.02 (as in 010).
- **Size holds** if the 011 point estimate is within the 010 95% CI widened by ±0.01.
Reported per sample too (descriptive).

## Run
`uv run python experiments/011/run.py` → `experiments/011/results/runs.csv`, `reports/011/tables.md`.
