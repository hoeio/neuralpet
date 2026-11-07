"""The creature's body (WP5a, docs/CREATURE.md): a 2D articulated chain moving by undulation.

Our design, not biology. Overdamped (low-Reynolds) dynamics with resistive-force drag:
each node's velocity is its force divided by an anisotropic drag (tangential c_t, normal c_n).
Joints are torsional springs + dampers driven by dorsal/ventral muscle torques from a chain of
coupled phase oscillators (CPG). Links are kept at fixed length by symmetric projection (so the
internal forces and the length constraint never move the centre of mass by themselves: with
isotropic drag the body cannot travel; tested). Deterministic, no randomness in here.

Units: body length (BL) = 1, time in seconds. Node 0 is the head.
"""
import numpy as np
from numba import njit

# physics constants (fixed; never change with age or play; docs/ADAPTERS.md v5)
N_SEG = 12
C_T, C_N = 1.0, 10.0          # drag per node (tangential, normal); ratio 10 ~ crawling on a gel
K_BEND, C_BEND = 1.0, 0.002   # joint spring and damper (explicit damper: C_BEND/(C_T·L²) < 1 for stability)
DT = 0.002                    # s, physics step (stability: tests/test_body.py)
TAU_MAX = 0.4                 # muscle torque at full activation
CPG_K = 4.0                   # oscillator coupling
WAVES = 1.0                   # body waves along the chain (head -> tail)
PROJ_ITERS = 4


@njit(cache=True)
def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


@njit(cache=True)
def _angles(x):
    n = x.shape[0] - 1
    ang = np.empty(n)
    for i in range(n):
        # link i points from node i+1 to node i (tail -> head), so angle = heading of that segment
        ang[i] = np.arctan2(x[i, 1] - x[i + 1, 1], x[i, 0] - x[i + 1, 0])
    th = np.empty(n - 1)
    for j in range(n - 1):
        th[j] = _wrap(ang[j] - ang[j + 1])        # joint j between links j (front) and j+1 (behind)
    return th


@njit(cache=True)
def _simulate(x, phi, th_prev, n_steps, amp, freq, steer, c_t, c_n, L0, arena, effort_out, tau_max, k_bend):
    n_nodes = x.shape[0]
    n_j = n_nodes - 2
    dphi = 2 * np.pi * WAVES / n_j
    F = np.zeros((n_nodes, 2))
    effort = 0.0
    for _ in range(n_steps):
        # --- CPG: head leads, wave travels to the tail
        new = np.empty(n_j)
        for j in range(n_j):
            c = 0.0
            if j > 0:
                c += np.sin(phi[j - 1] - phi[j] - dphi)
            if j < n_j - 1:
                c += np.sin(phi[j + 1] - phi[j] + dphi)
            new[j] = phi[j] + DT * (2 * np.pi * freq + CPG_K * c)
        phi[:] = new
        # --- joint torques
        th = _angles(x)
        F[:] = 0.0
        for j in range(n_j):
            tau_m = tau_max * (amp * np.sin(phi[j]) + steer)
            effort += (tau_m / tau_max) ** 2 * DT / n_j
            tau = -k_bend * th[j] - C_BEND * (th[j] - th_prev[j]) / DT + tau_m
            th_prev[j] = th[j]
            # +tau on the front link (nodes j+1 -> j), -tau on the link behind (nodes j+2 -> j+1)
            for (a, b, s) in ((j + 1, j, 1.0), (j + 2, j + 1, -1.0)):
                lx, ly = x[b, 0] - x[a, 0], x[b, 1] - x[a, 1]
                l2 = lx * lx + ly * ly
                fx, fy = -s * tau * ly / l2, s * tau * lx / l2
                F[b, 0] += fx
                F[b, 1] += fy
                F[a, 0] -= fx
                F[a, 1] -= fy
        # --- walls: soft repulsion inside a margin
        for i in range(n_nodes):
            for d in range(2):
                if x[i, d] < 0.0:
                    F[i, d] += 50.0 * (0.0 - x[i, d])
                elif x[i, d] > arena:
                    F[i, d] += 50.0 * (arena - x[i, d])
        # --- anisotropic drag: v = (F.t) t / c_t + (F.n) n / c_n, t = local body axis
        for i in range(n_nodes):
            if i == 0:
                tx, ty = x[0, 0] - x[1, 0], x[0, 1] - x[1, 1]
            elif i == n_nodes - 1:
                tx, ty = x[i - 1, 0] - x[i, 0], x[i - 1, 1] - x[i, 1]
            else:
                tx, ty = x[i - 1, 0] - x[i + 1, 0], x[i - 1, 1] - x[i + 1, 1]
            tn = np.sqrt(tx * tx + ty * ty)
            tx, ty = tx / tn, ty / tn
            ft = F[i, 0] * tx + F[i, 1] * ty
            fn = -F[i, 0] * ty + F[i, 1] * tx
            x[i, 0] += DT * (ft * tx / c_t - fn * ty / c_n)
            x[i, 1] += DT * (ft * ty / c_t + fn * tx / c_n)
        # --- inextensible links: symmetric projection (keeps the centre of mass)
        for _k in range(PROJ_ITERS):
            for i in range(n_nodes - 1):
                dx, dy = x[i, 0] - x[i + 1, 0], x[i, 1] - x[i + 1, 1]
                d = np.sqrt(dx * dx + dy * dy)
                corr = 0.5 * (d - L0) / d
                x[i, 0] -= corr * dx
                x[i, 1] -= corr * dy
                x[i + 1, 0] += corr * dx
                x[i + 1, 1] += corr * dy
    effort_out[0] += effort


class Body:
    """State of one creature body. step(seconds, amp, freq, steer) advances the physics."""

    def __init__(self, pos=(5.0, 5.0), heading=0.0, n_seg=N_SEG, arena=10.0, c_t=C_T, c_n=C_N):
        self.L0 = 1.0 / n_seg
        h = np.array([np.cos(heading), np.sin(heading)])
        self.x = np.array(pos, float) + np.outer(-np.arange(n_seg + 1) * self.L0 + 0.5, h)
        self.phi = -np.arange(n_seg - 1) * 2 * np.pi * WAVES / (n_seg - 1)
        self.th_prev = np.zeros(n_seg - 1)
        self.c_t, self.c_n, self.arena = c_t, c_n, arena
        self.effort = np.zeros(1)          # accumulated muscle effort (mean squared activation × s)
        self.t = 0.0

    def step(self, seconds, amp, freq, steer=0.0):
        n = int(round(seconds / DT))
        _simulate(self.x, self.phi, self.th_prev, n, float(amp), float(freq), float(steer),
                  self.c_t, self.c_n, self.L0, self.arena, self.effort, TAU_MAX, K_BEND)
        self.t += n * DT

    @property
    def head(self):
        return self.x[0]

    @property
    def heading(self):
        d = self.x[0] - self.x[2]
        return float(np.arctan2(d[1], d[0]))

    def sensors(self, offset=0.04, ahead=0.02):
        """Left and right head sensors (positions on the simulated body)."""
        h = self.heading
        f = np.array([np.cos(h), np.sin(h)])
        left = np.array([-f[1], f[0]])
        p = self.x[0] + ahead * f
        return p + offset * left, p - offset * left

    def com(self):
        return self.x.mean(0)
