"""NeuralPet play app: raise and teach one pet from a phone browser. docs/PLAY.md.

    scripts/run_play.sh            # or: uv run python -m neuralpet_play.server

Binds 127.0.0.1 only. Open http://127.0.0.1:8798/?t=<NEURALPET_PLAY_TOKEN> once; the token is
exchanged for an HttpOnly session cookie and removed from the URL. NEURALPET_PLAY=0 = read-only.
"""
import gzip
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

from neuralpet_play import security as S
from neuralpet_play.game import ROOT, Game

PLAY = ROOT / "play"
STATIC = {"/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8"),
          "/about": ("about.html", "text/html; charset=utf-8"), "/": ("index.html", "text/html; charset=utf-8")}


def play_token(env_path=ROOT / ".env"):
    for line in env_path.read_text().splitlines() if env_path.exists() else []:
        if line.startswith("NEURALPET_PLAY_TOKEN="):
            v = line.split("=", 1)[1].strip()
            if len(v) >= 16:
                return v
    t = secrets.token_urlsafe(24)
    fd = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a") as f:
        f.write(f"NEURALPET_PLAY_TOKEN={t}\n")
    return t


def brain_points(n_max=2500):
    """2D brain outline for drawing in the head: FlyWire synapse-sampled points if available, else
    neuron positions, else nothing. Normalised to the unit disc. Derived FlyWire data, served only to
    the token holder, never committed."""
    d = ROOT / "data" / "mb"
    pts, own = [], []
    try:
        if (d / "shapes.npz").exists():
            s = np.load(d / "shapes.npz")
            for g in ("kc", "pn", "mbon"):
                if f"{g}_xyz" in s.files:
                    pts.append(s[f"{g}_xyz"][:, :2])
                    own.append(np.stack([np.full(len(s[f"{g}_owner"]), ("kc", "pn", "mbon").index(g)), s[f"{g}_owner"]], 1))
        elif (d / "mb.npz").exists():
            m = np.load(d / "mb.npz")
            for i, g in enumerate(("kc", "pn", "mbon")):
                pts.append(m[f"pos_{g}"][:, :2])
                own.append(np.stack([np.full(len(m[f"pos_{g}"]), i), np.arange(len(m[f"pos_{g}"]))], 1))
    except (OSError, KeyError, ValueError):
        return dict(points=[], note="no brain geometry")
    if not pts:
        return dict(points=[], note="no brain geometry")
    P, O = np.concatenate(pts).astype(float), np.concatenate(own)
    idx = np.random.default_rng(0).permutation(len(P))[:n_max]
    P, O = P[idx], O[idx]
    P[:, 1] *= -1
    P -= P.mean(0)
    P /= np.abs(P).max()
    return dict(points=np.round(P, 3).tolist(), owner=O.tolist(),
                note="FlyWire v783 mushroom-body neurons (synapse-sampled points), scaled to fit the head: a display choice")


class App:
    def __init__(self, data_dir=ROOT / "play_data", token=None, cfg=None, genome=None, live=True):
        self.game = Game(data_dir, cfg, genome)
        self.token = token or play_token()
        self.sessions = S.Sessions()
        self.act_rl, self.fail_rl = S.RateLimiter(S.ACTIONS_PER_MIN), S.RateLimiter(S.AUTH_FAILS_PER_MIN)
        self.read_only = os.environ.get("NEURALPET_PLAY", "1") == "0"
        self.extra_hosts = tuple(h.strip().lower() for h in os.environ.get("NEURALPET_PLAY_HOSTS", "").split(",") if h.strip())
        self.port = self.game.cfg["port"]
        self.brain = gzip.compress(json.dumps(brain_points(), separators=(",", ":")).encode())
        if hasattr(self.game, "saved_at"):
            self.game.catch_up(max(0.0, time.time() - self.game.saved_at))
            self.game.save()
        self.prefs, self.prefs_t = [], 0.0
        if live:
            threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        last, last_save = time.monotonic(), time.monotonic()
        while True:
            time.sleep(0.1)
            now = time.monotonic()
            self.game.advance(min(1.0, now - last) * self.game.cfg["speed"])
            last = now
            if now - last_save > self.game.cfg["save_every_s"]:
                self.game.save()
                last_save = now

    def state(self):
        if time.monotonic() - self.prefs_t > 2.0:
            self.prefs, self.prefs_t = self.game.preferences(), time.monotonic()
        s = self.game.snapshot()
        s.update(preferences=self.prefs, mood=self.game.mood(self.prefs), read_only=self.read_only,
                 odorants=self.game.names)
        return s


