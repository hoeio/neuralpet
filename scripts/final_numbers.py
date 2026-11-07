"""Every number quoted in reports/FINAL.md, computed from raw results files (never typed by hand).

    uv run python scripts/final_numbers.py      # prints the dict; used by scripts/make_final_report.py
"""
import importlib.util
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from neuralpet import stats

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "experiments"


def ci(x, d=3):
    m, lo, hi = stats.boot_ci(np.asarray(x, float))
    return f"{m:+.{d}f} [{lo:+.{d}f}, {hi:+.{d}f}]"


def pair(df, a, b, metric, **where):
    d = df
    for k, v in where.items():
        d = d[d[k] == v]
    p = d.pivot_table(index="seed", columns="wiring", values=metric)
    return p[a] - p[b]


def early():
    """Headline contrasts of the exploratory experiments 001-009 (sparse code unless stated)."""
    N = {}
    d = pd.read_csv(E / "001" / "results" / "runs.csv")
    N["e001_m1"] = ci(pair(d, "real", "shuffle", "M1_trials", sparsity="sparse"), 0)
    N["e001_m2"] = ci(pair(d, "real", "shuffle", "M2_auc_sigma1.0", sparsity="sparse"))
    N["e001_cens_real"] = int(d[(d.sparsity == "sparse") & (d.wiring == "real")].M1_censored.sum())
    d = pd.read_csv(E / "004" / "results" / "runs.csv")
    N["e004_m1"] = ci(pair(d, "real", "shuffle", "M1_trials", sparsity="sparse"), 0)
    N["e004_m2"] = ci(pair(d, "real", "shuffle", "M2_auc_sigma1.0", sparsity="sparse"))
    d = pd.read_csv(E / "005" / "results" / "runs.csv")
    N["e005_groupings"] = list(map(str, d.grouping.unique()))
    d = pd.read_csv(E / "006" / "results" / "runs.csv")
    N["e006_m2_door"] = ci(pair(d, "real", "shuffle", "M2_ratio", sparsity="sparse", source="door"))
    N["e006_real_random_door"] = ci(pair(d, "real", "random", "M2_ratio", sparsity="sparse", source="door"))
    d = pd.read_csv(E / "007" / "results" / "runs.csv")
    N["e007_pnout_random_door"] = ci(pair(d, "pn_out", "random", "M2_ratio", sparsity="sparse", source="door"))
    N["e007_pnout_random_rand"] = ci(pair(d, "pn_out", "random", "M2_ratio", sparsity="sparse", source="random"))
    N["e007_real_shuffle_door"] = ci(pair(d, "real", "shuffle", "M2_ratio", sparsity="sparse", source="door"))
    d = pd.read_csv(E / "008" / "results" / "runs.csv")
    N["e008_pnout_perm"] = ci(pair(d, "pn_out", "pn_out_perm", "M2_ratio", sparsity="sparse", source="door"))
    d = pd.read_csv(E / "009" / "results" / "runs.csv")
    N["e009_pnout_permlive"] = ci(pair(d, "pn_out", "pn_out_perm_live", "M2_ratio", sparsity="sparse"))
    N["e009_pnout_permlive_lit"] = ci(pair(d, "pn_out", "pn_out_perm_live", "M2_ratio", sparsity="literal"))
    d = pd.read_csv(E / "002" / "results" / "runs.csv")
    p = d.pivot(index="seed", columns="cond", values="mean_energy")
    N["e002_energy"] = ci(p["on"] - p["off"])
    N["e002_starving"] = f"{d.frac_starving.mean():.2f}"
    return N


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def confirmatory():
    """010 (registered and deviation runs), 011, 012: parse the generated tables (themselves made by
    script from raw results) so FINAL.md quotes exactly the same numbers."""
    N = {}
    for key, path in [("t010", ROOT / "reports" / "010" / "tables.md"), ("t010dev", ROOT / "reports" / "010" / "deviation" / "tables.md"),
                      ("t011", ROOT / "reports" / "011" / "tables.md"), ("t011dev", ROOT / "reports" / "011" / "deviation" / "tables.md"),
                      ("t012", ROOT / "reports" / "012" / "tables.md")]:
        N[key] = path.read_text() if path.exists() else None
    return N


def family_rows(md):
    """Rows of the 010 confirmatory table as dicts."""
    out = []
    sec = md.split("## Confirmatory family")[1].split("##")[0]
    for line in sec.splitlines():
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) == 9 and c[0].startswith("H"):
            out.append(dict(h=c[0], contrast=c[1], sparsity=c[2], diff=c[3], ci90=c[4], dz=c[5], p=c[6], p_holm=c[7], verdict=c[8]))
    return out


def table_section(md, title):
    s = md.split(title, 1)[1]
    s = s.split("\n## ", 1)[0]
    return title + s


if __name__ == "__main__":
    print(json.dumps(early(), indent=1))
