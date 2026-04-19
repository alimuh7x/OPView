#!/usr/bin/env bash
# OPView (Viewer) runner
#
# Uses the existing venv in ./myenv and starts OPView.py.
# Override host/port with env vars:
#   OPVIEW_HOST=0.0.0.0 OPVIEW_PORT=8050 ./run_opview.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# shellcheck disable=SC1091
source myenv/bin/activate

python OPView.py
