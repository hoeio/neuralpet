# NeuralPet

A small research-and-play project: a digital "pet" whose brain is a sub-circuit of the
Drosophila FlyWire connectome (mushroom body), driven by a simple internal state, living in
a 2D world, watched through a local web page. CPU only (MacBook Pro M4).

It is **not** alive, conscious, or a faithful emulation. The links between layers are simple
rules we designed (`docs/ADAPTERS.md`). See `CLAUDE.md` for the project rules and `STATUS.md`
for where things stand.

## Quick start

```bash
uv sync
uv run python scripts/fetch_flywire.py   # downloads FlyWire FAFB v783 into data/ (CC BY-NC 4.0)
uv run python scripts/extract_mb.py      # builds data/mb/ sub-circuit
uv run python experiments/001/run.py     # all seeds + report (also 002, 003, 004)
uv run python viewer/server.py           # read-only viewer, prints a 127.0.0.1 URL with token
```

Each experiment `experiments/NNN/` (001–009) has a PLAN.md committed before its run and one command
that runs all seeds and writes the tables. Results: `reports/*_report.md`; summary in `STATUS.md`.
In short: real PN→KC partners never beat a degree-preserving shuffle; the connectome's PN out-degree,
on the right PNs, helps noise robustness for real (DoOR) odours. The pet's state rule was a null at floor.

## Data and citations

FlyWire FAFB v783 data are CC BY-NC 4.0 and are never committed. Cite:
- Dorkenwald et al. 2024, Nature 634:124–138, "Neuronal wiring diagram of an adult brain".
- Schlegel et al. 2024, Nature 634:139–152, "Whole-brain annotation and multi-connectome cell typing of Drosophila".
- Zheng et al. 2018, Cell 174:730–743, "A complete electron microscopy volume of the brain of adult Drosophila melanogaster".
