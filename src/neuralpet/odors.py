"""Real-odour adapter (docs/ADAPTERS.md v4): DoOR 2.0 responses -> per-PN odour vectors."""
from pathlib import Path

import numpy as np
import pandas as pd

DOOR = Path(__file__).resolve().parents[2] / "data" / "door"


def door_odors(glom_names, glom_of_pn, min_cov=0.6, target_mean=0.2):
    """Returns (odours (n, n_pn) float32, odorant InChIKeys, info dict).

    - responses minus the receptor's spontaneous rate (DoOR 'SFR' row), clipped at 0;
    - receptors mapped to glomeruli by door_mappings.csv; several receptors on one glomerulus -> mean;
    - odorants kept if measured for >= min_cov of our DoOR-covered glomeruli; missing -> 0;
    - glomeruli without DoOR data and multiglomerular PNs -> 0;
    - one global scale so the mean input-unit value equals target_mean (v1 random odours: 0.2).
    """
    R = pd.read_csv(DOOR / "door_response_matrix.csv", sep=";", index_col=0)
    M = pd.read_csv(DOOR / "door_mappings.csv", sep=";", index_col=0).drop_duplicates("receptor")
    rec2glom = M.set_index("receptor").glomerulus
    sfr = R.loc["SFR"]
    R = R.drop(index="SFR")
    ours = {g: i for i, g in enumerate(glom_names) if not str(g).startswith("m:")}
    cols = {}
    for rec in R.columns:
        g = rec2glom.get(rec)
        if g in ours:
            cols.setdefault(g, []).append(rec)
    raw = pd.DataFrame({g: R[recs].mean(axis=1) for g, recs in cols.items()})
    base = pd.Series({g: sfr[recs].mean() for g, recs in cols.items()}).fillna(0)   # NaN SFR -> 0
    keep = raw.notna().mean(axis=1) >= min_cov
    X = (raw[keep] - base).clip(lower=0).fillna(0)
    units = np.zeros((len(X), len(glom_names)), np.float64)
    for g in X.columns:
        units[:, ours[g]] = X[g].to_numpy()
    scale = target_mean / units.mean()
    units *= scale
    info = dict(n_odorants=int(len(X)), glomeruli_with_data=len(cols), scale=float(scale),
                frac_units_active=float((units > 0).mean()))
    return units[:, glom_of_pn].astype(np.float32), X.index.to_numpy(), info


def hallem_odors(glom_names, glom_of_pn, exclude=(), target_mean=0.2):
    """Second odour source (docs/ADAPTERS.md v6): Hallem & Carlson 2006 single-study ORN responses
    (column 'Hallem.2006.EN' of the DoOR.data per-receptor tables; spikes/s minus spontaneous rate),
    clipped at 0. Odorants in `exclude` (InChIKeys, e.g. the DoOR panel) are dropped so the two odour
    sources share no odorant. Receptors map to glomeruli by door_mappings.csv (receptors mapped to two
    glomeruli are skipped); several receptors on one glomerulus -> mean. Missing -> 0. Same global
    scaling rule as door_odors. Returns (odours (n, n_pn), InChIKeys, info)."""
    M = pd.read_csv(DOOR / "door_mappings.csv", sep=";", index_col=0).drop_duplicates("receptor")
    rec2glom = M.set_index("receptor").glomerulus
    ours = {g: i for i, g in enumerate(glom_names) if not str(g).startswith("m:")}
    cols = {}
    for f in sorted((DOOR / "receptors").glob("*.csv")):
        t = pd.read_csv(f, sep=";")
        g = rec2glom.get(f.stem)
        if "Hallem.2006.EN" in t.columns and g in ours:
            cols.setdefault(g, []).append(t.set_index("InChIKey")["Hallem.2006.EN"])
    X = pd.DataFrame({g: pd.concat(s, axis=1).mean(axis=1) for g, s in cols.items()})
    X = X.drop(index=[k for k in ["SFR", *exclude] if k in X.index]).dropna(how="all")
    X = X.clip(lower=0).fillna(0)
    units = np.zeros((len(X), len(glom_names)), np.float64)
    for g in X.columns:
        units[:, ours[g]] = X[g].to_numpy()
    scale = target_mean / units.mean()
    units *= scale
    info = dict(n_odorants=int(len(X)), glomeruli_with_data=len(cols), scale=float(scale),
                frac_units_active=float((units > 0).mean()))
    return units[:, glom_of_pn].astype(np.float32), X.index.to_numpy(), info
