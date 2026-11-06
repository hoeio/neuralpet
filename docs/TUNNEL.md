# Exposing the viewer

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

## Quick tunnel in use (2026-11-06, on the human's explicit request)

The human asked to "use Cloudflare tunnel for it". This overrides the CLAUDE.md rule for this one
purpose. To keep the change minimal and reversible, I started a **quick tunnel**:

    nohup cloudflared tunnel --config /dev/null --no-autoupdate --url http://127.0.0.1:8797 > .tunnel.log 2>&1 &

- It gives a random `https://<words>.trycloudflare.com` URL (in `.tunnel.log`, gitignored). Open it
  with `/?t=<NEURALPET_TOKEN>`.
- It does **not** touch the named tunnel or the Cloudflare account. Stop it with
  `pkill -f "url http://127.0.0.1:8797"`.
- **The URL changes every restart and dies on reboot.**
- **Quick tunnels cannot sit behind Cloudflare Access**, so the URL token is the only gate. The page is
  read-only.
- For a stable, Access-protected address, use the named-tunnel route above.

## Why the viewer "did not work well" through the tunnel (measured 2026-11-06)

The viewer used Server-Sent Events. Through the tunnel the event stream was held in **128 KiB
blocks**: with small messages nothing arrived for 27 s, then exactly 131,072 bytes at once.
- The original 16.8 KB-per-update stream filled a block every ~0.8 s, so it looked live but jerky
  (and cost ~1.3 Mbit/s).
- `no-transform`, `X-Accel-Buffering: no` and chunked encoding did not help.

**Fix:** the page now polls `/state?t=…&since=<step>` (~5×/s, one request in flight). History points
are sent incrementally. Each update is ~0.4 KB; median latency through the tunnel is 59 ms (20 polls).
