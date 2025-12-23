"""Multi-field VTK viewer with reusable tab panels."""
import time
_start_time = time.time()
print(f"[{time.time()-_start_time:.2f}s] Starting imports...")

import base64
import fnmatch
import hashlib
import os
import re
import warnings
from glob import glob
from pathlib import Path

print(f"[{time.time()-_start_time:.2f}s] Standard library imports done")

import numpy as np
import plotly.graph_objects as go
from dash import ALL, MATCH, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from flask import render_template_string
import markdown
from scipy import stats
import dash_mantine_components as dmc
from viewer.state import initial_state

print(f"[{time.time()-_start_time:.2f}s] Third-party imports done")

from utils.vtk_reader import VTKReader
# Defer ViewerPanel import for faster startup - import only when needed
ViewerPanel = None  # Lazy import later

print(f"[{time.time()-_start_time:.2f}s] Local imports done (ViewerPanel deferred)")

# OOP Data Sources
from data import (
    StressStrainData,
    StressData,
    StrainData,
    CRSSData,
    GrainSizeData,
)

# Callback factory system
from ui.callbacks import (
    create_histogram_callback,
    create_component_selection_callback,
    create_multi_output_callback,
)

# Utility functions (extracted from this file - now imported)
from utils import (
    scan_project_folders,
    get_reader,
    list_vtk_files,
    resolve_vtk_path,
    latest_file,
    reader_cache,
)
from utils.vtk_utils import list_comparison_files
from utils.project_scanner import get_project_folder_options
from utils.chart_utils import (
    compute_average_series,
    fit_best_distribution,
    format_fit_summary,
    build_histogram_figure,
    crss_series_values as _crss_series_values,
    stress_series_values as _stress_series_values,
    strain_series_values as _strain_series_values,
)
from utils.docs import render_docs as _render_docs

# Config functions
from config import comparison_data_dir

APP_TITLE = "OPView"
TENSOR_COMPONENTS = ['xx', 'yy', 'zz', 'xy', 'yz', 'zx']
BASE_DIR = Path(__file__).resolve().parent


def tensor_scalars(array_name: str, prefix: str):
    return [
        {'label': f"{prefix}_{comp}", 'array': array_name, 'component': idx}
        for idx, comp in enumerate(TENSOR_COMPONENTS)
    ]

TAB_CONFIGS = [
    {
        "id": "phase-field",
        "label": "Phase Field",
        "datasets": [
            {
                "id": "phase",
                "label": "Phase Field",
                "file_glob": "VTK/PhaseField_*.vts",
                "scalars": [
                    {'label': 'Phase Field', 'array': 'PhaseFields'},
                    {'label': 'Interfaces', 'array': 'Interfaces'},
                    {'label': 'Phase Fraction', 'array': 'PhaseFraction_0'},
                ]
            }
        ],
    },
    {
        "id": "composition",
        "label": "Composition",
        "datasets": [
            {
                "id": "composition",
                "label": "Composition",
                "file_glob": "VTK/Composition_*.vts",
                "scalars": [
                    {'label': 'Weight Fraction FE (Total)', 'array': 'WeightFractionsTotal_FE'},
                    {'label': 'Mole Fraction FE (Total)', 'array': 'MoleFractionsTotal_FE'},
                    {'label': 'Mole Fraction FE (Phase 0)', 'array': 'MoleFractionsPhase_FE(0)'},
                    {'label': 'Mole Fraction FE (Phase 1)', 'array': 'MoleFractionsPhase_FE(1)'},
                    {'label': 'Weight Fraction SOLVENT (Total)', 'array': 'WeightFractionsTotal_SOLVENT'},
                    {'label': 'Mole Fraction SOLVENT (Total)', 'array': 'MoleFractionsTotal_SOLVENT'},
                    {'label': 'Mole Fraction SOLVENT (Phase 0)', 'array': 'MoleFractionsPhase_SOLVENT(0)'},
                    {'label': 'Mole Fraction SOLVENT (Phase 1)', 'array': 'MoleFractionsPhase_SOLVENT(1)'},
                    {'label': 'Weight Fraction CL (Total)', 'array': 'WeightFractionsTotal_CL'},
                    {'label': 'Mole Fraction CL (Total)', 'array': 'MoleFractionsTotal_CL'},
                    {'label': 'Mole Fraction CL (Phase 0)', 'array': 'MoleFractionsPhase_CL(0)'},
                    {'label': 'Mole Fraction CL (Phase 1)', 'array': 'MoleFractionsPhase_CL(1)'},
                ]
            }
        ],
    },
    {
        "id": "mechanics",
        "label": "Mechanics",
        "datasets": [
            {
                "id": "stresses",
                "label": "Stress Tensor",
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "VTK/Stresses_*.vts",
                "scalars": [
                    {'label': 'Pressure', 'array': 'Pressure'},
                    {'label': 'von Mises', 'array': 'von Mises'},
                    *tensor_scalars('Stresses', 'σ')
                ],
            },
            {
                "id": "elastic",
                "label": "Elastic Strains",
                "file_glob": "VTK/ElasticStrains_*.vts",
                # Store elastic strains in percent for all components
                "units": "%",
                "scale": 100.0,
                "scalars": tensor_scalars('ElasticStrains', 'ε'),
            },
        ],
    },
    {
        "id": "plasticity",
        "label": "Plasticity",
        "datasets": [
            {
                "id": "crss",
                "label": "CRSS",
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "VTK/CRSS_00001000.vts",
                "scalars": [
                    {'label': f"CRSS {i}", 'array': f"CRSS_0_{i}"}
                    for i in range(12)
                ],
            },
            {
                "id": "plastic-strain",
                "label": "Plastic Strain",
                "file_glob": "VTK/PlasticStrain_*.vts",
                # Store plastic strains in percent for all components
                "units": "%",
                "scale": 100.0,
                "scalars": tensor_scalars('PlasticStrain', 'εᵖ'),
            },
        ],
    },
]

# Application context (injected by OPViewApp during initialization)
# When running standalone, this will be None and fall back to legacy globals
app_context = None
data_manager = None


def get_legacy_data(data_type: str):
    """
    Get legacy data from DataManager if available, otherwise from globals.

    Args:
        data_type: One of 'size_details', 'size_averages', 'stress_strain', 'crss', 'plastic_strain'

    Returns:
        Data dict or None
    """
    if data_manager is not None:
        return data_manager.get_legacy_data(data_type)

    # Fall back to legacy globals
    global SIZE_DETAILS_DATA, SIZE_AVERAGE_DATA, STRESS_STRAIN_DATA, CRSS_DATA, PLASTIC_STRAIN_DATA
    return {
        'size_details': SIZE_DETAILS_DATA,
        'size_averages': SIZE_AVERAGE_DATA,
        'stress_strain': STRESS_STRAIN_DATA,
        'crss': CRSS_DATA,
        'plastic_strain': PLASTIC_STRAIN_DATA,
    }.get(data_type)

# Legacy global variables (used when app_context is None for backwards compatibility)
reader_cache = {}

# Grid cache for comparison panel optimizations: key = (file_name, scalar, slice_index) → (figure, colorbar_figure)
comparison_grid_cache = {}
comparison_grid_cache_data = {}  # key = (file_name, scalar, slice_index) → (X_grid, Y_grid, Z_grid, stats, state_dict)

# Storage for discovered project folders (initialized at startup)
discovered_project_folders = {}
# Currently selected project folder path (updated when user selects from dropdown)
current_project_vtk_path = None
# Loaded project VTK file paths (across multiple projects)
loaded_project_vtk_files = []
loaded_project_names = []
loaded_project_vtk_files_by_project = {}

# Cache main ViewerPanels by dataset id to avoid duplicate callback registration.
main_panels_by_id = {}
# Cache manual single-file ViewerPanels by absolute path.
manual_panels_by_path = {}


# Phase 7A: Removed duplicate functions - now imported from utils module
# - _scan_vtk_dir() → utils.project_scanner._scan_vtk_dir()
# - get_project_folder_options() → utils.project_scanner.get_project_folder_options()


# Phase 7A: Removed scan_project_folders() - now imported from utils.project_scanner


# Cache for rendered heatmap rows to avoid rebuilding on tab switches
def vtk_data_dir():
    """Return the VTK data directory preferring the selected project folder, else CWD/VTK, else repo VTK."""
    # Use app_context if available, otherwise fall back to legacy global
    if app_context is not None:
        vtk_path = app_context.current_project_vtk_path
    else:
        global current_project_vtk_path
        vtk_path = current_project_vtk_path

    # If a project folder is selected, use its VTK path
    if vtk_path and vtk_path.exists():
        return vtk_path

    # Otherwise, use default behavior
    cwd_vtk = Path.cwd() / "VTK"
    if cwd_vtk.exists():
        return cwd_vtk
    fallback = BASE_DIR / "VTK"
    return fallback if fallback.exists() else Path.cwd()


DEFAULT_VTK_FOLDER_LABEL = vtk_data_dir().name or "VTK"
COMPARISON_FOLDER_NAME = "Comparison"
ALLOWED_VTK_EXTENSIONS = ('.vtk', '.vti', '.vtp', '.vtr', '.vts')


# Phase 7C: Removed comparison_data_dir() - now imported from config.paths


# Phase 7A: Removed duplicate functions - now imported from utils module
# - list_comparison_files() → utils.vtk_utils.list_comparison_files()
# - resolve_vtk_path() → utils.path_utils.resolve_vtk_path() (also imported from utils)
# - get_reader() → utils.vtk_utils.get_reader() (also imported from utils)



print(f"[{time.time()-_start_time:.2f}s] Creating Dash app...")
app = Dash(__name__, suppress_callback_exceptions=True)
app.title = APP_TITLE
print(f"[{time.time()-_start_time:.2f}s] Dash app created")

TEXTDATA_DIR = Path("TextData")
SIZE_DETAILS_FILE   = TEXTDATA_DIR / "SizeDetails.dat"
SIZE_AVERAGE_FILE   = TEXTDATA_DIR / "SizeAveInfo.dat"
STRESS_STRAIN_FILE  = TEXTDATA_DIR / "StressStrainFile.txt"
CRSS_FILE           = TEXTDATA_DIR / "CRSSFile.txt"
PLASTIC_STRAIN_FILE = TEXTDATA_DIR / "PlasticStrainFile.txt"
SIZE_AVERAGE_FILE   = TEXTDATA_DIR / "SizeAveInfo.dat"


# Phase 7B: Removed duplicate data loader functions - now in data/loaders.py
# - load_size_details() → data_manager.get_legacy_data('size_details')
# - load_size_averages() → data_manager.get_legacy_data('size_averages')


# Defer loading TextData files for fast startup - load only when needed
SIZE_DETAILS_DATA = None  # load_size_details()
SIZE_AVERAGE_DATA = None  # load_size_averages()


