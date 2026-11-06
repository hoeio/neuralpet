"""Read-only local viewer: runs the pet and streams its state to the browser (SSE).

    uv run python viewer/server.py      # prints http://127.0.0.1:8797/?t=<token> (port: NEURALPET_PORT)

Binds 127.0.0.1 only. Every request needs the token from .env (NEURALPET_TOKEN, created on first
run). No control endpoints: the page can only watch.
"""
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

from neuralpet.pet import Pet

ROOT = Path(__file__).resolve().parents[1]
HOST, PORT, STEPS_PER_S = "127.0.0.1", int(os.environ.get("NEURALPET_PORT", 8797)), 30


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


def load_wiring():
    p = ROOT / "data" / "mb" / "mb.npz"
    if p.exists():
        d = np.load(p)
        return d["W_pnkc"], d["W_kcmbon"], d["glom_of_pn"], "FlyWire v783 right MB (real wiring)"
    rng = np.random.default_rng(0)   # fallback so the viewer works without the data
    W_pk = ((rng.random((340, 2597)) < 0.02) * rng.integers(5, 30, (340, 2597))).astype(np.float32)
    W_km = ((rng.random((2597, 48)) < 0.3) * rng.integers(5, 15, (2597, 48))).astype(np.float32)
    return W_pk, W_km, np.arange(340) // 2, "SYNTHETIC random wiring (FlyWire data not fetched)"


class Sim(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        W_pk, W_km, glom, self.label = load_wiring()
        self.pet = Pet(W_pk, W_km, glom, seed=int(time.time()) % 10000)
        self.lock, self.history, self.snapshot = threading.Lock(), [], {}

    def run(self):
        while True:
            t0 = time.time()
            with self.lock:
                self.pet.step()
                if self.pet.t % 30 == 1:
                    self.history.append([self.pet.t, *np.round(self.pet.learned_valence(), 4).tolist()])
                    self.history = self.history[-400:]
                s = self.pet.state()
                s.update(wiring=self.label, events=self.pet.events[-8:], history=self.history[-400:],
                         n_eat=sum(e == "eat" for _, e in self.pet.events),
                         n_toxic=sum(e == "toxic" for _, e in self.pet.events))
                self.snapshot = s
            time.sleep(max(0.0, 1 / STEPS_PER_S - (time.time() - t0)))


def make_handler(sim, tok):
    files = {"/": (ROOT / "viewer" / "index.html", "text/html; charset=utf-8"),
             "/curves.png": (ROOT / "reports" / "001" / "learning_curves.png", "image/png")}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            u = urlparse(self.path)
            given = parse_qs(u.query).get("t", [""])[0]
            if not given or not tok or not hmac.compare_digest(given.encode(), tok.encode()):
                return self.send_error(403)
            if u.path == "/stream":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    while True:
                        with sim.lock:
                            msg = json.dumps(sim.snapshot)
                        self.wfile.write(f"data: {msg}\n\n".encode())
                        self.wfile.flush()
                        time.sleep(0.1)
                except (BrokenPipeError, ConnectionResetError):
                    return
            if u.path in files and files[u.path][0].exists():
                body = files[u.path][0].read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", files[u.path][1])
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return self.wfile.write(body)
            self.send_error(404)

    return H


def main():
    tok = token()
    sim = Sim()
    sim.start()
    srv = ThreadingHTTPServer((HOST, PORT), make_handler(sim, tok))
    print(f"NeuralPet viewer ({sim.label}): http://{HOST}:{PORT}/?t={tok}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
