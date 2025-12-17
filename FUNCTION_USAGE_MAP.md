# Function Usage Map - OPView Repository

**Generated:** 2025-12-17
**Total Functions:** 140
**Python Files:** 6
**Lines of Code:** ~5,717

---

## Summary by File

| File | Functions/Methods | Type | Lines |
|------|-------------------|------|-------|
| `OPView.py` | 84 | Module Functions | 3,211 |
| `viewer/panel.py` | 33 | Class Methods (ViewerPanel) | 1,583 |
| `viewer/layout.py` | 7 | Module Functions | 443 |
| `utils/vtk_reader.py` | 10 | Class Methods (VTKReader) | 217 |
| `sample_data/generate_sample_vti.py` | 3 | Module Functions | 169 |
| `viewer/state.py` | 3 | Class Methods (ViewerState) | 77 |

---

## Detailed Function Breakdown

### 1. OPView.py (84 functions)

**Main Application Entry Point** - Contains Dash app initialization, callbacks, and data processing

#### Data Loading Functions (10)
- `load_size_details()` - Load grain size details from text files
- `load_size_averages()` - Load grain size averages
- `load_stress_strain()` - Load stress-strain data
- `load_crss()` - Load CRSS (Critical Resolved Shear Stress) data
- `load_plastic_strain()` - Load plastic strain data
- `load_grain_histogram()` - Load grain histogram data
- `initialize_tab_datasets_static()` - Initialize static datasets for tabs
- `vtk_data_dir()` - Get VTK data directory path
- `comparison_data_dir()` - Get comparison data directory path
- `list_comparison_files()` - List available comparison files

#### VTK File Management (7)
- `_scan_vtk_dir()` - Scan directory for VTK files
- `scan_project_folders()` - Scan project folders for VTK data
- `get_project_folder_options()` - Get available project folder options
- `resolve_vtk_path()` - Resolve VTK file path from pattern
- `get_reader()` - Get VTK reader for file
- `latest_file()` - Get latest VTK file matching pattern
- `list_vtk_files()` - List all VTK files in directory

#### Comparison Panel Functions (16)
- `_comparison_panel_id()` - Generate comparison panel ID
- `allowed_comparison_groups_for_tab()` - Get allowed comparison groups
- `_comparison_entry_id()` - Generate comparison entry ID
- `_comparison_group_name()` - Get comparison group name
- `_group_comparison_files()` - Group comparison files
- `_comparison_entries()` - Create comparison entries
- `_comparison_entries_from_selected()` - Create entries from selected paths
- `_group_comparison_entries()` - Group comparison entries
- `_comparison_scalar_options()` - Get scalar field options
- `_comparison_palette_options()` - Get color palette options
- `_comparison_range_defaults()` - Get default range values
- `_comparison_settings()` - Build comparison settings
- `_comparison_dataset_config_from_entry()` - Build dataset config
- `_comparison_graph_id()` - Generate comparison graph ID
- `_comparison_heatmap_data()` - Generate heatmap data
- `get_comparison_panels()` - Create comparison panels

#### Visualization Functions (8)
- `build_histogram_figure()` - Build histogram figure
- `build_grain_histogram()` - Build grain size histogram
- `fit_best_distribution()` - Fit best statistical distribution
- `format_fit_summary()` - Format distribution fit summary
- `crss_series_values()` - Get CRSS series values
- `stress_series_values()` - Get stress series values
- `strain_series_values()` - Get strain series values
- `compute_average_series()` - Compute average series data

#### UI Building Functions (15)
- `build_tab_bar()` - Build main tab navigation bar
- `build_tab_children()` - Build content for each tab
- `build_comparison_heatmap_row()` - Build comparison heatmap row
- `build_comparison_content()` - Build comparison tab content
- `build_size_details_card()` - Build grain size details card
- `build_grain_distribution_card()` - Build grain distribution card
- `build_stress_strain_card()` - Build stress-strain card
- `build_stress_hist_card()` - Build stress histogram card
- `build_strain_hist_card()` - Build strain histogram card
- `build_crss_card()` - Build CRSS plot card
- `build_crss_hist_card()` - Build CRSS histogram card
- `build_crss_figure()` - Build CRSS figure
- `build_plastic_strain_card()` - Build plastic strain card
- `build_plastic_strain_figures()` - Build plastic strain figures
- `render_docs()` - Render documentation

