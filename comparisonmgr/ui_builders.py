"""
Comparison feature UI builders.

Extracted from OPView.py Phase 10.2 - provides UI building functions for:
- Comparison graph IDs
- Heatmap data generation with caching
- Heatmap row construction
- Full comparison content layout
"""

import re
from pathlib import Path
from dash import html, dcc
import dash_mantine_components as dmc

# Import helper functions from same package
from .helpers import (
    _comparison_entries,
    list_vtk_files,
    _group_comparison_entries,
    _comparison_entries_from_selected,
    get_comparison_panels,
    _comparison_settings,
    _comparison_range_defaults,
)


def _comparison_graph_id(file_name: str, group: str):
    """Generate a pattern-matched graph ID for comparison heatmaps."""
    safe_file = re.sub(r'[^a-z0-9]+', '-', file_name.lower()).strip('-')
    # Use the raw group key consistently across controls, stores, and graphs.
    return {'type': 'comparison-graph', 'group': group, 'file': safe_file or 'file'}


def _comparison_heatmap_data(panel, entry: dict, settings, override_range=None):
    """Build comparison heatmap with grid caching for performance.

    Args:
        panel: ViewerPanel instance
        entry: Dict with 'name', 'path', 'source' keys
        settings: Dict with 'scalar', 'range_min', 'range_max', 'palette', 'full_scale', 'slice_index'
        override_range: Optional tuple(min, max) to override settings range (e.g. for Full Scale)

    Returns:
        Heatmap bundle dict with 'figure', 'colorbar', 'fig_width' or None if error
    """
    # Import OPView module at runtime to access global cache
    import OPView

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
    if grid_cache_key in OPView.comparison_grid_cache_data:
        X_grid, Y_grid, Z_grid, stats, state_dict = OPView.comparison_grid_cache_data[grid_cache_key]
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
            OPView.comparison_grid_cache_data[grid_cache_key] = (X_grid, Y_grid, Z_grid, stats, state_dict)

    # Apply current settings to state
    range_min = settings.get('range_min')
    range_max = settings.get('range_max')

    # Note: we do NOT overwrite state.range_min/max with override_range here.
    # We want the state to reflect the user's slider selection so the colorscale 
    # generation logic knows where the "inner" (Blue/Red) cuts are.
    if range_min is not None:
        state.range_min = range_min
    if range_max is not None:
        state.range_max = range_max

    if state.range_min is not None and state.range_max is not None and state.range_min > state.range_max:
        state.range_min, state.range_max = sorted([state.range_min, state.range_max])
    if state.range_min is not None and state.range_max is not None:
        state.threshold = (state.range_min + state.range_max) / 2
    state.palette = settings.get('palette') or state.palette
    
    # If explicit global range is provided (Full Scale), we enable dynamic mode 
    # and pass the global limits. This ensures the colorbar spans the full global range
    # while the inner colors (Blue/Red) still align with the slider values (state.range_min/max).
    if override_range:
        state.colorscale_mode = 'dynamic'
    else:
        state.colorscale_mode = 'normal'
    
    state.slice_index = max(0, slice_index)
    state.interfaces_overlay_visible = bool(settings.get('interfaces_overlay_visible', False))

    heatmap_bundle = panel._build_heatmap_figures(reader, state, file_path, slice_data=None, data_limits=override_range)
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


