"""Read-only local viewer: runs the pet and serves its body state and brain activity.

    uv run python viewer/server.py      # prints http://127.0.0.1:8797/?t=<token> (port: NEURALPET_PORT)

Binds 127.0.0.1 only. Every request needs the token from .env (NEURALPET_TOKEN, created on first
run). No control endpoints: the page can only watch.

Endpoints (all need ?t=<token>):
  /            the page
  /brain       static brain geometry: neuron positions (FlyWire), optional synapse-sampled shapes,
               PN->KC edges, cell types. Sent once.
  /state       ?since=<step>: per-step brain frames after that step + body/world state
  /curves.png  experiment 001 figure
Polling, not SSE: through the Cloudflare tunnel an event stream was held in 128 KiB blocks
(measured 2026-11-06), see docs/TUNNEL.md.
"""
import base64
import collections
import hmac
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

from neuralpet.pet import FRAC, Pet

ROOT = Path(__file__).resolve().parents[1]
HOST, PORT = "127.0.0.1", int(os.environ.get("NEURALPET_PORT", 8797))
STEPS_PER_S = 15
B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def token():
    env = ROOT / ".env"
    for line in env.read_text().splitlines() if env.exists() else []:
        if line.startswith("NEURALPET_TOKEN="):
            val = line.split("=", 1)[1].strip()
            if len(val) >= 16:
                return val
    t = secrets.token_urlsafe(24)
    fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "a") as f:
        f.write(f"NEURALPET_TOKEN={t}\n")
    return t


def q36(x, top):
    """Quantise values in [0, top] to one base-36 character each."""
    i = np.clip(np.rint(np.asarray(x) / top * 35), 0, 35).astype(int)
    return "".join(B36[j] for j in i)


def load():
    p = ROOT / "data" / "mb" / "mb.npz"
    if not p.exists():
        raise SystemExit("data/mb/mb.npz missing: run scripts/fetch_flywire.py and scripts/extract_mb.py")
    return np.load(p)


def brain_geometry(d):
    """Positions in µm, centred on the KC centroid; y flipped so dorsal is up."""
    centre = d["pos_kc"].mean(0) / 1000

    def um(p):
        q = p / 1000 - centre
        q[:, 1] *= -1
        return np.round(q, 1).tolist()

    g = dict(
        groups={k: um(d[f"pos_{k}"]) for k in ["pn", "kc", "mbon", "dan", "apl"]},
        kc_type=d["kc_type"].tolist(), mbon_type=d["mbon_type"].tolist(), dan_type=d["dan_type"].tolist(),
        pn_kc=np.argwhere(d["W_pnkc"] > 0).tolist(), shapes=None)
    shp = ROOT / "data" / "mb" / "shapes.npz"
    if shp.exists():     # synapse-sampled points per neuron (scripts/extract_shapes.py)
        s = np.load(shp)
        g["shapes"] = {k: dict(owner=s[f"{k}_owner"].tolist(), xyz=um(s[f"{k}_xyz"])) for k in
                       ["pn", "kc", "mbon", "dan", "apl"] if f"{k}_xyz" in s.files}
    return json.dumps(g, separators=(",", ":")).encode()


class Sim(threading.Thread):
    def __init__(self, d):
        super().__init__(daemon=True)
        self.label = "FlyWire v783, right mushroom body (real wiring)"
        self.pet = Pet(d["W_pnkc"], d["W_kcmbon"], d["glom_of_pn"], seed=int(time.time()) % 10000)
        k = int(FRAC * d["W_pnkc"].shape[1])
        self.mbon_ref = np.maximum(k * d["W_kcmbon"].mean(0), 1e-9)   # expected drive of an average code
        self.lock, self.history = threading.Lock(), []
        self.frames = collections.deque(maxlen=150)
        self.world = {}

    def run(self):
        while True:
            t0 = time.time()
            with self.lock:
                n_ev = len(self.pet.events)
                self.pet.step()
                p, b = self.pet, self.pet.last
                if p.t % 30 == 1:
                    self.history.append([p.t, *np.round(p.learned_valence(), 4).tolist()])
                    self.history = self.history[-400:]
                self.frames.append(dict(
                    t=p.t, pos=p.pos.round(4).tolist(), heading=round(float(p.heading), 3),
                    energy=round(p.energy, 3), curiosity=round(p.curiosity, 3),
                    kc=base64.b64encode(np.packbits(b["kc"] > 0).tobytes()).decode(),
                    pn=q36(b["pn"], 2.0), mbon=q36(b["mbon"] / self.mbon_ref, 2.0),
                    da_r=round(float(b["da_r"]), 3), da_p=round(float(b["da_p"]), 3),
                    v=[round(b["v_left"], 4), round(b["v_right"], 4)],
                    events=[e for _, e in p.events[n_ev:]]))
                self.world = dict(sources=[dict(pos=s.pos.round(4).tolist(), kind=s.kind) for s in p.sources],
                                  wiring=self.label,
                                  n_eat=sum(e == "eat" for _, e in p.events),
                                  n_toxic=sum(e == "toxic" for _, e in p.events))
            time.sleep(max(0.0, 1 / STEPS_PER_S - (time.time() - t0)))


def make_handler(sim, tok, brain):
    files = {"/": (ROOT / "viewer" / "index.html", "text/html; charset=utf-8"),
             "/curves.png": (ROOT / "reports" / "001" / "learning_curves.png", "image/png")}

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def reply(self, body, ctype, cache="no-store"):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            given = q.get("t", [""])[0]
            if not given or not tok or not hmac.compare_digest(given.encode(), tok.encode()):
                return self.send_error(403)
            if u.path == "/state":
                try:
                    since = int(q.get("since", ["-1"])[0])
                except ValueError:
                    since = -1
                with sim.lock:
                    frames = [f for f in sim.frames if f["t"] > since][-40:]
                    hist_since = int(q.get("hsince", ["-1"])[0]) if q.get("hsince", [""])[0].lstrip("-").isdigit() else -1
                    msg = dict(sim.world, frames=frames,
                               history_add=[h for h in sim.history if h[0] > hist_since])
                return self.reply(json.dumps(msg, separators=(",", ":")).encode(), "application/json")
            if u.path == "/brain":
                return self.reply(brain, "application/json", "private, max-age=3600")
            if u.path in files and files[u.path][0].exists():
                return self.reply(files[u.path][0].read_bytes(), files[u.path][1])
            self.send_error(404)

    return H


def main():
    tok = token()
    d = load()
    sim = Sim(d)
    sim.start()
    srv = ThreadingHTTPServer((HOST, PORT), make_handler(sim, tok, brain_geometry(d)))
    print(f"NeuralPet viewer ({sim.label}): http://{HOST}:{PORT}/?t={tok}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
