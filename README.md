# OPView – OpenPhase Visualization Tool

A modular, web-based visualization tool for phase field simulation data built with Dash and VTK.

## Features

- **Interactive VTK Viewer**: Visualize 2D slices from VTK files (.vti, .vtp, .vtr, .vts)
- **Time Series Analysis**: Plot grain size evolution, stress-strain curves, and other metrics
- **Multi-Dataset Comparison**: Compare multiple VTK files side-by-side
- **Formula Plot**: Plot `y = f(x)` and `z = f(x,y)` expressions with interactive parameter sliders, derivative/integral overlays, and CSV/PNG export
- **Calculation Notebook**: Line-by-line scientific calculator with 100+ functions, unit arithmetic, physical constants, array operations, FFT, and a built-in side plot
- **Initializations Explorer**: Preview all 25+ OpenPhase microstructure initialization methods interactively with real-time 2D phase maps
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

## Calculation Notebook

OPView includes an integrated **Calculation Notebook** tab for scientific and engineering computations. Write expressions, assignments, and function calls directly in the notebook—variables carry forward, and results appear instantly in a results gutter.

### Key Features

- **Line-by-line evaluation**: Python AST-safe evaluator (no `exec()` or `eval()`), supporting scalars, vectors, matrices, and arrays.
- **Variables carry forward**: Define a variable and use it on the next line—notebook state persists across rows.
- **100+ functions**: Trigonometric, mathematical, statistical, linear algebra, FFT, signal processing, interpolation, engineering, and dimensionless numbers.
- **Physical constants**: Built-in constants like `g_n`, `c_0`, `R_gas`, `k_B`, `N_A`, `h_p`, `sigma_SB`.
- **Unit support**: Arithmetic with units (`10*mm`, `210*GPa`, `5*min`, `1.5*kN`).
- **Power operator alias**: Use `^` as shorthand for `**` (e.g., `x^2` → `x**2`).
- **Comment support**: Inline comments with `#` or `//` are ignored during evaluation.
- **Live preview**: Client-side JavaScript preview updates instantly; server-side Python evaluation is authoritative.
- **Side plot panel**: Select X and Y array variables to plot with multiple visualization types (lines, markers, bars, histograms).
- **Autocomplete**: Tab/Enter/click to complete function names, constants, units, and user-defined variables.
- **Save/Load**: Export notebook state to `.txt` files and load them back.
- **Comprehensive help**: Built-in function reference organized by category (Trig, Math, Stats, Arrays, Vectors, Matrices, Engineering, Constitutive models, etc.).

### Example Expressions

```
v = [1, 2, 3]                          # Vector definition
A = [[1, 2], [3, 4]]                   # Matrix definition
dot(v, [4, 5, 6])                      # Dot product
A @ [[5, 6], [7, 8]]                   # Matrix multiplication
vm = von_mises(200*MPa, 120*MPa, 0)    # Von Mises stress
ps = plane_stress(210*GPa, 0.3, 1e-3)  # Plane stress state
mean([1, 4, 9, 16, 25])                # Statistical operations
linspace(0, 1, 5)                      # Array builders
solve([[2,1],[1,3]], [5,10])           # Linear system solver
reynolds(1000, 0.5, 0.01, 1e-3)        # Dimensionless numbers
```

### Implementation Files

- `ui/calculation_notebook.py` — UI layout, help sections, save/load buttons, side plot panel
- `utils/notebook_eval.py` — AST-safe evaluator, function implementations, physical constants
- `assets/notebook_live_sync.js` — Client-side live preview evaluator
- `assets/notebook_autocomplete.js` — Autocomplete dropdown for the textarea
- `callbacks/notebook_manager.py` — Dash callbacks: evaluate, side plot, save/load

## Formula Plot

The **Formula Plot** tab lets you plot and analyse `y = f(x)` or `z = f(x,y)` expressions interactively.

- **Auto-detected parameter sliders**: free symbols (e.g. `a`, `b`, `tau`) become sliders automatically.
- **Notebook binding**: bind any parameter to a Calculation Notebook variable for live sync.
- **Multiple formula rows**: overlay curves with independent color, line style, and visibility.
- **Curve overlays**: derivative, 2nd derivative, and integral curve alongside the main trace.
- **Analysis panel**: value at a point, definite integral over a configurable interval.
- **2D mode**: heatmap or surface plot for `z = f(x,y)`.
- **Export**: CSV data and PNG image per panel.

Key files: `ui/formula_graphs.py`, `callbacks/formula_manager.py`

## Initializations Explorer

The **Initializations Explorer** tab previews all OpenPhase microstructure initialization methods with configurable parameters and a real-time 2D phase map.

**25+ supported methods** across five categories:

| Category | Methods |
|----------|---------|
| Random nuclei | QuasiRandomNuclei, QuasiRandomSpheres, RandomNuclei |
| Layered | Single, SectionalPlane, Layer, Fractional, ThreeFractionals, TwoWalls, TwoDifferentWalls |
| Geometric | Sphere, SphereInGrain, Ellipsoid, Rectangular, Cylinder, Paraboloid |
| Interface physics | ThermalGrooving, TripleJunction, Young3, Young4, Young4Periodic |
| Polycrystals | VoronoiTessellation, BlobbyAuto |

Each method exposes relevant sliders (grid size, radii, thicknesses, phase fractions, random seed). A **summary panel** shows phase fractions, layer dimensions, or grain statistics depending on the method.

Key files: `ui/initializations_explorer.py`, `utils/initializations_explorer.py`, `callbacks/` (initializations manager)

## Project Architecture

OPView uses a modular architecture with clear separation of concerns:

```
OPView.py (Entry Point, ~1,000 lines)
├── app/              - Application orchestration and state management
├── callbacks/        - Dash callback managers (tab, project, data, notebook)
├── comparisonmgr/    - Multi-dataset comparison feature
├── config/           - Configuration and dataset registry
├── data/             - Data sources and loaders (OOP pattern)
├── ui/               - UI components and layout builders
├── utils/            - Utility functions (charts, VTK, paths, docs, notebook evaluation)
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Part of the OpenPhase simulation framework.
