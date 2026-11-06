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

## v2 — 2026-11-06: the pet (src/neuralpet/pet.py; used by experiment 002)

Brain = v1 items 1–4 with real wiring, f = 0.10, PN noise σ = 0.1. Everything below is designed.

1. **World.** Unit square, walls reflect. 2 food and 2 toxic sources, each with its own random odour
   (v1 item 1). Odour at a point = Σ_sources odour_s · exp(−d²/(2·0.15²)).
2. **Valence readout.** V = (Σ_i KC_i · Σ_m W_im) / R_ref − 1, R_ref = k · mean KC out-weight at start.
3. **Output → action.** Two antennae ±0.03 to the sides. Heading += 0.6·tanh(5·(V_left − V_right)) +
   N(0, 0.2 + 0.8·curiosity). Speed 0.01 per step. Toxic contact also triggers a fixed 180° turn reflex.
4. **Energy.** −0.002 per step; eating (distance < 0.04) +0.25 (capped at 1), then the food source
   moves to a random place. Toxic contact −0.05.
5. **Curiosity.** c ← c + 0.01·(energy − c): follows energy slowly (sated → explores more). It changes
   exploration noise only, **not** dopamine.
6. **State → dopamine.** Reward DA on eating = drive reduction (Keramati & Gutkin 2014), with drive
   H(e) = (1 − e)²: DA_r = [H(e_before) − H(e_after)] / (2·0.25). Punishment DA = 1 on toxic contact.
   **Off-switch** (control): DA_r = a constant (experiment 002: per-seed mean DA_r of the "on" run).
7. **Plasticity.** Bidirectional, multiplicative: W_im ← W_im · (1 + η·KC_i·(DA_r − DA_p)), η = 0.05,
   clipped to [0, 3·W_im(0)]. Form after Bennett et al. 2021 (ΔW ∝ k·(d⁺ − d⁻)); potentiation by reward
   is a simplification (cf. Handler et al. 2019).

## v3 — 2026-11-06: compartment readout (experiment 005)

v1, except items 5–8 are restricted to a connectome-derived compartment set:
- P = MBONs receiving ≥ 20 synapses from any right `PPL1*` DAN (15 MBONs). The threshold was set from
  the DAN→MBON synapse table alone, before any learning run.
- Punishment DA depresses KC→MBON weights only onto MBONs in P (same rule, η = 0.02).
- Choice score S = Σ_{m∈P} R_m / μ_m, with μ_m the naive mean response of MBON m to 100 fixed
  noise-free reference odours (computed per condition before training; μ_m = 0 → MBON left out).
- Control grouping: 15 MBONs drawn at random from all 48 (rule 6).