# Phase 7B: Removed duplicate data loader functions - now in data/loaders.py
# - load_stress_strain() → data_manager.get_legacy_data('stress_strain')
# - load_crss() → data_manager.get_legacy_data('crss')


# Defer loading TextData files for fast startup - load only when needed
STRESS_STRAIN_DATA = None  # load_stress_strain()
CRSS_DATA = None  # load_crss()
PLASTIC_STRAIN_DATA = None


# Phase 7B: Removed duplicate data loader function - now in data/loaders.py
# - load_plastic_strain() → data_manager.get_legacy_data('plastic_strain')


# Phase 7: Data loading moved to DataManager.load_all_legacy()
# PLASTIC_STRAIN_DATA = load_plastic_strain()  # Removed - use data_manager.get_legacy_data('plastic_strain')
PLASTIC_STRAIN_DATA = None  # Will be loaded by DataManager if needed


# Phase 8: Documentation rendering - Flask route wrapper
@app.server.route('/docs')
def render_docs():
    """Flask route for documentation page. Implementation in utils.docs."""
    return _render_docs()


# Phase 8: Removed chart utility functions - now in utils/chart_utils.py
# - compute_average_series()
# - build_histogram_figure()
# - fit_best_distribution()
# - format_fit_summary()

# Wrapper functions for backwards compatibility
def crss_series_values(component):
    """Wrapper for crss_series_values from chart_utils."""
    return _crss_series_values(component, get_legacy_data)


def stress_series_values(component):
    """Wrapper for stress_series_values from chart_utils."""
    return _stress_series_values(component, get_legacy_data)


def strain_series_values(component):
    """Wrapper for strain_series_values from chart_utils."""
    return _strain_series_values(component, get_legacy_data)


def build_grain_histogram(time_value, bins, fit=False):
    """LEGACY - Replaced by grain_data.get_histogram_data()

    Uses get_legacy_data() to access SIZE_DETAILS_DATA.
    Use grain_data.get_histogram_data(time_value, bins, fit) instead.
    """
    data = get_legacy_data('size_details')
    if not data:
        return go.Figure(), "_No data available._"
    times = data['times']
    values = data['values']
    if not times or not values:
        return go.Figure(), "_No data available._"
    try:
        time_value = float(time_value)
    except (TypeError, ValueError):
        time_value = times[0]
    row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
    row_values = values[row_index]
    if not row_values:
        return go.Figure(), "_No data available._"
    fig, summary = build_histogram_figure(row_values, "Grain Size", bins, fit=fit)
    summary = f"**Time:** {times[row_index]:.3f}\n\n" + summary
    return fig, summary

# Phase 8: fit_best_distribution() and format_fit_summary() removed
# → Now imported from utils.chart_utils


def initialize_tab_datasets_static():
    """
    Initialize main tab panels at startup (no VTK reads).

    Why: Dash must know all callback dependencies on first page load; if we create
    ViewerPanels (and register callbacks) only after the user selects a project,
    the browser won't see those callbacks until a refresh.

    Panels use `projects-store` for project/file dropdown options and only read
    a VTK file when the user selects a file.
    """
    from viewer import ViewerPanel

    tab_data = {}
    debug = bool(os.environ.get("OPVIEW_DEBUG"))
    active_project_name = None
    # Panels populate project/file pickers from `projects-store` (paths only; no VTK reads).
    for tab in TAB_CONFIGS:
        datasets = []
        # Initialize the tab entry first to ensure it exists even if no datasets are found
        tab_data[tab["id"]] = {
            "label": tab["label"],
            "panels": datasets
        }

        for dataset in tab.get("datasets", []):
            # Panels start empty until user picks project+file.
            files = []
            file_pattern = None
            if dataset.get("file_glob"):
                file_pattern = Path(dataset["file_glob"]).name
            elif dataset.get("file"):
                file_pattern = Path(dataset["file"]).name

            dataset_config = {
                "id": f"{tab['id']}-{dataset['id']}",
                "label": dataset["label"],
                "scalars": dataset.get("scalars"),
                "colorA": dataset.get("colorA"),
                "colorB": dataset.get("colorB"),
                "file": None,
                "files": files,
                "project_value": active_project_name,
                "enable_project_picker": True,
                "file_pattern": file_pattern,
                "scale": dataset.get("scale"),
                "units": dataset.get("units"),
                "overrides": dataset.get("overrides"),
                "enable_line_scan": True,
            }
            panel_id = dataset_config["id"]
            if debug:
                sample = [Path(p).name for p in (files or [])[:5]]
                print(
                    f"[OPVIEW_DEBUG] init_tab panel={panel_id} files={len(files or [])} sample={sample}",
                    flush=True,
                )
            panel = main_panels_by_id.get(panel_id)
            if panel is None:
                try:
                    panel = ViewerPanel(app, get_reader, dataset_config)
                except (FileNotFoundError, ValueError):
                    continue
                main_panels_by_id[panel_id] = panel
            else:
                # Update existing panel to new file list without re-registering callbacks.
                try:
                    panel.files = dataset_config.get("files") or []
                    panel.file_path = None
                    panel.file_pattern = file_pattern
                    panel.enable_project_picker = True
                    panel.project_options = []
                    panel.project_value = active_project_name
                    panel.time_options = panel._build_time_options(panel.files)
                    panel.time_value = None
                    panel.reader = None
                    initial_scalar = panel.scalar_defs[0]['value']
                    panel.base_state = initial_state(
                        scalar_key=initial_scalar,
                        scalar_label=panel.scalar_defs[0]['label'],
                        axis=panel.axis,
                        slice_index=0,
                        stats={"min": 0.0, "max": 1.0},
                        colorA=panel.color_defaults[0],
                        colorB=panel.color_defaults[1],
                        file_path="",
                        scale=(panel.scalar_map.get(initial_scalar) or {}).get("scale", panel.dataset_scale or 1.0) or 1.0,
                        units=(panel.scalar_map.get(initial_scalar) or {}).get("units", panel.dataset_units),
                        palette="aqua-fire",
                    )
                    panel.initial_slider_max = 0
                    panel.initial_slider_disabled = True
                    panel.initial_heatmap_bundle = {"figure": go.Figure(), "colorbar": go.Figure(), "scaled_stats": {"min": 0.0, "max": 1.0}, "fig_width": 600}
                except Exception:
                    pass
            datasets.append((dataset["label"], panel))
    return tab_data


print(f"[{time.time()-_start_time:.2f}s] Initializing tab_datasets...")
tab_datasets = initialize_tab_datasets_static()
print(f"[{time.time()-_start_time:.2f}s] tab_datasets initialized")

comparison_panels = {}


# =============================================================================
# COMPARISON FEATURE - To be fully extracted in future dedicated refactoring
# =============================================================================
# The following ~30 comparison functions (~850 lines) remain in OPView.py.
# These functions handle the comparison tab functionality (uploading VTK files,
# grouping by prefix, rendering heatmap grids with synchronized controls).
#
# Future work: Extract to comparisonmgr/ module:
#   - Helper functions → comparisonmgr/helpers.py
#   - UI builders → comparisonmgr/ui_builder.py
#   - Callbacks → comparisonmgr/callbacks.py
#
# For now, these remain here as they're complex and interdependent. The
# ComparisonManager (comparisonmgr/manager.py) currently wraps these functions.
# =============================================================================

def _comparison_panel_id(group: str) -> str:
    safe = re.sub(r'[^a-z0-9]+', '-', group.lower()).strip('-')
    suffix = safe or 'group'
    return f"comparison-{suffix}"


def allowed_comparison_groups_for_tab(tab_id: str):
    """Return a set of filename prefixes that belong to the given module/tab."""
    if not tab_id:
        return set()
    groups = set()
    for tab in TAB_CONFIGS:
        if tab.get("id") != tab_id:
            continue
        for dataset in tab.get("datasets", []):
            glob_pat = dataset.get("file_glob") or ""
            base = Path(glob_pat).name
            stem = base.split(".")[0]
            stem = stem.split("*", 1)[0].rstrip("_")
            if stem:
                groups.add(stem.split("_", 1)[0])
        break
    return groups


def _comparison_entry_id(entry: dict) -> str:
    """Create a stable, unique panel id for a comparison entry.

    Uses the file basename plus a short hash of the absolute path to avoid collisions
    between similarly named files from different sources.
    """
    name = entry.get('name') or Path(entry.get('path') or '').name or 'file'
    safe_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'file'
    path_str = entry.get('path') or name
    digest = hashlib.md5(path_str.encode('utf-8')).hexdigest()[:8]
    return f"comparison-{safe_name}-{digest}"


def _comparison_group_name(file_name: str) -> str:
    return file_name.split('_', 1)[0] or file_name


def _group_comparison_files(file_names):
    grouped = {}
    for file_name in sorted(set(file_names or [])):
        group = _comparison_group_name(file_name)
        grouped.setdefault(group, []).append(file_name)
    return grouped


def list_vtk_files(directory=None):
    """Return sorted absolute file paths from the main VTK folder.

    Args:
        directory: Optional directory to scan. If None, checks if a project folder is selected.

    NOTE: Returns empty list at startup for speed. Scans when directory is provided or folder selected."""
    # Use app_context if available, otherwise fall back to legacy globals
    if app_context is not None:
        vtk_files = app_context.loaded_project_vtk_files
        vtk_path = app_context.current_project_vtk_path
    else:
        global current_project_vtk_path
        vtk_files = loaded_project_vtk_files
        vtk_path = current_project_vtk_path

    # If no directory specified, check if a project folder is selected
    if directory is None:
        # Multi-project mode: return union of loaded project files if present.
        if vtk_files:
            return sorted(set(vtk_files))
        if vtk_path and vtk_path.exists():
            directory = vtk_path
        else:
            # FAST STARTUP: Don't scan at import time
            return []

    # Scan the specified directory
    return _scan_vtk_dir(directory)


def _comparison_entries(comparison_file_names, selected_vtk_paths):
    """Build unified comparison entries from uploads and selected VTK paths."""
    entries = []
    seen = set()
    for name in (comparison_file_names or []):
        path = (comparison_data_dir() / name).resolve()
        if not path.exists():
            continue
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        entries.append({'name': name, 'path': key, 'source': 'comparison'})
    for p in (selected_vtk_paths or []):
        if not p:
            continue
        path = Path(p)
        if not path.is_absolute():
            path = resolve_vtk_path(p)
        path = path.resolve()
        if not path.exists():
            continue
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        entries.append({'name': path.name, 'path': key, 'source': 'vtk'})
    return entries