def build_comparison_heatmap_row(panels, entries, settings, group, app=None):
    """Return a single heatmap row for a comparison group.

    Args:
        panels: Dict mapping file paths to (label, panel, file_path) tuples
        entries: List of entry dicts for this group
        settings: Dict with scalar, range, palette, full_scale settings
        group: Group name (string)
        app: Dash app instance (unused, kept for compatibility)

    Returns:
        List containing a single Div with heatmap title row and graph row
    """
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
    override_range = None
    if full_scale_enabled:
        # If Full Scale is enabled, we ignore the slider/input settings and force the 
        # global min/max of the selected scalar across all panels in this group.
        # This allows the slider to keep its user-defined "zoomed" range, while the 
        # plots temporarily show the full data range.
        g_min, g_max = _comparison_range_defaults(panels, settings.get('scalar'))
        if g_min is not None and g_max is not None:
             override_range = (g_min, g_max)

    for entry, panel_entry in ordered:
        if not panel_entry:
            continue
        _, panel, _ = panel_entry
        heatmap_data = _comparison_heatmap_data(panel, entry, settings, override_range=override_range)
        if not heatmap_data:
            continue
        # Use the first available colorbar for the row.
        if colorbar_fig is None:
            colorbar_fig = heatmap_data['colorbar']
        file_name = entry.get('name') or Path(entry.get('path') or '').name
        fig_width = heatmap_data.get('fig_width')
        if fig_width:
            column_widths.append(f"{int(fig_width)}px")
        else:
            column_widths.append("320px")
        rendered.append(entry)
        graph_id = _comparison_graph_id(file_name, group)
        heatmap_children.append(html.Div(
            dcc.Graph(
                id=graph_id,
                className='heatmap-main-graph comparison-heatmap-graph',
                figure=heatmap_data['figure'],
                config=graph_config
            ),
            className='heatmap-main-card comparison-heatmap-main-card'
        ))

    if colorbar_fig:
        heatmap_children.append(html.Div(
            dcc.Graph(
                id=f'comparison-colorbar-{group}',
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
        html.Div(
            html.Button(
                [
                    html.Img(src='/assets/download.png', alt='Download', className='btn-icon'),
                    html.Span("PNG")
                ],
                id={'type': 'comparison-download', 'group': group},
                n_clicks=0,
                className='comparison-heatmap-download-all graph-toolbar-btn graph-toolbar-btn--icon',
                title='Download all heatmaps as PNG'
            ),
            className='comparison-heatmap-title-spacer',
            style={'width': '70px'}
        )
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
                id=f'comparison-heatmap-row-{group}',
                className='comparison-heatmap-row heatmap-row',
                style={'gridTemplateColumns': grid_template}
            ),
        ],
        className='comparison-group-block'
    )]


