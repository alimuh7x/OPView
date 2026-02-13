#!/usr/bin/env bash
# OPView - One-Click Launcher (macOS)
# Usage: chmod +x run-macos.sh && ./run-macos.sh
set -e

# Configuration
APP_URL="http://127.0.0.1:8050"

echo ""
echo "=========================================="
echo " OPView - One-Click Launcher (macOS)"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Step 1: Ensure Xcode Command Line Tools ─────────────────────────────
echo "[1/6] Checking prerequisites..."
if ! xcode-select -p >/dev/null 2>&1; then
    echo "  Installing Xcode Command Line Tools..."
    xcode-select --install
    echo "  Please complete the installation dialog, then re-run this script."
    exit 1
fi
echo "  Xcode CLI tools OK"

# ── Step 2: Find a supported Python (3.12 or 3.13) ──────────────────────
echo "[2/6] Looking for Python 3.12 or 3.13..."
PY_CMD=""

# Check Homebrew paths (Apple Silicon and Intel)
BREW_PREFIXES=("/opt/homebrew" "/usr/local")

for prefix in "${BREW_PREFIXES[@]}"; do
    for ver in 3.13 3.12; do
        candidate="${prefix}/bin/python${ver}"
        if [ -x "$candidate" ]; then
            PY_CMD="$candidate"
            break 2
        fi
    done
done

# Try PATH-based lookup
if [ -z "$PY_CMD" ]; then
    for candidate in python3.13 python3.12; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PY_CMD="$candidate"
            break
        fi
    done
fi

# Try generic python3
if [ -z "$PY_CMD" ]; then
    if command -v python3 >/dev/null 2>&1; then
        ver=$(python3 --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
        if [[ "$ver" == "3.13" || "$ver" == "3.12" ]]; then
            PY_CMD="python3"
        fi
    fi
fi

# Auto-install via Homebrew if possible
if [ -z "$PY_CMD" ]; then
    if command -v brew >/dev/null 2>&1; then
        echo ""
        echo "  Python 3.12/3.13 not found."
        echo "  Install with: brew install python@3.13"
        echo ""
        read -r -p "  Install Python 3.13 via Homebrew now? [y/N]: " reply
        if [[ $reply =~ ^[Yy]$ ]]; then
            echo "  Installing Python 3.13 via Homebrew..."
            brew install python@3.13
            for prefix in "${BREW_PREFIXES[@]}"; do
                if [ -x "${prefix}/bin/python3.13" ]; then
                    PY_CMD="${prefix}/bin/python3.13"
                    break
                fi
            done
        else
            echo ""
            echo "  Installation declined. Cannot continue without Python 3.12 or 3.13."
            echo ""
        fi
    fi
fi

if [ -z "$PY_CMD" ]; then
    echo ""
    echo "ERROR: Python 3.12 or 3.13 not found."
    echo ""
    echo "Install with Homebrew:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "  brew install python@3.13"
    echo ""
    echo "Or download from https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo "  Found $($PY_CMD --version 2>&1)"

# ── Step 3: Create or reuse virtual environment ─────────────────────────
if [ -f "myenv/bin/python" ]; then
    echo "[3/6] Virtual environment already exists - reusing"
else
    echo "[3/6] Creating virtual environment..."
    $PY_CMD -m venv myenv
fi

# ── Step 4: Activate virtual environment ─────────────────────────────────
echo "[4/6] Activating virtual environment..."
# shellcheck disable=SC1091
source myenv/bin/activate

# ── Step 5: Check and install dependencies ───────────────────────────────
echo "[5/6] Checking dependencies..."

# Fast startup policy: verify essential runtime deps only.
# To force a full dependency repair, run with OPVIEW_REPAIR_DEPS=1.
NEED_REPAIR=0
if [ "${OPVIEW_REPAIR_DEPS:-0}" = "1" ]; then
    NEED_REPAIR=1
    echo "  Repair mode enabled: installing all dependencies"
elif python -c "import dash, numpy, plotly, pandas, scipy, markdown, plyer" 2>/dev/null; then
    echo "  Essential dependencies present (skipping heavyweight import check)"
else
    NEED_REPAIR=1
    echo "  Missing essential dependencies"
fi

if [ "$NEED_REPAIR" -eq 1 ]; then
    echo "  Installing dependencies from requirements.txt..."
    python -m pip install --upgrade pip --quiet 2>/dev/null
    if ! python -m pip install --upgrade -r requirements.txt; then
        echo ""
        echo "ERROR: Failed to install dependencies."
        exit 1
    fi
    python -c "import dash, vtk, pyvista, numpy; print('  All core modules OK')"
fi

# ── Step 6: Launch server and open browser ───────────────────────────────
echo ""
echo "[6/6] Starting OPView server..."
echo ""
echo "=========================================="
echo " OPView will open at $APP_URL"
echo " Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Open browser after a short delay (background)
(
    sleep 3
    open "$APP_URL" 2>/dev/null
) &

# Run the application (blocks until Ctrl+C)
python OPView.py

echo ""
echo "OPView stopped."