def _comparison_entries_from_selected(selected_paths):
    """Build entries for explicitly selected absolute/relative paths (VTK or Comparison)."""
    entries = []
    seen = set()
    comparison_root = comparison_data_dir().resolve()
    for p in (selected_paths or []):
        if not p:
            continue
        path = Path(p)
        if not path.is_absolute():
            path = resolve_vtk_path(p)
        path = path.resolve()
        if not path.exists():
            continue
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        source = 'comparison' if comparison_root in path.parents else 'vtk'
        entries.append({'name': path.name, 'path': key, 'source': source})
    return entries


def _group_comparison_entries(entries):
    grouped = {}
    for entry in entries or []:
        name = entry.get('name') or ''
        group = _comparison_group_name(name)
        grouped.setdefault(group, []).append(entry)
    return grouped


def _comparison_scalar_options(panels):
    """Return unique scalar dropdown options aggregated from all panels."""
    seen = set()
    options = []
    for panel_entry in panels.values():
        if not panel_entry:
            continue
        _, panel, _ = panel_entry
        for opt in panel.scalar_options:
            value = opt['value']
            if value in seen:
                continue
            seen.add(value)
            options.append(opt)
    return options


def _comparison_palette_options(panels):
    """Return palette dropdown options for comparison controls."""
    if not panels:
        # ViewerPanel is lazily imported; fall back to importing it here when needed.
        from viewer import ViewerPanel as VP
        return [{'label': key.replace('-', ' ').title(), 'value': key} for key in VP.PALETTES.keys()]
    _, panel, _ = next(iter(panels.values()))
    return panel.palette_options


def _parse_float(value):
    try:
        if value is None or value == '':
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_range(min_val, max_val):
    if min_val is None or max_val is None:
        return min_val, max_val
    lo, hi = sorted([min_val, max_val])
    return lo, hi


def _comparison_range_defaults(panels, scalar_key):
    """Return global min/max across all panels for the requested scalar."""
    mins = []
    maxs = []
    for _, panel_entry in panels.items():
        if not panel_entry:
            continue
        _, panel, file_path = panel_entry
        descriptor = panel.scalar_map.get(scalar_key)
        if not descriptor:
            continue
        try:
            reader = panel.reader_factory(file_path)
        except FileNotFoundError:
            continue
        try:
            state, _, _ = panel._build_state(reader, file_path, descriptor['value'], return_slice=True)
        except Exception:
            continue
        if state.range_min is not None:
            mins.append(state.range_min)
        if state.range_max is not None:
            maxs.append(state.range_max)
    if not mins or not maxs:
        return None, None
    return min(mins), max(maxs)


def _comparison_settings(panels, scalar_value=None, range_min=None, range_max=None,
                         palette_value=None, full_scale=False, slider_range=None):
    """Normalize comparison control inputs into a settings dict plus dropdown options."""
    scalar_options = _comparison_scalar_options(panels)
    palette_options = _comparison_palette_options(panels)
    scalar_values = {opt['value'] for opt in scalar_options}
    palette_values = {opt['value'] for opt in palette_options}
    default_scalar = next((opt['value'] for opt in scalar_options), None)
    default_palette = next((opt['value'] for opt in palette_options), 'aqua-fire')

    selected_scalar = scalar_value if scalar_value in scalar_values else default_scalar
    selected_palette = palette_value if palette_value in palette_values else default_palette

    parsed_min = _parse_float(range_min)
    parsed_max = _parse_float(range_max)
    slider_min = None
    slider_max = None
    if slider_range and isinstance(slider_range, (list, tuple)) and len(slider_range) == 2:
        try:
            slider_min = float(slider_range[0])
            slider_max = float(slider_range[1])
        except (TypeError, ValueError):
            slider_min = None
            slider_max = None
    # Treat the range inputs as the source of truth; only fall back to the slider
    # when inputs are empty/None. The slider itself updates the inputs via
    # `_update_comparison_range`, so this avoids "manual input ignored" bugs.
    if parsed_min is None and parsed_max is None and slider_min is not None and slider_max is not None:
        parsed_min = slider_min
        parsed_max = slider_max
    if selected_scalar and (parsed_min is None or parsed_max is None):
        fallback_min, fallback_max = _comparison_range_defaults(panels, selected_scalar)
        if parsed_min is None:
            parsed_min = fallback_min
        if parsed_max is None:
            parsed_max = fallback_max

    clamped_min, clamped_max = _clamp_range(parsed_min, parsed_max)

    settings = {
        'scalar': selected_scalar,
        'range_min': clamped_min,
        'range_max': clamped_max,
        'palette': selected_palette,
        'full_scale': bool(full_scale),
    }
    return settings, scalar_options, palette_options


def _comparison_dataset_config_from_entry(entry: dict):
    path = Path(entry.get('path') or '')
    if not path.exists():
        return None
    name = entry.get('name') or path.name
    config = {
        "id": _comparison_entry_id(entry),
        "label": name,
        "file": str(path),
        "files": [str(path)],
        "scalars": None,
        "enable_line_scan": True,
        "axis": 'y',
    }
    return config


def _manual_viewer_id(file_path: str) -> str:
    digest = hashlib.md5(file_path.encode('utf-8')).hexdigest()[:10]
    base = Path(file_path).name
    safe = re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-') or 'file'
    return f"manual-{safe}-{digest}"


def get_manual_panel(file_path: str):
    """Return a cached ViewerPanel for a single file path."""
    from viewer import ViewerPanel as VP

    if not file_path:
        return None
    path = Path(file_path)
    if not path.is_absolute():
        path = resolve_vtk_path(str(path))
    path = path.resolve()
    if not path.exists():
        return None
    key = str(path)
    panel = manual_panels_by_path.get(key)
    if panel is None:
        config = {
            "id": _manual_viewer_id(key),
            "label": path.name,
            "file": key,
            "files": [key],
            "scalars": None,
            "enable_line_scan": True,
            "axis": 'y',
        }
        try:
            panel = VP(app, get_reader, config)
        except (FileNotFoundError, ValueError):
            return None
        manual_panels_by_path[key] = panel
    return panel


def get_comparison_panels(entries):
    """Build/return ViewerPanels for comparison entries, keyed by absolute path."""
    # Import ViewerPanel when needed (lazy loading for fast startup)
    from viewer import ViewerPanel as VP

    panels = {}
    paths = sorted({e.get('path') for e in (entries or []) if e and e.get('path')})
    for path_str in paths:
        entry_dict = next((e for e in entries if e.get('path') == path_str), None)
        if not entry_dict:
            continue
        config = _comparison_dataset_config_from_entry(entry_dict)
        if not config:
            continue
        cache_key = path_str
        entry = comparison_panels.get(cache_key)
        panel = entry['panel'] if entry and entry['axis'] == config["axis"] else None
        if panel is None:
            try:
                panel = VP(app, get_reader, config)
            except (FileNotFoundError, ValueError):
                continue
            comparison_panels[cache_key] = {'axis': config["axis"], 'panel': panel}
        panels[cache_key] = (config["label"], panel, config["file"])
    return panels


