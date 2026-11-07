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

## v4 — 2026-11-06: real odours (experiment 006; src/neuralpet/odors.py)

Replaces v1 item 1 when `odour source = DoOR`:
- DoOR 2.0 consensus responses (Münch & Galizia 2016), minus the receptor spontaneous rate (SFR row),
  clipped at 0.
- Receptors map to glomeruli via door_mappings.csv; several receptors on one glomerulus → mean.
- Odorants with data for ≥ 60% of our 47 DoOR-covered glomeruli are kept (60 odorants). Missing → 0.
  Glomeruli without data and multiglomerular PN units → 0.
- One global scale (4.89) so the mean input-unit value is 0.2, as for v1.

## v6 — 2026-11-07: learning task for experiments 010–011 (src/neuralpet/task.py)

Fixed on synthetic wiring only (`experiments/010/pilot.py`, grids 1–3, results in
`experiments/010/pilot_results/`) before any run on connectome wiring.
- Odour sources: DoOR (v4 rules, same 60 odorants in every sample) and **Hallem & Carlson 2006**
  single-study ORN responses (`Hallem.2006.EN` column of the DoOR.data receptor tables, minus
  spontaneous rate as published, clipped at 0, receptors → glomeruli via door_mappings.csv, receptors
  mapped to two glomeruli skipped, same global scaling to mean 0.2). Only the 57 Hallem odorants that are
  **not** in the DoOR panel are used, so the sources share no odorant (they are not independent labs:
  DoOR's consensus includes Hallem 2006).
- Per run: two disjoint sets A, B of n = 8 odorants each from one source; half of each set is CS+.
- PN noise σ_train = 0.2; test noise σ_test = 1.0 (M2).
- KC code: kWTA, f = 0.10 (sparse) or literal f = fraction of KCs with positive drive for 500 v1 random
  odours on that sample's real wiring (same rule as v1).
- Plasticity: v1 item 7, η = 0.02, punishment DA = 1 on CS+.
- **Readout:** ratio score r = R(W_t)/R(W_0) on the same KC code (v1 item 8 / experiment 004) **plus
  fixed output noise** N(0, 0.01²) per presentation. Without it the ratio readout reaches its plateau
  after one block (review finding 3), because the ordering of ratios does not depend on how much
  learning happened. With it, a learned change has to outgrow the noise.
- Schedule: 12 blocks on A (each odour once per block, random order), then 6 blocks on B.
  Evaluation: 12 noisy presentations per odour.
- Metrics: **AULC** = mean AUC over blocks 1–12 (replaces trials-to-criterion; never censored);
  **plateau** = mean AUC of blocks 10–12; **M2** = AUC at σ_test after block 12; **M3** = AUC drop on A
  after training B.
- Random v1 odours are not used in 010: on the synthetic random circuit they were at ceiling
  (plateau 1.0) at every setting that put natural odours off the floor.

## v7 — 2026-11-07: realistic-model variant (experiment 011; src/neuralpet/apl.py)
- **Graded APL.** KC rate r_k = clip((d_k − g·A_k·I)/D, 0, 1), APL activity I = Σ B_k r_k / Σ B_k,
  A_k = APL→KC synapses (normalised to mean 1), B_k = KC→APL synapses, real counts of each sample. Damped
  fixed-point iteration (30 steps, 0.5) + one undamped step. D = mean positive drive for 500 random v1
  odours on the real wiring. g by bisection so 10% of KCs have r > 0 for those odours on the real wiring;
  the same g for all wiring conditions. Calibrated values (printed by the run): FW right g ≈ 30.2, FW
  left ≈ 31.8, hemibrain ≈ 32.2.
- **Compartment DA.** P = MBONs receiving ≥ 20 synapses from any PPL1 DAN (v3 rule). Punishment DA
  depresses KC→MBON only onto P; choice score = Σ_{m∈P} R_m(W_t) / Σ_{m∈P} R_m(W_0) + readout noise.
  The plasticity rule with graded KCs: W_im ← W_im·(1 − η·DA·r_i).

## v5 — 2026-11-07: locomotor layer (WP5a; src/neuralpet/body.py, src/neuralpet/creature.py)
The brain never sets joint angles. A chain of 11 coupled phase oscillators (one per joint; coupling
4.0; one body wave, head → tail) drives dorsal/ventral muscle torque 0.4·(amp·sin φ_j + steer).
- **Steering (sensors × valence):** steer = 0.35·tanh(25·V·c) + OU exploration noise, where V = mean
  learned valence of the KC codes at the two head sensors (ratio readout, V = R(W_t)/R(W_0) − 1, so V = 0
  before any learning) and c = (I_L − I_R)/(I_L + I_R + 0.01), I = mean PN rate at that sensor.
- **State → CPG:** amp = 0.6 + 0.4·(1 − energy), freq = 0.6 + 0.6·(1 − energy) Hz; resting: amp = 0, no steering.
- **Reward and punishment are not motor commands:** dopamine only gates plasticity. The one innate motor
  rule is a 2 s avoidance turn after a toxic hit (away from the side with more odour).
- Exploration noise: OU process, rate 1/s, amplitude 0.04 + 0.1·curiosity.
Physics constants: in docs/CREATURE.md and body.py; they never change with age or play.

## v8 — 2026-11-07: the creature's world and state (experiment 012 and the play app)
Fixed by `experiments/012/pilot.py` on synthetic wiring with reward modulation off (constant DA 0.5),
rounds 1–7 (`experiments/012/pilot_results/`). Criterion: median fraction of time with energy > 0 ≥ 0.9
and mean energy between 0.3 and 0.8, so that the state rule has room to matter. History of the pilot:
round 1 (arena 6–8, 2-BL plumes, drain 0.001–0.0015 + 0.002·effort): ~1 meal per 30 min, starving;
round 2 (lower drain, more food): energy fine, but food and toxic were learned alike (plumes as wide as
the arena); round 3 (narrow plumes): creature circled in place (steering noise too large); round 4:
pinned against walls 79% of the time → **the world became a torus** (round 5); round 5: repeated toxic
hits during one slow contact → **one hit per contact episode** (round 6); round 6: mean energy ≈ 0.85,
too easy; round 7: final values below (median time above zero 1.0, mean energy 0.60 with steering on,
0.60 off). Steering did not change meals on the synthetic circuit; not tuned for it.
- World: 6 × 6 BL torus (minimum-image distances; the body is never wrapped), 4 food + 2 toxic sources,
  each with a DoOR odorant (random per world). Odour at a point = Σ_s exp(−d²/(2·0.8²))·odour_s.
- Contact: head within 0.4 BL. Food: +0.3 energy (cap 1), the source moves to a random place after a 5 s
  cooldown. Toxic: −0.05 energy, punishment DA 1, once per contact episode (the head must leave 0.6 BL)
  and at most once per 3 s.
- Energy drain per second: 0.0015 + 0.0012·effort, effort = mean squared muscle activation (≈ 0.3–0.6
  when moving). Curiosity c ← c + 0.05·dt·(energy − c).
- Reward DA on eating: "on" = drive reduction [H(e_before) − H(e_after)]/(2·0.3), H(e) = (1 − e)²
  (Keramati & Gutkin 2014); "const" = the per-seed mean of the "on" run; "generic" = max(0, a + b·e + c·e²)
  with random (a, b, c) per seed, rescaled to the same mean (experiment 012).
- Plasticity (v2 item 7): W_im ← W_im·(1 + 0.05·KC_i·(DA_r − DA_p)), clipped to [0, 3·W_im(0)], on the
  KC code at the head at the moment of contact.
- Mortality (precariousness): 120 s continuously at zero energy ends the individual (research; the play
  app uses torpor instead unless `hard_mode`).
