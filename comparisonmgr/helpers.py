"""
Comparison feature helper functions.

Extracted from OPView.py Phase 10.1 - provides utility functions for:
- Panel and group management
- File management and entry processing
- UI option generation
- Range/value parsing
- Panel creation and caching
"""

import re
import hashlib
from pathlib import Path


def _comparison_panel_id(group: str) -> str:
    safe = re.sub(r'[^a-z0-9]+', '-', group.lower()).strip('-')
    suffix = safe or 'group'
    return f"comparison-{suffix}"


def allowed_comparison_groups_for_tab(tab_id: str):
    """Return a set of filename prefixes that belong to the given module/tab."""
    from config import TAB_CONFIGS

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
    # Try underscore first (PhaseField_001.vtk -> PhaseField)
    if '_' in file_name:
        return file_name.split('_', 1)[0]
    # Try dot (PhaseField.vtk -> PhaseField) - ignore numeric parts if possible?
    # Simply taking main stem before first dot usually works for typical VTK naming
    return file_name.split('.', 1)[0]


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
    # Import globals at runtime to avoid circular imports
    import OPView
    from utils.project_scanner import _scan_vtk_dir

    # Use app_context if available, otherwise fall back to legacy globals
    if OPView.app_context is not None:
        vtk_files = OPView.app_context.loaded_project_vtk_files
        vtk_path = OPView.app_context.current_project_vtk_path
    else:
        vtk_files = OPView.loaded_project_vtk_files
        vtk_path = OPView.current_project_vtk_path

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
    """Build unified comparison entries from Comparison folder files and selected VTK paths."""
    from config import comparison_data_dir
    from utils import resolve_vtk_path

    entries = []
    seen = set()
    for name in (comparison_file_names or []):
        if not name:
            continue
        # Support absolute paths directly (e.g. from Add Folder)
        # pathlib / operator ignores LHS if RHS is absolute, but explicit check is safer/clearer
        p_obj = Path(name)
        if p_obj.is_absolute():
            path = p_obj.resolve()
        else:
            path = (comparison_data_dir() / name).resolve()
            
        if not path.exists():
            continue
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        # Use basename for 'name' to ensure proper grouping later
        entries.append({'name': path.name, 'path': key, 'source': 'comparison'})
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
    from config import comparison_data_dir
    from utils import resolve_vtk_path

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
                         palette_value=None, full_scale=False, slider_range=None,
                         interfaces_overlay_visible=False):
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
        'interfaces_overlay_visible': bool(interfaces_overlay_visible),
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
    from utils import resolve_vtk_path, get_reader
    import OPView

    if not file_path:
        return None
    path = Path(file_path)
    if not path.is_absolute():
        path = resolve_vtk_path(str(path))
    path = path.resolve()
    if not path.exists():
        return None
    key = str(path)
    panel = OPView.manual_panels_by_path.get(key)
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
            panel = VP(OPView.app, get_reader, config)
        except (FileNotFoundError, ValueError):
            return None
        OPView.manual_panels_by_path[key] = panel
    return panel


def get_comparison_panels(entries):
    """Build/return ViewerPanels for comparison entries, keyed by absolute path."""
    # Import ViewerPanel when needed (lazy loading for fast startup)
    from viewer import ViewerPanel as VP
    from utils import get_reader
    import OPView

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
        entry = OPView.comparison_panels.get(cache_key)
        panel = entry['panel'] if entry and entry['axis'] == config["axis"] else None
        if panel is None:
            try:
                panel = VP(OPView.app, get_reader, config)
            except (FileNotFoundError, ValueError):
                continue
            OPView.comparison_panels[cache_key] = {'axis': config["axis"], 'panel': panel}
        panels[cache_key] = (config["label"], panel, config["file"])
    return panels

def get_project_options(entries):
    """Extract unique projects from entries for the project picker.

    Returns project/VTK folder paths in 'Project/VTK' format.

    Supports:
    1. Standard OP structure: .../ProjectName/VTK/file.vtk -> ProjectName/VTK
    2. direct custom path: .../FolderName/file.vtk -> FolderName
    """
    from pathlib import Path
    projects_found = set()
    for e in entries:
        path_obj = Path(e.get('path') or '')
        parts = list(path_obj.parts)

        # 1. Try standard OP structure
        found_standard = False
        for idx, part in enumerate(parts):
            if part.lower() == 'vtk' and idx > 0:
                project_name = parts[idx - 1]
                vtk_folder = part  # "VTK" or "vtk"
                full_path = f"{project_name}/{vtk_folder}"
                projects_found.add(full_path)
                found_standard = True
                break

        # 2. If not standard, use immediate parent folder name
        if not found_standard and len(parts) > 1:
            projects_found.add(parts[-2])

    return [{'label': p, 'value': p} for p in sorted(projects_found)]
