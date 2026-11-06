"""The pet: MB model (src/neuralpet/mb.py) in a 2D arena with an internal state.
All rules are designed adapters, written down in docs/ADAPTERS.md (v2). Not biology.
"""
from dataclasses import dataclass, field

import numpy as np

from neuralpet import mb

ARENA, R_EAT, ODOR_LEN, SPEED, ANT = 1.0, 0.04, 0.15, 0.01, 0.03
DRAIN, FOOD_E, TOXIC_E = 0.002, 0.25, 0.05
ETA, PN_SIGMA, FRAC, W_MAX = 0.05, 0.1, 0.10, 3.0


@dataclass
class Source:
    pos: np.ndarray
    kind: str        # "food" | "toxic"
    odor: int        # index into Pet.odors


@dataclass
class Pet:
    W_pk: np.ndarray
    W_km: np.ndarray
    glom: np.ndarray
    seed: int = 0
    da_const: float | None = None    # None = state-modulated reward DA; a number = fixed reward DA (off)
    t: int = 0
    events: list = field(default_factory=list)

    def __post_init__(self):
        self.rng = np.random.default_rng(self.seed)
        self.W0 = self.W_km.astype(np.float64).copy()
        self.W = self.W0.copy()
        self.odors = mb.make_odors(4, self.glom, self.rng)          # 0,1 food; 2,3 toxic
        self.sources = [Source(self._rand_pos(), k, i)
                        for i, k in enumerate(["food", "food", "toxic", "toxic"])]
        self.pos, self.heading = self._rand_pos(), self.rng.uniform(0, 2 * np.pi)
        self.energy, self.curiosity = 0.6, 0.5
        self.da_rewards = []
        self.k = int(FRAC * self.W_pk.shape[1])
        self.R_ref = self.k * self.W0.sum(1).mean()                  # R of an average code

    def _rand_pos(self):
        return self.rng.uniform(0.1, 0.9, 2)

    def smell(self, p):
        d2 = np.array([((s.pos - p) ** 2).sum() for s in self.sources])
        c = np.exp(-d2 / (2 * ODOR_LEN ** 2))
        return (c[:, None] * self.odors[[s.odor for s in self.sources]]).sum(0)

    def kc(self, odor):
        self._pn = mb.pn_rates(odor[None], PN_SIGMA, self.rng)      # kept for the viewer
        return mb.kc_code(self._pn, self.W_pk, FRAC)[0]

    def valence(self, kc):
        """Learned approach drive relative to an average code (>0 approach, <0 avoid)."""
        return float(kc @ self.W.sum(1)) / self.R_ref - 1.0

    def step(self):
        self.t += 1
        # sense with two antennae, turn toward higher valence (klinotaxis), noise grows with curiosity
        side = np.array([np.cos(self.heading + np.pi / 2), np.sin(self.heading + np.pi / 2)])
        vl = self.valence(self.kc(self.smell(self.pos + ANT * side)))
        vr = self.valence(self.kc(self.smell(self.pos - ANT * side)))
        self.heading += 2.0 * np.tanh(5 * (vl - vr)) * 0.3 + self.rng.normal(0, 0.2 + 0.8 * self.curiosity)
        self.pos = self.pos + SPEED * np.array([np.cos(self.heading), np.sin(self.heading)])
        for i in range(2):                                           # reflect off walls
            if not 0 < self.pos[i] < ARENA:
                self.pos[i] = np.clip(self.pos[i], 0, ARENA)
                self.heading = np.pi - self.heading if i == 0 else -self.heading
        # internal state
        self.energy = max(0.0, self.energy - DRAIN)
        self.curiosity += 0.01 * (self.energy - self.curiosity)     # sated -> curious, hungry -> focused
        kc_here = self.kc(self.smell(self.pos))
        pn_here = self._pn[0]
        da_r = da_p = 0.0
        for s in self.sources:
            if np.linalg.norm(s.pos - self.pos) < R_EAT:
                if s.kind == "food":
                    before = self.energy
                    self.energy = min(1.0, self.energy + FOOD_E)
                    # Keramati & Gutkin 2014: reward = drive reduction, drive H(e) = (1-e)^2,
                    # scaled by 1/(2*FOOD_E) so eating at e=0 gives ~0.88. Off-switch: constant da_const.
                    drop = (1 - before) ** 2 - (1 - self.energy) ** 2
                    da_r += drop / (2 * FOOD_E) if self.da_const is None else self.da_const
                    s.pos = self._rand_pos()
                    self.events.append((self.t, "eat"))
                    self.da_rewards.append(da_r)
                else:
                    self.energy = max(0.0, self.energy - TOXIC_E)
                    da_p += 1.0
                    self.events.append((self.t, "toxic"))
                    self.heading += np.pi                            # reflex: turn away
        if da_r or da_p:
            # bidirectional three-factor rule (Bennett et al. 2021 form; Handler et al. 2019)
            self.W *= (1 + ETA * kc_here * (da_r - da_p))[:, None]
            np.clip(self.W, 0, W_MAX * self.W0, out=self.W)
        # what the brain did this step (read-only record for the viewer; no extra random draws)
        self.last = dict(pn=pn_here, kc=kc_here, mbon=kc_here @ self.W, mbon0=kc_here @ self.W0,
                         da_r=da_r, da_p=da_p, v_left=vl, v_right=vr)
        return da_r, da_p

    def learned_valence(self):
        """Valence of each pure source odour (noise-free mean over 5 draws; no learning)."""
        return [float(np.mean([self.valence(self.kc(o)) for _ in range(5)])) for o in self.odors]

    def state(self):
        return dict(t=self.t, pos=self.pos.round(4).tolist(), heading=round(float(self.heading), 3),
                    energy=round(self.energy, 4), curiosity=round(self.curiosity, 4),
                    sources=[dict(pos=s.pos.round(4).tolist(), kind=s.kind) for s in self.sources])


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    W_pk = ((rng.random((340, 2597)) < 0.02) * rng.integers(5, 30, (340, 2597))).astype(np.float32)
    W_km = ((rng.random((2597, 48)) < 0.3) * rng.integers(5, 15, (2597, 48))).astype(np.float32)
    p = Pet(W_pk, W_km, np.arange(340) // 2, seed=1)
    for _ in range(3000):
        p.step()
    ev = [e for _, e in p.events]
    assert 0 <= p.energy <= 1 and (p.W >= 0).all()
    print("pet self-check ok: eats", ev.count("eat"), "toxic", ev.count("toxic"),
          "valence", np.round(p.learned_valence(), 3))
