# Decisions

- 2026-11-06: Python 3.12 via uv; NumPy/Numba stack (Brian2 only if needed). The repo dir was an existing git repo with one commit; used it in place.
- 2026-11-06: `origin` (github.com/hoeio/neuralpet) exists and the unauthenticated GitHub API returns 200, i.e. it is **public**. CLAUDE.md says push to origin if it exists, so I push code/docs only. Never pushed: `data/`, `.env`, derived connectivity, raw result arrays. Flagged in OPEN_QUESTIONS.
- 2026-11-06: `graft/` (a local code-index tool cache) is gitignored.
