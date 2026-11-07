"""WP5a acceptance tests for the creature body and the creature (run: uv run python tests/test_body.py)."""
import time

import numpy as np

from neuralpet import creature as C
from neuralpet.body import Body, _angles


def synth(seed=0):
    r = np.random.default_rng(seed)
    W_pk = ((r.random((60, 800)) < 0.06) * r.integers(5, 30, (60, 800))).astype(np.float32)
    W_km = ((r.random((800, 10)) < 0.3) * r.integers(5, 12, (800, 10))).astype(np.float32)
    odors = ((r.random((8, 60)) < 0.3) * r.exponential(1, (8, 60))).astype(np.float32)
    return W_pk, W_km, odors


def test_deterministic():
    a, b = Body(heading=0.3), Body(heading=0.3)
    a.step(5, 1, 1, 0.1), b.step(5, 1, 1, 0.1)
    assert np.array_equal(a.x, b.x)
    x = [C.Creature(*synth(), seed=4) for _ in range(2)]
    for c in x:
        c.run(60)
    assert np.array_equal(x[0].body.x, x[1].body.x) and x[0].energy == x[1].energy and np.array_equal(x[0].W, x[1].W)


def test_stable():
    b = Body()
    for _ in range(100):
        b.step(1, 1, 1.2, 0.2)
        L = np.linalg.norm(np.diff(b.x, axis=0), axis=1)
        assert np.isfinite(b.x).all() and np.abs(L - b.L0).max() < 0.05 * b.L0
        assert np.abs(_angles(b.x)).max() < 1.0


def test_anisotropic_drag_gives_travel_isotropic_does_not():
    for cn, want in [(10.0, True), (1.0, False)]:
        b = Body(heading=0.0, c_n=cn)
        c0 = b.com().copy()
        b.step(20, 1, 1)
        d = np.linalg.norm(b.com() - c0)
        assert (d > 1.0) if want else (d < 1e-9), (cn, d)


def test_wave_moves_head_first():
    b = Body(heading=0.0)
    c0 = b.com().copy()
    b.step(10, 1, 1)
    assert (b.com() - c0)[0] > 0.5      # started pointing +x, moved +x


def test_steering_direction():
    turn = {}
    for s in (-0.1, 0.0, 0.1):
        b = Body(heading=0.0)
        h = []
        for _ in range(40):
            b.step(0.25, 1, 1, s)
            h.append(b.heading)
        turn[s] = np.unwrap(h)[-1] - np.unwrap(h)[0]
    assert turn[0.1] > turn[0.0] + 0.2 and turn[-0.1] < turn[0.0] - 0.2, turn   # + steer = turn left (CCW)


def test_effort_costs_energy():
    W_pk, W_km, odors = synth()
    drains = []
    for resting in (True, False):
        c = C.Creature(W_pk, W_km, odors, seed=1, roles=[("food", 0)])
        c.sources[0].cooldown = 1e9                         # nothing to eat or smell
        c.resting = resting
        c.run(30)
        drains.append(0.7 - c.energy)
    assert np.isclose(drains[0], 30 * C.E_BASE, rtol=0.02) and drains[1] > drains[0] * 1.1, drains


def test_realtime_factor():
    c = C.Creature(*synth(), seed=2)
    c.run(5)
    t = time.time()
    c.run(60)
    f = 60 / (time.time() - t)
    assert f >= 20, f
    return f


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            r = v()
            print("ok", k, "" if r is None else f"({r:.0f}x real time)")
