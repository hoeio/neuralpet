# Exposing the viewer (not done — instructions only)

No Cloudflare tunnel was created or changed by this project. The viewer binds `127.0.0.1:8797`
(override with `NEURALPET_PORT`) and needs the token in `.env` (`NEURALPET_TOKEN`).

If the human decides to expose it through an existing named tunnel, add an ingress rule like this
to that tunnel's `config.yml` (hostname is a placeholder):

```yaml
ingress:
  - hostname: neuralpet.example.com
    service: http://127.0.0.1:8797
  - service: http_status:404
```

**Before exposing:** turn on **Cloudflare Access** for that hostname (an Access application with an
allow policy for your own identity only). The URL token is a second layer, not a substitute: it is
visible in browser history and in any shared link. Rotate it by deleting the `NEURALPET_TOKEN` line
from `.env` and restarting the server.

## Why it was not reachable (2026-11-06)

1. The viewer was not running: I stopped it after a test in session 1. It is now running detached.
   Check with `lsof -nP -iTCP:8797 -sTCP:LISTEN`; restart with
   `nohup uv run python -u viewer/server.py > .viewer.log 2>&1 &`.
2. No running cloudflared points at 8797. This Mac runs one named tunnel (managed from the Cloudflare
   dashboard via a token file) and several quick tunnels for other ports (8765, 8090, 8642, 8060,
   47821).
   - **To expose the viewer:** in the dashboard, add a Public Hostname to that named tunnel with
     service `http://127.0.0.1:8797`, protected by Cloudflare Access.
   - cloudflared runs on this same Mac, so the viewer's 127.0.0.1-only binding is fine. Do not
     change it to 0.0.0.0.
3. The page streams live state with Server-Sent Events (`/stream`). If the page loads but the arena
   stays empty behind the tunnel, look for something in front buffering the stream.
