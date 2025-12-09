# VTK 2D Slice Viewer - Setup Instructions

Complete guide to set up the VTK 2D Slice Viewer application on your system.

---

## Prerequisites

- Python 3.12 or 3.13 (Python 3.14 is NOT compatible with VTK)
- pip (Python package installer)
- Internet connection for downloading packages

---

## Option 1: Quick Setup (Linux/macOS/WSL)

### Step-by-Step Commands

```bash
# 1. Navigate to the project directory
cd /path/to/Dash

# 2. Check available Python versions
python3 --version
python3.13 --version  # Or python3.12

# 3. Create virtual environment with Python 3.13 (recommended)
# If you have Python 3.13 from Homebrew:
/home/linuxbrew/.linuxbrew/bin/python3.13 -m venv myenv

# OR if you have system Python 3.13:
python3.13 -m venv myenv

# OR if you have Python 3.12:
python3.12 -m venv myenv

# 4. Activate the virtual environment
source myenv/bin/activate

# 5. Upgrade pip to latest version
pip install --upgrade pip

# 6. Install all dependencies from requirements.txt
pip install -r requirements.txt

# 7. Verify installation
python -c "import dash, plotly, pyvista, vtk; print('All packages installed successfully!')"

# 8. Run the application
python app.py
```

### Access the Application

Open your browser and navigate to: **http://127.0.0.1:8050**

---

## Option 2: Quick Setup (Windows)

### Step-by-Step Commands

```cmd
# 1. Navigate to the project directory
cd C:\path\to\Dash

# 2. Check available Python versions
python --version
py -3.13 --version

# 3. Create virtual environment with Python 3.13
py -3.13 -m venv myenv

# OR with default Python:
python -m venv myenv

# 4. Activate the virtual environment
myenv\Scripts\activate

# 5. Upgrade pip
python -m pip install --upgrade pip

# 6. Install all dependencies
pip install -r requirements.txt

# 7. Verify installation
python -c "import dash, plotly, pyvista, vtk; print('All packages installed successfully!')"

# 8. Run the application
python app.py
```

### Access the Application

Open your browser and navigate to: **http://127.0.0.1:8050**

---

## Option 3: One-Line Installation Script

### For Linux/macOS/WSL

Create a file called `setup.sh`:

```bash
#!/bin/bash

# VTK 2D Slice Viewer - Setup Script

echo "========================================"
echo "VTK 2D Slice Viewer - Setup"
echo "========================================"

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
    echo "  Please install Python 3.12 or 3.13"
    exit 1
fi

echo "Using: $PYTHON_CMD ($($PYTHON_CMD --version))"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv myenv
if [ $? -ne 0 ]; then
    echo "✗ ERROR: Failed to create virtual environment"
    exit 1
fi
echo "✓ Virtual environment created"

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✓ pip upgraded"

# Install requirements
echo "Installing dependencies (this may take several minutes)..."
echo "  - Downloading packages..."
echo "  - Installing: dash, plotly, numpy, scipy, pyvista, vtk, and others"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ ERROR: Failed to install dependencies"
    exit 1
fi
echo "✓ All dependencies installed"

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import dash, plotly, pyvista, vtk; print('✓ All packages verified successfully!')"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To run the application:"
echo "  1. Activate the virtual environment:"
echo "     source myenv/bin/activate"
echo ""
echo "  2. Run the app:"
echo "     python app.py"
echo ""
echo "  3. Open your browser to:"
echo "     http://127.0.0.1:8050"
echo ""
echo "========================================"
```

Make it executable and run:

```bash
chmod +x setup.sh
./setup.sh
```

### For Windows

Create a file called `setup.bat`:

```batch
@echo off
ECHO ========================================
ECHO VTK 2D Slice Viewer - Setup
ECHO ========================================

REM Check for Python
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Python not found!
    ECHO Please install Python 3.12 or 3.13
    EXIT /B 1
)

python --version
ECHO.

REM Create virtual environment
ECHO Creating virtual environment...
python -m venv myenv
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Failed to create virtual environment
    EXIT /B 1
)
ECHO Virtual environment created

REM Activate virtual environment
ECHO Activating virtual environment...
CALL myenv\Scripts\activate
ECHO Virtual environment activated

REM Upgrade pip
ECHO Upgrading pip...
python -m pip install --upgrade pip
ECHO pip upgraded

REM Install requirements
ECHO Installing dependencies (this may take several minutes)...
ECHO   - Downloading packages...
ECHO   - Installing: dash, plotly, numpy, scipy, pyvista, vtk, and others
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Failed to install dependencies
    EXIT /B 1
)
ECHO All dependencies installed

REM Verify installation
ECHO.
ECHO Verifying installation...
python -c "import dash, plotly, pyvista, vtk; print('All packages verified successfully!')"

ECHO.
ECHO ========================================
ECHO Setup Complete!
ECHO ========================================
ECHO.
ECHO To run the application:
ECHO   1. Activate the virtual environment:
ECHO      myenv\Scripts\activate
ECHO.
ECHO   2. Run the app:
ECHO      python app.py
ECHO.
ECHO   3. Open your browser to:
ECHO      http://127.0.0.1:8050
ECHO.
ECHO ========================================
PAUSE
```

Run it:

