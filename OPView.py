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
# Removed: from scipy import stats (not used in OPView.py - moved to utils/chart_utils.py)
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

# UI Manager
from ui import UIManager, build_app_layout

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

# Comparison helpers (Phase 10.1)
from comparisonmgr.helpers import (
    _comparison_panel_id,
    allowed_comparison_groups_for_tab,
    _comparison_entry_id,
    _comparison_group_name,
    _group_comparison_files,
    list_vtk_files as _comparison_list_vtk_files,
    _comparison_entries,
    _comparison_entries_from_selected,
    _group_comparison_entries,
    _comparison_scalar_options,
    _comparison_palette_options,
    _parse_float,
    _clamp_range,
    _comparison_range_defaults,
    _comparison_settings,
    _comparison_dataset_config_from_entry,
    _manual_viewer_id,
    get_manual_panel,
    get_comparison_panels,
)

# Comparison UI builders (Phase 10.2)
from comparisonmgr.ui_builders import (
    _comparison_graph_id,
    _comparison_heatmap_data,
    build_comparison_heatmap_row,
    build_comparison_content,
)

# Comparison callbacks (Phase 10.3)
from comparisonmgr.callbacks import (
    register_comparison_callbacks,
    _comparison_upload,
)

APP_TITLE = "OpenPhase OPView"
APP_FAVICON = "OP_Logo.png"
APP_BG_COLOR = "#f5f7fb"
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
app._favicon = APP_FAVICON
print(f"[{time.time()-_start_time:.2f}s] Dash app created")

# Register comparison callbacks (Phase 10.3)
print(f"[{time.time()-_start_time:.2f}s] Registering comparison callbacks...")
register_comparison_callbacks(app)
print(f"[{time.time()-_start_time:.2f}s] Comparison callbacks registered")

# Register project callbacks (Phase 13)
print(f"[{time.time()-_start_time:.2f}s] Registering callbacks...")
from callbacks import ProjectCallbackManager, TabCallbackManager
project_cb_manager = ProjectCallbackManager(app, app_context)
project_cb_manager.register()
print(f"[{time.time()-_start_time:.2f}s] Project callbacks registered: {project_cb_manager.count()}")

tab_cb_manager = TabCallbackManager(app, app_context)
tab_cb_manager.register()
print(f"[{time.time()-_start_time:.2f}s] Tab callbacks registered: {tab_cb_manager.count()}")

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

# Phase 9: build_grain_histogram() removed - now in ui/ui_manager.py
# (Wrapper function exists later in the file)

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
    _init_start = time.time()

    from viewer import ViewerPanel
    print(f"  - ViewerPanel import took {time.time()-_init_start:.3f}s")

    tab_data = {}
    debug = bool(os.environ.get("OPVIEW_DEBUG"))
    active_project_name = None
    # Panels populate project/file pickers from `projects-store` (paths only; no VTK reads).
    for tab in TAB_CONFIGS:
        tab_id = tab['id']
        tab_start = time.time()
        print(f"  - Initializing tab '{tab_id}'...")
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
        print(f"  - Tab '{tab_id}' initialized in {time.time()-tab_start:.3f}s ({len(datasets)} panels)")
    return tab_data


print(f"[{time.time()-_start_time:.2f}s] Initializing tab panels...")
tab_datasets = initialize_tab_datasets_static()
print(f"[{time.time()-_start_time:.2f}s] Tab panels initialized ({len(tab_datasets)} tabs)")

comparison_panels = {}


# =============================================================================
# COMPARISON FEATURE - PHASE 10.1 COMPLETE ✓
# =============================================================================
# Comparison helper functions extracted to comparisonmgr/helpers.py (20 functions)
#
# Extracted functions:
#   - _comparison_panel_id()           - allowed_comparison_groups_for_tab()
#   - _comparison_entry_id()           - _comparison_group_name()
#   - _group_comparison_files()        - list_vtk_files()
#   - _comparison_entries()            - _comparison_entries_from_selected()
#   - _group_comparison_entries()      - _comparison_scalar_options()
#   - _comparison_palette_options()    - _parse_float()
#   - _clamp_range()                   - _comparison_range_defaults()
#   - _comparison_settings()           - _comparison_dataset_config_from_entry()
#   - _manual_viewer_id()              - get_manual_panel()
#   - get_comparison_panels()
#
# Imported at lines 79-100 from comparisonmgr.helpers
#
# Remaining comparison extraction:
#   Phase 10.2: UI builders (~280 lines)
#   Phase 10.3: Callbacks (~300 lines)
# =============================================================================


