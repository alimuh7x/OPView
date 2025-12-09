#!/bin/bash

# VTK 2D Slice Viewer - Automated Setup Script
# For Linux, macOS, and WSL systems

echo "========================================"
echo "VTK 2D Slice Viewer - Setup"
echo "========================================"
echo ""

# Check if Python 3.13 is available
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD=python3.13
    echo "✓ Found Python 3.13"
elif command -v /home/linuxbrew/.linuxbrew/bin/python3.13 &> /dev/null; then
    PYTHON_CMD=/home/linuxbrew/.linuxbrew/bin/python3.13
    echo "✓ Found Python 3.13 (Homebrew)"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
    echo "✓ Found Python 3.12"
else
    echo "✗ ERROR: Python 3.12 or 3.13 not found!"
    echo ""
    echo "  Please install Python 3.12 or 3.13:"
    echo ""
    echo "  Ubuntu/Debian:"
    echo "    sudo apt update"
    echo "    sudo apt install python3.13 python3.13-venv"
    echo ""
    echo "  macOS (Homebrew):"
    echo "    brew install python@3.13"
    echo ""
    echo "  Note: Python 3.14 is NOT compatible with VTK"
    echo ""
    exit 1
fi

echo "Using: $PYTHON_CMD ($($PYTHON_CMD --version))"
echo ""

# Check if virtual environment already exists
if [ -d "myenv" ]; then
    echo "⚠ Virtual environment 'myenv' already exists!"
    read -p "Do you want to remove it and create a fresh one? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old virtual environment..."
        rm -rf myenv
        echo "✓ Old environment removed"
    else
        echo "Keeping existing environment and updating packages..."
        source myenv/bin/activate
        pip install --upgrade pip
        pip install --upgrade -r requirements.txt
        echo ""
        echo "✓ Packages updated!"
        echo ""
        echo "To run the application:"
        echo "  source myenv/bin/activate"
        echo "  python app.py"
        echo ""
        exit 0
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv myenv
if [ $? -ne 0 ]; then
    echo "✗ ERROR: Failed to create virtual environment"
    echo ""
    echo "  You may need to install the venv module:"
    echo "  sudo apt install python3.13-venv"
    echo ""
    exit 1
fi
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip to latest version..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded to version $(pip --version | awk '{print $2}')"
echo ""

# Install requirements
echo "Installing dependencies..."
echo "  This may take 3-5 minutes depending on your internet speed"
echo "  Total download size: ~200 MB"
echo ""
echo "  Installing packages:"
echo "    - dash (web framework)"
echo "    - plotly (visualization)"
echo "    - numpy (numerical computing)"
echo "    - scipy (scientific computing)"
echo "    - pyvista (3D visualization)"
echo "    - vtk (112 MB - largest package)"
echo "    - and 42 other dependencies..."
echo ""

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ ERROR: Failed to install dependencies"
    echo ""
    echo "  Please check:"
    echo "    1. Internet connection is stable"
    echo "    2. requirements.txt file exists"
    echo "    3. Sufficient disk space (~500 MB)"
    echo ""
    exit 1
fi

echo ""
echo "✓ All dependencies installed successfully!"
echo ""

# Verify installation
echo "Verifying installation..."
python -c "import dash; print('  ✓ Dash version:', dash.__version__)"
python -c "import plotly; print('  ✓ Plotly version:', plotly.__version__)"
python -c "import numpy; print('  ✓ NumPy version:', numpy.__version__)"
python -c "import scipy; print('  ✓ SciPy version:', scipy.__version__)"
python -c "import pyvista; print('  ✓ PyVista version:', pyvista.__version__)"
python -c "import vtk; print('  ✓ VTK version:', vtk.vtkVersion.GetVTKVersion())"

echo ""
echo "========================================"
echo "✓ Setup Complete!"
echo "========================================"
echo ""
echo "To run the application:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source myenv/bin/activate"
echo ""
echo "  2. Run the app:"
echo "     python app.py"
echo ""
echo "  3. Open your browser to:"
echo "     http://127.0.0.1:8050"
echo ""
echo "To stop the app: Press Ctrl+C"
echo "To deactivate: Run 'deactivate'"
echo ""
echo "========================================"
echo ""

# Ask if user wants to run the app now
read -p "Would you like to run the application now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting application..."
    echo "Access it at: http://127.0.0.1:8050"
    echo "Press Ctrl+C to stop"
    echo ""
    python app.py
fi
