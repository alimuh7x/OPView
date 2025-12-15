#!/usr/bin/env bash
set -e

echo "========================================"
echo "OPView setup (Linux / macOS / WSL)"
echo "========================================"
echo ""

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
echo "Setup complete."
echo "To run the application:"
echo "  source myenv/bin/activate"
echo "  python OPView.py"
echo "Then open http://127.0.0.1:8050 in your browser."
echo ""

read -r -p "Start the application now? [y/N]: " reply
echo ""
if [[ $reply =~ ^[Yy]$ ]]; then
    python OPView.py
fi
