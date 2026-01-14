# OPView – OpenPhase Visualization Tool

A modular, web-based visualization tool for phase field simulation data built with Dash and VTK.

## Features

- **Interactive VTK Viewer**: Visualize 2D slices from VTK files (.vti, .vtp, .vtr, .vts)
- **Time Series Analysis**: Plot grain size evolution, stress-strain curves, and other metrics
- **Multi-Dataset Comparison**: Compare multiple VTK files side-by-side
- **Project Management**: Automatically scan and load multiple simulation projects
- **Modular Architecture**: Clean separation of UI, callbacks, data handling, and utilities

## Quick Start

### Prerequisites

**System Dependencies (Linux/WSL):**

VTK requires OpenGL and X11 libraries. Install them before running setup:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.13 python3.13-venv \
  libgl1-mesa-dev libxrender-dev libxcursor-dev \
  libxrandr-dev libxinerama-dev libxi-dev

# Fedora/RHEL
sudo dnf install python3.13 mesa-libGL-devel \
  libXrender-devel libXcursor-devel libXrandr-devel \
  libXinerama-devel libXi-devel
```

**macOS:**
```bash
# Install Python via Homebrew
brew install python@3.13

# Xcode Command Line Tools (usually already installed)
xcode-select --install
```

### Installation (Linux / macOS / WSL)

```bash
cd /path/to/OPView
chmod +x setup.sh          # one time
./setup.sh                 # creates myenv and installs requirements
source myenv/bin/activate
python OPView.py
```

Open http://127.0.0.1:8050 in your browser. Stop the server with `Ctrl+C`, and exit the virtual environment with `deactivate`.

### Restarting Later

```bash
cd /path/to/OPView
source myenv/bin/activate
python OPView.py
```

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
  - numpy, scipy
  - vtk, pyvista
  - markdown
  - plyer (for file chooser dialogs)

## Troubleshooting

### Virtual Environment Issues
If you encounter issues with the existing environment:
```bash
rm -rf myenv
./setup.sh  # Recreate from scratch
```

### Python Version
Ensure you're using Python 3.12 or 3.13:
```bash
python --version
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