def build_tab_children(tab_id):
    panels = tab_datasets[tab_id]["panels"]
    if not panels:
        return [html.Div("No datasets available for this tab.", className='dataset-empty')]
    cards = []

    # Add main viewer cards
    for label, panel in panels:
        # Main viewer card
        cards.append(html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(label, className='dataset-title')
            ], className='dataset-header'),
            html.Div(panel.build_layout(), className='dataset-body')
        ], className='dataset-block'))

        cards.append(panel.build_line_scan_card())
        # build_histogram_card() returns None (deprecated - now combined with line scan)
        histogram_card = panel.build_histogram_card()
        if histogram_card:
            cards.append(histogram_card)

    if tab_id == 'phase-field':
        # Phase-field tab: show size-details and grain distribution cards.
        for builder in (build_size_details_card, build_grain_distribution_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'mechanics':
        for builder in (build_stress_strain_card, build_stress_hist_card, build_strain_hist_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'plasticity':
        for builder in (build_crss_card, build_plastic_strain_card):
            card = builder()
            if card:
                cards.append(card)
    return [html.Div(cards, className='dataset-grid')]


def _comparison_graph_id(file_name: str, group: str):
    safe_file = re.sub(r'[^a-z0-9]+', '-', file_name.lower()).strip('-')
    # Use the raw group key consistently across controls, stores, and graphs.
    return {'type': 'comparison-graph', 'group': group, 'file': safe_file or 'file'}


def _comparison_heatmap_data(panel, entry: dict, settings):
    """Build comparison heatmap with grid caching for performance."""
    file_name = entry.get('name') or Path(entry.get('path') or '').name
    file_path = entry.get('path')
    scalar_value = settings.get('scalar')
    descriptor = panel.scalar_map.get(scalar_value) or panel.scalar_defs[0]

    # Create cache key for grid data (independent of range/palette/full_scale)
    slice_index = settings.get('slice_index')
    if slice_index is None:
        slice_index = 0
    else:
        try:
            slice_index = int(slice_index)
        except (TypeError, ValueError):
            slice_index = 0

    grid_cache_key = (file_path, scalar_value, slice_index)

    # Check if we have cached grid data
    data_min = None
    data_max = None
    if grid_cache_key in comparison_grid_cache_data:
        X_grid, Y_grid, Z_grid, stats, state_dict = comparison_grid_cache_data[grid_cache_key]
        # Reconstruct state from cached data and apply current settings
        try:
            reader = panel.reader_factory(file_path)
        except FileNotFoundError:
            return None

        from viewer.state import ViewerState
        state = ViewerState(**state_dict)
        try:
            scale = float(state_dict.get('scale') or 1.0)
            data_min = float(stats.get('min')) * scale if stats and 'min' in stats else state.range_min
            data_max = float(stats.get('max')) * scale if stats and 'max' in stats else state.range_max
        except Exception:
            data_min, data_max = state.range_min, state.range_max
    else:
        # First access: build state and cache the grid data
        try:
            reader = panel.reader_factory(file_path)
        except FileNotFoundError:
            return None
        try:
            state, slice_data, _ = panel._build_state(
                reader, file_path, descriptor['value'], return_slice=True
            )
        except Exception:
            return None

        data_min, data_max = state.range_min, state.range_max

        # Cache the grid data
        if 'slice_data' in locals() and slice_data:
            # slice_data is a tuple: (X_grid, Y_grid, Z_grid, stats)
            X_grid, Y_grid, Z_grid, stats = slice_data

            # Store state as dict for serialization
            state_dict = {
                'scalar_key': state.scalar_key,
                'scalar_label': state.scalar_label,
                'axis': state.axis,
                'slice_index': state.slice_index,
                'colorA': state.colorA,
                'colorB': state.colorB,
                'palette': state.palette,
                'threshold': state.threshold,
                'range_min': state.range_min,
                'range_max': state.range_max,
                'file_path': state.file_path,
                'scale': state.scale,
                'units': state.units,
                'colorscale_mode': state.colorscale_mode,
            }
            comparison_grid_cache_data[grid_cache_key] = (X_grid, Y_grid, Z_grid, stats, state_dict)

    # Apply current settings to state
    range_min = settings.get('range_min')
    range_max = settings.get('range_max')

    if range_min is not None:
        state.range_min = range_min
    if range_max is not None:
        state.range_max = range_max
    if state.range_min is not None and state.range_max is not None and state.range_min > state.range_max:
        state.range_min, state.range_max = sorted([state.range_min, state.range_max])
    if state.range_min is not None and state.range_max is not None:
        state.threshold = (state.range_min + state.range_max) / 2
    state.palette = settings.get('palette') or state.palette
    # Comparison "Full Scale" means snap to group-global range, not per-file dynamic scaling.
    state.colorscale_mode = 'normal'
    state.slice_index = max(0, slice_index)

    heatmap_bundle = panel._build_heatmap_figures(reader, state, file_path, slice_data=None)
    # Widen colorbar only for comparison panels.
    try:
        colorbar_fig = heatmap_bundle.get('colorbar')
        if colorbar_fig is not None:
            colorbar_fig.update_layout(width=140)
            colorbar_fig.update_traces(
                marker=dict(colorbar=dict(thickness=18, thicknessmode="pixels"))
            )
    except Exception:
        pass
    return heatmap_bundle


def build_comparison_heatmap_row(panels, entries, settings, group):
    """Return a single heatmap row for a comparison group."""
    ordered = [
        (entry, panels.get(entry.get('path')))
        for entry in (entries or [])
        if entry and entry.get('path') in panels
    ]
    if not ordered:
        return []
    graph_config = {
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': False,
        'toImageButtonOptions': {'scale': 4}
    }
    heatmap_children = [
        html.Div(
            html.Img(src='/assets/OP_Logo.png', className='heatmap-logo', alt='OP logo'),
            className='heatmap-logo-card comparison-heatmap-logo-card'
        )
    ]
    column_widths = ["70px"]
    colorbar_fig = None
    rendered = []
    full_scale_enabled = bool(settings.get('full_scale'))
    for entry, panel_entry in ordered:
        if not panel_entry:
            continue
        _, panel, _ = panel_entry
        heatmap_data = _comparison_heatmap_data(panel, entry, settings)
        if not heatmap_data:
            continue
        # Only use a shared colorbar when not in full-scale mode.
        if not full_scale_enabled and colorbar_fig is None:
            colorbar_fig = heatmap_data['colorbar']
        file_name = entry.get('name') or Path(entry.get('path') or '').name
        fig_width = heatmap_data.get('fig_width')
        if fig_width:
            column_widths.append(f"{int(fig_width)}px")
        else:
            column_widths.append("320px")
        rendered.append(entry)
        heatmap_children.append(html.Div(
            dcc.Graph(
                id=_comparison_graph_id(file_name, group),
                className='heatmap-main-graph comparison-heatmap-graph',
                figure=heatmap_data['figure'],
                config=graph_config
            ),
            className='heatmap-main-card comparison-heatmap-main-card'
        ))

    if colorbar_fig:
        heatmap_children.append(html.Div(
            dcc.Graph(
                className='heatmap-colorbar-graph comparison-heatmap-colorbar-graph',
                figure=colorbar_fig,
                config={'displayModeBar': False, 'displaylogo': False, 'responsive': False}
            ),
            className='heatmap-colorbar-card comparison-heatmap-colorbar-card',
            style={'width': '160px', 'height': '380px'}
        ))
        column_widths.append("160px")

    # Build a separate title row above the heatmaps.
    title_children = [
        html.Div(className='comparison-heatmap-title-spacer', style={'width': '70px'})
    ]
    for entry in rendered:
        file_name = entry.get('name') or Path(entry.get('path') or '').name
        title_children.append(
            html.Div(
                [
                    html.Span(file_name, className='comparison-heatmap-title-text'),
                    html.Button(
                        "×",
                        id={'type': 'comparison-remove-file', 'group': group, 'path': entry.get('path')},
                        n_clicks=0,
                        className='comparison-heatmap-remove',
                        title='Remove from comparison'
                    ),
                ],
                className='comparison-heatmap-title-cell',
                style={
                    'flex': '1 1 0',
                    'minWidth': '140px',
                    'padding': '0 4px',
                    'whiteSpace': 'nowrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'lineHeight': '1.2',
                }
            )
        )

    grid_template = " ".join(column_widths)
    return [html.Div(
        [
            html.Div(
                title_children,
                className='comparison-heatmap-title-row',
                style={'gridTemplateColumns': grid_template}
            ),
            html.Div(
                heatmap_children,
                className='comparison-heatmap-row heatmap-row',
                style={'gridTemplateColumns': grid_template}
            ),
        ],
        className='comparison-group-block'
    )]


# ===== SECTION 4: Build Comparison Content with Grouped Controls =====
def build_comparison_content(files, group_controls_by_group=None, group_selected_paths_by_group=None, allowed_groups=None):
    """Render the comparison tab body showing uploaded files, grouped by prefix.

    Args:
        files: List of comparison file names from Comparison folder.
        group_controls_by_group: Optional dict {group: stored_controls}.
        group_selected_paths_by_group: Optional dict {group: [vtk_paths]} selected from VTK folder.
        allowed_groups: Optional set/list of group prefixes to show.
    """
    group_selected_paths_by_group = group_selected_paths_by_group or {}

    # Available entries for building pickers (all VTK + all Comparison files).
    available_entries = _comparison_entries(files, list_vtk_files())
    grouped_available = _group_comparison_entries(available_entries)
    if allowed_groups:
        allowed_set = set(allowed_groups)
        grouped_available = {g: v for g, v in grouped_available.items() if g in allowed_set}

    # Selected entries for rendering (only what user picked).
    selected_paths_all = []
    for paths in group_selected_paths_by_group.values():
        selected_paths_all.extend(paths or [])
    selected_entries = _comparison_entries_from_selected(selected_paths_all)

    panels = get_comparison_panels(selected_entries)
    if not grouped_available:
        return [html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3('Comparison Files', className='dataset-title')
            ], className='dataset-header'),
            html.Div(
                "No comparison files uploaded yet. Switch to Comparison tab and use \"Add VTK File\".",
                className='comparison-empty'
            )
        ], className='dataset-block comparison-card')]

    cards = []

    stored_controls_by_group = group_controls_by_group or {}

    for group, available_group_entries in grouped_available.items():
        selected_paths = group_selected_paths_by_group.get(group) or []
        selected_group_entries = [
            e for e in selected_entries
            if e.get('path') in set(selected_paths)
        ]
        panels_for_group = {
            entry.get('path'): panels.get(entry.get('path'))
            for entry in selected_group_entries
            if entry and entry.get('path') in panels
        }

        # Lazy behavior: do NOT load/read any VTK files until the user selects at least one file.
        panels_for_settings = panels_for_group

        def _label_for_entry(e):
            name = e.get('name') or Path(e.get('path') or '').name
            if e.get('source') == 'comparison':
                return f"{name} (Comparison)"
            # VTK entry: prefix label with project folder if possible.
            p = Path(e.get('path') or '')
            parts = list(p.parts)
            proj = None
            for idx, part in enumerate(parts):
                if part.lower() == 'vtk' and idx > 0:
                    proj = parts[idx - 1]
                    break
            return f"{proj}/{name}" if proj else name

        group_options = [{'label': _label_for_entry(e), 'value': e['path']} for e in available_group_entries]

        stored = stored_controls_by_group.get(group) or {}

        has_selection = bool(panels_for_settings)
        settings, scalar_options, palette_options = _comparison_settings(
            panels_for_settings,
            scalar_value=stored.get('scalar') if has_selection else None,
            range_min=stored.get('range_min') if has_selection else None,
            range_max=stored.get('range_max') if has_selection else None,
            palette_value=stored.get('palette'),
            full_scale=stored.get('full_scale', False) if has_selection else False,
            slider_range=stored.get('slider_range') if has_selection else None,
        )
        slider_min_default, slider_max_default = _comparison_range_defaults(panels_for_settings, settings['scalar'])
        if slider_min_default is None or slider_max_default is None:
            slider_min_default, slider_max_default = 0.0, 1.0
        slider_value_min = settings['range_min'] if settings['range_min'] is not None else slider_min_default
        slider_value_max = settings['range_max'] if settings['range_max'] is not None else slider_max_default

        controls_layout = html.Div([
            html.Div([
                html.Label([
                    html.Span("S", className="label-icon"),
                    "Field"
                ], className='field-label grid-label'),
                dcc.Dropdown(
                    id={'type': 'comparison-heatmap-field', 'group': group},
                    options=scalar_options,
                    value=settings['scalar'],
                    clearable=False,
                    searchable=False,
                    disabled=not has_selection,
                    placeholder="Select files first…" if not has_selection else None,
                    className='dropdown-wrapper'
                ),
                html.Label("Files", className='field-label grid-label'),
                dcc.Dropdown(
                    id={'type': 'comparison-vtk-picker', 'group': group},
                    options=group_options,
                    value=selected_paths,
                    multi=True,
                    placeholder=f"Pick {group} files from VTK/",
                    clearable=True,
                    searchable=False,
                    className='dropdown-wrapper comparison-file-picker'
                ),
                html.Label([
                    html.Img(src='/assets/color-scale.png', className="label-img"),
                    "Palette"
                ], className='field-label grid-label'),
                dcc.Dropdown(
                    id={'type': 'comparison-heatmap-palette', 'group': group},
                    options=palette_options,
                    value=settings['palette'],
                    clearable=False,
                    searchable=False,
                    className='dropdown-wrapper'
                )
            ], className='comparison-control-row comparison-palette-group'),

            html.Div([
                html.Label([
                    html.Img(src='/assets/bar-chart.png', className="label-img"),
                    "Range"
                ], className='field-label grid-label'),
                html.Div([
                dcc.Input(
                    id={'type': 'comparison-heatmap-range-min', 'group': group},
                    type='number',
                    value=settings['range_min'],
                    step='any',
                    placeholder='Min',
                    disabled=not has_selection,
                    className='comparison-range-input'
                ),
                dcc.Input(
                    id={'type': 'comparison-heatmap-range-max', 'group': group},
                    type='number',
                    value=settings['range_max'],
                    step='any',
                    placeholder='Max',
                    disabled=not has_selection,
                    className='comparison-range-input'
                ),
                html.Button(
                    html.Img(src='/assets/Reset.png', alt='Reset range', className='btn-icon'),
                    id={'type': 'comparison-heatmap-reset', 'group': group},
                    n_clicks=0,
                    className='btn btn-danger reset-btn',
                    title='Reset range',
                    disabled=not has_selection
                )
            ], className='comparison-range-row'),

                html.Div([
                    dcc.RangeSlider(
                        id={'type': 'comparison-heatmap-range-slider', 'group': group},
                        min=slider_min_default,
                        max=slider_max_default,
                        value=[slider_value_min, slider_value_max],
                        marks=None,
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": True},
                        # Reuse main-tab styling for a consistent look.
                        className='range-slider-dual comparison-range-slider',
                        disabled=not has_selection
                    )
                ], className='comparison-range-slider-row'),
                html.Div(
                    dmc.Switch(
                        id={'type': 'comparison-heatmap-full-scale', 'group': group},
                        label="Full Scale",
                        checked=settings['full_scale'],
                        labelPosition="right",
                        size="xs",
                        radius="xs",
                        color="#c50623",
                        withThumbIndicator=True,
                        disabled=not has_selection,
                    ),
                    className='scan-option scan-option--inline'
                )

            ], className='comparison-control-row comparison-range-group'),
        ], className='comparison-controls-grid')

        range_selector_store = dcc.Store(
            id={'type': 'comparison-range-selection', 'group': group},
            data={'click_count': 0, 'first_click': None},
            storage_type='session',
        )

        group_selected_store = dcc.Store(
            id={'type': 'comparison-selected-files-store', 'group': group},
            data=selected_paths,
            storage_type='session',
        )

        group_controls_store = dcc.Store(
            id={'type': 'comparison-controls-store', 'group': group},
            data={
                'scalar': settings['scalar'],
                'range_min': settings['range_min'],
                'range_max': settings['range_max'],
                'palette': settings['palette'],
                'full_scale': settings['full_scale'],
                'slider_range': [slider_value_min, slider_value_max],
            },
            storage_type='session',
        )

        heatmap_sections = []
        if panels_for_group:
            heatmap_sections = build_comparison_heatmap_row(panels_for_group, selected_group_entries, settings, group)
        comparison_block = html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(f'Comparison: {group}', className='dataset-title')
            ], className='dataset-header'),
            html.Div([
                controls_layout,
                range_selector_store,
                group_selected_store,
                group_controls_store,
                html.Div(heatmap_sections, id={'type': 'comparison-heatmap-rows', 'group': group}, className='comparison-heatmap-area-inner')
            ], className='comparison-heatmap-area')
        ], className='dataset-block comparison-card comparison-heatmap-panel')

        cards.append(comparison_block)

    return [html.Div(cards, className='comparison-root')]
