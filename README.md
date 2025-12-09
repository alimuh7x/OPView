# VTK Multi-Field Slice Viewer

A configuration-driven Dash/Plotly application for visualizing multiple VTK files across scientific fields (phase field, temperature, mechanics, plasticity, ...).

## Features

- Load VTK files (.vtk, .vti, .vtp, .vtr, .vts)
- Automatic detection of 2D/3D data
- Automatic detection of newest snapshots inside `VTK/` per dataset (no manual dropdowns)
- Configuration-driven tabs (Phase Field, Temperature, Mechanics, Plasticity by default)
- Shared two-click range selection logic per tab with manual overrides
- Dropdown-based color presets for below/above threshold (no manual typing needed)
- Consistent light theme with glass cards and top map titles
- Slice slider + number input (auto-hidden for 2D data) with cached interpolation for smooth rendering
- Reset button restores defaults for the active tab/file combination

## Installation

### Prerequisites

- Python 3.12 or higher (recommended)
- Windows/Linux/macOS

### Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Generating Sample Data

Generate synthetic VTI test files:

```bash
python sample_data/generate_sample_vti.py
```

This creates:
- `sample_data/sample_3d.vti` - 3D dataset (50x40x30)
- `sample_data/sample_2d.vti` - 2D dataset (100x80)
- `sample_data/phase_field.vti` - Phase field simulation (60x50x40)

## Running the Application

```bash
python app.py
```

Then open your browser to: **http://127.0.0.1:8050**

## Usage

### Controls

**Left Panel (per dataset):**
- **Scalar Field Dropdown** – switch between available arrays inside the selected VTK file
- **Color Presets** – choose colors for below/above threshold without typing codes
- **Range Inputs** – set min/max numerically or by selecting two points on the heatmap
- **Slice Slider/Input** – for 3D data; hidden automatically for 2D files
- **Reset Button** – restore defaults (colors, range, slice, threshold)

**Right Panel:**
- **Heatmap** – 2D visualization with white transition at the threshold and smoothing
- **Map Title** – Displays the active scalar and units (e.g., `σxx (MPa)`)
- **Click Helper** – Reminds when the viewer is waiting for the second click or shows the selected range

### Loading Your Own VTK Files

1. Place your VTK files in the `VTK/` directory, preferably with a numbered suffix (e.g., `PhaseField_00005000.vts`).
2. In `app.py`, add or edit a dataset entry inside the relevant tab and set its `file_glob` (e.g., `"file_glob": "VTK/MyData_*.vts"`).
3. Restart the app – it automatically loads the most recent file that matches each glob. If no file matches, the dataset block is omitted.

### Adding/Customizing Tabs

Tabs are declared in `app.py` via `TAB_CONFIGS`. Each tab defines one or more dataset blocks by specifying a unique `id`, display `label`, and `file_glob`:

```python
{
    "id": "mechanics",
    "label": "Mechanics",
    "datasets": [
        {
            "id": "stresses",
            "label": "Stress Tensor",
            "file_glob": "VTK/Stresses_*.vts",
            "scale": 1e-6,
            "units": "MPa",
            "scalars": [
                {"label": "Pressure", "array": "Pressure"},
                {"label": "von Mises", "array": "von Mises"},
                {"label": "σ_xx", "array": "Stresses", "component": 0}
            ]
        },
        {
            "id": "elastic",
            "label": "Elastic Strains",
            "file_glob": "VTK/ElasticStrains_*.vts",
            "scalars": [{"label": "ε_xx", "array": "ElasticStrains", "component": 0}]
        }
    ]
}
```

Each dataset inherits the shared controls (color presets, range selection, slice slider). If a glob matches no files the block is skipped automatically.

## Project Structure

```
Dash/
│
├── app.py                          # Main Dash application & tab configuration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── viewer/
│   ├── __init__.py                 # Exposes ViewerPanel
│   ├── defaults.py                 # Shared defaults for all tabs
│   ├── layout.py                   # Control/graph builders
│   ├── panel.py                    # ViewerPanel class (callbacks + layout)
│   └── state.py                    # Dataclass used in dcc.Store
│
├── utils/
│   ├── __init__.py
│   └── vtk_reader.py              # Cached VTK file loading/slicing
│
├── sample_data/
│   ├── generate_sample_vti.py     # Sample data generator
│   ├── sample_3d.vti              # Generated 3D test file
│   ├── sample_2d.vti              # Generated 2D test file
│   └── phase_field.vti            # Generated phase field data
│
└── assets/
    └── style.css                   # Custom CSS styling
```

## Technical Details

### Two-Color Threshold Logic

Each tab shares the same Plotly `zmid` logic: colors below threshold use `colorA`, above threshold use `colorB`, and white at the midpoint for a crisp two-tone view. Thresholds automatically follow the currently selected data range (two-click selection or manual inputs).

### Viewer Package

- `ViewerPanel` owns layout + callbacks per tab.
- `ViewerState` is stored in `dcc.Store`, ensuring each tab/user keeps isolated settings.
- Shared behaviours (range selection, color updates, click helper) reside in `viewer/panel.py`.

### Efficient Slicing

- `VTKReader.get_interpolated_slice` caches interpolated grids per (scalar, axis, slice, resolution) making quick tab switching inexpensive.
- Slice origins respect dataset bounds, so structured/rectilinear grids that do not start at zero are handled correctly.

### Data Flow

1. **Load VTK** → `VTKReader` (per file with caching)
2. **Tab Initialization** → Each tab merges shared defaults with overrides and instantiates `ViewerState`
3. **Slice Extraction** → PyVista slice + SciPy interpolation (cached)
4. **Dash Callback** → Shared handler updates state, figure, and click helper text
5. **Visualization** → Plotly heatmap per tab, all reusing the same controls logic

## Troubleshooting

### VTK Import Error

If you see `ModuleNotFoundError: No module named 'vtk'`:

1. Ensure you're using Python 3.12 (VTK compatibility issue with 3.14)
2. Reinstall VTK: `pip install --force-reinstall vtk`
3. Check virtual environment is activated

### File Not Found

If sample files are missing:
```bash
python sample_data/generate_sample_vti.py
```

### Port Already in Use

Change the port in `app.py`:
```python
app.run_server(debug=True, host='127.0.0.1', port=8051)  # Change port
```

## Dependencies

- **dash** >= 2.14.0 - Web framework
- **plotly** >= 5.18.0 - Interactive plotting
- **pyvista** >= 0.43.0 - VTK file handling
- **numpy** >= 1.24.0 - Numerical arrays
- **scipy** >= 1.11.0 - Interpolation
- **vtk** >= 9.2.0 - VTK backend

## Future Enhancements

Possible extensions now that the viewer is modular:
- Runtime file picker per tab
- Volume rendering / 3D scenes in separate tabs
- Axis selection dropdowns (leveraging the shared state object)
- Export (PNG/GIF) utilities layered on top of the shared viewer hooks
- Custom per-tab controls (e.g., units switch for temperature) without duplicating layout logic

## License

This project is open-source and available for educational and research purposes.

## Contact

For issues or questions, please open an issue in the project repository.
