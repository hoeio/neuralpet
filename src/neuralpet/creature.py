"""The creature: mushroom-body brain (src/neuralpet/mb.py) in the WP5a body (src/neuralpet/body.py)
living in a 2D world with odour sources. All layer-to-layer rules are fixed and written down in
docs/ADAPTERS.md v8 and docs/CREATURE.md. Not biology, not alive.

The brain never sets joint angles. It only biases the CPG: left/right steering from the two head
sensors x learned MBON valence, and amplitude / frequency from internal state (energy).
"""
from dataclasses import dataclass, field

import numpy as np

from neuralpet import mb
from neuralpet.body import Body

# ---- world and adapter constants (v8; fixed by experiments/012/pilot.py round 7 on synthetic wiring,
#      reward modulation off; registered in docs/ADAPTERS.md v8 and asserted by experiments/012/run.py) ----
ARENA = 6.0           # BL; the world is a torus (periodic), so there are no walls to get trapped on
ODOR_SIGMA = 0.8      # BL, Gaussian plume width
R_EAT = 0.4           # BL, head within this of a source = contact
TICK = 0.2            # s, brain update interval
PN_SIGMA, FRAC = 0.1, 0.10
ETA, W_MAX = 0.05, 3.0
STEER_MAX, K_CONTRAST = 0.35, 25.0
FOOD_E, TOXIC_E = 0.3, 0.05
E_BASE, E_EFFORT = 0.0015, 0.0012   # energy per s: baseline + per unit muscle effort rate
TOXIC_REFRACT, REFLEX_S = 3.0, 2.0   # s: no repeated toxic hit / avoidance reflex duration
STEER_NOISE = (0.04, 0.1)  # OU steering noise: base + per unit curiosity (exploration)
T_DEATH = 120.0       # s at zero energy -> end of life (hard mode / precariousness)
N_FOOD, N_TOXIC = 4, 2


def cpg_rule(energy, resting=False):
    """Internal state -> CPG drive (designed rule): hungrier = larger, faster undulation (search).
    Returns (amplitude 0..1, frequency Hz)."""
    if resting:
        return 0.0, 0.0
    h = 1.0 - energy
    return 0.6 + 0.4 * h, 0.6 + 0.6 * h


def drive(e):
    return (1.0 - e) ** 2


@dataclass
class Source:
    pos: np.ndarray
    kind: str          # "food" | "toxic" | "toy" (a neutral odour source: smelled, never eaten)
    odor: int          # row of Creature.odors
    cooldown: float = 0.0


