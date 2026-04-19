#!/usr/bin/env bash
# OPPre (Tools) runner
#
# Uses the existing venv in ./myenv and starts OPPre.py.
# Override host/port with env vars:
#   OPVIEW_HOST=0.0.0.0 OPVIEW_PORT=8051 ./run_oppre.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# shellcheck disable=SC1091
source myenv/bin/activate

python OPPre.py
