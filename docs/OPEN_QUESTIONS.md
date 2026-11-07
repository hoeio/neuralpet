# Open questions / recommendations for the human

- ~~Repo visibility~~ — resolved 2026-11-06: the human confirmed the repo is public on purpose ("This research will be public"). Still never pushed: `data/`, `.env`, derived connectivity, neuron root IDs. FlyWire data are CC BY-NC 4.0: figures and aggregate numbers are shared with attribution (README), for non-commercial research.
- **Viewer behind the Cloudflare tunnel.** I do not create or change tunnels (CLAUDE.md). To expose the viewer, add a public hostname to your *named* tunnel (the one running from `/Library/Application Support/com.cloudflare.cloudflared/token`, managed in the dashboard) with service `http://127.0.0.1:8797`, and put Cloudflare Access in front of it first. See docs/TUNNEL.md.
- **Viewer still not reachable remotely (2026-11-06, human report).** Locally it is up: 127.0.0.1:8797 returns 200 and streams. Most likely no tunnel route points to it yet. I cannot check or change the Cloudflare side. Please add the hostname in the named tunnel (docs/TUNNEL.md). If it still fails, run `curl -sI https://<hostname>/?t=<token>` and check the status code: 403 = wrong token; 502 = tunnel cannot reach 127.0.0.1:8797; Access login page = Access is working.

## 2026-11-06: 9.5 GB synapse table on disk
`data/flywire/flywire_synapses_783.feather` (~9.5 GB) is being downloaded only to draw neuron shapes in the
viewer. Recommendation: after `scripts/extract_shapes.py` has produced `data/mb/shapes.npz`, the human may
delete the big file to free space (I will not delete data). It is re-downloadable with
`scripts/fetch_flywire.py --synapses`.

## 2026-11-07 (final session)
- **Move to a named tunnel with Cloudflare Access, then rotate the tokens.** The viewer (and the play app,
  if you expose it) are reachable through a quick tunnel protected only by a URL token. Recommended: add
  hostnames to your named tunnel (docs/TUNNEL.md), put an Access policy for your own identity in front, then
  rotate `NEURALPET_TOKEN` and `NEURALPET_PLAY_TOKEN` by deleting their lines in `.env` and restarting. I did
  not do any of this (no Cloudflare changes, no token rotation while the tunnel is your live access).
- **The 9.5 GB synapse file** `data/flywire/flywire_synapses_783.feather` is only used to make
  `data/mb/shapes.npz` (already made). You can delete it to free space; it can be re-downloaded with
  `scripts/fetch_flywire.py --synapses`. I did not delete it.
- **Licence of the code:** no earlier decision was found, so the code is MIT (LICENSE). Data keep their own
  licences (FlyWire CC BY-NC 4.0, hemibrain CC BY 4.0, DoOR CC BY-SA 4.0) and are not in the repo.

## 2026-11-08
- **Brain-driven steering is weak under the registered constants.** With `K_CONTRAST` = 25 a forced
  valence of ±0.3 barely changes how close the creature gets to a source 1 BL away (exploratory check,
  docs/PLAY.md); 4× the gain makes a liked smell reduce the drift away from it; avoidance stayed indistinguishable from steering off. Recommendation: a new pre-registered
  experiment (013) that fixes the steering gain on the modulation-off synthetic pilot with an explicit
  chemotaxis criterion, then repeats the 012 comparisons. Not done here (outside WP1–WP7).
  The same new plan should also match the rule-6 generic substitute on its *realised* reward dopamine
  (in 012 it was matched only in expectation: reports/FINAL.md, reviews/final.md #3) and include a
  learning-off condition.
