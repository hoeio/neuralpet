"""Security helpers for the play app (docs/PLAY.md, "Security model"). Stdlib only."""
import hmac
import json
import secrets
import threading
import time
from collections import deque

MAX_BODY = 1024              # bytes per POST
ACTIONS_PER_MIN = 30         # per session
AUTH_FAILS_PER_MIN = 10      # token failures, global (everything arrives from 127.0.0.1 via the tunnel)
SESSION_TTL = 30 * 24 * 3600
NAME_MAX = 24


class RateLimiter:
    def __init__(self, n, window=60.0):
        self.n, self.window, self.hits, self.lock = n, window, {}, threading.Lock()

    def allow(self, key, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            q = self.hits.setdefault(key, deque())
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.n:
                return False
            q.append(now)
            return True

    def blocked(self, key, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            q = self.hits.get(key, deque())
            return sum(now - t <= self.window for t in q) >= self.n


class Sessions:
    """Server-side sessions: random id (cookie) -> CSRF token + expiry. In memory: a restart logs out."""

    def __init__(self):
        self.s, self.lock = {}, threading.Lock()

    def new(self):
        sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self.lock:
            self.s[sid] = (csrf, time.time() + SESSION_TTL)
        return sid, csrf

    def get(self, sid):
        with self.lock:
            v = self.s.get(sid or "")
            if not v or v[1] < time.time():
                self.s.pop(sid or "", None)
                return None
            return v[0]


def token_ok(given, expected):
    return bool(given) and bool(expected) and hmac.compare_digest(given.encode(), expected.encode())


def host_ok(host, port, extra=()):
    """DNS-rebinding guard: only our own local names, quick-tunnel names, or hosts listed by the owner."""
    h = (host or "").lower()
    name = h.rsplit(":", 1)[0] if ":" in h else h
    return h in (f"127.0.0.1:{port}", f"localhost:{port}") or name.endswith(".trycloudflare.com") or name in extra


def origin_ok(origin, host):
    """State-changing requests must come from a page served by this same host."""
    return bool(origin) and origin.lower() in (f"http://{host}".lower(), f"https://{host}".lower())


def cookie(name, value, secure, max_age=SESSION_TTL):
    c = f"{name}={value}; Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}"
    return c + "; Secure" if secure else c


def parse_cookies(header):
    out = {}
    for part in (header or "").split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            out[k] = v
    return out


HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                               "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def validate_action(raw, odorant_names):
    """Parse and check one action request body against the whitelist. Returns (dict, None) or (None, error)."""
    if len(raw) > MAX_BODY:
        return None, "too large"
    try:
        a = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "bad json"
    if not isinstance(a, dict) or not isinstance(a.get("action"), str):
        return None, "bad shape"
    allowed = {"feed": set(), "praise": set(), "scold": set(), "rest": {"on"}, "offer_odor": {"odor"},
               "drop": {"item", "x", "y", "odor"}, "rename": {"name"}, "new_pet": {"confirm"}}
    act = a["action"]
    if act not in allowed or set(a) - {"action"} - allowed[act]:
        return None, "unknown action or field"

    def num(k):
        v = a.get(k)
        return isinstance(v, (int, float)) and not isinstance(v, bool) and 0.0 <= v <= 1.0

    if act == "rest" and not isinstance(a.get("on"), bool):
        return None, "rest.on must be boolean"
    if act in ("offer_odor",) and a.get("odor") not in odorant_names:
        return None, "unknown odorant"
    if act == "drop":
        if a.get("item") not in ("food", "toy") or not (num("x") and num("y")):
            return None, "bad drop"
        if a["item"] == "toy" and a.get("odor") not in odorant_names:
            return None, "unknown odorant"
        if a["item"] == "food" and "odor" in a:
            return None, "food has its own smell"
    if act == "rename":
        n = a.get("name")
        if not isinstance(n, str) or not (1 <= len(n.strip()) <= NAME_MAX) or any(ord(ch) < 32 for ch in n):
            return None, "bad name"
        a["name"] = n.strip()
    if act == "new_pet" and a.get("confirm") is not True:
        return None, "confirm required"
    return a, None