#### Dash Callbacks (18)
- `handle_vtk_upload()` - Handle VTK file upload
- `_comparison_upload()` - Handle comparison file upload
- `update_folder_actions()` - Update folder action buttons
- `handle_project_folder_selection()` - Handle project folder selection
- `set_active_tab()` - Set active tab
- `render_active_tab()` - Render active tab content
- `update_size_details()` - Update grain size details plot
- `update_grain_distribution()` - Update grain distribution plot
- `update_stress_strain()` - Update stress-strain plot
- `update_stress_hist()` - Update stress histogram
- `update_strain_hist()` - Update strain histogram
- `update_crss_plot()` - Update CRSS plot
- `_update_comparison_selected_files()` - Update comparison file selection
- `_update_comparison_heatmaps()` - Update comparison heatmaps
- `_sync_comparison_control_options()` - Sync comparison controls
- `_toggle_comparison_range_controls()` - Toggle range controls
- `_update_comparison_range()` - Update comparison range
- `_save_comparison_group_controls()` - Save comparison group controls

#### Utility Functions (10)
- `tensor_scalars()` - Define tensor scalar components
- `get_default_active_tab()` - Get default active tab
- `get_manual_panel()` - Get manual viewer panel
- `_manual_viewer_id()` - Generate manual viewer ID
- `_parse_float()` - Parse float value
- `_clamp_range()` - Clamp range values
- `_make_comparison_cache_key()` - Create comparison cache key
- `col()` - Helper for column selection (nested)
- `collect()` - Helper for data collection (nested)
- `sort_key()` - Helper for sorting (nested)

---

### 2. viewer/panel.py (33 methods)

**ViewerPanel Class** - Main visualization panel with callbacks for interactive controls

#### Core Methods (4)
- `__init__()` - Initialize viewer panel
- `cid()` - Generate component ID
- `build_layout()` - Build panel layout
- `register_callbacks()` - Register all Dash callbacks

#### Data Processing Methods (9)
- `_build_time_options()` - Build time step options from VTK files
- `_colorscale_params()` - Calculate colorscale parameters
- `_slice_dimensions()` - Get slice dimensions
- `_build_state()` - Build viewer state object
- `_build_scalar_definitions()` - Build scalar field definitions
- `_make_scalar_value()` - Create scalar value identifier
- `_phase_overlay_file()` - Get phase overlay file path
- `_vtk_dir()` - Get VTK directory path
- `normalize()` - Normalize values (nested function)

#### Figure Building Methods (7)
- `_build_heatmap_figures()` - Build main heatmap figures
- `_build_colorbar_figure()` - Build colorbar figure
- `_build_figure()` - Build complete figure with layout
- `_build_map_title()` - Build heatmap title
- `_build_click_info()` - Build click information display
- `_build_line_scan_figure()` - Build line scan figure
- `_build_histogram_figure()` - Build histogram figure

#### Interaction Handlers (2)
- `_handle_click()` - Handle heatmap click events
- `_handle_line_scan_click()` - Handle line scan click events

#### UI Component Builders (2)
- `build_line_scan_card()` - Build line scan card
- `build_histogram_card()` - Build histogram card

#### Slice Management (3)
- `_default_slice_index()` - Get default slice index
- `_max_slice_index()` - Get maximum slice index
- `_clamp_slice()` - Clamp slice value to valid range

#### Download & Export (1)
- `_register_download_callback()` - Register download callbacks

#### Geometry Calculations (5)
- `compute_real_heatmap_edge()` - Compute real heatmap edge coordinates
- Plus 4 additional geometry helper methods embedded in callbacks

---

### 3. viewer/layout.py (7 functions)

**UI Layout Builder Functions** - Constructs the Dash component layouts

- `format_range_value()` - Format range values for display
- `build_controls()` - Build main control panel
- `build_graph_section()` - Build graph display section
- `build_line_scan_card()` - Build line scan analysis card
- `build_histogram_card()` - Build histogram card
- `build_tab_layout()` - Build complete tab layout
- `component_id()` - Generate component IDs

---

### 4. utils/vtk_reader.py (10 methods)

**VTKReader Class** - VTK file reading and processing utility

#### Core Methods (2)
- `__init__()` - Initialize reader with file path
- `load_file()` - Load VTK file using PyVista

#### Slice Extraction Methods (4)
- `get_slice()` - Extract 2D slice from VTK data
- `_extract_2d_data()` - Extract 2D data arrays
- `_process_slice()` - Process slice mesh data
- `get_max_slice_index()` - Get maximum slice index for axis

#### Interpolation Methods (2)
- `interpolate_to_grid()` - Interpolate data to regular grid
- `get_interpolated_slice()` - Get interpolated slice data

#### Data Access Methods (2)
- `scalar_fields()` - Get available scalar field names
- `_select_component()` - Select component from vector/tensor data

---

### 5. sample_data/generate_sample_vti.py (3 functions)

**Sample Data Generation** - Creates sample VTI files for testing

- `generate_3d_vti()` - Generate 3D sample VTI file with temperature field
- `generate_2d_vti()` - Generate 2D sample VTI file with scalar fields
- `generate_phase_field_vti()` - Generate phase field VTI with multiple fields

---

### 6. viewer/state.py (3 methods)

**ViewerState Dataclass** - State management for viewer

