# NeuralPet

A small research-and-play project: a digital "pet" whose brain is a sub-circuit of the Drosophila FlyWire connectome (mushroom body first), driven by a simple internal state (energy, curiosity), living in a simple virtual world, watched through a local web page. Runs on a MacBook Pro M4, CPU only. Edge devices come much later, if ever.

## Rules

1. **Honest claims.** Say only what was measured. Never call it alive, conscious, or a faithful emulation. The links between layers are simple rules we designed, not biology. Report failed and null results too. Never invent numbers or citations; verify a source before citing it.
2. **One real question first.** Does the real mushroom-body wiring help dopamine-gated associative learning compared with matched fake wiring? Compare: (a) random wiring, (b) degree-preserving shuffle, (c) real. Same neuron count, edge count, and weight scale. Metrics: trials to learn, noise robustness, interference between odors.
3. **Write the plan before the run.** Put a short note in `experiments/NNN/PLAN.md` first: question, conditions, metric, and what result would prove the idea wrong. Commit it before running. Don't change it afterward; add a new note instead.
4. **At least 20 seeds per condition.** Report effect sizes with confidence intervals, not just p-values. Keep raw outputs untouched; make tables and figures by script, never by hand.
5. **Don't tune on the answer.** Rules that connect layers (sensor to neuron, state to dopamine gain, output to action) are fixed and written down in `docs/ADAPTERS.md`. Don't train or adjust them to make results look good.
6. **Control every "biological" claim.** If a biological module is claimed to matter, also test a size-matched random substitute. If there is no difference, say so.
7. **Kenyon-cell sparsity.** Reading the connectome literally gives a far denser Kenyon-cell code than real flies (about 68% active versus 5 to 10%). Treat sparsity as an explicit setting and report results both ways.

## Data and licensing

FlyWire data (FAFB v783, from codex.flywire.ai) is CC BY-NC 4.0. Do not commit raw or derived connectivity. Keep a `scripts/fetch_flywire.py` that downloads it into a gitignored `data/`, and list the citations (Dorkenwald 2024, Schlegel 2024, Zheng 2018). Check the current terms on the official site and note what you found.

## Autonomy

The human will not answer questions. Decide, write the decision in `docs/DECISIONS.md`, continue. Never do these; write a recommendation in `docs/OPEN_QUESTIONS.md` instead: make a repo public, force-push, delete data, touch Cloudflare, spend money. If the same problem fails five times, log it in `docs/BLOCKERS.md` and move on. Keep `STATUS.md` current so a new session can resume from it.

## Tools

Python with `uv`, NumPy/Numba or Brian2 (verify it actually runs fast enough on this machine; don't assume). Seed everything. One command per experiment should run all seeds and produce the report.

## Viewer

A read-only local web page on `127.0.0.1` with an access token (kept in a gitignored `.env`), showing the pet, its internal state, and learning curves. Render in the browser from a state stream, not with MuJoCo. No control buttons. Do not create or change any Cloudflare tunnel; write `docs/TUNNEL.md` with an ingress snippet and a reminder to turn on Cloudflare Access before exposing it.

## Git and notes

Commit small and often. Keep a short dated entry in `notebook/` after each work session (what was run, the numbers from the result files, what it means, next step); a Sonnet subagent may write it from the git diff and result files. Push to `origin` if it exists. Otherwise create a private repo only if `gh` is logged in. Before pushing, check that no secrets, FlyWire data, or large files are included. End commit messages with the attribution lines the harness provides.

## Prior work to read first (verify before citing)

- Minnick et al. 2026, arXiv 2610.33881: whole-CNS fly connectome in a body, with a degree-preserving rewired control. Closest prior work.
- Brunton et al. 2026, "The digital sphinx": a worm connectome can drive a fly body only because a decoder was trained, and that proves nothing. This is why rule 5 and rule 6 exist.
- Zheng 2022 (Current Biology), Li 2020 (eLife), Eichler 2017: mushroom-body wiring versus random models.
- Keramati and Gutkin 2014: homeostatic reinforcement learning, for the internal-state part.