def build_tab_children(tab_id):
    _tab_start = time.time()
    print(f"      [tab_children] Building content for '{tab_id}'...")

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
        for builder in (ui_manager.build_size_details_card, ui_manager.build_grain_distribution_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'mechanics':
        for builder in (ui_manager.build_stress_strain_card, ui_manager.build_stress_hist_card, ui_manager.build_strain_hist_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'plasticity':
        for builder in (ui_manager.build_crss_card, ui_manager.build_plastic_strain_card):
            card = builder()
            if card:
                cards.append(card)

    print(f"      [tab_children] '{tab_id}' content built in {time.time()-_tab_start:.3f}s")
    return [html.Div(cards, className='dataset-grid')]


# =============================================================================
# COMPARISON FEATURE - PHASE 10.2 COMPLETE ✓
# =============================================================================
# Comparison UI builders extracted to comparisonmgr/ui_builders.py (4 functions)
#
# Extracted functions:
#   - _comparison_graph_id()           - Generate pattern-matched graph IDs
#   - _comparison_heatmap_data()       - Build heatmaps with grid caching
#   - build_comparison_heatmap_row()   - Construct heatmap rows for groups
#   - build_comparison_content()       - Full comparison tab layout
#
# Imported at lines 102-108 from comparisonmgr.ui_builders
#
# =============================================================================
# COMPARISON FEATURE - PHASE 10.3 COMPLETE ✓
# =============================================================================
# Comparison callbacks extracted to comparisonmgr/callbacks.py (6 callbacks + 2 helpers)
#
# Extracted callbacks:
#   - _update_comparison_selected_files()   - File selection/removal
#   - _update_comparison_heatmaps()         - Heatmap rendering
#   - _sync_comparison_control_options()    - Control synchronization
#   - _toggle_comparison_range_controls()   - Control enable/disable
#   - _update_comparison_range()            - Range updates (largest)
#   - _save_comparison_group_controls()     - Control persistence
#
# Helper functions:
#   - _make_comparison_cache_key()          - Cache key generation (deprecated)
#   - _comparison_upload()                  - Upload button component
#
# Registered at line 327 via register_comparison_callbacks(app)
# =============================================================================


TAB_ORDER = [tab['id'] for tab in TAB_CONFIGS]


def get_default_active_tab():
    for tab_id in TAB_ORDER:
        if tab_datasets.get(tab_id, {}).get("panels"):
            return tab_id
    return TAB_ORDER[0] if TAB_ORDER else None


# =============================================================================
# TAB BAR BUILDER - Removed (Phase 14 - Dynamic Tab Management) ✅
# =============================================================================
# Static tab buttons replaced with dynamic dropdown-based tab creation.
# Tab headers now rendered by callbacks/tab_manager.py:_register_render_tab_headers
# User selects module from dropdown → tab header appears with close button
# =============================================================================




INITIAL_ACTIVE_TAB = get_default_active_tab()

# Scan for project folders at startup (before layout creation)
print(f"[{time.time()-_start_time:.2f}s] Scanning for project folders...")
discovered_project_folders = scan_project_folders()
print(f"[{time.time()-_start_time:.2f}s] Found {len(discovered_project_folders)} project folder(s)")

# Initialize OOP data sources (before card builders)
print(f"[{time.time()-_start_time:.2f}s] Creating OOP data sources...")
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
print(f"[{time.time()-_start_time:.2f}s] OOP data sources created and loaded")

# Phase 9: Instantiate UIManager with data sources
print(f"[{time.time()-_start_time:.2f}s] Creating UIManager...")
ui_manager = UIManager(
    grain_data=grain_data,
    stress_strain_data=stress_strain_data,
    stress_data=stress_data,
    strain_data=strain_data,
    crss_data=crss_data,
    get_legacy_data_fn=get_legacy_data,
    build_histogram_figure_fn=build_histogram_figure
)
print(f"[{time.time()-_start_time:.2f}s] UIManager created")


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
        title_font=dict(size=16, family='Roboto Condensed, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Roboto Condensed, sans-serif', color='#0f1b2b')
    )
    fig.update_yaxes(
        title="CRSS (MPa)",
        title_font=dict(size=16, family='Roboto Condensed, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Roboto Condensed, sans-serif', color='#0f1b2b')
    )
    return fig

print(f"[{time.time()-_start_time:.2f}s] Building app layout...")
app.layout = html.Div(
    build_app_layout(
        discovered_project_folders=discovered_project_folders,
        comparison_files=list_comparison_files(comparison_data_dir()),
        initial_active_tab=INITIAL_ACTIVE_TAB,
        build_tab_children_func=build_tab_children,
        build_comparison_content_func=build_comparison_content,
        allowed_comparison_groups_func=allowed_comparison_groups_for_tab,
        get_project_folder_options_func=get_project_folder_options,
        default_vtk_folder_label=DEFAULT_VTK_FOLDER_LABEL,
    ),
    style={"backgroundColor": APP_BG_COLOR, "minHeight": "100vh"},
)
print(f"[{time.time()-_start_time:.2f}s] App layout built")

# =============================================================================
# PROJECT MANAGEMENT CALLBACKS - Extracted to callbacks/project_manager.py (Phase 13) ✅
# =============================================================================
# Callbacks for VTK upload, project folder selection, and folder actions.
# Registered at line 330-335 via ProjectCallbackManager.
# =============================================================================

# =============================================================================
# SET ACTIVE TAB CALLBACK - Removed (Phase 14 - Dynamic Tab Management) ✅
# =============================================================================
# Old callback for tab-button clicks removed.
# Replaced by TabCallbackManager.activate_tab_from_header() for dynamic tabs.
# =============================================================================

# =============================================================================
# RENDER TAB CALLBACK - Moved to callbacks/tab_manager.py (Phase 14) ✅
# =============================================================================
# Tab rendering callback moved to TabCallbackManager for dynamic tab system.
# Old callback had 5 outputs (including className for old tab buttons).
# New callback has 4 outputs (no className, uses dynamic tab headers instead).
# Registered via TabCallbackManager._register_render_tab_content() method.
# =============================================================================


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
        axis_title_font = dict(size=16, family='Roboto Condensed, sans-serif', color='#12294f')
        tick_font = dict(size=16, family='Roboto Condensed, sans-serif', color='#0f1b2b')
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
        return ui_manager.build_grain_histogram(float(time_value), bins or 15, fit=fit_enabled)


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

    # Disable reloader to prevent double initialization
    # use_reloader=False keeps debug features but prevents spawning two processes
    app.run(debug=True, use_reloader=False, host='127.0.0.1', port=8050)
