#!/bin/sh
# Start the NeuralPet play app on 127.0.0.1:8798 (docs/PLAY.md). Prints the sign-in link once.
# NEURALPET_PLAY=0 scripts/run_play.sh   -> read-only emergency mode.
cd "$(dirname "$0")/.." || exit 1
exec uv run python -u -m neuralpet_play.server
