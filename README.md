# OPView – OpenPhase Visualization Tool

A modular, web-based visualization tool for phase field simulation data built with Dash and VTK.

## Features

- **Interactive VTK Viewer**: Visualize 2D slices from VTK files (.vti, .vtp, .vtr, .vts)
- **Time Series Analysis**: Plot grain size evolution, stress-strain curves, and other metrics
- **Multi-Dataset Comparison**: Compare multiple VTK files side-by-side
- **Project Management**: Automatically scan and load multiple simulation projects
- **Modular Architecture**: Clean separation of UI, callbacks, data handling, and utilities

## Quick Start (One-Click Launchers)

Each platform has a single script that handles everything automatically: finds or installs Python, creates a virtual environment, installs all dependencies, starts the server, and opens the browser.

### Windows

Double-click `run.bat` or run from a terminal:
```powershell
run.bat
```

**Prerequisite:** Python 3.12 or 3.13 must be installed and on PATH.
```powershell
# Install Python via winget (Windows 10/11)
winget install Python.Python.3.12
# Or download from https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation
```

### Linux

```bash
chmod +x run.sh    # one time
./run.sh
```

The script auto-installs missing system libraries (OpenGL, X11) via your package manager and the Python `venv` module if needed. Python 3.12 or 3.13 must be available on the system.

```bash
# If Python is not installed:
# Ubuntu/Debian
sudo apt install python3.13 python3.13-venv
# Fedora/RHEL
sudo dnf install python3.13
```

### macOS

```bash
chmod +x run-macos.sh    # one time
./run-macos.sh
```

The script checks for Xcode Command Line Tools, finds Python via Homebrew (Apple Silicon and Intel paths), and auto-installs `python@3.13` via Homebrew if no supported version is found.

```bash
# If Homebrew is not installed:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### What the scripts do

1. Find Python 3.12 or 3.13 (install system dependencies if needed)
2. Create a `myenv` virtual environment (or reuse an existing one)
3. Install/update all dependencies from `requirements.txt`
4. Start the OPView server and open http://127.0.0.1:8050 in the browser

Press `Ctrl+C` to stop the server.

### Manual Installation

<details>
<summary>Click to expand manual setup steps</summary>

**Windows:**
```powershell
cd E:\path\to\OPView
py -3.12 -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
python OPView.py
```

**Linux / macOS / WSL:**
```bash
cd /path/to/OPView
chmod +x setup.sh
./setup.sh
source myenv/bin/activate
python OPView.py
```

Open http://127.0.0.1:8050 in your browser. Stop the server with `Ctrl+C`, and exit the virtual environment with `deactivate`.

</details>

## Data Layout

OPView scans immediate subfolders for simulation projects containing:
- `VTK/` directory with VTK files (.vti, .vtp, .vtr, .vts)
- `TextData/` directory with time series data (optional)

**Example structure:**
```
OPView/
├── Project1/
│   ├── VTK/           # VTK simulation outputs
│   └── TextData/      # Time series data files
├── Project2/
│   └── VTK/
└── OPView.py
```

Place your simulation data in project folders before launching the app.

## Project Architecture

OPView uses a modular architecture with clear separation of concerns:

```
OPView.py (Entry Point, ~1,000 lines)
├── app/              - Application orchestration and state management
├── callbacks/        - Dash callback managers (tab, project, data)
├── comparisonmgr/    - Multi-dataset comparison feature
├── config/           - Configuration and dataset registry
├── data/             - Data sources and loaders (OOP pattern)
├── ui/               - UI components and layout builders
├── utils/            - Utility functions (charts, VTK, paths, docs)
└── viewer/           - VTK 2D slice viewer panel
```

Each module has a single, well-defined responsibility for maintainability.

## Requirements

- **Python**: 3.12 or 3.13 (VTK is not compatible with 3.14+)
- **Dependencies**: Listed in `requirements.txt`
  - dash, dash-mantine-components
  - plotly, kaleido
  - numpy, scipy, pandas
  - vtk, pyvista
  - markdown
  - plyer (for file chooser dialogs)
  - pywin32 (Windows only - required for plyer on Windows)

## Troubleshooting

### Virtual Environment Issues

**Windows:**
```powershell
# Remove existing environment
Remove-Item -Recurse -Force myenv
# Recreate from scratch
py -3.12 -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```

**Linux:**
```bash
rm -rf myenv
./run.sh  # Recreate from scratch
```

**macOS:**
```bash
rm -rf myenv
./run-macos.sh  # Recreate from scratch
```

### Python Version

**Windows:**
```powershell
py -3.12 --version
# or
python --version
```

**Linux/macOS/WSL:**
```bash
python --version
# or
python3 --version
```

### Port Already in Use
If port 8050 is occupied, modify the port in `OPView.py`:
```python
app.run(host='127.0.0.1', port=8050, debug=False)
```

## Development

The codebase follows OOP patterns for managers and functional patterns for utilities. See `CLAUDE.md` for detailed coding standards and architecture guidelines.

**Key Design Principles:**
- Separation of concerns across modules
- Lazy imports for heavy dependencies (VTK, ViewerPanel)
- Manager-based callback registration
- Modular UI component system

## License

This project is part of the OpenPhase simulation framework.
