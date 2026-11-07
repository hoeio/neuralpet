"""Play app tests: auth, CSRF, Origin/Host, rate limits, malformed input, read-only switch,
save/load round trip, crash while saving. Uses a synthetic genome and a temp data dir.

    uv run python tests/test_play.py
"""
import http.client
import json
import os
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np

from neuralpet_play import game as G
from neuralpet_play import security as S
from neuralpet_play.server import App, make_handler

TOKEN = "test-token-0123456789abcdef"


def genome():
    r = np.random.default_rng(0)
    W_pk = ((r.random((40, 500)) < 0.08) * r.integers(5, 30, (40, 500))).astype(np.float32)
    W_km = ((r.random((500, 8)) < 0.3) * r.integers(5, 12, (500, 8))).astype(np.float32)
    odors = ((r.random((6, 40)) < 0.3) * r.exponential(0.6, (6, 40))).astype(np.float32)
    return W_pk, W_km, odors, ["ethyl acetate", "linalool", "geraniol", "acetone", "butanal", "eugenol"], "synthetic test genome"


class Server:
    def __init__(self, read_only=False):
        self.dir = tempfile.mkdtemp()
        os.environ["NEURALPET_PLAY"] = "0" if read_only else "1"
        self.app = App(self.dir, token=TOKEN, cfg=dict(port=0), genome=genome(), live=False)
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.app))
        self.port = self.app.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.host = f"127.0.0.1:{self.port}"

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Host": self.host, **(headers or {})}
        c.request(method, path, body=body, headers=h)
        r = c.getresponse()
        return r.status, dict(r.getheaders()), r.read()

    def login(self):
        st, h, _ = self.req("GET", f"/?t={TOKEN}")
        assert st == 303 and h["Location"] == "/", (st, h)
        ck = h["Set-Cookie"]
        assert "HttpOnly" in ck and "SameSite=Strict" in ck and "Secure" not in ck
        sid = ck.split(";")[0]
        st, _, b = self.req("GET", "/api/state", headers={"Cookie": sid})
        assert st == 200
        return sid, json.loads(b)["csrf"]

    def post(self, sid, csrf, obj, origin=None, raw=None, ctype="application/json"):
        body = raw if raw is not None else json.dumps(obj).encode()
        return self.req("POST", "/api/action", body, {"Cookie": sid, "X-CSRF-Token": csrf, "Content-Type": ctype,
                                                      "Origin": origin or f"http://{self.host}", "Content-Length": str(len(body))})