def make_handler(app):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "neuralpet-play"
        sys_version = ""

        def log_message(self, *a):
            pass

        def secure(self):
            return self.headers.get("X-Forwarded-Proto", "").lower() == "https"

        def send(self, code, body=b"", ctype="text/plain; charset=utf-8", headers=(), gz=False):
            if gz and "gzip" in self.headers.get("Accept-Encoding", ""):
                headers = list(headers) + [("Content-Encoding", "gzip")]
            elif gz:
                body = gzip.decompress(body)
            self.send_response(code)
            for k, v in list(S.HEADERS.items()) + list(headers):
                self.send_header(k, v)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if self.secure():
                self.send_header("Strict-Transport-Security", "max-age=31536000")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def json(self, obj, code=200, headers=()):
            self.send(code, json.dumps(obj, separators=(",", ":")).encode(), "application/json", headers)

        def session(self):
            sid = S.parse_cookies(self.headers.get("Cookie")).get("np_sid")
            return sid, app.sessions.get(sid)

        def guard_host(self):
            if not S.host_ok(self.headers.get("Host"), app.port, app.extra_hosts):
                self.send(421, b"misdirected request")
                return False
            return True

        def do_GET(self):
            if not self.guard_host():
                return
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if u.path == "/favicon.ico":
                return self.send(204)
            if "t" in q:                                   # one-time token exchange -> cookie, clean URL
                if app.fail_rl.blocked("auth"):
                    return self.send(429, b"too many attempts, wait a minute")
                if not S.token_ok(q["t"][0], app.token):
                    app.fail_rl.allow("auth")
                    return self.send(403, b"forbidden")
                sid, _ = app.sessions.new()
                return self.send(303, b"", headers=[("Location", "/"), ("Set-Cookie", S.cookie("np_sid", sid, self.secure()))])
            sid, csrf = self.session()
            if csrf is None:
                return self.send(403, b"open the link with ?t=<token> once to sign in")
            if u.path == "/api/state":
                st = app.state()
                st["csrf"] = csrf
                return self.json(st)
            if u.path == "/api/brain":
                return self.send(200, app.brain, "application/json", gz=True)
            if u.path == "/api/memorials":
                return self.json(app.game.memorials())
            if u.path in STATIC:
                f, ct = STATIC[u.path]
                return self.send(200, (PLAY / f).read_bytes(), ct)
            self.send(404, b"not found")

        do_HEAD = do_GET

        def do_POST(self):
            # Any early refusal below leaves the body unread; never reuse such a connection, or the body
            # would be parsed as a second request (HTTP/1.1 desync, reviews/final.md #14).
            self.close_connection = True
            if not self.guard_host():
                return
            sid, csrf = self.session()
            if csrf is None:
                return self.send(403, b"not signed in")
            if not S.origin_ok(self.headers.get("Origin"), self.headers.get("Host")):
                return self.send(403, b"bad origin")
            if not S.token_ok(self.headers.get("X-CSRF-Token", ""), csrf):
                return self.send(403, b"bad csrf token")
            if urlparse(self.path).path != "/api/action":
                return self.send(404, b"not found")
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self.send(415, b"json only")
            try:
                n = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                n = -1
            if not 0 < n <= S.MAX_BODY:
                return self.send(413, b"body size")
            raw = self.rfile.read(n)
            if app.read_only:
                return self.send(403, b"read-only mode (NEURALPET_PLAY=0)")
            if not app.act_rl.allow(sid):
                return self.send(429, b"slow down: 30 actions per minute")
            a, err = S.validate_action(raw, app.game.names)
            if err:
                return self.json(dict(error=err), 400)
            app.game.act(a)
            app.prefs_t = 0.0
            self.close_connection = False                   # body fully read: keep-alive is safe again
            self.json(dict(ok=True))

        def do_PUT(self):
            self.send(405, b"method not allowed")

        do_DELETE = do_PATCH = do_OPTIONS = do_PUT

    return H


def main():
    app = App()
    srv = ThreadingHTTPServer(("127.0.0.1", app.port), make_handler(app))
    print(f"NeuralPet play: http://127.0.0.1:{app.port}/?t={app.token}" + ("  [READ-ONLY]" if app.read_only else ""), flush=True)
    try:
        srv.serve_forever()
    finally:
        app.game.save()


if __name__ == "__main__":
    main()
