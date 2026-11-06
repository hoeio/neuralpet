# STATUS (updated 2026-11-06)

## What exists
- `scripts/fetch_flywire.py`: downloads FlyWire v783 connections (Zenodo 10676866, md5-checked) and
  Schlegel annotations into gitignored `data/flywire/` (~900 MB). Codex itself needs Google sign-in.
- `scripts/extract_mb.py`: right-hemisphere MB → `data/mb/mb.npz` (2,597 KCs, 48 MBONs, 165 DANs,
  1 APL, 149 PNs; ≥5 synapses). Details: `docs/MB_EXTRACTION.md`.
- `src/neuralpet/mb.py`: binary-KC model, kWTA "APL", Hige-style DA-gated depression, random and
  degree-preserving (curveball) controls. Self-check: `uv run python src/neuralpet/mb.py`.
- `src/neuralpet/pet.py`: the pet (2D arena, energy, curiosity, state → reward DA).
- `viewer/server.py` + `viewer/index.html`: read-only viewer on 127.0.0.1:8797, token in `.env`.
  3D: MB point cloud at FlyWire positions with live model activity (PN, binary KC, MBON, DA), a
  drawn 3D fly, an activity raster. No spiking model (binary units, labelled as such).
  Run `uv run python viewer/server.py`. Uses real wiring if `data/mb/mb.npz` exists, otherwise
  synthetic. Exposed through a quick tunnel at the human's request (`docs/TUNNEL.md`).
- Experiments, one command each (`uv run python experiments/NNN/run.py`):
  - 001: wiring test;
  - 002: pet state rule;
  - 003: which layer;
  - 004: ratio readout;
  - 005: connectome-derived compartment readout (PPL1→MBON ≥20 synapses) vs random grouping;
  - 006: real odours (DoOR 2.0, 60 odorants; `scripts/fetch_door.py`) vs random odours;
  - 007: which PN→KC degree property matters (pn_out / kc_in controls);
  - 008: does the real PN ↔ out-degree pairing matter (PN-row-permuted controls);
  - 009: the same permutation only within DoOR-input PNs / only within silent PNs.
  Each has a PLAN.md committed before running. Reports: `reports/001_report.md` (001+003+004),
  `reports/002_report.md`, `reports/005_report.md`, `reports/006_report.md`, `reports/007_report.md`, `reports/008_report.md`, `reports/009_report.md`.
- Reproducibility (2026-11-06): all of 001–007 rerun from a clean worktree; every runs.csv, table and
  figure is byte-identical (only wall_s differs). Total ~3 min.
- Docs: `docs/ADAPTERS.md` (all designed rules; v1 model, v2 pet), `LITERATURE.md`, `DATA.md`,
  `DECISIONS.md`, `OPEN_QUESTIONS.md`, `TUNNEL.md`.

## What was found (30 seeds per condition, paired; CIs are 95% bootstrap)
- **The main question: real wiring did not help.**
  - With the pooled readout (001), real MB wiring learned *slower* than a degree-preserving shuffle:
    +214 trials [187, 241] to AUC 0.9 with a sparse KC code. It was also less noise-robust (AUC
    −0.16).
  - 003: the deficit is in PN→KC wiring (+187 trials); KC→MBON adds only ~11.
  - 004: most of the learning-speed deficit comes from our pooled readout. Real PN→KC couples odour
    identity to KC types with very different MBON output, so naive MBON drive varies 3× more across
    odours. With a ratio readout the gap is +27 [−3, 68] trials. Real is still never better than
    shuffle, and slightly worse on noise robustness (−0.032 [−0.041, −0.022]).
  - Random wiring is best or tied-best on learning speed and noise robustness.
- **005, compartment readout:** still no advantage for real wiring. Real − shuffle (sparse): M1 +93
  trials [59, 127], M2 −0.124 [−0.159, −0.090]. The connectome-derived compartment grouping did not
  beat a size-matched random grouping with real wiring (M2 −0.006 [−0.029, 0.018]). The primary
  readout was hard: real wiring never reached criterion in any seed. Exploratory: the grouping helps
  *shuffled* wiring, most likely because the chosen MBONs have unusually high KC in-degree (above
  98.5% of random groups).
- **006, real odours (DoOR):** real wiring still does not beat the shuffle (M2 −0.007 [−0.017, 0.002]
  sparse), but its gap to the shuffle shrinks compared with random odours (interaction +0.015
  [0.0005, 0.030] sparse, +0.029 [0.013, 0.044] literal). With real odours, connectome-degree wirings
  beat random wiring (real − random +0.029 [0.012, 0.046]): degree structure helps, specific partners
  do not. The real-odour task is near its floor (M1 mostly censored).
- **007, degree components (PN→KC only):** keeping each PN's out-degree beats random wiring with
  real odours (sparse +0.025 [0.010, 0.040], literal +0.043 [0.025, 0.061]) but *hurts* with random
  odours (−0.033, −0.036): a crossover. KC in-degree alone does nothing. Real is still below the
  shuffle (−0.014 [−0.025, −0.004] sparse, DoOR). Exploratory: glomeruli with more KC partners
  respond more strongly and more variably in DoOR (Spearman r ≈ 0.38, p ≈ 0.01).
- **008, pairing:** the 007 benefit needs the *real* PN ↔ out-degree pairing. With DoOR odours,
  pn_out − pn_out_perm +0.052 [0.035, 0.072] sparse, +0.047 [0.029, 0.068] literal; shuffle − shuffle_perm
  +0.067 / +0.041. Skew on random PNs does not help (−0.027 sparse, −0.004 literal). With random odours
  all ≈ 0. Caveat: real puts 82% of KC edges on the 95 PNs with DoOR input, permuted 64%, so wasted edges
  on silent PNs may explain much of it.
- **009, within live PNs:** matching still matters. pn_out − pn_out_perm_live +0.022 [0.004, 0.040]
  sparse, +0.031 [0.011, 0.052] literal (~40–65% of the 008 effect). Permuting silent PNs: ≈ 0 (sanity).
- **Pet (002): null at the floor.** The energy-dependent reward DA made no detectable difference
  (mean energy −0.006 [−0.018, 0.005]). The pet starves ~75% of the time in both conditions, so the
  test was weak.
- Speed is no issue: one 001 run takes ~0.5 s, and all 180 runs take ~13 s on 10 cores.

## Recommended next
0. Why real < shuffle: a control that keeps KC co-convergence of glomeruli (Zheng 2022). Also an
   easier real-odour task (M1 off the cap) and a second odour dataset to check the 007–009 effect.
1. A degree-matched random grouping as the rule-6 control for compartments (005 follow-up). Also a
   less noisy compartment readout, pre-registered as new experiments.
2. Structured odours (real receptor statistics), since real PN→KC bias is towards specific glomeruli.
3. Pet experiment 005: a world where foraging is feasible (set on the modulation-off run). Add a fix
   for getting stuck at toxic sources, and a real-vs-shuffled wiring comparison in the pet.
4. The viewer runs detached on 127.0.0.1:8797 (log `.viewer.log`). A quick Cloudflare tunnel exposes
   it (URL in `.tunnel.log`; append `/?t=<token>`). Neither survives a reboot; restart commands are
   in docs/TUNNEL.md. The page polls `/state` (SSE was buffered by the tunnel). The pet itself is
   still mostly starving (energy ≈ 0), as found in 002; that is the model, not the viewer.
5. Neuron shapes: done. `scripts/extract_shapes.py` (7 s) samples synapse positions per neuron from
   `flywire_synapses_783.feather` into gitignored `data/mb/shapes.npz` (~71k points); viewer uses them.
