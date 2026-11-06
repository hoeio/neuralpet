# Open questions / recommendations for the human

- ~~Repo visibility~~ — resolved 2026-11-06: the human confirmed the repo is public on purpose ("This research will be public"). Still never pushed: `data/`, `.env`, derived connectivity, neuron root IDs. FlyWire data are CC BY-NC 4.0: figures and aggregate numbers are shared with attribution (README), for non-commercial research.
- **Viewer behind the Cloudflare tunnel.** I do not create or change tunnels (CLAUDE.md). To expose the viewer, add a public hostname to your *named* tunnel (the one running from `/Library/Application Support/com.cloudflare.cloudflared/token`, managed in the dashboard) with service `http://127.0.0.1:8797`, and put Cloudflare Access in front of it first. See docs/TUNNEL.md.