def build_comparison_content(files, group_controls_by_group=None, group_selected_paths_by_group=None, allowed_groups=None, app=None):
    """Render the comparison tab body showing files from Comparison folder, grouped by prefix.

    Args:
        files: List of comparison file names from Comparison folder.
        group_controls_by_group: Optional dict {group: stored_controls}.
        group_selected_paths_by_group: Optional dict {group: [vtk_paths]} selected from VTK folder.
        allowed_groups: Optional set/list of group prefixes to show.
        app: Dash app instance (for callback registration)

    Returns:
        List containing a single Div with all comparison group cards
    """
    group_selected_paths_by_group = group_selected_paths_by_group or {}

    # Available entries for building pickers (all VTK + all Comparison files).
    available_entries = _comparison_entries(files, list_vtk_files())
    grouped_available = _group_comparison_entries(available_entries)
    # Treat an empty set/list as "show none" (filter active), and only treat
    # `None` as "no filter" (show all).
    allowed_set = set(allowed_groups) if allowed_groups is not None else None

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
                "No comparison files found. Add VTK files to the Comparison folder to use this feature.",
                className='comparison-empty'
            )
        ], className='dataset-block comparison-card')]

    cards = []

    stored_controls_by_group = group_controls_by_group or {}

    for group, available_group_entries in grouped_available.items():
        # Important: keep all groups in the layout once rendered, even if filtered
        # by the currently active module, so pattern-matching callbacks don't
        # try to update components that disappeared mid-flight.
        group_allowed = True if allowed_set is None else group in allowed_set
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
        # Use stored values regardless of file selection to preserve settings during tab switches
        settings, scalar_options, palette_options = _comparison_settings(
            panels_for_settings,
            scalar_value=stored.get('scalar'),
            range_min=stored.get('range_min'),
            range_max=stored.get('range_max'),
            palette_value=stored.get('palette'),
            full_scale=stored.get('full_scale', False),
            slider_range=stored.get('slider_range'),
            interfaces_overlay_visible=stored.get('interfaces_overlay_visible', False),
        )
        slider_min_default, slider_max_default = _comparison_range_defaults(panels_for_settings, settings['scalar'])
        if slider_min_default is None or slider_max_default is None:
            slider_min_default, slider_max_default = 0.0, 1.0
        slider_value_min = settings['range_min'] if settings['range_min'] is not None else slider_min_default
        slider_value_max = settings['range_max'] if settings['range_max'] is not None else slider_max_default

        # Extract unique project/VTK paths from available entries for the project picker
        projects_found = set()
        for e in available_group_entries:
            path_obj = Path(e.get('path') or '')
            parts = list(path_obj.parts)
            for idx, part in enumerate(parts):
                if part.lower() == 'vtk' and idx > 0:
                    project_name = parts[idx - 1]
                    vtk_folder = part  # "VTK" or "vtk"
                    full_path = f"{project_name}/{vtk_folder}"
                    projects_found.add(full_path)
                    break
        project_options = [{'label': p, 'value': p} for p in sorted(projects_found)]

        # Determine if the current 'group' corresponds to one of these projects.
        # If so, pre-select it and simplify file labels.
        current_project = group if group in projects_found else None

        def _label_for_entry(e):
            name = e.get('name') or Path(e.get('path') or '').name
            if e.get('source') == 'comparison':
                return f"{name} (Comparison)"
            
            # If we are in a project-specific view, just show the filename.
            if current_project:
                # Double check this file belongs to current_project
                p = Path(e.get('path') or '')
                parts = list(p.parts)
                for idx, part in enumerate(parts):
                    if part.lower() == 'vtk' and idx > 0:
                        if parts[idx - 1] == current_project:
                            return name
            
            # Fallback: Show full Project/Filename
            p = Path(e.get('path') or '')
            parts = list(p.parts)
            proj = None
            for idx, part in enumerate(parts):
                if part.lower() == 'vtk' and idx > 0:
                    proj = parts[idx - 1]
                    break
            return f"{proj}/{name}" if proj else name

        group_options = [{'label': _label_for_entry(e), 'value': e['path']} for e in available_group_entries]

        controls_layout = html.Div([
            # Row 1: Files and Field (Flex Layout to match Viewer)
            html.Div([
                # Project Picker (New)
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id={'type': 'comparison-project-picker', 'group': group},
                            options=project_options,
                            value=current_project,  # Pre-select matching project
                            placeholder="Select Folder",
                            clearable=True,
                            searchable=False,
                            persistence=True,
                            persistence_type='session',
                        )
                    ], className='dropdown-wrapper')
                ], className='control-pair project-control-pair'),

                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id={'type': 'comparison-vtk-picker', 'group': group},
                            options=group_options,
                            value=selected_paths,
                            multi=True,
                            placeholder=f"Select File",
                            clearable=True,
                            searchable=False,
                            className='comparison-file-picker'
                        )
                    ], className='dropdown-wrapper')
                ], className='control-pair'),

                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id={'type': 'comparison-heatmap-field', 'group': group},
                            options=scalar_options,
                            value=settings['scalar'],
                            clearable=False,
                            searchable=False,
                            disabled=not has_selection,
                            placeholder="Select files first…" if not has_selection else "Select Field",
                        )
                    ], className='dropdown-wrapper')
                ], className='control-pair')
            ], className='controls-flex-row'),

            # Row 2: Range Controls (Grid Layout to match Viewer)
            html.Div([
                html.Label([
                    html.Img(src='/assets/bar-chart.png', className="label-img"),
                    "Range:",
                ], className='field-label grid-label'),
                dcc.Input(
                    id={'type': 'comparison-heatmap-range-min', 'group': group},
                    type='number',
                    value=settings['range_min'],
                    step='any',
                    placeholder='Min',
                    disabled=not has_selection,
                ),
                dcc.Input(
                    id={'type': 'comparison-heatmap-range-max', 'group': group},
                    type='number',
                    value=settings['range_max'],
                    step='any',
                    placeholder='Max',
                    disabled=not has_selection,
                ),
                html.Button(
                    html.Img(src='/assets/Reset.png', alt='Reset', className='btn-icon'),
                    id={'type': 'comparison-heatmap-reset', 'group': group},
                    n_clicks=0,
                    className='btn btn-danger reset-btn',
                    title='Reset range',
                    disabled=not has_selection
                ),
            ], className='controls-grid-row range-row-extended'),

            # Row 3: Palette, Slider, Full Scale (Grid/Flex Mixed Layout)
            html.Div([
                html.Label([
                    html.Img(src='/assets/color-scale.png', className="label-img"),
                ], className='field-label grid-label'),

                html.Div([
                    dcc.Dropdown(
                        id={'type': 'comparison-heatmap-palette', 'group': group},
                        options=palette_options,
                        value=settings['palette'],
                        clearable=False,
                        searchable=False,
                    )
                ], className='dropdown-wrapper'),

                html.Div([
                    dcc.RangeSlider(
                        id={'type': 'comparison-heatmap-range-slider', 'group': group},
                        min=slider_min_default,
                        max=slider_max_default,
                        value=[slider_value_min, slider_value_max],
                        marks=None,
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className='range-slider-dual comparison-range-slider',
                        disabled=not has_selection
                    )
                ], className='range-slider-track'),

                html.Div([
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
                    )
                ], className='scan-option scan-option--inline'),

                html.Div([
                    dmc.Switch(
                        id={'type': 'comparison-overlay-toggle', 'group': group},
                        label="Show Interfaces",
                        checked=settings.get('interfaces_overlay_visible', False),
                        labelPosition="right",
                        size="xs",
                        radius="xs",
                        color="#c50623",
                        withThumbIndicator=True,
                        disabled=not has_selection,
                    )
                ], className='scan-option scan-option--inline')
            ], className='range-slider-row range-slider-with-mode')
        ])

        range_selector_store = dcc.Store(
            id={'type': 'comparison-range-selection', 'group': group},
            data={'click_count': 0, 'first_click': None},
            storage_type='session',
        )
        clear_flag_store = dcc.Store(
            id={'type': 'comparison-clear-flag', 'group': group},
            data=False,
            storage_type='memory',
        )

        group_selected_store_props = {
            'id': {'type': 'comparison-selected-files-store', 'group': group},
            'storage_type': 'session',
        }
        # Only set data when we actually have a selection.
        if selected_paths:
            group_selected_store_props['data'] = selected_paths
        group_selected_store = dcc.Store(**group_selected_store_props)

        group_controls_store = dcc.Store(
            id={'type': 'comparison-controls-store', 'group': group},
            data={
                'scalar': settings['scalar'],
                'range_min': settings['range_min'],
                'range_max': settings['range_max'],
                'palette': settings['palette'],
                'full_scale': settings['full_scale'],
                'interfaces_overlay_visible': settings.get('interfaces_overlay_visible', False),
                'slider_range': [slider_value_min, slider_value_max],
            },
            storage_type='session',
        )

        heatmap_sections = []
        if panels_for_group:
            heatmap_sections = build_comparison_heatmap_row(panels_for_group, selected_group_entries, settings, group, app=app)

        comparison_block = html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(f'Comparison: {group}', className='dataset-title')
            ], className='dataset-header'),
            html.Div([
                controls_layout,
                # add_path_control removed (Phase 16 - consolidated to Sidebar)
                html.Div(id={'type': 'comparison-remove-file-dummy', 'group': group}, style={'display': 'none'}),
                range_selector_store,
                clear_flag_store,
                group_selected_store,
                group_controls_store,
                html.Div(heatmap_sections, id={'type': 'comparison-heatmap-rows', 'group': group}, className='comparison-heatmap-area-inner')
            ], className='comparison-heatmap-area')
        ], className='dataset-block comparison-card comparison-heatmap-panel', style=None if group_allowed else {'display': 'none'})

        cards.append(comparison_block)

    return [html.Div(cards, className='comparison-root')]