@dataclass
class Creature:
    W_pk: np.ndarray
    W_km: np.ndarray
    odors: np.ndarray                 # (n_odorants, n_pn) odour vectors available in this world
    seed: int = 0                     # history seed: world layout (and noise unless noise_seed is given)
    noise_seed: int = None            # separate PN/steering noise stream (individuality analysis)
    roles: list = None                # list of (kind, odor index) for sources; default random
    da_mode: str = "on"               # "on" (homeostatic), "const", "generic"
    da_const: float = 0.5
    generic_coef: tuple = None        # (a, b, c) for da_mode="generic": DA = max(0, a + b e + c e^2)
    steering: bool = True
    mortal: bool = False
    c_n: float = None                 # drag override (tests only)
    t: float = 0.0
    events: list = field(default_factory=list)

    def __post_init__(self):
        self.rng = np.random.default_rng([self.seed, 1])
        self.noise = np.random.default_rng([self.seed if self.noise_seed is None else self.noise_seed, 2])
        if self.roles is None:
            idx = self.rng.permutation(len(self.odors))[:N_FOOD + N_TOXIC]
            self.roles = [("food", int(i)) for i in idx[:N_FOOD]] + [("toxic", int(i)) for i in idx[N_FOOD:]]
        self.sources = [Source(self._free_pos(), k, o) for k, o in self.roles]
        kw = {} if self.c_n is None else dict(c_n=self.c_n)
        self.body = Body(pos=self.rng.uniform(0, ARENA, 2), heading=self.rng.uniform(-np.pi, np.pi), arena=1e9, **kw)
        self.W0 = self.W_km.astype(np.float64).copy()
        self.W = self.W0.copy()
        self.wsum0 = self.W0.sum(1)
        self.energy, self.curiosity = 0.7, 0.5
        self.zero_time, self.alive, self.resting = 0.0, True, False
        self.reflex, self.last_toxic, self.steer_noise = 0.0, -1e9, 0.0
        self.da_r_log, self.energy_log = [], []
        self.last = {}

    # ---- world
    def _free_pos(self):
        return self.rng.uniform(0.0, ARENA, 2)

    @staticmethod
    def dist2(a, b):
        """Squared distance on the torus (minimum image). The body itself is never wrapped."""
        d = (np.asarray(a) - np.asarray(b) + ARENA / 2) % ARENA - ARENA / 2
        return float((d ** 2).sum())

    def field(self, p):
        """PN input at point p: sum over sources of Gaussian concentration x odour vector."""
        out = np.zeros(self.odors.shape[1])
        for s in self.sources:
            if s.cooldown <= 0:
                out += np.exp(-self.dist2(s.pos, p) / (2 * ODOR_SIGMA ** 2)) * self.odors[s.odor]
        return out

    # ---- brain
    def code(self, pn_in):
        pn = mb.pn_rates(pn_in[None].astype(np.float32), PN_SIGMA, self.noise)
        return pn[0], mb.kc_code(pn, self.W_pk, FRAC)[0]

    def valence(self, kc):
        """Learned valence: MBON drive relative to the naive drive of the same code (0 before learning)."""
        r0 = float(kc @ self.wsum0)
        return float(kc @ self.W.sum(1)) / r0 - 1.0 if r0 > 0 else 0.0

    def valence_of(self, odor_vec, n=5):
        return float(np.mean([self.valence(self.code(odor_vec)[1]) for _ in range(n)]))

    def learn(self, kc, da_r, da_p):
        self.W *= (1 + ETA * kc * (da_r - da_p))[:, None]
        np.clip(self.W, 0, W_MAX * self.W0, out=self.W)

    def reward_da(self, before, after):
        if self.da_mode == "on":
            return (drive(before) - drive(after)) / (2 * FOOD_E)
        if self.da_mode == "const":
            return self.da_const
        a, b, c = self.generic_coef
        return max(0.0, a + b * before + c * before ** 2)

    # ---- one brain tick (TICK seconds of physics)
    def tick(self):
        if not self.alive:
            return
        sl, sr = self.body.sensors()
        pl, kl = self.code(self.field(sl))
        pr, kr = self.code(self.field(sr))
        il, ir = pl.mean(), pr.mean()
        vl, vr = self.valence(kl), self.valence(kr)
        v = 0.5 * (vl + vr)
        contrast = (il - ir) / (il + ir + 0.01)
        self.steer_noise += -self.steer_noise * TICK + np.sqrt(TICK) * (STEER_NOISE[0] + STEER_NOISE[1] * self.curiosity) * self.noise.standard_normal()
        steer = STEER_MAX * np.tanh(K_CONTRAST * v * contrast) if self.steering else 0.0
        if self.reflex > 0:                        # innate avoidance reflex after a toxic hit (fixed)
            steer, self.reflex = -STEER_MAX * np.sign(il - ir or 1.0), self.reflex - TICK
        steer = 0.0 if self.resting else float(np.clip(steer + self.steer_noise, -1, 1))
        amp, freq = cpg_rule(self.energy, self.resting)
        e0 = self.body.effort[0]
        self.body.step(TICK, amp, freq, steer)
        effort = (self.body.effort[0] - e0) / TICK
        self.t += TICK
        # internal state
        self.energy = max(0.0, self.energy - TICK * (E_BASE + E_EFFORT * effort))
        self.curiosity += 0.05 * TICK * (self.energy - self.curiosity)
        da_r = da_p = 0.0
        head = self.body.head
        pn_h, kc_h = self.code(self.field(head))
        for s in self.sources:
            s.cooldown = max(0.0, s.cooldown - TICK)
            if getattr(s, "inside", False) and self.dist2(s.pos, head) > (1.5 * R_EAT) ** 2:
                s.inside = False
            if s.cooldown > 0 or self.dist2(s.pos, head) > R_EAT ** 2:
                continue
            if s.kind == "food":
                before = self.energy
                self.energy = min(1.0, self.energy + FOOD_E)
                da_r += self.reward_da(before, self.energy)
                self.da_r_log.append(da_r)
                s.pos, s.cooldown = self._free_pos(), 5.0
                self.events.append((round(self.t, 1), "eat", s.odor))
            elif s.kind == "toxic" and not getattr(s, "inside", False) and self.t - self.last_toxic > TOXIC_REFRACT:
                # fix for getting stuck at toxic sources: one hit per contact episode (the head must
                # leave 1.5 x the contact radius before the same source can hit again) + refractory time
                s.inside = True
                self.energy = max(0.0, self.energy - TOXIC_E)
                da_p += 1.0
                self.last_toxic, self.reflex = self.t, REFLEX_S
                self.events.append((round(self.t, 1), "toxic", s.odor))
        if da_r or da_p:
            self.learn(kc_h, da_r, da_p)
        self.zero_time = self.zero_time + TICK if self.energy <= 0 else 0.0
        if self.mortal and self.zero_time >= T_DEATH:
            self.alive = False
            self.events.append((round(self.t, 1), "death", -1))
        self.energy_log.append(self.energy)
        self.last = dict(pn=pn_h, kc=kc_h, mbon=kc_h @ self.W, da_r=da_r, da_p=da_p, v=v, v_left=vl, v_right=vr, steer=steer, effort=effort, amp=amp, freq=freq)

    def run(self, seconds):
        for _ in range(int(round(seconds / TICK))):
            if not self.alive:
                break
            self.tick()

    def preferences(self, idx=None):
        """Learned valence of each world odorant (noise-averaged), the creature's 'personality'."""
        idx = range(len(self.odors)) if idx is None else idx
        return np.array([self.valence_of(self.odors[i]) for i in idx])
