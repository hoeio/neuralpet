# Reproduction

## Clean-clone check (2026-11-08)

- **Machine and tools:** Apple M4 Pro, macOS (Darwin 24.3), uv 0.12.21, Python from `.python-version`,
  dependencies from the committed `uv.lock`.
- **Fresh clone:** `git clone` of the repository at commit 502e47d into an empty directory. Then
  `uv sync`, all tests, and every confirmatory command:
  `experiments/010/verify_nulls.py`, `010/run.py`, `011/run.py`, `012/run.py`,
  `experiments/explore/steer_check.py`, `scripts/play_teach_demo.py` and `scripts/make_final_report.py`.
  Total time: 1166 s.
- **Result: every raw result file, table, figure and `reports/FINAL.md` was byte-identical** to the
  committed versions. The only difference was the `wall_s` field (run time) in three `meta.json` files.
- **Tests:** `test_body` and `test_play` passed. `test_freeze`'s guard failed at that commit because the
  exploratory script had been added after the `research-freeze` tag (audit finding #11). After the fix,
  the clone was updated to 143edcd. There `test_freeze` and `test_play` pass, and the teaching demo and
  final report regenerate with no difference from the committed files.
- **Not re-downloaded:** the connectome data. `data/` was symlinked from the working copy to avoid
  fetching ~1 GB again. The fetch scripts check checksums where the source publishes them (FlyWire on
  Zenodo, hemibrain). DoOR is fetched from the `master` branch of ropensci/DoOR.data and is not pinned
  to a commit, so a future upstream change could alter odour inputs. If that happens, pin `COMMIT` in
  `scripts/fetch_door.py`.
- **Earlier check:** experiments 001–007 were rerun from a clean worktree on 2026-11-06 with
  byte-identical outputs (STATUS history).

## From scratch

```bash
git clone <this repo> neuralpet && cd neuralpet
uv sync
uv run python scripts/fetch_flywire.py                 # FlyWire v783 (Zenodo, md5-checked) -> data/flywire
uv run python scripts/extract_mb.py --side right
uv run python scripts/extract_mb.py --side left
uv run python scripts/fetch_hemibrain.py               # hemibrain v1.2 adjacency export -> data/hemibrain
uv run python scripts/extract_hemibrain.py
uv run python scripts/fetch_door.py                    # DoOR 2.0 + Hallem & Carlson tables -> data/door
for t in body play freeze; do uv run python tests/test_$t.py; done
uv run python experiments/010/verify_nulls.py
uv run python experiments/010/run.py                   # ~2-4 min on 10 cores
uv run python experiments/011/run.py                   # ~6-8 min
uv run python experiments/012/run.py                   # ~8-13 min
uv run python experiments/explore/steer_check.py       # ~2 min (exploratory)
uv run python scripts/play_teach_demo.py               # play demo -> docs/play_teach.*
uv run python scripts/make_final_report.py             # reports/FINAL.md + reports/figures
```

- **Deviation runs:** `uv run python experiments/010/run.py --results results` (and the same for 011)
  reproduce them; see the DEVIATION.md files.
- **Seeds:** every seed is fixed in each experiment's `run.py` and recorded in `meta.json`.
- **Optional:** the 9.5 GB synapse table (`fetch_flywire.py --synapses`, then
  `scripts/extract_shapes.py`) is only needed to draw neuron shapes in the viewer and play app.
