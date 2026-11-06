# Adapters (fixed rules connecting layers)

These are designed rules, not biology. They are fixed before experiments and not tuned on results
(CLAUDE.md rule 5). Changing one requires a new dated entry here and a new experiment number.
Code: `src/neuralpet/mb.py` (sections "adapters").

## v1 — 2026-11-06 (used by experiment 001)

1. **Odour → glomeruli.** For each odour, each glomerulus is active independently with probability
   0.2, with amplitude ~ Exp(1); inactive glomeruli are 0. Uniglomerular PNs take their glomerulus's
   value. Each multiglomerular PN counts as its own "glomerulus" (independent value). Random odours,
   no real receptor data.
2. **PN noise.** Each presentation: rate = max(0, odour value + σ·N(0,1)), independent per PN.
3. **PN → KC.** Drive = Σ_p W_pk · rate_p, with W_pk = synapse count (≥5 synapses, see
   MB_EXTRACTION.md).
4. **APL / sparsity (explicit setting, rule 7).** KC output is binary. The top `f` fraction of KCs by
   drive fire (k-winners-take-all = idealised global APL inhibition); KCs with zero drive never fire.
   - `sparse`: f = 0.10.
   - `literal`: f = mean fraction of KCs with positive drive for noise-free odours on the real wiring
     (measured, script `experiments/001/run.py` prints it), i.e. what "any active input fires a KC"
     gives. The same f is used for all wiring conditions.
   - The APL's own connectome wiring is **not** used (it is one cell contacting nearly all KCs).
5. **KC → MBON readout.** Pooled MBON drive R = Σ_m Σ_i W_im · KC_i, W_im initialised to synapse
   counts. All MBONs are pooled; no compartment or valence structure (v1 simplification).
6. **Dopamine.** A single punishment DA signal: DA = 1 on CS+ (punished) trials, 0 otherwise. It
   reaches all KC→MBON synapses equally (DAN connectome wiring not used in v1).
7. **Plasticity (Hige et al. 2015, form ours).** After each trial: W_im ← W_im · (1 − η · DA · KC_i),
   η = 0.02 (the value used by Minnick et al. 2026). Depression only; weights stay ≥ 0.
8. **Choice.** For a pair of odours, the model avoids the one with lower R. Performance = AUC over test
   presentations = P(R(CS−) > R(CS+)); 0.5 = chance.

## Pet adapters (step 3)

To be added as v2 before any pet experiment.