# ===== END SECTION 4 =====


@app.callback(
    Output({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
    Output({'type': 'comparison-vtk-picker', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-vtk-picker', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-remove-file', 'group': MATCH, 'path': ALL}, 'n_clicks'),
    State({'type': 'comparison-remove-file', 'group': MATCH, 'path': ALL}, 'id'),
    State({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
    prevent_initial_call=True
)
def _update_comparison_selected_files(selected_values, remove_clicks, remove_ids, current_selected):
    """Persist selected VTK/Comparison files per group and handle remove buttons."""
    triggered = ctx.triggered_id
    # Picker change wins.
    if isinstance(triggered, dict) and triggered.get('type') == 'comparison-vtk-picker':
        picked = selected_values or []
        # Since we clear the dropdown display, Dash may only report the newly picked item(s).
        # Merge with existing selection to preserve multi-select behavior.
        values = list(current_selected or [])
        for p in picked:
            if p not in values:
                values.append(p)
        return values, []
    # Remove button clicked.
    if isinstance(triggered, dict) and triggered.get('type') == 'comparison-remove-file':
        # Ignore spurious triggers from layout re-rendering (n_clicks == 0/None).
        triggered_value = ctx.triggered[0].get('value') if ctx.triggered else None
        if not triggered_value:
            raise PreventUpdate
        path = triggered.get('path')
        values = list(current_selected or [])
        if path in values:
            values.remove(path)
        return values, []
    raise PreventUpdate


def _make_comparison_cache_key(files, field, range_min, range_max, palette, full_scale, slider_range):
    """Deprecated: cache key helper (unused)."""
    files_tuple = tuple(sorted(files)) if files else ()
    slider_tuple = tuple(slider_range) if slider_range else ()
    return (files_tuple, field, range_min, range_max, palette, full_scale, slider_tuple)


@app.callback(
    Output({'type': 'comparison-heatmap-rows', 'group': MATCH}, 'children'),
    Input({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'checked'),
    State({'type': 'comparison-heatmap-rows', 'group': MATCH}, 'id'),
    State('comparison-files-store', 'data'),
    State({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
)
def _update_comparison_heatmaps(field, range_min, range_max, palette, full_scale, rows_id, files, selected_paths):
    """Update heatmaps for a single comparison group."""
    group = rows_id.get('group') if isinstance(rows_id, dict) else None
    group_entries = _comparison_entries_from_selected(selected_paths)
    panels = get_comparison_panels(group_entries)
    panels_for_group = {
        entry.get('path'): panels.get(entry.get('path'))
        for entry in group_entries
        if entry and entry.get('path') in panels
    }
    if not panels_for_group:
        return []

    settings, _, _ = _comparison_settings(
        panels_for_group, field, range_min, range_max, palette, full_scale
    )
    return build_comparison_heatmap_row(panels_for_group, group_entries, settings, group)


@app.callback(
    Output({'type': 'comparison-heatmap-field', 'group': MATCH}, 'options'),
    Output({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
    Output({'type': 'comparison-heatmap-field', 'group': MATCH}, 'disabled'),
    Output({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'options'),
    Output({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'value'),
    Output({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'disabled'),
    Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
    State({'type': 'comparison-controls-store', 'group': MATCH}, 'data'),
)
def _sync_comparison_control_options(selected_paths, stored_controls):
    """Lazy-load comparison control options only after user selects files."""
    group_entries = _comparison_entries_from_selected(selected_paths)
    panels = get_comparison_panels(group_entries)
    panels_for_group = {
        entry.get('path'): panels.get(entry.get('path'))
        for entry in group_entries
        if entry and entry.get('path') in panels
    }

    has_selection = bool(panels_for_group)
    stored = stored_controls or {}
    settings, scalar_options, palette_options = _comparison_settings(
        panels_for_group,
        scalar_value=stored.get('scalar') if has_selection else None,
        range_min=stored.get('range_min') if has_selection else None,
        range_max=stored.get('range_max') if has_selection else None,
        palette_value=stored.get('palette'),
        full_scale=stored.get('full_scale', False) if has_selection else False,
        slider_range=stored.get('slider_range') if has_selection else None,
    )

    return (
        scalar_options or [],
        settings.get('scalar'),
        not has_selection,
        palette_options or [],
        settings.get('palette'),
        not has_selection,
    )


@app.callback(
    Output({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'disabled'),
    Output({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'disabled'),
    Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'disabled'),
    Output({'type': 'comparison-heatmap-reset', 'group': MATCH}, 'disabled'),
    Output({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'disabled'),
    Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
)
def _toggle_comparison_range_controls(selected_paths):
    """Enable range controls only when this group has a selection."""
    has_selection = bool(_comparison_entries_from_selected(selected_paths))
    disabled = not has_selection
    return disabled, disabled, disabled, disabled, disabled


@app.callback(
    Output({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
    Output({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
    Output({'type': 'comparison-range-selection', 'group': MATCH}, 'data'),
    Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'value'),
    Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'min'),
    Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'max'),
    Output({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'checked'),
    Input({'type': 'comparison-heatmap-reset', 'group': MATCH}, 'n_clicks'),
    Input({'type': 'comparison-graph', 'group': MATCH, 'file': ALL}, 'clickData'),
    Input({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
    State({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
    State({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
    State({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
    State('comparison-files-store', 'data'),
    State({'type': 'comparison-range-selection', 'group': MATCH}, 'data'),
    State({'type': 'comparison-heatmap-rows', 'group': MATCH}, 'id'),
    prevent_initial_call=True
)
def _update_comparison_range(reset_clicks, clicks, slider_values, selected_paths, input_min, input_max, field, files, store_data, rows_id):
    group = rows_id.get('group') if isinstance(rows_id, dict) else None
    group_entries = _comparison_entries_from_selected(selected_paths)
    panels = get_comparison_panels(group_entries)
    panels_for_group = {
        entry.get('path'): panels.get(entry.get('path'))
        for entry in group_entries
        if entry and entry.get('path') in panels
    }
    default_lo, default_hi = (None, None)
    if panels_for_group and field:
        default_lo, default_hi = _comparison_range_defaults(panels_for_group, field)

    triggered = ctx.triggered_id
    if isinstance(triggered, dict) and triggered.get('type') == 'comparison-selected-files-store':
        if not panels_for_group:
            raise PreventUpdate
        min_val, max_val = _comparison_range_defaults(panels_for_group, field)
        if min_val is None or max_val is None:
            raise PreventUpdate
        return (
            min_val,
            max_val,
            {'click_count': 0, 'first_click': None},
            [min_val, max_val],
            min_val,
            max_val,
            False,
        )
    if isinstance(triggered, dict) and triggered.get('type') == 'comparison-heatmap-reset':
        if not panels_for_group:
            raise PreventUpdate
        min_val, max_val = _comparison_range_defaults(panels_for_group, field)
        if min_val is None or max_val is None:
            raise PreventUpdate
        return (
            min_val,
            max_val,
            {'click_count': 0, 'first_click': None},
            [min_val, max_val],
            min_val,
            max_val,
            False,
        )

    if isinstance(triggered, dict) and triggered.get('type') == 'comparison-graph':
        triggered_value = ctx.triggered[0].get('value') if ctx.triggered else None
        click_data = triggered_value if triggered_value and 'points' in triggered_value else None
        if not click_data:
            click_list = clicks or []
            for cd in click_list:
                if cd and 'points' in cd and cd['points']:
                    click_data = cd
                    break
        if not click_data or 'points' not in click_data or not click_data['points']:
            raise PreventUpdate
        try:
            point = click_data['points'][0]
        except (IndexError, KeyError):
            raise PreventUpdate
        z_val = point.get('z')
        if z_val is None:
            raise PreventUpdate
        try:
            z_val = float(z_val)
        except (TypeError, ValueError):
            raise PreventUpdate
        store = store_data or {'click_count': 0, 'first_click': None}
        click_count = store.get('click_count', 0)
        first_click = store.get('first_click')
        if click_count == 0 or first_click is None:
            current_lo = input_min if input_min is not None else default_lo
            current_hi = input_max if input_max is not None else default_hi
            return (
                current_lo,
                current_hi,
                {'click_count': 1, 'first_click': z_val},
                [current_lo, current_hi],
                default_lo if default_lo is not None else current_lo,
                default_hi if default_hi is not None else current_hi,
                False,
            )
        lo, hi = sorted([first_click, z_val])
        return (
            lo,
            hi,
            {'click_count': 0, 'first_click': None},
            [lo, hi],
            default_lo if default_lo is not None else lo,
            default_hi if default_hi is not None else hi,
            False,
        )

    if triggered == {'type': 'comparison-heatmap-range-slider', 'group': group}:
        if not slider_values or len(slider_values) != 2:
            raise PreventUpdate
        try:
            lo = float(slider_values[0])
            hi = float(slider_values[1])
        except (TypeError, ValueError):
            raise PreventUpdate
        lo, hi = sorted([lo, hi])
        return (
            lo,
            hi,
            {'click_count': 0, 'first_click': None},
            [lo, hi],
            default_lo if default_lo is not None else lo,
            default_hi if default_hi is not None else hi,
            False,
        )

    raise PreventUpdate


@app.callback(
    Output({'type': 'comparison-controls-store', 'group': MATCH}, 'data'),
    Input({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'value'),
    Input({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'checked'),
    Input({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'value'),
    prevent_initial_call=True
)
def _save_comparison_group_controls(field, range_min, range_max, palette, full_scale, slider_range):
    """Persist control values per comparison group."""
    return {
        'scalar': field,
        'range_min': range_min,
        'range_max': range_max,
        'palette': palette,
        'full_scale': bool(full_scale),
        'slider_range': slider_range,
    }


TAB_ORDER = [tab['id'] for tab in TAB_CONFIGS]


def get_default_active_tab():
    for tab_id in TAB_ORDER:
        if tab_datasets.get(tab_id, {}).get("panels"):
            return tab_id
    return TAB_ORDER[0] if TAB_ORDER else None


def build_tab_bar():
    icons = {
        "phase-field": "⛶",
        "composition": "⚛",
        "mechanics": "⚙",
        "plasticity": "🧪",
    }
    return [
        html.Button(
            [
                html.Span(icons.get(tab_id, "•"), className="tab-icon"),
                html.Span(
                    tab_datasets.get(tab_id, {}).get("label", tab_id.title()),
                    className="tab-label"
                ),
            ],
            id={'type': 'tab-button', 'tab': tab_id},
            n_clicks=0,
            className='custom-tab'
        )
        for tab_id in TAB_ORDER
    ]


INITIAL_ACTIVE_TAB = get_default_active_tab()

# Scan for project folders at startup (before layout creation)
print(f"[{time.time()-_start_time:.2f}s] Scanning for project folders...")
discovered_project_folders = scan_project_folders()
print(f"[{time.time()-_start_time:.2f}s] Found {len(discovered_project_folders)} project folder(s)")

# Initialize OOP data sources (before card builders)
data_dir = Path('TextData')
grain_data = GrainSizeData(data_dir)
stress_strain_data = StressStrainData(data_dir)
stress_data = StressData(data_dir)
strain_data = StrainData(data_dir)
crss_data = CRSSData(data_dir)

# Load data
grain_data.load()
stress_strain_data.load()
stress_data.load()
strain_data.load()
crss_data.load()


# =============================================================================
# UI CARD BUILDERS - To be extracted to ui/ui_manager.py in future
# =============================================================================
# The following UI card builder functions (~500 lines) remain in OPView.py:
#   - build_tab_bar() - Main tab navigation bar
#   - build_tab_children() - Tab content builder
#   - build_size_details_card() - Grain size details card
#   - build_grain_distribution_card() - Grain distribution histogram card
#   - build_stress_strain_card() - Stress-strain curve card
#   - build_stress_hist_card() - Stress histogram card
#   - build_strain_hist_card() - Strain histogram card
#   - build_crss_card() - CRSS analysis card
#   - build_crss_hist_card() - CRSS histogram card
#   - build_plastic_strain_card() - Plastic strain card
#
# Future extraction plan:
#   1. Create ui/ui_manager.py with UIManager class
#   2. Move all build_* functions as methods
#   3. Inject data sources via constructor
#   4. Update references in layout and callbacks
# =============================================================================


def build_size_details_card():
    """Build size details card using OOP structure"""
    if not grain_data.is_available:
        return None

    # Get time steps from OOP data source
    times = grain_data.get_time_steps()
    if not times:
        return None

    time_options = []
    for t in times:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        time_options.append({'label': label, 'value': str(t)})

    # Get grain labels from OOP data source
    value_labels = grain_data._data.get('labels', [])
    if not value_labels:
        return None
    default_time = time_options[0]['value'] if time_options else None

    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Grain Details', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Div([
                    html.Label('Time Step', className='textdata-label'),
                    dcc.Dropdown(
                        id='size-card-time',
                        options=time_options,
                        value=default_time,
                        clearable=False,
                        searchable=False,
                        className='textdata-input'
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Chart Style', className='textdata-label'),
                    dcc.RadioItems(
                        id='size-card-mode',
                        options=[
                            {'label': 'Bar', 'value': 'bar'},
                            {'label': 'Line', 'value': 'line'}
                        ],
                        value='bar',
                        inline=True,
                        className='textdata-radio',
                        labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                        inputStyle={'marginRight': '4px'}
                    )
                ], className='textdata-control'),
            ], className='textdata-controls'),
            dcc.Graph(id='size-card-main', className='textdata-plot'),
            dcc.Graph(id='size-card-line', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_grain_distribution_card():
    """Build grain distribution card using OOP structure"""
    if not grain_data.is_available:
        return None

    # Get time steps from OOP data source
    times = grain_data.get_time_steps()
    if not times:
        return None

    time_options = []
    for t in times:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        time_options.append({'label': label, 'value': str(t)})

    default_time = time_options[0]['value']
    default_time_val = float(default_time)
    default_bins = 15

    # Use legacy function for histogram (grain uses time-based, not component-based)
    default_fig, default_summary = build_grain_histogram(
        time_value=default_time_val,
        bins=default_bins,
        fit=False
    )
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Grain Distribution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Div([
                    html.Label('Time Step', className='textdata-label'),
                    dcc.Dropdown(
                        id='grain-dist-time',
                        options=time_options,
                        value=default_time,
                        clearable=False,
                        searchable=False,
                        className='textdata-input'
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Number of Bins', className='textdata-label'),
                    dcc.Slider(
                        id='grain-dist-bins',
                        min=5,
                        max=50,
                        step=5,
                        value=default_bins,
                        marks={10: '10', 25: '25', 40: '40'},
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Analysis', className='textdata-label'),
                    dcc.Checklist(
                        id='grain-dist-fit',
                        options=[{'label': 'Show Best-fit PDF', 'value': 'fit'}],
                        value=[],
                        className='hist-toggle'
                    )
                ], className='textdata-control')
            ], className='textdata-controls'),
            dcc.Graph(id='grain-dist-fig', figure=default_fig, className='textdata-plot')
        ], className='textdata-graphs'),
        dcc.Markdown(default_summary, id='grain-dist-summary', className='hist-summary', mathjax=True)
    ], className='dataset-block textdata-card')


def build_stress_strain_card():
    """Build stress-strain card using OOP structure"""
    if not stress_strain_data.is_available:
        return None

    # Use new OOP data source to get options
    options = [
        {'label': 'σ_xx', 'value': 'Sigma_xx'},
        {'label': 'σ_yy', 'value': 'Sigma_yy'},
        {'label': 'σ_zz', 'value': 'Sigma_zz'},
        {'label': 'von Mises', 'value': 'Mises'},
    ]
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Stress–Strain Curves', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
        html.Div([
            html.Div([
                html.Label('Components', className='textdata-label'),
                dcc.Checklist(
                    id='stress-components',
                    options=options,
                    value=stress_strain_data.get_default_components(),
                    className='textdata-radio',
                    labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                    inputStyle={'marginRight': '4px'}
                )
            ], className='textdata-control')
        ], className='textdata-controls'),
            dcc.Graph(id='stress-strain-fig', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_stress_hist_card():
    """Legacy PDF-based stress histogram card – hidden from UI."""
    return None


def build_strain_hist_card():
    """Legacy PDF-based strain histogram card – hidden from UI."""
    return None


def build_crss_card():
    """Build CRSS card using OOP structure"""
    if not crss_data.is_available:
        return None

    # Use OOP data source to get options
    options = crss_data.get_component_options()
    default_components = crss_data.get_default_components()
    fig = crss_data.build_figure(default_components)

    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('CRSS Evolution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
        html.Div([
            html.Div([
                html.Label('Components', className='textdata-label'),
                dcc.Checklist(
                    id='crss-component-select',
                    options=options,
                    value=default_components,
                    className='crss-checklist'
                )
            ], className='textdata-control crss-control')
        ], className='textdata-controls'),
            dcc.Graph(id='crss-avg-fig', figure=fig, className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


# =============================================================================
# LEGACY FUNCTIONS - Replaced by OOP data sources
# =============================================================================
# The following functions are no longer used. They have been replaced by:
# - crss_data.build_figure() for building CRSS charts
# - crss_data.get_histogram_data() for histogram generation
# Keeping for reference during migration period.
# =============================================================================

def build_crss_hist_card():
    """LEGACY - Incomplete function, not used. Use build_crss_card() instead."""
    data = get_legacy_data('crss')
    if not data:
        return None
    series = data.get('series') or {}
    # NOTE: This function was never completed


def build_crss_figure(selected=None):
    """LEGACY - Replaced by crss_data.build_figure()"""
    data = get_legacy_data('crss')
    if not data:
        return go.Figure()
    times = data['times']
    series = data.get('series') or {}
    available = {'Average'}
    available.update({name for name, values in series.items() if values})
    if not selected:
        selected = ['Average']
    filtered = [key for key in selected if key in available]
    if not filtered:
        filtered = ['Average'] if 'Average' in available else list(available)
    selected = filtered
    traces = []
    for key in selected:
        if key == 'Average':
            values = data['averages']
            label = 'Average'
        else:
            values = series.get(key)
            label = key.replace('ss_', 'SS ').upper()
        if not values:
            continue
        traces.append(go.Scatter(
            x=times,
            y=np.array(values) / 1e6,
            mode='lines',
            line=dict(width=2),
            name=label
        ))
    fig = go.Figure(data=traces)
    fig.update_layout(
        margin=dict(l=50, r=30, t=70, b=60),
        height=320,
        template='plotly_white',
        legend=dict(
            orientation='h',
            x=0,
            xanchor='left',
            y=1.18,
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(24,53,104,0.15)',
            borderwidth=1
        )
    )
    fig.update_xaxes(
        title="Time",
        title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
    )
    fig.update_yaxes(
        title="CRSS (MPa)",
        title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
    )
    return fig


def build_plastic_strain_card():
    """Build plastic strain card.

    Uses get_legacy_data() to access plastic strain data.
    """
    data = get_legacy_data('plastic_strain')
    if not data:
        return None
    strain_fig, rate_fig = build_plastic_strain_figures()
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Plastic Strain Insights', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            dcc.Graph(id='plastic-strain-eps', figure=strain_fig, className='textdata-plot'),
            dcc.Graph(id='plastic-strain-rate', figure=rate_fig, className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_plastic_strain_figures():
    """LEGACY - Helper for build_plastic_strain_card()"""
    data = get_legacy_data('plastic_strain')
    times = data['times']
    eps = data['epsilons']
    rates = data['rates']
    strain_traces = []
    for name, values in sorted(eps.items()):
        display = name.replace('_', ' ').title()
        strain_traces.append(go.Scatter(
            x=times,
            y=values,
            mode='lines',
            line=dict(width=2),
            name=display
        ))
    rate_traces = []
    for name, values in sorted(rates.items()):
        display = name.replace('_', ' ').title()
        rate_traces.append(go.Scatter(
            x=times,
            y=values,
            mode='lines',
            line=dict(width=2),
            name=display
        ))
    strain_fig = go.Figure(data=strain_traces)
    strain_fig.update_layout(
        margin=dict(l=50, r=30, t=40, b=60),
        height=320,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.3)
    )
    rate_fig = go.Figure(data=rate_traces)
    rate_fig.update_layout(
        margin=dict(l=50, r=30, t=40, b=60),
        height=320,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.3)
    )
    for fig, y_title in ((strain_fig, "Strain"), (rate_fig, "Strain Rate")):
        fig.update_xaxes(
            title="Time",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title=y_title,
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
    return strain_fig, rate_fig


print(f"[{time.time()-_start_time:.2f}s] Building app layout...")
app.layout = dmc.MantineProvider(
    html.Div(
        id='app-container',
        children=[
            dcc.Store(id='active-tab', data=INITIAL_ACTIVE_TAB),
            dcc.Store(id='comparison-files-store', data=list_comparison_files()),
            dcc.Store(id='loaded-project-folders', data=[], storage_type='session'),
            dcc.Store(id='selected-project-folder', data=None, storage_type='session'),
            dcc.Store(id='projects-store', data={'names': [], 'active': None, 'files_by_project': {}}, storage_type='session'),
            dcc.Location(id='url', refresh=False),
            html.Div([
                html.Div([
                    html.Div([
                        html.Img(src='/assets/OP_Logo_main.png', className='app-logo', alt='OP logo'),
                        html.H1([
                            "OPV",
                            html.Span("iew", className='app-title-sub'),
                        ], className='app-title')
                    ], className='top-left'),
                    html.Div([
                        html.A("Documentation", href='/docs', target='_blank', className='doc-link')
                    ], className='top-right')
            ], className='top-bar')
        ], className='app-header'),

        html.Div([
            html.Div([
                html.Div([
                         html.Span(DEFAULT_VTK_FOLDER_LABEL, className='vtk-folder-badge'),
                         html.Span("Add Projects", className='vtk-folder-heading-text')
                    ], className='vtk-folder-heading'),

                     html.Div([
                        html.Label("Projects:", className='project-folder-label', style={'marginRight': '8px'}),
                        dcc.Dropdown(
                            id='project-folder-dropdown',
                            options=get_project_folder_options(discovered_project_folders),
                            placeholder="Load project folder(s)…",
                            clearable=True,
                            multi=True,
                            searchable=False,
                            className='project-folder-dropdown',
                            style={'minWidth': '320px'}
                        ),
                     ], style={'display': 'flex', 'alignItems': 'center' })
            ], className='vtk-folder-row'),
                

            html.Div([
                html.Div([
                         html.Span(DEFAULT_VTK_FOLDER_LABEL, className='vtk-folder-badge'),
                         html.Span("Tabs", className='vtk-folder-heading-text')
                ], className='vtk-folder-heading'),
                dcc.Tabs(
                    id='vtk-folder-tabs',
                    value='current',
                    className='vtk-tabs',
                    children=[
                    dcc.Tab(
                        label=DEFAULT_VTK_FOLDER_LABEL,
                        value='current',
                        className='vtk-tab',
                        selected_className='vtk-tab--selected'
                    ),
                    dcc.Tab(
                        label='Comparison',
                        value='comparison',
                        className='vtk-tab',
                        selected_className='vtk-tab--selected'
                    )
                    ]
                ),
                html.Div(id='vtk-folder-actions', className='vtk-folder-actions'),
                html.Div(id='vtk-upload-feedback', className='vtk-upload-feedback')

            ], className='vtk-folder-row')

        ], className='vtk-folder-section'),

## -------------------------------------------------------------------------------
            html.Div([
                html.Div([
                    html.Span("Modules", className='sidebar-title'),
                    html.Div(build_tab_bar(), className='sidebar-tabs')
                ], className='sidebar'),
                html.Div([
                    html.Div(
                        id='tab-content',
                        children=build_tab_children(INITIAL_ACTIVE_TAB) if INITIAL_ACTIVE_TAB else []
                    ),
                    html.Div(
                        id='comparison-content',
                        children=build_comparison_content(
                            list_comparison_files(),
                            {},
                            {},
                            allowed_comparison_groups_for_tab(INITIAL_ACTIVE_TAB)
                        ),
                        style={'display': 'none'}
                    ),
                ], className='main-panel')
            ], className='layout-shell')
        ]
    )
)
print(f"[{time.time()-_start_time:.2f}s] App layout built")


@app.callback(
    Output('vtk-upload-feedback', 'children'),
    Output('comparison-files-store', 'data'),
    Input('vtk-file-upload', 'contents'),
    State('vtk-file-upload', 'filename'),
    State('comparison-files-store', 'data'),
    State('vtk-folder-tabs', 'value'),
    prevent_initial_call=True
)
def handle_vtk_upload(contents, filename, stored_files, active_folder):
    """Save an uploaded VTK file into the comparison directory."""
    if active_folder != 'comparison':
        raise PreventUpdate
    if not contents or not filename:
        raise PreventUpdate
    if not filename.lower().endswith(ALLOWED_VTK_EXTENSIONS):
        return (
            html.Div(
                "Only VTK files (.vtk/.vti/.vtp/.vtr/.vts) are supported.",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    try:
        _, encoded = contents.split(',', 1)
    except ValueError:
        return (
            html.Div(
                "Unable to parse the uploaded file.",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    try:
        payload = base64.b64decode(encoded)
    except Exception:
        return (
            html.Div(
                "Uploaded data could not be decoded.",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    target_dir = comparison_data_dir()
    target_path = target_dir / Path(filename).name
    reader_cache.pop(str(target_path), None)
    try:
        target_path.write_bytes(payload)
    except OSError as exc:
        return (
            html.Div(
                f"Failed to save {target_path.name}: {exc}",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    return (
        html.Div(
            f"Saved {target_path.name} to {target_dir}",
            className='vtk-upload-feedback vtk-upload-feedback--success'
        ),
        list_comparison_files()
    )


def _comparison_upload():
    """Return the upload button for the Comparison tab."""
    return dcc.Upload(
        id='vtk-file-upload',
        accept='.vtk,.vti,.vtp,.vtr,.vts',
        multiple=False,
        className='vtk-file-upload',
        children=html.Span("Add VTK File", className='vtk-file-upload__text')
    )


@app.callback(
    Output('vtk-folder-actions', 'children'),
    Input('vtk-folder-tabs', 'value')
)
def update_folder_actions(active_tab):
    if active_tab == 'comparison':
        return _comparison_upload()
    return None


@app.callback(
    Output('loaded-project-folders', 'data'),
    Output('selected-project-folder', 'data'),
    Output('vtk-upload-feedback', 'children', allow_duplicate=True),
    Output('projects-store', 'data'),
    Input('project-folder-dropdown', 'value'),
    State('active-tab', 'data'),
    prevent_initial_call=True
)
def handle_project_folder_selection(selected_folders, active_tab):
    """Handle project folder selection for multi-project browsing.

    - `project-folder-dropdown` loads one or more project folders.
    - Comparison can pick files from any loaded project without clearing selections.
    """
    # Use app_context if available, otherwise fall back to legacy globals
    use_context = app_context is not None

    if not use_context:
        global current_project_vtk_path, loaded_project_vtk_files, loaded_project_names, loaded_project_vtk_files_by_project

    # Normalize
    if not selected_folders:
        selected_folders = []
    if isinstance(selected_folders, str):
        selected_folders = [selected_folders]

    # Get discovered folders from context or global
    folders_dict = app_context.discovered_project_folders if use_context else discovered_project_folders
    selected_folders = [f for f in selected_folders if f in folders_dict]

    # Update loaded VTK files union for comparison pickers.
    loaded_vtk_paths = []
    loaded_names = []
    for name in selected_folders:
        info = folders_dict.get(name) or {}
        if info.get('has_vtk') and info.get('vtk_path'):
            loaded_names.append(name)
            loaded_vtk_paths.append(info['vtk_path'])

    # Build files_by_project mapping
    files_by_project_dict = {}
    all_files = []
    for name, vtk_dir in zip(loaded_names, loaded_vtk_paths):
        # Use imported list_vtk_files instead of _scan_vtk_dir
        from utils.vtk_utils import list_vtk_files as scan_vtk
        scanned = scan_vtk(Path(vtk_dir))
        files_by_project_dict[name] = scanned
        all_files.extend(scanned)
    all_files_sorted = sorted(set(all_files))

    # Update context or globals
    if use_context:
        app_context.loaded_project_names = loaded_names
        app_context.loaded_project_vtk_files_by_project = files_by_project_dict
        app_context.loaded_project_vtk_files = all_files_sorted
    else:
        loaded_project_names = loaded_names
        loaded_project_vtk_files_by_project = files_by_project_dict
        loaded_project_vtk_files = all_files_sorted

    # Choose active project (first loaded) for legacy paths and defaults.
    active_name = selected_folders[0] if selected_folders else None
    if not active_name:
        if use_context:
            app_context.current_project_vtk_path = None
        else:
            current_project_vtk_path = None
        msg = html.Div("No project loaded. Load one or more projects to enable Dash tabs and Comparison pickers.",
                       className='vtk-upload-feedback vtk-upload-feedback--error')
        return selected_folders, None, msg, {'names': loaded_names, 'active': None, 'files_by_project': files_by_project_dict}

    folder_info = folders_dict[active_name]

    # Update the VTK path to point to selected folder
    vtk_path = folder_info['vtk_path'] if folder_info.get('has_vtk') else None
    if use_context:
        app_context.current_project_vtk_path = vtk_path
    else:
        current_project_vtk_path = vtk_path

    # Main tabs are initialized at startup (no VTK reads). Selecting projects only
    # updates `projects-store`; panels react instantly without requiring a refresh.

    print(f"\n{'='*60}")
    print(f"PROJECTS LOADED: {', '.join(selected_folders) if selected_folders else '(none)'}")
    print(f"ACTIVE PROJECT: {active_name}")
    print(f"{'='*60}")
    print(f"Path: {folder_info['path']}")
    if folder_info.get('has_vtk'):
        print(f"VTK Path: {folder_info['vtk_path']}")
        print(f"VTK Files (active project): {folder_info.get('vtk_file_count', 0)}")
        print(f"VTK Files (loaded union): {len(loaded_project_vtk_files)}")
        print(f"✓ VTK data directory updated to: {current_project_vtk_path}")
    if folder_info.get('has_textdata'):
        print(f"TextData Path: {folder_info['textdata_path']}")
        print(f"TextData Files: {folder_info['textdata_file_count']}")
    print(f"{'='*60}\n")

    feedback_msg = html.Div([
        html.Div([
            html.Span("✓ ", style={'color': '#28a745', 'fontWeight': 'bold', 'fontSize': '16px'}),
            html.Span(f"Loaded projects: {', '.join(selected_folders) if selected_folders else '(none)'}", style={'fontWeight': '500'}),
        ]),
        html.Div([
            html.Span(f"Active: {active_name} | ", style={'color': '#666', 'fontSize': '12px'}),
            html.Span(f"VTK files (union): {len(loaded_project_vtk_files)} | ",
                      style={'color': '#666', 'fontSize': '12px'}),
            html.Span(f"TextData Files: {folder_info['textdata_file_count']}",
                      style={'color': '#666', 'fontSize': '12px'}),
        ], style={'marginTop': '4px'}),
        html.Div([
            html.Span("💡 Comparison can pick files from any loaded project; module panels pick a project inside each panel.",
                      style={'color': '#0066cc', 'fontSize': '12px', 'fontStyle': 'italic'})
        ], style={'marginTop': '8px'})
    ], className='vtk-upload-feedback vtk-upload-feedback--success',
       style={'padding': '12px', 'lineHeight': '1.4', 'maxHeight': '300px', 'overflowY': 'auto'})

    # Store the selected folder data
    folder_data = {
        'name': active_name,
        'path': str(folder_info['path']),
        'vtk_path': str(folder_info['vtk_path']) if folder_info['has_vtk'] else None,
        'textdata_path': str(folder_info['textdata_path']) if folder_info['has_textdata'] else None,
        'loaded': selected_folders,
    }

    return selected_folders, folder_data, feedback_msg, {'names': loaded_project_names, 'active': active_name, 'files_by_project': loaded_project_vtk_files_by_project}

@app.callback(
    Output('active-tab', 'data'),
    Input({'type': 'tab-button', 'tab': ALL}, 'n_clicks'),
    State('active-tab', 'data'),
    prevent_initial_call=True
)
def set_active_tab(n_clicks, current_tab):
    trigger = ctx.triggered_id
    if isinstance(trigger, dict) and trigger.get('tab'):
        return trigger['tab']
    return current_tab


# ===== SECTION 3: Render Tab with Persistent Control Values =====
@app.callback(
    Output('tab-content', 'children'),
    Output('tab-content', 'style'),
    Output('comparison-content', 'children'),
    Output('comparison-content', 'style'),
    Output({'type': 'tab-button', 'tab': ALL}, 'className'),
    Input('active-tab', 'data'),
    Input('comparison-files-store', 'data'),
    Input('selected-project-folder', 'data'),
    Input('loaded-project-folders', 'data'),
    Input('vtk-folder-tabs', 'value'),
    State({'type': 'comparison-controls-store', 'group': ALL}, 'data'),
    State({'type': 'comparison-controls-store', 'group': ALL}, 'id'),
    State({'type': 'comparison-selected-files-store', 'group': ALL}, 'data'),
    State({'type': 'comparison-selected-files-store', 'group': ALL}, 'id'),
)
def render_active_tab(active_tab, comparison_files, _active_project, _loaded_projects, active_folder,
                      group_controls_data, group_controls_ids,
                      selected_group_data, selected_group_ids):
    if active_tab is None and active_folder != 'comparison':
        return (
            html.Div("No tabs available", className='dataset-empty'),
            {},
            [],
            {'display': 'none'},
            ['custom-tab'] * len(TAB_ORDER),
        )
    classes = [
        'custom-tab active-tab' if tab_id == active_tab else 'custom-tab'
        for tab_id in TAB_ORDER
    ]
    if active_folder == 'comparison':
        stored_by_group = {}
        if group_controls_data and group_controls_ids:
            for store_id, store_data in zip(group_controls_ids, group_controls_data):
                if not isinstance(store_id, dict) or not store_data:
                    continue
                grp = store_id.get('group')
                if grp is not None:
                    stored_by_group[grp] = store_data
        selected_by_group = {}
        if selected_group_data and selected_group_ids:
            for store_id, store_data in zip(selected_group_ids, selected_group_data):
                if not isinstance(store_id, dict):
                    continue
                grp = store_id.get('group')
                if grp is not None:
                    selected_by_group[grp] = store_data or []
        allowed_groups = allowed_comparison_groups_for_tab(active_tab)
        return (
            no_update,
            {'display': 'none'},
            build_comparison_content(comparison_files or [], stored_by_group, selected_by_group, allowed_groups),
            {'display': 'block'},
            classes,
        )
    children = build_tab_children(active_tab)
    return (
        children,
        {'display': 'block'},
        no_update,
        {'display': 'none'},
        classes,
    )
# ===== END SECTION 3 =====


# ===== SECTION 4: Main Tab Callbacks (OOP Data Sources) =====

# Grain Size Callbacks
# Multi-output callback for size details (main + line charts) - uses legacy data
if get_legacy_data('size_details'):
    def build_size_figures(time, mode):
        """Wrapper for size details figures using legacy size_details data"""
        data = get_legacy_data('size_details')
        times = data['times']
        labels = data['labels']
        values = data['values']
        if not times or not labels:
            return go.Figure(), go.Figure()
        try:
            time_value = float(time)
        except (TypeError, ValueError):
            time_value = times[0]
        row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
        row_values = values[row_index]

        if mode not in {'line', 'bar'}:
            mode = 'bar'

        main_fig = go.Figure()
        if mode == 'bar':
            main_fig.add_bar(x=labels, y=row_values, marker_color='#183568')
        else:
            main_fig.add_scatter(x=labels, y=row_values, mode='lines+markers',
                               line=dict(color='#183568'))
        main_fig.update_layout(
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
            template='plotly_white'
        )
        axis_title_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f')
        tick_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
        main_fig.update_xaxes(title="Grain Number", title_font=axis_title_font, tickfont=tick_font)
        main_fig.update_yaxes(title="Grain Size", title_font=axis_title_font, tickfont=tick_font)

        avg_data = get_legacy_data('size_averages')
        if avg_data:
            avg_times = avg_data['times']
            avg_values = avg_data['averages']
        else:
            avg_times = times
            avg_values = [sum(row) / len(row) if row else 0 for row in values]

        line_fig = go.Figure(
            data=[go.Scatter(x=avg_times, y=avg_values, mode='lines+markers',
                           line=dict(color='#c50623'))]
        )
        line_fig.update_layout(
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
            template='plotly_white'
        )
        line_fig.update_xaxes(title="Time Step", title_font=axis_title_font, tickfont=tick_font)
        line_fig.update_yaxes(title="Average Grain Size", title_font=axis_title_font, tickfont=tick_font)

        return main_fig, line_fig

    create_multi_output_callback(
        app,
        outputs=[('size-card-main', 'figure'), ('size-card-line', 'figure')],
        inputs=[('size-card-time', 'value'), ('size-card-mode', 'value')],
        callback_func=build_size_figures
    )

# Histogram callback for grain distribution using legacy implementation
# Note: Grain histogram uses time-based selection, so we use legacy callback
if grain_data.is_available:
    @app.callback(
        Output('grain-dist-fig', 'figure'),
        Output('grain-dist-summary', 'children'),
        Input('grain-dist-time', 'value'),
        Input('grain-dist-bins', 'value'),
        Input('grain-dist-fit', 'value')
    )
    def update_grain_histogram(time_value, bins, fit_value):
        """Update grain histogram based on time, bins, and fit selection"""
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        if time_value is None:
            times = grain_data.get_time_steps()
            time_value = times[0] if times else 0
        return build_grain_histogram(float(time_value), bins or 15, fit=fit_enabled)


# Stress-Strain Callbacks using OOP data sources
if stress_strain_data.is_available:
    # Component selection for stress-strain curves
    create_component_selection_callback(
        app,
        stress_strain_data,
        'stress-strain-fig',
        'stress-components'
    )

if stress_data.is_available:
    # Histogram for stress distribution
    create_histogram_callback(app, stress_data, 'stress-hist')

if strain_data.is_available:
    # Histogram for strain distribution
    create_histogram_callback(app, strain_data, 'strain-hist')


# CRSS Callbacks using OOP data source
if crss_data.is_available:
    # Component selection for CRSS evolution
    create_component_selection_callback(
        app,
        crss_data,
        'crss-avg-fig',
        'crss-component-select'
    )

# ===== END SECTION 4 =====




if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(APP_TITLE.upper())
    print("=" * 60)

    # Scan for project folders containing VTK or TextData
    print("\nScanning for project folders...")
    discovered_project_folders = scan_project_folders()

    if discovered_project_folders:
        print(f"\nFound {len(discovered_project_folders)} project folder(s):")
        for folder_name, folder_info in sorted(discovered_project_folders.items()):
            print(f"\n  [{folder_name}]")
            print(f"    Path: {folder_info['path']}")
            if folder_info['has_vtk']:
                print(f"    VTK Files: {folder_info['vtk_file_count']} files in {folder_info['vtk_path'].name}/")
            if folder_info['has_textdata']:
                print(f"    TextData Files: {folder_info['textdata_file_count']} files in {folder_info['textdata_path'].name}/")
    else:
        print("  No project folders with VTK or TextData found.")

    print("\n" + "-" * 60)
    print("Current VTK Data Directory: {}".format(vtk_data_dir()))
    print("-" * 60)

    for tab_id, info in tab_datasets.items():
        print(f"[{info['label']}]")
        if not info['panels']:
            print("  - No datasets found.")
            continue
        for dataset_label, panel in info['panels']:
            print(f"  - {dataset_label}: {panel.file_path}")
    print(f"\n[{time.time()-_start_time:.2f}s] Total startup time")
    print("\nStarting Dash server on http://127.0.0.1:8050\n")

    app.run(debug=True, host='127.0.0.1', port=8050)
