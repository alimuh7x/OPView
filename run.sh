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
    echo "  Python 3.12 or 3.13 not found."
    echo ""

    if command -v apt-get >/dev/null 2>&1; then
        read -r -p "  Install Python 3.13 now? (requires sudo) [y/N]: " reply
        if [[ $reply =~ ^[Yy]$ ]]; then
            sudo apt-get update -qq
            sudo apt-get install -y python3.13 python3.13-venv
        else
            echo ""
            echo "ERROR: Python 3.12 or 3.13 is required. Exiting."
            exit 1
        fi
    elif command -v dnf >/dev/null 2>&1; then
        read -r -p "  Install Python 3.13 now? (requires sudo) [y/N]: " reply
        if [[ $reply =~ ^[Yy]$ ]]; then
            sudo dnf install -y python3.13
        else
            echo ""
            echo "ERROR: Python 3.12 or 3.13 is required. Exiting."
            exit 1
        fi
    elif command -v pacman >/dev/null 2>&1; then
        read -r -p "  Install Python now? (requires sudo) [y/N]: " reply
        if [[ $reply =~ ^[Yy]$ ]]; then
            sudo pacman -Sy --noconfirm python
        else
            echo ""
            echo "ERROR: Python 3.12 or 3.13 is required. Exiting."
            exit 1
        fi
    else
        echo "ERROR: Could not find a supported package manager."
        echo "Please install Python 3.12 or 3.13 manually and re-run."
        echo ""
        exit 1
    fi

    # Re-detect after installation
    for candidate in python3.13 python3.12; do
        if command -v "$candidate" >/dev/null 2>&1; then
            ver=$("$candidate" --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
            if [[ "$ver" == "3.13" || "$ver" == "3.12" ]]; then
                PY_CMD="$candidate"
                break
            fi
        fi
    done

    if [ -z "$PY_CMD" ]; then
        echo ""
        echo "ERROR: Installation succeeded but Python 3.12/3.13 still not found. Exiting."
        exit 1
    fi
fi

echo "  Found $($PY_CMD --version 2>&1)"

# ── Helper: install python venv package and retry ────────────────────────
install_venv_pkg() {
    local ver
    ver=$($PY_CMD --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
    echo ""
    echo "  Python venv package (python${ver}-venv) is not installed."
    if command -v apt-get >/dev/null 2>&1; then
        read -r -p "  Install python${ver}-venv now? (requires sudo) [y/N]: " reply
        if [[ $reply =~ ^[Yy]$ ]]; then
            sudo apt-get install -y "python${ver}-venv"
        else
            echo ""
            echo "  ERROR: python${ver}-venv is required to continue."
            exit 1
        fi
    else
        echo "  ERROR: python${ver}-venv is required but could not be installed automatically."
        echo "  Please install it manually and re-run."
        exit 1
    fi
}

# ── Step 4: Create or reuse virtual environment ──────────────────────────
if [ -f "myenv/bin/python" ] && [ -f "myenv/bin/activate" ]; then
    existing_ver=$(myenv/bin/python --version 2>&1 | sed -n 's/Python \([0-9]*\.[0-9]*\).*/\1/p')
    if [[ "$existing_ver" == "3.12" || "$existing_ver" == "3.13" ]]; then
        echo "[4/6] Virtual environment already exists - reusing"
    else
        echo "[4/6] Existing venv uses Python ${existing_ver:-unknown} (not 3.12/3.13) — removing it..."
        rm -rf myenv
        echo "  Creating new virtual environment with $($PY_CMD --version 2>&1)..."
            if ! $PY_CMD -m venv myenv >/dev/null 2>&1; then
            install_venv_pkg
            $PY_CMD -m venv myenv
        fi
    fi
else
    if [ -d "myenv" ]; then
        echo "[4/6] Existing venv is incomplete — removing it..."
        rm -rf myenv
    else
        echo "[4/6] Creating virtual environment..."
    fi
    if ! $PY_CMD -m venv myenv >/dev/null 2>&1; then
        install_venv_pkg
        $PY_CMD -m venv myenv
    fi
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