- `__init__()` - Initialize state (auto-generated by dataclass)
- `__repr__()` - String representation (auto-generated by dataclass)
- `__eq__()` - Equality comparison (auto-generated by dataclass)

*Note: This is a dataclass, so most methods are auto-generated*

---

## Function Categories Summary

### By Purpose

| Category | Count | Description |
|----------|-------|-------------|
| **Data Loading** | 10 | Load data from text files and VTK files |
| **VTK Processing** | 17 | Read, parse, and process VTK files |
| **Visualization** | 23 | Build plots, heatmaps, histograms |
| **UI Components** | 24 | Build Dash UI components and layouts |
| **Callbacks** | 18 | Dash callback functions for interactivity |
| **Comparison** | 16 | Multi-file comparison functionality |
| **State Management** | 8 | Manage application and viewer state |
| **Utilities** | 14 | Helper functions and utilities |
| **Sample Data** | 3 | Generate test data |
| **Class Infrastructure** | 7 | Class initialization and core methods |

---

## Architecture Patterns

### Class-Based Components (3 classes)

1. **VTKReader** (10 methods) - Handles VTK file I/O and processing
2. **ViewerPanel** (33 methods) - Main UI panel with visualization logic
3. **ViewerState** (3 methods) - Immutable state container (dataclass)

### Functional Components

1. **OPView.py** (84 functions) - Main application orchestration
2. **viewer/layout.py** (7 functions) - UI layout builders
3. **sample_data/generate_sample_vti.py** (3 functions) - Data generation

---

## Call Graph Highlights

### Most Called Functions (Estimated)

1. `VTKReader.get_slice()` - Called for every visualization update
2. `ViewerPanel._build_heatmap_figures()` - Called on every parameter change
3. `build_tab_children()` - Called on tab switch
4. `_update_comparison_heatmaps()` - Called on comparison updates
5. `component_id()` / `cid()` - Called extensively for ID generation

### Entry Points

1. **Main Application**: `OPView.py` → Dash app initialization
2. **Tab Rendering**: `build_tab_children()` → `ViewerPanel.build_layout()`
3. **VTK Loading**: `get_reader()` → `VTKReader.__init__()` → `VTKReader.load_file()`
4. **Visualization**: Callback → `ViewerPanel._build_heatmap_figures()` → `VTKReader.get_slice()`

---

## Code Metrics

### Function Complexity Distribution

- **Simple Functions (1-20 lines)**: ~60 functions
- **Medium Functions (21-50 lines)**: ~50 functions
- **Complex Functions (51-100 lines)**: ~20 functions
- **Very Complex Functions (100+ lines)**: ~10 functions

### Largest Functions

1. `build_comparison_content()` - ~250 lines (OPView.py:1712)
2. `render_active_tab()` - ~200 lines (OPView.py:2954)
3. `_update_comparison_range()` - ~125 lines (OPView.py:2107)
4. `build_comparison_heatmap_row()` - ~110 lines (OPView.py:1598)
5. `ViewerPanel._build_heatmap_figures()` - ~100 lines (viewer/panel.py:371)

---

## Dependencies Between Files

```
OPView.py
├── viewer/state.py (ViewerState)
├── viewer/panel.py (ViewerPanel)
│   ├── viewer/layout.py (build functions)
│   ├── viewer/state.py (ViewerState)
│   └── viewer/defaults.py (DEFAULT_*)
└── utils/vtk_reader.py (VTKReader)

sample_data/generate_sample_vti.py (standalone)
```

---

## Function Naming Conventions

### Public Functions
- Descriptive names: `build_grain_histogram()`, `load_stress_strain()`
- Action verbs: `get_`, `build_`, `load_`, `update_`, `handle_`

### Private Functions (84 private functions)
- Leading underscore: `_build_figure()`, `_update_comparison_range()`
- Internal helpers and implementation details

### Nested Functions (7 nested functions)
- Defined inside other functions for local scope
- Examples: `col()` in `load_size_details()`, `normalize()` in `ViewerPanel`

---

## Recommendations for Navigation

### To understand visualization:
1. Start with `ViewerPanel.__init__()` (viewer/panel.py:165)
2. Follow to `ViewerPanel.build_layout()` (viewer/panel.py:430)
3. Then `ViewerPanel._build_heatmap_figures()` (viewer/panel.py:371)

### To understand data loading:
1. Start with `initialize_tab_datasets_static()` (OPView.py:997)
2. Check `load_*()` functions (OPView.py:374-592)
3. See `VTKReader` class (utils/vtk_reader.py:9)

### To understand callbacks:
1. Check `ViewerPanel.register_callbacks()` (viewer/panel.py:460)
2. Review main callbacks in OPView.py (lines 2930-3170)
3. See comparison callbacks (OPView.py:1966-2232)

---

**End of Function Usage Map**