```cmd
setup.bat
```

---

## Installed Packages

The `requirements.txt` installs the following packages:

### Core Dependencies
- **dash** (3.3.0) - Web application framework
- **dash-mantine-components** (2.4.0) - UI components
- **plotly** (6.5.0) - Interactive plotting library
- **numpy** (2.3.5) - Numerical computing
- **scipy** (1.16.3) - Scientific computing
- **pyvista** (0.46.4) - 3D visualization toolkit
- **vtk** (9.5.2) - Visualization Toolkit (112 MB)
- **markdown** (3.10) - Markdown support
- **kaleido** (1.2.0) - Static image export

### Additional Dependencies (48 packages total)
Including: Flask, Werkzeug, matplotlib, pillow, pytest, and many others

**Total Download Size:** ~200 MB
**Installation Time:** 3-5 minutes (depending on internet speed)

---

## Troubleshooting

### Issue 1: Python Version Incompatibility

**Error:** `ERROR: Could not find a version that satisfies the requirement vtk`

**Solution:**
- VTK does not support Python 3.14
- Use Python 3.12 or 3.13
- Check your Python version: `python --version`

### Issue 2: Missing venv Module

**Error:** `The virtual environment was not created successfully because ensurepip is not available`

**Solution (Linux/Ubuntu):**
```bash
sudo apt update
sudo apt install python3.13-venv
```

**Solution (macOS):**
```bash
# Install Python 3.13 via Homebrew
brew install python@3.13
```

### Issue 3: Port 8050 Already in Use

**Solution:** Change the port in `app.py` (line 489):
```python
app.run(debug=True, host='127.0.0.1', port=8051)
```

### Issue 4: Slow Installation (WSL/Linux)

**Reason:** Large packages like VTK (112 MB) take time to extract and install

**Solution:** Be patient, the installation will complete in 3-5 minutes

### Issue 5: Import Error After Installation

**Solution:**
```bash
# Make sure virtual environment is activated
source myenv/bin/activate  # Linux/macOS
myenv\Scripts\activate     # Windows

# Verify packages are installed
pip list | grep dash
pip list | grep vtk
```

---

## Verifying Successful Installation

Run these commands to verify everything is working:

```bash
# Activate environment
source myenv/bin/activate  # Linux/macOS
# OR
myenv\Scripts\activate     # Windows

# Test imports
python -c "import dash; print(f'Dash version: {dash.__version__}')"
python -c "import plotly; print(f'Plotly version: {plotly.__version__}')"
python -c "import vtk; print(f'VTK version: {vtk.vtkVersion.GetVTKVersion()}')"
python -c "import pyvista; print(f'PyVista version: {pyvista.__version__}')"

# List all installed packages
pip list
```

Expected output:
```
Dash version: 3.3.0
Plotly version: 6.5.0
VTK version: 9.5.2
PyVista version: 0.46.4
```

---

## Daily Usage

### Starting the Application

```bash
# 1. Navigate to project directory
cd /path/to/Dash

# 2. Activate virtual environment
source myenv/bin/activate  # Linux/macOS
# OR
myenv\Scripts\activate     # Windows

# 3. Run the application
python app.py

# 4. Open browser to http://127.0.0.1:8050
```

### Stopping the Application

Press `Ctrl+C` in the terminal

### Deactivating Virtual Environment

```bash
deactivate
```

---

## Updating Dependencies

To update all packages to their latest versions:

```bash
# Activate environment
source myenv/bin/activate

# Update all packages
pip install --upgrade -r requirements.txt

# Or update specific package
pip install --upgrade dash
```

---

## Uninstalling

To completely remove the installation:

```bash
# Deactivate virtual environment (if active)
deactivate

# Remove virtual environment directory
rm -rf myenv  # Linux/macOS
# OR
rmdir /s myenv  # Windows
```

---

## System Requirements

- **OS:** Linux, macOS, Windows (including WSL)
- **Python:** 3.12 or 3.13 (NOT 3.14)
- **RAM:** Minimum 2 GB (4 GB recommended)
- **Disk Space:** ~500 MB for virtual environment and packages
- **Internet:** Required for initial package download

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review `README.md` for application usage
3. Review `CLAUDE.md` for development details
4. Check VTK file compatibility

---

## Quick Reference Card

```
╔════════════════════════════════════════════╗
║  VTK 2D Slice Viewer - Quick Reference     ║
╠════════════════════════════════════════════╣
║  Create Environment:                       ║
║    python3.13 -m venv myenv                ║
║                                            ║
║  Activate (Linux/Mac):                     ║
║    source myenv/bin/activate               ║
║                                            ║
║  Activate (Windows):                       ║
║    myenv\Scripts\activate                  ║
║                                            ║
║  Install Packages:                         ║
║    pip install -r requirements.txt         ║
║                                            ║
║  Run Application:                          ║
║    python app.py                           ║
║                                            ║
║  Access:                                   ║
║    http://127.0.0.1:8050                   ║
║                                            ║
║  Stop: Ctrl+C                              ║
║  Deactivate: deactivate                    ║
╚════════════════════════════════════════════╝
```

---

**Last Updated:** 2025-12-08
**Python Version:** 3.13 (recommended)
**VTK Version:** 9.5.2
