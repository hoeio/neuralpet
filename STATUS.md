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
  Run `uv run python viewer/server.py`. Uses real wiring if `data/mb/mb.npz` exists, otherwise
  synthetic. No tunnel was created (`docs/TUNNEL.md`).
- Experiments, one command each (`uv run python experiments/NNN/run.py`):
  - 001: wiring test;
  - 002: pet state rule;
  - 003: which layer;
  - 004: ratio readout.
  Each has a PLAN.md committed before running. Reports: `reports/001_report.md` (001+003+004) and
  `reports/002_report.md`.
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
- **Pet (002): null at the floor.** The energy-dependent reward DA made no detectable difference
  (mean energy −0.006 [−0.018, 0.005]). The pet starves ~75% of the time in both conditions, so the
  test was weak.
- Speed is no issue: one 001 run takes ~0.5 s, and all 180 runs take ~13 s on 10 cores.

## Recommended next
1. A compartment readout using real DAN/MBON compartment groupings, against a matched random
   grouping (rule 6). This removes the pooling artifact.
2. Structured odours (real receptor statistics), since real PN→KC bias is towards specific glomeruli.
3. Pet experiment 005: a world where foraging is feasible (set on the modulation-off run). Add a fix
   for getting stuck at toxic sources, and a real-vs-shuffled wiring comparison in the pet.
4. Human decisions: repo visibility (it is public; see `docs/OPEN_QUESTIONS.md`).
