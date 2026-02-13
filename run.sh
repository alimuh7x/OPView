#!/usr/bin/env bash
# OPView - One-Click Launcher (Linux)
# Usage: chmod +x run.sh && ./run.sh
set -e

# Configuration
APP_URL="http://127.0.0.1:8050"

echo ""
echo "=========================================="
echo " OPView - One-Click Launcher (Linux)"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Step 1: Check GUI dependencies for WSL2 (file dialogs) ───────────────
echo "[1/6] Checking GUI dependencies for file dialogs (WSL2)..."
IS_WSL=0
if grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null || grep -qiE "(microsoft|wsl)" /proc/sys/kernel/osrelease 2>/dev/null; then
    IS_WSL=1
fi

if [ "$IS_WSL" -eq 1 ]; then
    if command -v apt-get >/dev/null 2>&1 && command -v dpkg-query >/dev/null 2>&1; then
        MISSING_GUI_PKGS=()
        dpkg-query -W -f='${Status}' python3-tk 2>/dev/null | grep -q "install ok installed" || MISSING_GUI_PKGS+=("python3-tk")
        dpkg-query -W -f='${Status}' zenity 2>/dev/null | grep -q "install ok installed" || MISSING_GUI_PKGS+=("zenity")

        if [ ${#MISSING_GUI_PKGS[@]} -gt 0 ]; then
            echo "  Installing missing WSL GUI dependencies: ${MISSING_GUI_PKGS[*]}"
            sudo apt-get install -y -qq "${MISSING_GUI_PKGS[@]}" 2>/dev/null || true
        else
            echo "  WSL GUI dependencies already installed"
        fi
    else
        echo "  WSL detected, but apt/dpkg-query not available; skipping GUI dependency install"
    fi
else
    echo "  Non-WSL environment - skipping WSL GUI dependency check"
fi

# ── Step 2: Check VTK system dependencies ────────────────────────────────
echo "[2/6] Checking VTK system dependencies..."
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
    echo ""
    echo "  WARNING: Missing system libraries required for VTK:"
    for pkg in "${MISSING_PKGS[@]}"; do
        echo "    - $pkg"
    done
    echo ""
    
    if command -v apt-get >/dev/null 2>&1; then
        echo "  Install them with:"
        echo "    sudo apt-get update && sudo apt-get install -y ${MISSING_PKGS[*]}"
    elif command -v dnf >/dev/null 2>&1; then
        # Map Debian names to Fedora names
        FEDORA_PKGS=()
        for pkg in "${MISSING_PKGS[@]}"; do
            case "$pkg" in
                libgl1-mesa-dev) FEDORA_PKGS+=("mesa-libGL-devel") ;;
                *) FEDORA_PKGS+=("${pkg%-dev}-devel") ;;
            esac
        done
        echo "  Install them with:"
        echo "    sudo dnf install -y ${FEDORA_PKGS[*]}"
    elif command -v pacman >/dev/null 2>&1; then
        echo "  Install them with:"
        echo "    sudo pacman -Sy mesa libxrender libxcursor libxrandr libxinerama libxi"
    else
        echo "  WARNING: Could not determine package manager."
        echo "  Please install manually: ${MISSING_PKGS[*]}"
    fi
    
    echo ""
    read -r -p "  Install missing packages now? [y/N]: " reply
    if [[ $reply =~ ^[Yy]$ ]]; then
        echo "  Installing missing system libraries..."
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update -qq && sudo apt-get install -y -qq "${MISSING_PKGS[@]}"
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y "${FEDORA_PKGS[@]}"
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -Sy --noconfirm mesa libxrender libxcursor libxrandr libxinerama libxi
        fi
    else
        echo ""
        echo "  Skipping system package installation."
        echo "  Note: The application may not work without these libraries."
        echo ""
    fi
else
    echo "  System dependencies OK"
fi

# ── Step 3: Find a supported Python (3.12 or 3.13) ──────────────────────
echo "[3/6] Looking for Python 3.12 or 3.13..."
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

# ── Step 4: Ensure venv module is available ──────────────────────────────
if ! $PY_CMD -m venv --help >/dev/null 2>&1; then
    ver=$($PY_CMD --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
    echo ""
    echo "  Python venv module not found."
    if command -v apt-get >/dev/null 2>&1; then
        echo "  Install with: sudo apt-get install -y python${ver}-venv"
        echo ""
        read -r -p "  Install python venv module now? [y/N]: " reply
        if [[ $reply =~ ^[Yy]$ ]]; then
            echo "  Installing python venv module..."
            sudo apt-get install -y -qq "python${ver}-venv"
        else
            echo ""
            echo "  ERROR: venv module is required to continue."
            exit 1
        fi
    else
        echo "  ERROR: venv module is required but not available."
        exit 1
    fi
fi

# ── Step 4: Create or reuse virtual environment ──────────────────────────
if [ -f "myenv/bin/python" ]; then
    echo "[3/5] Virtual environment already exists - reusing"
else
    echo "[3/5] Creating virtual environment..."
    $PY_CMD -m venv myenv
fi

# ── Step 5: Activate virtual environment ─────────────────────────────────
echo "[4/5] Activating virtual environment..."
# shellcheck disable=SC1091
source myenv/bin/activate

# Verify we're using the venv Python
ACTIVE_PYTHON=$(which python)
echo "  Using: $ACTIVE_PYTHON"

# ── Step 6: Check and install dependencies ───────────────────────────────
echo "[5/5] Checking dependencies..."

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
    if ! python -m pip install -r requirements.txt; then
        echo ""
        echo "ERROR: Failed to install dependencies."
        exit 1
    fi
    python -c "import dash, vtk, pyvista, numpy; print('  All core modules OK')"
fi

# ── Step 7: Launch server and open browser ───────────────────────────────
echo ""
echo "Starting OPView server..."
echo ""
echo "=========================================="
echo " OPView will open at $APP_URL"
echo " Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Open browser after a short delay (background)
(
    sleep 3
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$APP_URL" 2>/dev/null
    elif command -v sensible-browser >/dev/null 2>&1; then
        sensible-browser "$APP_URL" 2>/dev/null
    elif command -v firefox >/dev/null 2>&1; then
        firefox "$APP_URL" 2>/dev/null
    elif command -v google-chrome >/dev/null 2>&1; then
        google-chrome "$APP_URL" 2>/dev/null
    fi
) &

# Run the application (blocks until Ctrl+C)
python OPView.py

echo ""
echo "OPView stopped."
