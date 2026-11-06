# Decisions

- 2026-11-06: Python 3.12 via uv; NumPy/Numba stack (Brian2 only if needed). The repo dir was an existing git repo with one commit; used it in place.
- 2026-11-06: `origin` (github.com/hoeio/neuralpet) exists and the unauthenticated GitHub API returns 200, i.e. it is **public**. CLAUDE.md says push to origin if it exists, so I push code/docs only. Never pushed: `data/`, `.env`, derived connectivity, raw result arrays. Flagged in OPEN_QUESTIONS.
- 2026-11-06: `graft/` (a local code-index tool cache) is gitignored.
- 2026-11-06: **Data source.** Codex download requires Google sign-in (not automatable). Used the public Zenodo record 10676866 (FlyWire v783 connectivity, `proofread_connections_783.feather`) plus Schlegel et al. annotations from github.com/flyconnectome/flywire_annotations. Details in docs/DATA.md.
- 2026-11-06: **Licence.** Zenodo lists CC BY 4.0 for connectivity; FlyWire ToS says community annotations are CC BY-NC 4.0; CLAUDE.md says CC BY-NC 4.0. Treat all FlyWire-derived data as CC BY-NC 4.0 (strictest), never commit it.
- 2026-11-06: **Model level.** Binary KC / rate model in NumPy, not Brian2: the MB sub-circuit is ~3k neurons and one run takes < 1 s (measured), so spiking is unnecessary for the question. Spiking would add parameters with no data to fix them.
- 2026-11-06: **Right hemisphere only**, ≥5 synapses per connection (FlyWire convention).
- 2026-11-06: **APL = kWTA** (idealised global inhibition), sparsity set explicitly (f = 0.10 or the literal fraction). APL connectome wiring not used.
- 2026-11-06: **Pooled MBON readout + one global punishment DA** (v1). DAN/compartment wiring deferred to a later experiment.
- 2026-11-06: **Task difficulty from a synthetic pilot** (experiments/001/pilot_synthetic.py; random synthetic circuit, no FlyWire data). η = 0.1 with 10 odours was at ceiling for every wiring, so it could not separate conditions. Chose η = 0.02 (as in Minnick 2026), 20 odours/set, independent odours, M2 at σ = 1. Done before PLAN.md was committed.
- 2026-11-06: After 001 showed real wiring worse, ran **003** (hybrids, pre-registered) and, from exploratory checks (experiments/003/explore.py), **004** (ratio readout, pre-registered). No 001 parameter was changed.
- 2026-11-06: Experiment 002 (pet) ran as planned. It gave a null at the floor (the pet starves most of the time). I did not retune the world after seeing this; a feasible-world experiment needs a new plan (recommended as 005).
- 2026-11-06: Viewer port 8797 (8765 was in use by another program on this machine). Token is checked with hmac.compare_digest; empty or short tokens are rejected; `.env` is created 0600.
- 2026-11-06: Stopping after step 2 write-up + step 3 first pass, as instructed. Next steps are listed in STATUS.md.
- 2026-11-06: Repo visibility: the human said the research will be public, so pushing to the public repo is intended. Data rules unchanged.
- 2026-11-06: Compartments derived from direct DAN→MBON synapses (≥20 from PPL1). KC-input similarity between DANs and MBONs was too noisy (KC→DAN is sparse at ≥5 synapses). Names→compartment tables from memory were not used (unverified).
- 2026-11-06: 005's exploratory contrast (grouping effect on shuffled wiring) was added to the generated table after seeing the figure. It is labelled exploratory everywhere.
- 2026-11-06: Viewer restarted with nohup (log `.viewer.log`, gitignored). No tunnel config was read or changed beyond listing running cloudflared processes.
- 2026-11-06: **Cloudflare (human override).** The human asked to use a Cloudflare tunnel for the viewer. I started a quick tunnel (trycloudflare, `--config /dev/null`) instead of editing the named tunnel: smallest, reversible, no account changes. Trade-off: no Cloudflare Access on quick tunnels, so the token is the only gate. Recorded in docs/TUNNEL.md.
- 2026-11-06: **Viewer moved from SSE to polling.** The tunnel buffered the event stream in 128 KiB blocks (measured), making updates arrive in bursts or not at all. Polling `/state` is plain request/response and works through any proxy.

## 2026-11-06: 3D creature + brain viewer
- The viewer now shows (a) the right MB as a 3D point cloud at FlyWire v783 annotation positions, with the
  model's per-step PN input, binary KC state, MBON drive and dopamine events drawn on it; (b) a drawn 3D
  fly (three.js) that follows the model's position and heading; (c) a scrolling activity raster.
- **No spiking is modelled.** KCs are binary per step (kWTA); a flash is a unit turning on, labelled so on
  the page. A LIF variant would be a separate pre-registered experiment, not a viewer change.
- Dopamine is one global signal in the model; drawing it on PAM (reward) and PPL1 (punishment) cells is a
  display convention, stated on the page.
- Positions come from `extract_mb.py` (`pos_*`, nm). They are derived FlyWire data, so they are kept in
  gitignored `data/` and only served to the token holder at runtime.
- Planned: synapse-sampled neuron shapes (`data/mb/shapes.npz`) once `flywire_synapses_783.feather` (9.5 GB)
  finishes downloading; the viewer uses them automatically if present.
