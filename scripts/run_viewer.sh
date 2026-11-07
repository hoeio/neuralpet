#!/bin/sh
# Start the read-only research viewer on 127.0.0.1:8797 (docs/TUNNEL.md).
cd "$(dirname "$0")/.." || exit 1
exec uv run python -u viewer/server.py