def build_comparison_group_content(group, files, group_controls_by_group=None, group_selected_paths_by_group=None, app=None):
    """Render a single comparison group card (Multi View panels use this).

    Args:
        group: Group name
        files: List of comparison files
        group_controls_by_group: Optional dict of stored controls
        group_selected_paths_by_group: Optional dict of selected paths
        app: Dash app instance (for callback registration)
    """
    group_selected_paths_by_group = group_selected_paths_by_group or {}

    available_entries = _comparison_entries(files, list_vtk_files())
    grouped_available = _group_comparison_entries(available_entries)
    available_group_entries = grouped_available.get(group) or []

    if not available_group_entries:
        return [html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(f'Comparison: {group}', className='dataset-title')
            ], className='dataset-header'),
            html.Div(
                "No matching files found for this panel.",
                className='comparison-empty'
            )
        ], className='dataset-block comparison-card')]

    selected_paths = group_selected_paths_by_group.get(group) or []
    selected_entries = _comparison_entries_from_selected(selected_paths)

    panels = get_comparison_panels(selected_entries)
    panels_for_group = {
        entry.get('path'): panels.get(entry.get('path'))
        for entry in selected_entries
        if entry and entry.get('path') in panels
    }

    stored_controls_by_group = group_controls_by_group or {}
    stored = stored_controls_by_group.get(group) or {}

    # Reuse the same card structure as `build_comparison_content`, but for one group.
    cards = []

    # ---- Begin inlined card builder logic (kept consistent with build_comparison_content) ----
    from pathlib import Path

    # Extract unique project/VTK paths from available entries for the project picker
    projects_found = set()
    for e in available_group_entries:
        path_obj = Path(e.get('path') or '')
        parts = list(path_obj.parts)
        for idx, part in enumerate(parts):
            if part.lower() == 'vtk' and idx > 0:
                project_name = parts[idx - 1]
                vtk_folder = part  # "VTK" or "vtk"
                full_path = f"{project_name}/{vtk_folder}"
                projects_found.add(full_path)
                break
    project_options = [{'label': p, 'value': p} for p in sorted(projects_found)]

    # Determine if the current 'group' corresponds to one of these projects.
    current_project = group if group in projects_found else None

    def _label_for_entry(e):
        name = e.get('name') or Path(e.get('path') or '').name
        if e.get('source') == 'comparison':
            return f"{name} (Comparison)"

        if current_project:
            p = Path(e.get('path') or '')
            parts = list(p.parts)
            for idx, part in enumerate(parts):
                if part.lower() == 'vtk' and idx > 0:
                    if parts[idx - 1] == current_project:
                        return name

        p = Path(e.get('path') or '')
        parts = list(p.parts)
        proj = None
        for idx, part in enumerate(parts):
            if part.lower() == 'vtk' and idx > 0:
                proj = parts[idx - 1]
                break
        return f"{proj}/{name}" if proj else name

    group_options = [{'label': _label_for_entry(e), 'value': e['path']} for e in available_group_entries]

    has_selection = bool(panels_for_group)
    # Use stored values from State if available, regardless of whether files are selected
    # This preserves control settings when switching tabs
    print(f"[DEBUG UI] stored.get('range_min')={stored.get('range_min')}, stored.get('range_max')={stored.get('range_max')}, interfaces={stored.get('interfaces_overlay_visible')}")
    settings, scalar_options, palette_options = _comparison_settings(
        panels_for_group,
        scalar_value=stored.get('scalar'),
        range_min=stored.get('range_min'),
        range_max=stored.get('range_max'),
        palette_value=stored.get('palette'),
        full_scale=stored.get('full_scale', False),
        slider_range=stored.get('slider_range'),
        interfaces_overlay_visible=stored.get('interfaces_overlay_visible', False),
    )
    print(f"[DEBUG UI] After _comparison_settings: settings['range_min']={settings.get('range_min')}, settings['range_max']={settings.get('range_max')}, interfaces={settings.get('interfaces_overlay_visible')}")
    slider_min_default, slider_max_default = _comparison_range_defaults(panels_for_group, settings['scalar'])
    if slider_min_default is None or slider_max_default is None:
        slider_min_default, slider_max_default = 0.0, 1.0
    slider_value_min = settings['range_min'] if settings['range_min'] is not None else slider_min_default
    slider_value_max = settings['range_max'] if settings['range_max'] is not None else slider_max_default

    controls_layout = html.Div([
        html.Div([
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'comparison-project-picker', 'group': group},
                        options=project_options,
                        value=current_project,
                        placeholder="Select Folder",
                        clearable=True,
                        searchable=False,
                        persistence=True,
                        persistence_type='session',
                    )
                ], className='dropdown-wrapper')
            ], className='control-pair project-control-pair'),

            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'comparison-vtk-picker', 'group': group},
                        options=group_options,
                        value=selected_paths,
                        multi=True,
                        placeholder=f"Select File",
                        clearable=True,
                        searchable=False,
                        className='comparison-file-picker'
                    )
                ], className='dropdown-wrapper')
            ], className='control-pair'),

            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'comparison-heatmap-field', 'group': group},
                        options=scalar_options,
                        value=settings['scalar'],
                        clearable=False,
                        searchable=False,
                        disabled=not has_selection,
                        placeholder="Select files first…" if not has_selection else "Select Field",
                    )
                ], className='dropdown-wrapper')
            ], className='control-pair')
        ], className='controls-flex-row'),

        html.Div([
            html.Label([
                html.Img(src='/assets/bar-chart.png', className="label-img"),
                "Range:",
            ], className='field-label grid-label'),
            dcc.Input(
                id={'type': 'comparison-heatmap-range-min', 'group': group},
                type='number',
                value=settings['range_min'],
                step='any',
                placeholder='Min',
                disabled=not has_selection,
            ),
            dcc.Input(
                id={'type': 'comparison-heatmap-range-max', 'group': group},
                type='number',
                value=settings['range_max'],
                step='any',
                placeholder='Max',
                disabled=not has_selection,
            ),
            html.Button(
                html.Img(src='/assets/Reset.png', alt='Reset', className='btn-icon'),
                id={'type': 'comparison-heatmap-reset', 'group': group},
                n_clicks=0,
                className='btn btn-danger reset-btn',
                title='Reset range',
                disabled=not has_selection
            ),
        ], className='controls-grid-row range-row-extended'),

        html.Div([
            html.Label([
                html.Img(src='/assets/color-scale.png', className="label-img"),
            ], className='field-label grid-label'),

            html.Div([
                dcc.Dropdown(
                    id={'type': 'comparison-heatmap-palette', 'group': group},
                    options=palette_options,
                    value=settings['palette'],
                    clearable=False,
                    searchable=False,
                )
            ], className='dropdown-wrapper'),

            html.Div([
                dcc.RangeSlider(
                    id={'type': 'comparison-heatmap-range-slider', 'group': group},
                    min=slider_min_default,
                    max=slider_max_default,
                    value=[slider_value_min, slider_value_max],
                    marks=None,
                    allowCross=False,
                    tooltip={"placement": "bottom", "always_visible": True},
                    className='range-slider-dual comparison-range-slider',
                    disabled=not has_selection
                )
            ], className='range-slider-track'),

            html.Div([
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
                )
            ], className='scan-option scan-option--inline'),

            html.Div([
                dmc.Switch(
                    id={'type': 'comparison-overlay-toggle', 'group': group},
                    label="Show Interfaces",
                    checked=settings.get('interfaces_overlay_visible', False),
                    labelPosition="right",
                    size="xs",
                    radius="xs",
                    color="#c50623",
                    withThumbIndicator=True,
                    disabled=not has_selection,
                )
            ], className='scan-option scan-option--inline')
        ], className='range-slider-row range-slider-with-mode')
    ])

    # Range selector doesn't need persistence - always reset on tab render
    range_selector_store = dcc.Store(
        id={'type': 'comparison-range-selection', 'group': group},
        data={'click_count': 0, 'first_click': None},
        storage_type='session',
    )
    clear_flag_store = dcc.Store(
        id={'type': 'comparison-clear-flag', 'group': group},
        data=False,
        storage_type='memory',
    )

    # Only initialize data if we have selected paths from arguments, otherwise load from sessionStorage
    group_selected_store_props = {
        'id': {'type': 'comparison-selected-files-store', 'group': group},
        'storage_type': 'session',
    }
    if selected_paths:  # Only set data if we have paths to initialize
        group_selected_store_props['data'] = selected_paths
    group_selected_store = dcc.Store(**group_selected_store_props)

    # Initialize data if State has controls (during tab switches), otherwise let clientside restore from sessionStorage
    group_controls_store_props = {
        'id': {'type': 'comparison-controls-store', 'group': group},
        'storage_type': 'session',
    }
    if stored:  # If we have any data from State, use it to prevent reset during tab switches
        group_controls_store_props['data'] = {
            'scalar': settings['scalar'],
            'range_min': settings['range_min'],
            'range_max': settings['range_max'],
            'palette': settings['palette'],
            'full_scale': settings['full_scale'],
            'interfaces_overlay_visible': settings.get('interfaces_overlay_visible', False),
            'slider_range': [slider_value_min, slider_value_max],
        }
        print(f"[DEBUG UI] Creating store with data: range_min={settings['range_min']}, range_max={settings['range_max']}")
    else:
        print(f"[DEBUG UI] Creating store WITHOUT data (will load from sessionStorage)")
    group_controls_store = dcc.Store(**group_controls_store_props)

    heatmap_sections = []
    if panels_for_group:
        heatmap_sections = build_comparison_heatmap_row(panels_for_group, selected_entries, settings, group, app=app)

    comparison_block = html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3(f'Comparison: {group}', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            controls_layout,
            html.Div(id={'type': 'comparison-remove-file-dummy', 'group': group}, style={'display': 'none'}),
            range_selector_store,
            clear_flag_store,
            group_selected_store,
            group_controls_store,
            html.Div(heatmap_sections, id={'type': 'comparison-heatmap-rows', 'group': group}, className='comparison-heatmap-area-inner')
        ], className='comparison-heatmap-area')
    ], className='dataset-block comparison-card comparison-heatmap-panel')
    # ---- End inlined card builder logic ----

    cards.append(comparison_block)
    return [html.Div(cards, className='comparison-root')]
