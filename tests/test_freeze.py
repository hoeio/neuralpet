"""Research-freeze regression: rerun a small slice of experiment 010 (registered run) and of 012 from
the current code and check the outputs equal the committed raw results. Run before every tag.

    uv run python tests/test_freeze.py
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_010_slice_unchanged():
    r = load("r010", ROOT / "experiments" / "010" / "run.py")
    ref = pd.read_csv(ROOT / "experiments" / "010" / "results_registered" / "runs.csv")
    for seed, smp, cond in [(1000, "fw_right", "real"), (1001, "hemibrain", "n2b_subtype")]:
        for row in r.job((seed, smp, cond)):
            want = ref[(ref.seed == seed) & (ref["sample"] == smp) & (ref.cond == cond) & (ref.source == row["source"])
                       & (ref.sparsity == row["sparsity"])].iloc[0]
            for k in ["aulc", "plateau", "m2", "m3"]:
                assert np.isclose(row[k], want[k], rtol=0, atol=1e-12), (seed, smp, cond, k, row[k], want[k])
            assert json.loads(row["curve"]) == json.loads(want["curve"])


def test_012_slice_unchanged():
    r = load("r012", ROOT / "experiments" / "012" / "run.py")
    r.check_constants()            # also catches a play Game having changed creature.K_CONTRAST in this process
    ref = pd.read_csv(ROOT / "experiments" / "012" / "results" / "main.csv")
    seed = int(ref.seed.min())
    out, _, _ = r.life(seed, "on")
    want = ref[(ref.seed == seed) & (ref.cond == "on")].iloc[0]
    for k in ["survival_s", "mean_energy", "meals", "toxic"]:
        assert np.isclose(out[k], want[k], rtol=0, atol=1e-9), (k, out[k], want[k])


def test_research_code_unchanged_since_tag():
    """The play app may only import the research code: src/neuralpet and experiments/ equal the tag."""
    import subprocess
    out = subprocess.run(["git", "diff", "--name-only", "research-freeze", "--", "src/neuralpet", "experiments",
                          ":(exclude)experiments/explore"],   # post-hoc exploratory scripts are added after the freeze
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert out == "", out


if __name__ == "__main__":
    test_research_code_unchanged_since_tag()
    print("ok research code unchanged since research-freeze")
    test_010_slice_unchanged()
    print("ok 010 slice")
    test_012_slice_unchanged()
    print("ok 012 slice")
