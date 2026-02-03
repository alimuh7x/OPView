#!/usr/bin/env bash
# OPView - One-Click Launcher (Linux)
# Usage: chmod +x run.sh && ./run.sh
set -e

echo ""
echo "=========================================="
echo " OPView - One-Click Launcher (Linux)"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Step 1: Check system dependencies ────────────────────────────────────
echo "[1/5] Checking system dependencies..."
MISSING_PKGS=()

if ! ldconfig -p 2>/dev/null | grep -q "libGL.so"; then
    MISSING_PKGS+=("libgl1-mesa-dev")
fi
for lib in libXrender libXcursor libXrandr libXinerama libXi; do
    if ! ldconfig -p 2>/dev/null | grep -q "${lib}.so"; then
        MISSING_PKGS+=("${lib,,}-dev")
    fi
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo "  Installing missing system libraries: ${MISSING_PKGS[*]}"
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y -qq "${MISSING_PKGS[@]}"
    elif command -v dnf >/dev/null 2>&1; then
        # Map Debian names to Fedora names
        FEDORA_PKGS=()
        for pkg in "${MISSING_PKGS[@]}"; do
            case "$pkg" in
                libgl1-mesa-dev) FEDORA_PKGS+=("mesa-libGL-devel") ;;
                *) FEDORA_PKGS+=("${pkg%-dev}-devel") ;;
            esac
        done
        sudo dnf install -y "${FEDORA_PKGS[@]}"
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm mesa libxrender libxcursor libxrandr libxinerama libxi
    else
        echo "  WARNING: Could not auto-install system libraries."
        echo "  Please install manually: ${MISSING_PKGS[*]}"
    fi
else
    echo "  System dependencies OK"
fi

# ── Step 2: Find a supported Python (3.12 or 3.13) ──────────────────────
echo "[2/5] Looking for Python 3.12 or 3.13..."
PY_CMD=""

for candidate in python3.13 python3.12 /home/linuxbrew/.linuxbrew/bin/python3.13 /home/linuxbrew/.linuxbrew/bin/python3.12; do
    if command -v "$candidate" >/dev/null 2>&1; then
        ver=$("$candidate" --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
        if [[ "$ver" == "3.13" || "$ver" == "3.12" ]]; then
            PY_CMD="$candidate"
            break
        fi
    fi
done

# Try generic python3
if [ -z "$PY_CMD" ]; then
    if command -v python3 >/dev/null 2>&1; then
        ver=$(python3 --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
        if [[ "$ver" == "3.13" || "$ver" == "3.12" ]]; then
            PY_CMD="python3"
        fi
    fi
fi

if [ -z "$PY_CMD" ]; then
    echo ""
    echo "ERROR: Python 3.12 or 3.13 not found."
    echo ""
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt install python3.13 python3.13-venv"
    echo "  Fedora:        sudo dnf install python3.13"
    echo "  Arch:          sudo pacman -S python"
    echo ""
    exit 1
fi

echo "  Found $($PY_CMD --version 2>&1)"

# ── Step 3: Ensure venv module is available ──────────────────────────────
if ! $PY_CMD -m venv --help >/dev/null 2>&1; then
    echo "  Installing python venv module..."
    ver=$($PY_CMD --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get install -y -qq "python${ver}-venv"
    fi
fi

# ── Step 4: Create or reuse virtual environment ──────────────────────────
if [ -f "myenv/bin/python" ]; then
    echo "[3/5] Virtual environment already exists - reusing"
else
    echo "[3/5] Creating virtual environment..."
    $PY_CMD -m venv myenv
fi

# ── Step 5: Install / update dependencies ────────────────────────────────
echo "[4/5] Installing dependencies..."
# shellcheck disable=SC1091
source myenv/bin/activate

pip install --upgrade pip --quiet 2>/dev/null
pip install --upgrade -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo ""
    echo "Retrying with verbose output..."
    pip install --upgrade -r requirements.txt
fi

# Quick verification
python -c "import dash, vtk, pyvista, numpy; print('  All core modules OK')"

# ── Step 6: Launch server and open browser ───────────────────────────────
echo "[5/5] Starting OPView server..."
echo ""
echo "=========================================="
echo " OPView will open at http://127.0.0.1:8050"
echo " Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Open browser after a short delay (background)
(
    sleep 3
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "http://127.0.0.1:8050" 2>/dev/null
    elif command -v sensible-browser >/dev/null 2>&1; then
        sensible-browser "http://127.0.0.1:8050" 2>/dev/null
    elif command -v firefox >/dev/null 2>&1; then
        firefox "http://127.0.0.1:8050" 2>/dev/null
    elif command -v google-chrome >/dev/null 2>&1; then
        google-chrome "http://127.0.0.1:8050" 2>/dev/null
    fi
) &

# Run the application (blocks until Ctrl+C)
python OPView.py

echo ""
echo "OPView stopped."
