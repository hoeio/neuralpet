"""One pet's life for the play app: the frozen research creature (src/neuralpet/creature.py) plus care
actions, persistence, catch-up, torpor, diary. Gameplay settings live in play/config.json only.
Never modifies src/neuralpet; never feeds confirmatory results.
"""
import io
import json
import os
import shutil
import threading
import time
from pathlib import Path

import numpy as np

from neuralpet import creature as C

ROOT = Path(__file__).resolve().parents[2]
SAVE_VERSION = 1
CONFIG = json.loads((ROOT / "play" / "config.json").read_text())


def load_genome():
    """Real FlyWire right MB wiring if present, else a synthetic stand-in (labelled as such)."""
    p = ROOT / "data" / "mb" / "mb.npz"
    if p.exists():
        d = np.load(p)
        from neuralpet.odors import door_odors
        odors, keys, _ = door_odors(d["glom_names"], d["glom_of_pn"])
        return d["W_pnkc"], d["W_kcmbon"], odors, odorant_names(keys), "FlyWire v783 right mushroom body"
    r = np.random.default_rng(0)
    W_pk = ((r.random((60, 800)) < 0.06) * r.integers(5, 30, (60, 800))).astype(np.float32)
    W_km = ((r.random((800, 10)) < 0.3) * r.integers(5, 12, (800, 10))).astype(np.float32)
    odors = ((r.random((12, 60)) < 0.3) * r.exponential(0.6, (12, 60))).astype(np.float32)
    return W_pk, W_km, odors, [f"odour {i + 1}" for i in range(12)], "synthetic stand-in (no FlyWire data found)"


def odorant_names(keys):
    import pandas as pd
    t = pd.read_csv(ROOT / "data" / "door" / "odor.csv", sep=";").set_index("InChIKey")
    names = [str(t.Name.get(k, k)).strip() for k in keys]
    seen = {}
    out = []
    for n in names:                            # make names unique for the menu
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else f"{n} ({seen[n]})")
    return out


def _gen_state(g):
    return json.loads(json.dumps(g.bit_generator.state))


def _set_gen(g, st):
    g.bit_generator.state = st