def test_auth_and_cookie():
    s = Server()
    assert s.req("GET", "/api/state")[0] == 403                       # no session
    assert s.req("GET", "/?t=wrong")[0] == 403
    sid, csrf = s.login()
    st, h, _ = s.req("GET", "/", headers={"Cookie": sid})
    assert st == 200 and "script-src 'self'" in h["Content-Security-Policy"] and h["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in h
    st, h, _ = s.req("GET", f"/?t={TOKEN}", headers={"X-Forwarded-Proto": "https"})
    assert "Secure" in h["Set-Cookie"]                                # Secure when behind HTTPS


def test_token_failures_rate_limited():
    s = Server()
    codes = [s.req("GET", f"/?t=bad{i}")[0] for i in range(S.AUTH_FAILS_PER_MIN + 2)]
    assert codes[:S.AUTH_FAILS_PER_MIN] == [403] * S.AUTH_FAILS_PER_MIN and codes[-1] == 429
    assert s.req("GET", f"/?t={TOKEN}")[0] == 429                     # locked out for the window, even with the right token


def test_host_check():
    s = Server()
    assert s.req("GET", f"/?t={TOKEN}", headers={"Host": "evil.example"})[0] == 421
    assert s.req("GET", f"/?t={TOKEN}", headers={"Host": "abc-def.trycloudflare.com"})[0] == 303


def test_csrf_origin_and_method():
    s = Server()
    sid, csrf = s.login()
    assert s.post(sid, "nope", {"action": "praise"})[0] == 403
    assert s.post(sid, csrf, {"action": "praise"}, origin="https://evil.example")[0] == 403
    assert s.req("POST", "/api/action", b"{}", {"Cookie": sid, "X-CSRF-Token": csrf, "Content-Type": "application/json",
                                                 "Content-Length": "2"})[0] == 403          # missing Origin
    assert s.post(sid, csrf, {"action": "praise"})[0] == 200
    assert s.req("PUT", "/api/action")[0] == 405


def test_malformed_input():
    s = Server()
    sid, csrf = s.login()
    bad = [{"action": "shell", "cmd": "ls"}, {"action": "praise", "x": 1}, {"action": "offer_odor", "odor": "../../etc/passwd"},
           {"action": "drop", "item": "food", "x": 2, "y": 0.5}, {"action": "drop", "item": "rock", "x": 0.1, "y": 0.1},
           {"action": "rename", "name": "x" * 25}, {"action": "rename", "name": "a\nb"}, {"action": "rest", "on": "yes"},
           {"action": "new_pet"}, [1, 2], "praise"]
    for b in bad:
        assert s.post(sid, csrf, b)[0] == 400, b
    assert s.post(sid, csrf, None, raw=b"{not json")[0] == 400
    assert s.post(sid, csrf, None, raw=b"\xff\xfe")[0] == 400
    assert s.post(sid, csrf, None, raw=b"{" + b" " * 2000 + b"}")[0] == 413
    assert s.post(sid, csrf, {"action": "praise"}, ctype="text/plain")[0] == 415


def test_name_is_escaped_text():
    s = Server()
    sid, csrf = s.login()
    assert s.post(sid, csrf, {"action": "rename", "name": "<img src=x onerror=1>"})[0] == 200
    st = json.loads(s.req("GET", "/api/state", headers={"Cookie": sid})[2])
    assert st["name"] == "<img src=x onerror=1>"                     # stored as data, rendered with textContent only
    js = (G.ROOT / "play" / "app.js").read_text()
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js


def test_action_rate_limit():
    s = Server()
    sid, csrf = s.login()
    codes = [s.post(sid, csrf, {"action": "praise"})[0] for _ in range(S.ACTIONS_PER_MIN + 2)]
    assert codes.count(200) == S.ACTIONS_PER_MIN and codes[-1] == 429


def test_read_only_switch():
    s = Server(read_only=True)
    sid, csrf = s.login()
    assert s.post(sid, csrf, {"action": "praise"})[0] == 403
    os.environ["NEURALPET_PLAY"] = "1"


def test_every_action_works():
    s = Server()
    sid, csrf = s.login()
    for a in [{"action": "feed"}, {"action": "praise"}, {"action": "scold"}, {"action": "offer_odor", "odor": "linalool"},
              {"action": "drop", "item": "food", "x": 0.2, "y": 0.8}, {"action": "drop", "item": "toy", "x": 0.5, "y": 0.5, "odor": "acetone"},
              {"action": "rest", "on": True}, {"action": "rest", "on": False}, {"action": "rename", "name": "Mochi"}]:
        assert s.post(sid, csrf, a)[0] == 200, a
    st = json.loads(s.req("GET", "/api/state", headers={"Cookie": sid})[2])
    kinds = {x["kind"] for x in st["sources"]}
    assert st["name"] == "Mochi" and {"toy", "food"} <= kinds and {p["odor"] for p in st["preferences"]} >= {"linalool", "acetone"}
    log = [json.loads(l) for l in (Path(s.dir) / "interactions.jsonl").read_text().splitlines()]
    assert len(log) == 9 and log[0]["action"]["action"] == "feed"
    assert s.post(sid, csrf, {"action": "new_pet", "confirm": True})[0] == 200
    assert len(s.app.game.memorials()) == 1


def test_save_load_round_trip_exact():
    d = tempfile.mkdtemp()
    g = G.Game(d, cfg=dict(port=0), genome=genome())
    g.advance(20)
    g.act({"action": "offer_odor", "odor": "geraniol"})
    g.act({"action": "praise"})
    g.save()
    h = G.Game(d, cfg=dict(port=0), genome=genome())
    for k in ("x", "phi", "th_prev", "effort"):
        assert np.array_equal(getattr(g.pet.body, k), getattr(h.pet.body, k))
    assert np.array_equal(g.pet.W, h.pet.W) and g.meta == h.meta and g.pet.energy == h.pet.energy
    g.advance(15)
    h.advance(15)                                                    # same future: RNG state restored too
    assert np.array_equal(g.pet.body.x, h.pet.body.x) and np.array_equal(g.pet.W, h.pet.W)


def test_crash_while_saving_keeps_last_good_save():
    d = tempfile.mkdtemp()
    g = G.Game(d, cfg=dict(port=0), genome=genome())
    g.advance(5)
    g.save()
    good = (Path(d) / "pet.npz").read_bytes()
    real_replace = os.replace

    def boom(a, b):
        if str(b).endswith("pet.npz"):
            raise OSError("simulated crash before rename")
        return real_replace(a, b)

    G.os.replace = boom
    try:
        g.advance(5)
        try:
            g.save()
        except OSError:
            pass
    finally:
        G.os.replace = real_replace
    assert (Path(d) / "pet.npz").read_bytes() == good                # the half-written file never replaced it
    (Path(d) / "pet.npz").write_bytes(good[: len(good) // 2])        # and a torn main file falls back to a backup
    h = G.Game(d, cfg=dict(port=0), genome=genome())
    assert h.pet.t > 0


def test_refused_post_body_is_not_a_second_request():
    """A refused POST must not leave its body to be parsed as another request (HTTP/1.1 desync)."""
    import socket
    s = Server()
    smuggled = f"GET /?t=wrongtoken HTTP/1.1\r\nHost: {s.host}\r\n\r\n".encode()
    head = (f"POST /api/action HTTP/1.1\r\nHost: {s.host}\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(smuggled)}\r\n\r\n").encode()
    with socket.create_connection(("127.0.0.1", s.port), timeout=5) as c:
        c.sendall(head + smuggled)
        data = b""
        while True:
            try:
                chunk = c.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
    assert data.count(b"HTTP/1.1 ") == 1, data                      # one response, then the connection closes
    assert not s.app.fail_rl.hits.get("auth")                        # the smuggled bad token never ran


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
            print("ok", k)
