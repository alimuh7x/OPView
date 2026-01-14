#!/usr/bin/env bash
set -e

echo "=========================================="
echo "OPView Setup - OpenPhase Visualization"
echo "=========================================="
echo ""

# Check for required system libraries (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
    echo "Checking system dependencies..."
    MISSING_LIBS=()

    # Check for OpenGL
    if ! ldconfig -p | grep -q "libGL.so"; then
        MISSING_LIBS+=("libgl1-mesa-dev")
    fi

    # Check for X11 libraries
    for lib in libXrender libXcursor libXrandr; do
        if ! ldconfig -p | grep -q "${lib}.so"; then
            MISSING_LIBS+=("${lib,,}-dev")
        fi
    done

    if [ ${#MISSING_LIBS[@]} -gt 0 ]; then
        echo ""
        echo "WARNING: Missing system libraries required for VTK:"
        printf '  - %s\n' "${MISSING_LIBS[@]}"
        echo ""
        echo "Install them with:"
        echo "  sudo apt install ${MISSING_LIBS[*]}"
        echo ""
        read -r -p "Continue anyway? [y/N]: " reply
        if [[ ! $reply =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "System dependencies OK."
    fi
    echo ""
fi

# Select a supported Python version (prefer 3.13, fall back to 3.12)
PYTHON_CMD=""
for candidate in python3.13 /home/linuxbrew/.linuxbrew/bin/python3.13 python3.12; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_CMD="$candidate"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    cat <<'EOF'
ERROR: Python 3.12 or 3.13 not found.

Install one of these versions and retry (VTK is not compatible with Python 3.14).

Ubuntu/Debian:
  sudo apt update
  sudo apt install python3.13 python3.13-venv

macOS (Homebrew):
  brew install python@3.13
EOF
    exit 1
fi

echo "Using $PYTHON_CMD ($($PYTHON_CMD --version))"
echo ""

# Reuse or recreate the virtual environment
if [ -d "myenv" ]; then
    read -r -p "Virtual env 'myenv' already exists. Recreate it? [y/N]: " reply
    echo ""
    if [[ $reply =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf myenv
    else
        echo "Updating existing environment..."
        # shellcheck disable=SC1091
        source myenv/bin/activate
        pip install --upgrade pip
        pip install --upgrade -r requirements.txt
        echo ""
        echo "Environment updated."
        echo "Run: source myenv/bin/activate && python OPView.py"
        exit 0
    fi
fi

echo "Creating virtual environment..."
$PYTHON_CMD -m venv myenv

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source myenv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Verifying installation..."
python -c "
import sys
modules_ok = True
required_modules = ['dash', 'plotly', 'numpy', 'vtk', 'pyvista', 'markdown']
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        print(f'ERROR: Failed to import {module}')
        modules_ok = False
        sys.exit(1)
print('All core modules imported successfully.')
"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "OPView uses a modular architecture with:"
echo "  • app/          - Application orchestration"
echo "  • callbacks/    - Callback managers"
echo "  • ui/           - UI components"
echo "  • data/         - Data sources"
echo "  • viewer/       - VTK visualization"
echo "  • utils/        - Utility functions"
echo ""
echo "To run the application:"
echo "  source myenv/bin/activate"
echo "  python OPView.py"
echo ""
echo "Then open http://127.0.0.1:8050 in your browser."
echo ""

read -r -p "Start the application now? [y/N]: " reply
echo ""
if [[ $reply =~ ^[Yy]$ ]]; then
    python OPView.py
fi