class Game:
    def __init__(self, data_dir, cfg=None, genome=None):
        self.cfg = dict(CONFIG, **(cfg or {}))
        # Play-only steering gain (docs/PLAY.md): the registered research value (creature.K_CONTRAST = 25)
        # gives almost no chemotaxis, so taught preferences would not show in behaviour. This changes the
        # module value inside the play process only; research runs never import neuralpet_play.
        C.K_CONTRAST = float(self.cfg["steer_gain"])
        self.dir = Path(data_dir)
        (self.dir / "memorials").mkdir(parents=True, exist_ok=True)
        self.W_pk, self.W_km, self.odors, self.names, self.genome_label = genome or load_genome()
        self.lock = threading.RLock()
        self.food_odor = self.names.index(self.cfg["food_odor"]) if self.cfg["food_odor"] in self.names else 0
        if not self.load():
            self.new_pet()

    # ---------- life
    def new_pet(self, name=None):
        with self.lock:
            if getattr(self, "pet", None) is not None:
                self.memorialise()
            seed = self.cfg.get("seed") or int.from_bytes(os.urandom(4), "little")
            roles = [("food", self.food_odor)] * self.cfg["n_food"]
            self.pet = C.Creature(self.W_pk, self.W_km, self.odors, seed=seed, roles=roles, mortal=self.cfg["hard_mode"])
            for s in self.pet.sources:
                s.natural = True
            self.meta = dict(name=name or self.cfg["default_name"], born=time.time(), seed=seed, torpor=False,
                             known=[self.food_odor], diary=[], pid=os.urandom(6).hex())
            self.diary("born", f"{self.meta['name']} hatched. Its brain is wired from the {self.genome_label}.")
            self.save()

    def diary(self, kind, text):
        self.meta["diary"].append(dict(t=time.time(), age=round(self.pet.t, 1), kind=kind, text=text))
        self.meta["diary"] = self.meta["diary"][-300:]

    def advance(self, seconds):
        """Simulate `seconds` of pet time (catch-up and the live loop)."""
        with self.lock:
            p = self.pet
            for _ in range(int(round(seconds / C.TICK))):
                if not p.alive:
                    break
                n_ev = len(p.events)
                p.resting = self.meta["torpor"] or self.meta.get("lights_off", False)
                p.tick()
                for t, kind, o in p.events[n_ev:]:
                    if kind == "eat":
                        self.diary("eat", f"Ate something that smelled of {self.names[o]}.")
                    elif kind == "toxic":
                        self.diary("toxic", f"Touched something unpleasant ({self.names[o]}).")
                    elif kind == "death":
                        self.diary("death", f"{self.meta['name']}'s life ended after a long time without energy (hard mode).")
                # owner-dropped food disappears once eaten; offered odours fade
                p.sources = [s for s in p.sources if not (getattr(s, "once", False) and s.cooldown > 0)
                             and getattr(s, "until", 1e18) > p.t]
                if not self.cfg["hard_mode"]:
                    if not self.meta["torpor"] and p.zero_time >= self.cfg["torpor_after_s"]:
                        self.meta["torpor"] = True
                        self.diary("torpor", f"{self.meta['name']} curled up and went into torpor. Feeding wakes it.")

    def catch_up(self, elapsed_real):
        sim = min(elapsed_real * self.cfg["speed"], self.cfg["catch_up_cap_s"])
        if sim >= C.TICK:
            self.advance(sim)
            self.diary("away", f"You were away {fmt_dur(elapsed_real)}; {self.meta['name']} lived {fmt_dur(sim)} "
                               f"of fast-forwarded time" + (" (capped)" if sim < elapsed_real * self.cfg["speed"] else "") + ".")

    # ---------- actions (whitelisted and validated by security.validate_action)
    def act(self, a):
        with self.lock:
            p, n = self.pet, self.meta["name"]
            k = a["action"]
            if k == "feed":
                self._drop("food", p.body.head + 0.1 * np.array([np.cos(p.body.heading), np.sin(p.body.heading)]), self.food_odor)
                if self.meta["torpor"]:
                    self.meta["torpor"] = False
                    p.zero_time = 0.0
                    p.energy = max(p.energy, 0.05)
                    self.diary("wake", f"{n} woke up from torpor.")
                self.diary("feed", f"You fed {n}.")
            elif k in ("praise", "scold"):
                kc = p.code(p.field(p.body.head))[1]
                if k == "praise":
                    p.learn(kc, self.cfg["praise_da"], 0.0)
                else:
                    p.learn(kc, 0.0, self.cfg["scold_da"])
                smell = self.dominant_smell()
                self.diary(k, f"You {'praised' if k == 'praise' else 'scolded'} {n}" + (f" while it smelled {smell}." if smell else "."))
            elif k == "offer_odor":
                i = self.names.index(a["odor"])
                h = p.body.head + 0.6 * np.array([np.cos(p.body.heading), np.sin(p.body.heading)])
                s = C.Source(h % C.ARENA, "toy", i)
                s.until = p.t + self.cfg["offer_s"]
                s.whiff = True                                  # a new whiff replaces the previous one
                p.sources = [x for x in p.sources if not getattr(x, "whiff", False)] + [s]
                self._know(i)
                self.diary("offer", f"You held out a whiff of {a['odor']}.")
            elif k == "drop":
                pos = (np.array([a["x"], a["y"]]) * C.ARENA) % C.ARENA
                if a["item"] == "food":
                    self._drop("food", pos, self.food_odor)
                    self.diary("drop", "You dropped a food pellet.")
                else:
                    i = self.names.index(a["odor"])
                    s = C.Source(pos, "toy", i)
                    s.until = p.t + self.cfg["toy_s"]
                    p.sources = [x for x in p.sources if not getattr(x, "toy", False)] + [s]
                    s.toy = True
                    self._know(i)
                    self.diary("toy", f"You put down a toy that smells of {a['odor']}.")
            elif k == "rest":
                self.meta["lights_off"] = a["on"]
                self.diary("rest", "Lights off: resting." if a["on"] else "Lights on.")
            elif k == "rename":
                old, self.meta["name"] = n, a["name"]
                self.diary("rename", f"{old} is now called {a['name']}.")
            elif k == "new_pet":
                self.new_pet()
            self.log(a)
            self.save()

    def _drop(self, kind, pos, odor):
        s = C.Source(np.asarray(pos, float) % C.ARENA, kind, odor)
        s.once = True
        self.pet.sources.append(s)

    def _know(self, i):
        if i not in self.meta["known"]:
            self.meta["known"].append(i)

    def dominant_smell(self):
        p = self.pet
        best, bi = 0.05, None
        for s in p.sources:
            c = np.exp(-((s.pos - p.body.head) ** 2).sum() / (2 * C.ODOR_SIGMA ** 2))
            if c > best:
                best, bi = c, s.odor
        return self.names[bi] if bi is not None else None

    def log(self, a):
        rec = dict(t=time.time(), action=a, pid=self.meta["pid"], age=round(self.pet.t, 1),
                   energy=round(self.pet.energy, 4), torpor=self.meta["torpor"])
        with open(self.dir / "interactions.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")

    # ---------- readouts
    def preferences(self):
        with self.lock:
            return [dict(odor=self.names[i], valence=round(self.pet.valence_of(self.odors[i]), 4)) for i in self.meta["known"]]

    def mood(self, prefs=None):
        p = self.pet
        if not p.alive:
            return "at rest forever (memorial)"
        if self.meta["torpor"]:
            return "in torpor (feed to wake)"
        if self.meta.get("lights_off"):
            return "resting"
        smell = self.dominant_smell()
        wary = [x for x in (prefs or []) if x["valence"] < -0.05 and x["odor"] == smell]
        if wary:
            return f"wary of {smell}"
        if p.energy < 0.3:
            return "hungry"
        if p.curiosity > 0.6:
            return "curious"
        return "content"

    def snapshot(self):
        with self.lock:
            p = self.pet
            return dict(name=self.meta["name"], age_s=round(p.t, 1), born=self.meta["born"], energy=round(p.energy, 4),
                        curiosity=round(p.curiosity, 4), torpor=self.meta["torpor"], alive=p.alive,
                        lights_off=bool(self.meta.get("lights_off")), body=(p.body.x - np.floor(p.body.head / C.ARENA) * C.ARENA).round(4).tolist(),  # torus: shift so the head is inside [0, ARENA)
                        heading=round(p.body.heading, 4),
                        sources=[dict(pos=s.pos.round(3).tolist(), kind=s.kind, odor=self.names[s.odor],
                                      active=s.cooldown <= 0) for s in p.sources],
                        kc=np.flatnonzero(p.last.get("kc", np.zeros(1)) > 0).tolist(),
                        da=dict(r=round(float(p.last.get("da_r", 0)), 3), p=round(float(p.last.get("da_p", 0)), 3)),
                        arena=C.ARENA, diary=self.meta["diary"][-12:], genome=self.genome_label)

    # ---------- persistence: one npz written atomically, rolling backups
    def state_bytes(self):
        p = self.pet
        meta = dict(version=SAVE_VERSION, saved_at=time.time(), meta=self.meta, t=p.t, energy=p.energy, curiosity=p.curiosity,
                    zero_time=p.zero_time, alive=p.alive, reflex=p.reflex, last_toxic=p.last_toxic, steer_noise=p.steer_noise,
                    body_t=p.body.t, seed=p.seed, mortal=p.mortal, events=p.events[-500:],
                    sources=[dict(pos=s.pos.tolist(), kind=s.kind, odor=s.odor, cooldown=s.cooldown,
                                  extra={k: getattr(s, k) for k in ("once", "until", "toy", "natural", "whiff") if hasattr(s, k)})
                             for s in p.sources],
                    rng=_gen_state(p.rng), noise=_gen_state(p.noise))
        buf = io.BytesIO()
        np.savez_compressed(buf, meta=np.array(json.dumps(meta)), W=p.W, x=p.body.x, phi=p.body.phi, th_prev=p.body.th_prev,
                            effort=p.body.effort)
        return buf.getvalue()

    def save(self):
        with self.lock:
            data = self.state_bytes()
            f = self.dir / "pet.npz"
            if f.exists():                                  # rolling backup: pet.npz.1 .. .3
                for i in (2, 1):
                    b = self.dir / f"pet.npz.{i}"
                    if b.exists():
                        os.replace(b, self.dir / f"pet.npz.{i + 1}")
                shutil.copy2(f, self.dir / "pet.npz.1")
            tmp = self.dir / f"pet.npz.tmp{os.getpid()}"
            with open(tmp, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, f)                              # atomic on POSIX
            dfd = os.open(self.dir, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)

    def load(self):
        for f in [self.dir / "pet.npz"] + [self.dir / f"pet.npz.{i}" for i in (1, 2, 3)]:
            if not f.exists():
                continue
            try:
                self._restore(np.load(f, allow_pickle=False))
                return True
            except Exception as e:                          # corrupt file: fall back to the next backup
                print(f"could not load {f.name}: {e!r}; trying backup", flush=True)
        return False

    def _restore(self, z):
        m = json.loads(str(z["meta"]))
        if m["version"] != SAVE_VERSION:
            raise ValueError(f"save version {m['version']}")
        p = C.Creature(self.W_pk, self.W_km, self.odors, seed=m["seed"], roles=[("food", 0)], mortal=m["mortal"])
        p.W = z["W"].astype(np.float64)
        p.body.x, p.body.phi, p.body.th_prev, p.body.effort = (z[k].copy() for k in ("x", "phi", "th_prev", "effort"))
        p.body.t = m["body_t"]
        for k in ("t", "energy", "curiosity", "zero_time", "alive", "reflex", "last_toxic", "steer_noise"):
            setattr(p, k, m[k])
        p.events = [tuple(e) for e in m["events"]]
        p.sources = []
        for s in m["sources"]:
            src = C.Source(np.array(s["pos"]), s["kind"], s["odor"], s["cooldown"])
            for k, v in s["extra"].items():
                setattr(src, k, v)
            p.sources.append(src)
        _set_gen(p.rng, m["rng"])
        _set_gen(p.noise, m["noise"])
        self.pet, self.meta, self.saved_at = p, m["meta"], m["saved_at"]

    def memorialise(self):
        p = self.pet
        ev = [e[1] for e in p.events]
        summary = dict(name=self.meta["name"], born=self.meta["born"], ended=time.time(), age_s=round(p.t, 1),
                       meals=ev.count("eat"), preferences=self.preferences(), diary=self.meta["diary"][-50:],
                       alive_at_end=p.alive, genome=self.genome_label)
        (self.dir / "memorials" / f"{self.meta['pid']}.json").write_text(json.dumps(summary))

    def memorials(self):
        out = []
        for f in sorted((self.dir / "memorials").glob("*.json")):
            try:
                out.append(json.loads(f.read_text()))
            except (OSError, json.JSONDecodeError):
                pass
        return out


def fmt_dur(s):
    s = int(s)
    if s < 60:
        return f"{s} s"
    if s < 3600:
        return f"{s // 60} min {s % 60} s"
    return f"{s // 3600} h {(s % 3600) // 60} min"
