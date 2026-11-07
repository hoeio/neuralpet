# Data (checked 2026-11-06)

All FlyWire-derived data lives in gitignored `data/`. Fetch: `uv run python scripts/fetch_flywire.py`.

## What exists

- **Codex** (codex.flywire.ai): the FAFB v783 dataset is listed as 139,255 neurons / 3,732,460
  connections. Its "Download Data" app requires Google sign-in ("access to its apps requires signing in
  with a Google account"), so it cannot be fetched by script without the human's account.
- **Zenodo record 10676866**, "FlyWire Whole-brain Connectome Connectivity Data", version 783.0,
  published 2024-06-02. Files: `proofread_connections_783.feather` (852 MB, used),
  `proofread_root_ids_783.npy` (1.1 MB, used), `flywire_synapses_783.feather` (9.5 GB, not used),
  `per_neuron_neuropil_count_{pre,post}_783.feather` (not used). md5 checked by the fetch script.
- **flyconnectome/flywire_annotations** (GitHub): `Supplemental_file1_neuron_annotations.tsv`
  (Schlegel et al. 2024), 139,248 neurons, columns incl. `super_class`, `cell_class`, `cell_type`, `side`.

## Terms

- Zenodo record metadata: licence **CC BY 4.0**.
- FlyWire Terms of Service (flywire.ai/tos): contributed edits and annotations "will be made freely
  available under a CC-BY-NC 4.0 license".
- CLAUDE.md: CC BY-NC 4.0.
- **Decision:** treat all of it as CC BY-NC 4.0 (non-commercial, attribution). No raw or derived
  connectivity is committed. Aggregate results (AUCs, counts) and figures are committed.

## Citations

- Dorkenwald S et al. (2024) Neuronal wiring diagram of an adult brain. Nature 634:124–138.
  doi:10.1038/s41586-024-07558-y
- Schlegel P et al. (2024) Whole-brain annotation and multi-connectome cell typing of Drosophila.
  Nature 634:139–152. doi:10.1038/s41586-024-07686-5
- Zheng Z et al. (2018) A complete electron microscopy volume of the brain of adult Drosophila
  melanogaster. Cell 174:730–743.e22. doi:10.1016/j.cell.2018.06.019
- Synapse detection / NT prediction used inside the Zenodo data: Buhmann et al. 2021 (Nat Methods),
  Heinrich et al. 2018, Eckstein, Bates et al. 2024 (Cell), as listed by the Zenodo record.

## Synapse table (viewer only)
`scripts/fetch_flywire.py --synapses` downloads `flywire_synapses_783.feather` (9.49 GB, Zenodo 10676866,
same CC BY-NC 4.0 terms). `scripts/extract_shapes.py` samples per-neuron synapse positions into
`data/mb/shapes.npz` for drawing. Not used by any experiment. Nothing derived is committed.

## Added 2026-11-07 (experiments 010–012)

- **Hemibrain v1.2** (an independent fly, right central brain): `scripts/fetch_hemibrain.py` downloads
  `https://storage.googleapis.com/hemibrain/v1.2/exported-traced-adjacencies-v1.2.tar.gz` (46 MB, md5
  `7B4HbRVELzaPpZeLAPSmHA==` base64, checked) into gitignored `data/hemibrain/`. Licence: the Janelia
  hemibrain page states "Hemibrain is licensed under CC-BY" (checked 2026-11-07). Nothing derived is
  committed except aggregate results. Cite: Scheffer LK et al. (2020) A connectome and analysis of the
  adult Drosophila central brain. eLife 9:e57443. doi:10.7554/eLife.57443.
- **Hallem & Carlson 2006** single-study ORN responses, read from the DoOR.data per-receptor tables
  (column `Hallem.2006.EN`; `scripts/fetch_door.py` now downloads those 78 tables too). Same licence as
  DoOR.data (CC BY-SA 4.0). Cite: Hallem EA, Carlson JR (2006) Coding of odors by a receptor repertoire.
  Cell 125:143–160. doi:10.1016/j.cell.2006.01.050.
- **FlyWire left hemisphere**: from the same Zenodo files, `scripts/extract_mb.py --side left`.
