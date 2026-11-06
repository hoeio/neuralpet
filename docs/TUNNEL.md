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
