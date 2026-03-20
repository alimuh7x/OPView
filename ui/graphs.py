"""
Graphs tab UI builder for TextData file plotting.

Extracted Phase 17 - dedicated tab for text file visualization.
"""

from pathlib import Path
from typing import List, Dict, Optional
from dash import html, dcc
import plotly.graph_objects as go
import numpy as np


def build_graphs_tab_layout(textdata_files):
    """Build the Graphs tab layout.

    Args:
        textdata_files: List of available TextData file paths

    Returns:
        Dash layout component with file selector and graph cards grid
    """
    # File picker dropdown - show project name and filename
    file_options = []
    for f in textdata_files:
        file_path = Path(f)
        # Get project name (parent of TextData folder)
        project_name = file_path.parent.parent.name if file_path.parent.name == 'TextData' else 'Unknown'
        label = f"{project_name} / {file_path.name}"
        file_options.append({'label': label, 'value': str(f)})

    # Show message if no files available
    if not file_options:
        return html.Div([
            html.Div(
                "No TextData files found. Please load a project folder that contains a TextData directory.",
                className='dataset-empty',
                style={'padding': '40px', 'text-align': 'center'}
            )
        ])

    # Return just the file selector - cards container already exists in main layout
    return html.Div([
        html.Label("Select a TextData file to add a graph:",
                  style={'marginBottom': '8px', 'fontWeight': '500', 'fontSize': '14px'}),
        dcc.Dropdown(
            id='graphs-file-selector',
            options=file_options,
            value=None,
            placeholder="Choose a text file to plot...",
            clearable=True,
            style={'width': '500px'}
        )
    ], style={'marginBottom': '20px'})


def build_graph_card(file_path: str, available_columns: List[str], selected_columns: List[str] = None) -> html.Div:
    """Build a single graph card for a text file.

    Args:
        file_path: Path to the text file
        available_columns: List of column names available in the file
        selected_columns: Previously selected columns (optional, defaults to empty)

    Returns:
        Card component with header, controls, and graph
    """
    from ui.components import card_header

    path = Path(file_path)
    # Get project name and filename for display
    project_name = path.parent.parent.name if path.parent.name == 'TextData' else 'Unknown'
    card_title = f"{project_name} / {path.name}"

    # Use provided selections, or default to empty (user must select columns)
    if selected_columns is None:
        default_columns = []
    else:
        default_columns = selected_columns

    return html.Div([
        # Header with close button
        html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(card_title, className='dataset-title')
            ], style={'flex': '1'}),
            html.Button(
                '×',
                id={'type': 'graph-close-btn', 'file': file_path},
                className='graph-close-btn',
                style={
                    'background': 'none',
                    'border': 'none',
                    'color': '#999',
                    'fontSize': '28px',
                    'cursor': 'pointer',
                    'padding': '0 8px',
                    'lineHeight': '1'
                }
            )
        ], className='dataset-header', style={'display': 'flex', 'alignItems': 'center'}),

        # Card body with controls and graph
        html.Div([
            # Controls section
            html.Div([
                html.Label("Select columns:", style={
                    'marginBottom': '8px',
                    'fontWeight': '500',
                    'fontSize': '13px',
                    'color': '#666'
                }),
                dcc.Checklist(
                    id={'type': 'graph-column-selector', 'file': file_path},
                    options=[{'label': col, 'value': col} for col in available_columns],
                    value=default_columns,
                    inline=True,  # Horizontal layout
                    className='graph-column-checklist',
                    labelStyle={
                        'display': 'inline-flex',
                        'alignItems': 'center',
                        'marginRight': '15px',
                        'marginBottom': '8px',
                        'fontSize': '13px'
                    },
                    inputStyle={'marginRight': '5px'}
                )
            ], style={'marginBottom': '15px'}),

            # Graph
            dcc.Graph(
                id={'type': 'graph-plot', 'file': file_path},
                config={'displayModeBar': True, 'displaylogo': False},
                style={'height': '400px'}
            )
        ], className='dataset-body')
    ], className='dataset-block')


def get_textdata_files(loaded_project_folders=None) -> List[str]:
    """Get list of all text files from loaded project folders.

    Scans all loaded project folders for text/CSV files in any subdirectory.
    Looks for .txt, .dat, and .csv files in TextData/ first, then other subdirectories.

    Args:
        loaded_project_folders: List of loaded project folder names (e.g., ['Fracture', 'Test1'])

    Returns:
        List of absolute file paths
    """
    text_files = []

    if not loaded_project_folders:
        return []

    # Get discovered folders dict to resolve full paths
    import OPView
    use_context = OPView.app_context is not None
    folders_dict = OPView.app_context.discovered_project_folders if use_context else OPView.discovered_project_folders

    # File patterns to search for
    patterns = ['*.txt', '*.dat', '*.csv']

    # Scan each loaded project folder
    for project_name in loaded_project_folders:
        # Resolve full path from folder name
        folder_info = folders_dict.get(project_name)
        if not folder_info:
            continue

        # If the selected entry is already a TextData folder, scan it directly.
        if folder_info.get('has_textdata') and folder_info.get('textdata_path'):
            textdata_dir = Path(folder_info['textdata_path'])
            if textdata_dir.exists() and textdata_dir.is_dir():
                for pattern in patterns:
                    text_files.extend(textdata_dir.glob(pattern))
            continue

        # Fallback (not used with current UI): treat as project root and look for TextData child + other subdirs.
        project_dir = Path(folder_info['path'])
        if not project_dir.exists():
            continue

        textdata_dir = project_dir / 'TextData'
        if textdata_dir.exists() and textdata_dir.is_dir():
            for pattern in patterns:
                text_files.extend(textdata_dir.glob(pattern))

        try:
            for subdir in project_dir.iterdir():
                if subdir.is_dir() and subdir.name not in ['TextData', 'VTK', 'vtk', 'RawData', '.git', '__pycache__']:
                    for pattern in patterns:
                        text_files.extend(subdir.glob(pattern))
        except (OSError, PermissionError):
            continue

    # Sort by filename and return as strings (remove duplicates)
    return sorted(list(set([str(f) for f in text_files])))


def _build_x_axis_column_options(selected_files: List[str]) -> List[Dict]:
    """Build x-axis column options - ALL unique columns from all selected files.

    Args:
        selected_files: List of selected file paths

    Returns:
        List of dropdown options with all unique column names from all files
    """
    from data.sources import GenericTextDataSource

    if not selected_files:
        # No files selected - provide generic options
        return [{'label': f'Column {i+1}', 'value': f'col_{i}'} for i in range(5)]

    # Collect all unique columns from all files (preserving order)
    all_columns = []
    seen_columns = set()

    for file_path in selected_files:
        try:
            ds = GenericTextDataSource(Path(file_path))
            if ds.load():
                # Get ALL columns directly from dataframe (including first column)
                columns = ds._data.columns.tolist() if hasattr(ds._data, 'columns') else []
                for col in columns:
                    if col not in seen_columns:
                        all_columns.append(col)
                        seen_columns.add(col)
        except Exception as e:
            print(f"Error loading columns from {file_path}: {e}")
            continue

    # Build options with all unique columns
    options = []
    if all_columns:
        for col in all_columns:
            options.append({'label': col, 'value': col})
    else:
        # No files loaded successfully - provide generic options
        options = [{'label': f'Column {i+1}', 'value': f'col_{i}'} for i in range(5)]

    return options


def _build_column_settings_table(panel_id: str, panel_state: Dict) -> html.Div:
    """Build compact settings list for selected columns only (Units + Y-Axis).

    Args:
        panel_id: Panel identifier
        panel_state: Panel state dict containing files, columns_by_file, column_settings

    Returns:
        html.Div containing compact settings list for selected columns
    """
    from pathlib import Path

    # Get selected columns from all files
    selected_columns = []
    columns_by_file = panel_state.get('columns_by_file', {})
    column_settings = panel_state.get('column_settings', {})

    for file_path, columns in columns_by_file.items():
        file_name = Path(file_path).name
        for col in columns:
            # Get current settings for this column
            file_settings = column_settings.get(file_path, {})
            col_setting = file_settings.get(col, {})
            unit = col_setting.get('unit', 'Raw')
            yaxis = col_setting.get('yaxis', 'y1')
            legend = col_setting.get('legend', col)  # Default to column name

            selected_columns.append({
                'file': file_path,
                'file_name': file_name,
                'column': col,
                'unit': unit,
                'yaxis': yaxis,
                'legend': legend
            })

    if not selected_columns:
        return html.Div("No columns selected", style={'fontSize': '14px', 'fontStyle': 'italic', 'color': '#888'})

    # Build compact column rows (only showing Y-Axis selection)
    column_rows = []
    for item in selected_columns:
        # Get custom legend label, default to column name
        legend_label = item.get('legend', item['column'])

        column_rows.append(
            html.Div([
                # Column label
                html.Div(f"{item['file_name']} → {item['column']}",
                        style={'fontSize': '14px', 'fontWeight': '500', 'marginBottom': '4px'}),
                # Legend label input and Y-Axis radio buttons in one row
                html.Div([
                    html.Label("Legend:", style={'fontSize': '13px', 'marginRight': '4px', 'color': '#666'}),
                    dcc.Input(
                        id={'type': 'multifile-column-legend', 'panel': panel_id,
                            'file': item['file'], 'column': item['column']},
                        type='text',
                        value=legend_label,
                        placeholder=item['column'],
                        style={'width': '100%', 'maxWidth': '200px', 'padding': '4px', 'fontSize': '14px', 'marginRight': '16px'}
                    ),
                    html.Label("Y-Axis:", style={'fontSize': '13px', 'marginRight': '8px', 'color': '#666'}),
                    dcc.RadioItems(
                        id={'type': 'multifile-column-yaxis', 'panel': panel_id,
                            'file': item['file'], 'column': item['column']},
                        options=[
                            {'label': 'Y1', 'value': 'y1'},
                            {'label': 'Y2', 'value': 'y2'}
                        ],
                        value=item['yaxis'],
                        inline=True,
                        labelStyle={'marginRight': '12px', 'fontSize': '14px'},
                        inputStyle={'marginRight': '4px'}
                    ),
                ], style={'display': 'flex', 'alignItems': 'center'}),
            ], style={'marginBottom': '12px', 'paddingBottom': '12px', 'borderBottom': '1px solid #eee'})
        )

    return html.Div(column_rows)


def build_multifile_panel(panel_id: str, available_files: List[str],
                         panel_state: Optional[Dict] = None) -> html.Div:
    """Build a graph panel with file selector, column checklists, and graph.

    Supports 1-3 files with optional separate y-axes.

    Args:
        panel_id: Unique identifier (e.g., 'panel_0')
        available_files: List of TextData file paths
        panel_state: Dict with 'files', 'columns_by_file', 'separate_yaxes'

    Returns:
        Graph panel component
    """
    from data.sources import GenericTextDataSource

    # Initialize state if not provided
    if panel_state is None:
        panel_state = {
            'files': [],
            'columns_by_file': {},
            'separate_yaxes': False,
            'x_axis_title': 'Time',
            'y_axis_title': 'Value',
            'yaxis_titles': {},  # Separate titles for each y-axis when separate_yaxes enabled
            'unit_conversion': 'Raw',  # Raw, MPa, GPa, %
            'legend_position': 'top-left',  # top-left, top-right, bottom-left, bottom-right
            'legend_title': '',  # Custom legend title
            'show_grid': True,  # Show/hide grid lines
            'show_legend': True,  # Show/hide legend
            'x_axis_column': None,  # Which column to use as x-axis (column name)
            'source_mode': 'file',
            'pasted_data': '',  # Excel/CSV style pasted text
            'extend_two_point_lines': False,
            'show_intersections': False,
            'show_roots_intercepts': False,
            'line_range_min': 0.0,
            'line_range_max': 1.0,
            'pasted_point_mode': 'line_only',
            'pasted_marker_count': 25,
        }

    # Set default x_axis_column to first column of first file if not set
    if not panel_state.get('x_axis_column'):
        files = panel_state.get('files', [])
        if files:
            from data.sources import GenericTextDataSource
            try:
                ds = GenericTextDataSource(Path(files[0]))
                if ds.load():
                    cols = ds.get_available_columns()
                    if cols:
                        panel_state['x_axis_column'] = cols[0]
            except Exception:
                pass
        # Fallback if no files or can't load
        if not panel_state.get('x_axis_column'):
            panel_state['x_axis_column'] = 'col_0'

    # Build file selector options
    file_options = []
    for f in available_files:
        file_path = Path(f)
        # Get project name (parent of TextData folder)
        project_name = file_path.parent.parent.name if file_path.parent.name == 'TextData' else 'Unknown'
        label = f"{project_name} / {file_path.name}"
        file_options.append({'label': label, 'value': f})

    # Build file selector dropdown (multi-select 1-3 files)
    file_selector = dcc.Dropdown(
        id={'type': 'multifile-file-selector', 'panel': panel_id},
        options=file_options,
        value=panel_state.get('files', []),
        multi=True,
        placeholder="Select 1-3 files...",
        className='multifile-file-selector'
    )

    # Build per-file column sections (simple checkboxes)
    file_sections = []
    for file_path in panel_state.get('files', [])[:3]:  # Limit to 3 files
        # Load file to get columns
        try:
            data_source = GenericTextDataSource(Path(file_path))
            if data_source.load():
                columns = data_source.get_available_columns()
                selected = panel_state.get('columns_by_file', {}).get(file_path, [])

                # Get just the filename for display
                file_name = Path(file_path).name

                file_sections.append(
                    html.Div([
                        html.Label(file_name, className='multifile-file-label'),
                        dcc.Checklist(
                            id={'type': 'multifile-column-selector',
                                'panel': panel_id, 'file': file_path},
                            options=[{'label': col, 'value': col} for col in columns],
                            value=selected,
                            inline=True,
                            className='graph-column-checklist',
                            labelStyle={
                                'display': 'inline-flex',
                                'alignItems': 'center',
                                'marginRight': '12px',
                                'marginBottom': '6px',
                                'fontSize': '12px'
                            },
                            inputStyle={'marginRight': '4px'}
                        )
                    ], className='multifile-file-section')
                )
        except Exception:
            # Skip files that can't be loaded
            continue

    # Extract panel number for display (use count from state instead of ID)
    # Count existing panels to get sequential number
    if panel_state and 'panel_number' in panel_state:
        panel_num = panel_state['panel_number']
    else:
        # Fallback to parsing ID
        panel_num = panel_id.split('_')[-1] if '_' in panel_id else '0'

    source_mode = panel_state.get('source_mode', 'file')

    # Panel layout - Two column design: Graph (left) | Controls (right)
    # Panel layout - Hybrid Design (Top Data, Right Settings)
    is_file_mode = source_mode == 'file'

    return html.Div([
        # Header with close button
        html.Div([
            html.Div([
                html.Div([
                    html.H3(f"Graph Panel {panel_num}", className='dataset-title', style={'marginBottom': '4px'}),
                    html.Div(
                        "Data Mode",
                        style={
                            'display': 'inline-block',
                            'padding': '4px 10px',
                            'borderRadius': '999px',
                            'fontSize': '12px',
                            'fontWeight': '700',
                            'letterSpacing': '0.04em',
                            'textTransform': 'uppercase',
                            'background': '#dcfce7',
                            'color': '#0f172a',
                        }
                    ) if not is_file_mode else html.Div(),
                ]),
            ], style={'flex': '1'}),
            html.Button(
                '×',
                id={'type': 'multifile-close-btn', 'panel': panel_id},
                className='graph-close-btn',
                style={
                    'background': 'none',
                    'border': 'none',
                    'color': '#999',
                    'fontSize': '28px',
                    'cursor': 'pointer',
                    'padding': '0 8px',
                    'lineHeight': '1'
                }
            )
        ], className='dataset-header', style={'display': 'flex', 'alignItems': 'center'}),

        # TOP AREA: DATA SELECTION
        html.Div([
            # Files Selection
            html.Div([
                html.Label("Data Sources:", className='multifile-label'),
                file_selector,
            ], style={
                'marginBottom': '12px',
                'display': 'block' if source_mode == 'file' else 'none'
            }),

            html.Div([
                html.Label("Add Data:", className='multifile-label'),
                dcc.Textarea(
                    id={'type': 'multifile-pasted-data', 'panel': panel_id},
                    value=panel_state.get('pasted_data', ''),
                    placeholder=(
                        "Paste Excel / CSV data here.\n\n"
                        "One dataset with shared x:\n"
                        "x<TAB>Line A<TAB>Line B\n0<TAB>1<TAB>2\n1<TAB>3<TAB>5\n\n"
                        "Different x/y for each dataset: separate blocks with blank lines\n"
                        "0<TAB>1\n1<TAB>3\n\n"
                        "0.2<TAB>5\n0.8<TAB>9"
                    ),
                    style={
                        'width': '100%',
                        'minHeight': '130px',
                        'padding': '10px 12px',
                        'fontSize': '13px',
                        'fontFamily': 'monospace',
                        'border': '1px solid #dbe3ef',
                        'borderRadius': '10px',
                        'resize': 'vertical',
                        'marginBottom': '6px',
                    },
                ),
                html.Div(
                    "Blank lines create separate datasets. This lets you plot multiple lines even when each dataset has a different x column.",
                    style={'fontSize': '12px', 'color': '#64748b'}
                ),
            ], style={
                'marginBottom': '12px',
                'display': 'block' if source_mode == 'data' else 'none'
            }),

            # Columns Selection (Grid)
            html.Div([
                html.Div(file_sections, className='multifile-columns-grid'),
            ], style={'display': 'block' if file_sections and source_mode == 'file' else 'none', 'marginBottom': '4px'}),
        ], className='multifile-top-controls', style={
            'background': '#f8f9fa',
            'borderBottom': '1px solid #e0e0e0',
            'padding': '16px 16px 8px 16px',
            'flexShrink': '0',
        } if is_file_mode else None),

        # MAIN CONTENT AREA (Split View)
        html.Div([
            # LEFT: GRAPH
            html.Div([
                html.Div([
                    html.Img(
                        src='/assets/OP_Logo.png',
                        className='multifile-logo',
                        alt='OP logo'
                    ),
                    dcc.Graph(
                        id={'type': 'multifile-plot', 'panel': panel_id},
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '700px', 'width': '1000px'}
                    ),
                ], className='multifile-plot-shell', style={
                    'position': 'relative',
                    'width': '1000px',
                    'maxWidth': '1000px',
                    'margin': '0',
                }),
            ], className='multifile-graph-area', style={
                'flex': '1',
                'position': 'relative',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'minWidth': '0',
                'padding': '10px',
                'overflow': 'auto',
            }),

            # RIGHT: SETTINGS SIDEBAR
            html.Div([
                html.H4("Settings", className='multifile-settings-header', style={'fontSize': '16px'}),

                # X-Axis Settings
                html.Div([
                     html.Label("X-Axis", className='multifile-sublabel', style={'fontSize': '15px'}),
                     html.Div([
                        html.Div([
                            html.Label("Column:", className='multifile-mini-label', style={'fontSize': '14px'}),
                            dcc.Dropdown(
                                id={'type': 'multifile-x-axis-column', 'panel': panel_id},
                                options=_build_x_axis_column_options(panel_state.get('files', [])),
                                value=panel_state.get('x_axis_column'),
                                clearable=False,
                                style={'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                        ], style={'display': 'block' if source_mode == 'file' else 'none'}),
                        html.Div(
                            "Each pasted dataset carries its own x-values, so no shared x-column is needed in data mode.",
                            style={
                                'display': 'block' if source_mode == 'data' else 'none',
                                'fontSize': '12px',
                                'color': '#64748b',
                                'marginBottom': '8px',
                                'lineHeight': '1.45',
                            }
                        ),
                        html.Label("Title:", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Input(
                            id={'type': 'multifile-x-axis-title', 'panel': panel_id},
                            type='text',
                            value=panel_state.get('x_axis_title', 'Time'),
                            placeholder='X-axis title...',
                            style={'width': '100%', 'padding': '5px', 'fontSize': '14px', 'marginBottom': '8px'}
                        ),
                     ], className='multifile-setting-group')
                ], className='multifile-setting-section'),

                html.Div([
                     html.Label("Line Construction", className='multifile-sublabel', style={'fontSize': '15px'}),
                     html.Div([
                        dcc.Checklist(
                            id={'type': 'multifile-extend-two-point-lines', 'panel': panel_id},
                            options=[{'label': 'Extend lines', 'value': 'extend'}],
                            value=['extend'] if panel_state.get('extend_two_point_lines', False) else [],
                            style={'marginBottom': '10px'},
                            labelStyle={'fontSize': '13px'}
                        ),
                        dcc.Checklist(
                            id={'type': 'multifile-show-intersections', 'panel': panel_id},
                            options=[{'label': 'Show intersections', 'value': 'show'}],
                            value=['show'] if panel_state.get('show_intersections', False) else [],
                            style={'marginBottom': '10px'},
                            labelStyle={'fontSize': '13px'}
                        ),
                        dcc.Checklist(
                            id={'type': 'multifile-show-roots-intercepts', 'panel': panel_id},
                            options=[{'label': 'Show roots', 'value': 'show'}],
                            value=['show'] if panel_state.get('show_roots_intercepts', False) else [],
                            style={'marginBottom': '10px'},
                            labelStyle={'fontSize': '13px'}
                        ),
                        html.Div("When enabled, any dataset with exactly two points is extended across the x-range below.", style={'fontSize': '12px', 'color': '#64748b', 'marginBottom': '8px', 'lineHeight': '1.45'}),
                        html.Div([
                            html.Div([
                                html.Label("X Min", className='multifile-mini-label', style={'fontSize': '14px'}),
                                dcc.Input(
                                    id={'type': 'multifile-line-range-min', 'panel': panel_id},
                                    type='number',
                                    value=panel_state.get('line_range_min', 0.0),
                                    debounce=True,
                                    style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                                ),
                            ], style={'flex': '1'}),
                            html.Div([
                                html.Label("X Max", className='multifile-mini-label', style={'fontSize': '14px'}),
                                dcc.Input(
                                    id={'type': 'multifile-line-range-max', 'panel': panel_id},
                                    type='number',
                                    value=panel_state.get('line_range_max', 1.0),
                                    debounce=True,
                                    style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                                ),
                            ], style={'flex': '1'}),
                        ], style={'display': 'flex', 'gap': '10px'}),
                     ], className='multifile-setting-group')
                ], className='multifile-setting-section', style={'display': 'block' if source_mode == 'data' else 'none'}),

                html.Div([
                     html.Label("Pasted Data Points", className='multifile-sublabel', style={'fontSize': '15px'}),
                     html.Div([
                        dcc.Dropdown(
                            id={'type': 'multifile-pasted-point-mode', 'panel': panel_id},
                            options=[
                                {'label': 'Line Only', 'value': 'line_only'},
                                {'label': 'All Points', 'value': 'all_points'},
                                {'label': 'Sampled Points', 'value': 'sampled_points'},
                            ],
                            value=panel_state.get('pasted_point_mode', 'line_only'),
                            clearable=False,
                            style={'fontSize': '14px', 'marginBottom': '8px'}
                        ),
                        html.Label("Marker Count", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Input(
                            id={'type': 'multifile-pasted-marker-count', 'panel': panel_id},
                            type='number',
                            value=panel_state.get('pasted_marker_count', 25),
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                        ),
                        html.Div("Use Line Only for clean plots, or Sampled Points to show just a subset of markers.", style={'fontSize': '12px', 'color': '#64748b', 'marginTop': '8px', 'lineHeight': '1.45'}),
                     ], className='multifile-setting-group')
                ], className='multifile-setting-section', style={'display': 'block' if source_mode == 'data' else 'none'}),

                # Display Options
                html.Div([
                     html.Label("Display", className='multifile-sublabel', style={'fontSize': '15px'}),
                     html.Div([
                        html.Label("Legend Pos:", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Dropdown(
                            id={'type': 'multifile-legend-position', 'panel': panel_id},
                            options=[
                                {'label': 'Top Left', 'value': 'top-left'},
                                {'label': 'Top Right', 'value': 'top-right'},
                                {'label': 'Bottom Left', 'value': 'bottom-left'},
                                {'label': 'Bottom Right', 'value': 'bottom-right'}
                            ],
                            value=panel_state.get('legend_position', 'top-left'),
                            clearable=False,
                            style={'fontSize': '14px', 'marginBottom': '8px'}
                        ),
                        dcc.Checklist(
                            id={'type': 'multifile-display-options', 'panel': panel_id},
                            options=[
                                {'label': 'Legend', 'value': 'legend'},
                                {'label': 'Grid', 'value': 'grid'}
                            ],
                            value=(
                                (['legend'] if panel_state.get('show_legend', True) else []) +
                                (['grid'] if panel_state.get('show_grid', True) else [])
                            ),
                            inline=True,
                            labelStyle={'fontSize': '14px'},
                            style={'fontSize': '14px'}
                        ),
                        # Hidden inputs for state
                        dcc.Input(id={'type': 'multifile-legend-title', 'panel': panel_id}, type='text', value='', style={'display': 'none'}),
                     ], className='multifile-setting-group')
                ], className='multifile-setting-section'),

                # Y-Axis Settings
                html.Div([
                     html.Label("Y-Axis", className='multifile-sublabel', style={'fontSize': '15px'}),
                     html.Div([
                        html.Label("Y-Axis 1 Title:", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Input(
                            id={'type': 'multifile-y-axis-title', 'panel': panel_id},
                            type='text',
                            value=panel_state.get('y_axis_title', 'Value'),
                            placeholder='Y-axis 1 title...',
                            style={'width': '100%', 'padding': '5px', 'fontSize': '14px', 'marginBottom': '8px'}
                        ),
                        html.Label("Y-Axis 1 Units:", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Dropdown(
                            id={'type': 'multifile-yaxis1-units', 'panel': panel_id},
                            options=[
                                {'label': 'Raw', 'value': 'Raw'},
                                {'label': 'MPa', 'value': 'MPa'},
                                {'label': 'GPa', 'value': 'GPa'},
                                {'label': '%', 'value': '%'}
                            ],
                            value=panel_state.get('yaxis1_units', 'Raw'),
                            clearable=False,
                            style={'fontSize': '14px', 'marginBottom': '12px'}
                        ),
                        # Hidden mirror input
                        dcc.Input(id={'type': 'multifile-yaxis1-title', 'panel': panel_id},
                                 type='text', value=panel_state.get('y_axis_title', 'Value'), style={'display': 'none'}),

                        # Y-Axis 2 Settings
                        html.Div(
                            id={'type': 'multifile-yaxis-titles-container', 'panel': panel_id},
                            children=[
                            html.Label("Y-Axis 2 Title:", className='multifile-mini-label', style={'fontSize': '14px'}),
                            dcc.Input(
                                id={'type': 'multifile-yaxis2-title', 'panel': panel_id},
                                type='text',
                                value=panel_state.get('yaxis_titles', {}).get('y2', ''),
                                placeholder='Y-Axis 2 Title...',
                                style={'width': '100%', 'padding': '5px', 'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                            html.Label("Y-Axis 2 Units:", className='multifile-mini-label', style={'fontSize': '14px'}),
                            dcc.Dropdown(
                                id={'type': 'multifile-yaxis2-units', 'panel': panel_id},
                                options=[
                                    {'label': 'Raw', 'value': 'Raw'},
                                    {'label': 'MPa', 'value': 'MPa'},
                                    {'label': 'GPa', 'value': 'GPa'},
                                    {'label': '%', 'value': '%'}
                                ],
                                value=panel_state.get('yaxis2_units', 'Raw'),
                                clearable=False,
                                style={'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                        ], style={'display': 'block'})

                     ], className='multifile-setting-group')
                ], className='multifile-setting-section'),

                # Column Settings (Units + Y-Axis per column)
                html.Div([
                     html.Label("Column Settings", className='multifile-sublabel', style={'fontSize': '15px'}),
                     html.Div(
                         id={'type': 'multifile-column-settings-container', 'panel': panel_id},
                         children=_build_column_settings_table(panel_id, panel_state),
                         style={'marginBottom': '12px'}
                     ),
                ], className='multifile-setting-section'),
            ], className='multifile-settings-sidebar', style={
                'width': '650px',
                'maxWidth': '650px',
                'minWidth': '400px',
                'flexShrink': '1',
                'flexGrow': '0',
                'borderLeft': '1px solid #e0e0e0',
                'background': '#fafbfc',
                'padding': '16px',
                'overflowY': 'auto',
                'maxHeight': '800px',
                'display': 'grid',
                'gridTemplateColumns': '1fr 1fr',
                'gap': '16px',
                'alignContent': 'start',
            }),
        ], className='multifile-main-content', style={
            'display': 'flex',
            'flexDirection': 'row',
            'alignItems': 'stretch',
            'minHeight': '500px',
            'background': '#ffffff',
        }),
        html.Div(
            id={'type': 'multifile-analysis', 'panel': panel_id},
            className='multifile-analysis-section',
            style={'display': 'none'} if is_file_mode else None,
        ),

    ], className='dataset-block multifile-panel', id=f'multifile-{panel_id}')


def build_multifile_figure(files_and_columns: Dict[str, List[str]],
                          column_settings: Dict[str, Dict[str, Dict]] = None,
                          x_axis_title: str = 'Time',
                          y_axis_title: str = 'Value',
                          yaxis_titles: Dict[str, str] = None,
                          legend_position: str = 'top-left',
                          legend_title: str = '',
                          show_grid: bool = True,
                          show_legend: bool = True,
                          x_axis_column: str = 'auto',
                          yaxis1_units: str = 'Raw',
                          yaxis2_units: str = 'Raw',
                          pasted_data: str = '',
                          extend_two_point_lines: bool = False,
                          show_intersections: bool = False,
                          show_roots_intercepts: bool = False,
                          line_range_min: float | None = None,
                          line_range_max: float | None = None,
                          pasted_point_mode: str = 'line_only',
                          pasted_marker_count: int = 25) -> tuple[go.Figure, html.Div, tuple[float | None, float | None]]:
    """Build Plotly figure combining multiple files with per-yaxis unit settings.

    Args:
        files_and_columns: {'/path/file1.dat': ['Col1', 'Col2'], ...}
        column_settings: {'/path/file1.dat': {'Col1': {'yaxis': 'y1'}, ...}, ...}
        x_axis_title: Custom title for x-axis
        y_axis_title: Custom title for y-axis
        yaxis_titles: Dict of custom titles for each y-axis {'y1': 'Title 1', 'y2': ...}
        legend_position: Legend position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
        legend_title: Custom legend title
        show_grid: Whether to show grid lines
        show_legend: Whether to show legend
        x_axis_column: Which column to use as x-axis ('auto', 'col_0', 'col_1', etc.)
        yaxis1_units: Unit conversion for Y-Axis 1 ('Raw', 'MPa', 'GPa', '%')
        yaxis2_units: Unit conversion for Y-Axis 2 ('Raw', 'MPa', 'GPa', '%')

    Returns:
        Plotly figure with all traces and configured axes, and an analysis summary component
    """
    from data.sources import GenericTextDataSource

    if not files_and_columns and not (pasted_data or '').strip():
        # Return empty figure
        return go.Figure().update_layout(
            title="Select files and columns to display the graph",
            xaxis_title=x_axis_title,
            yaxis_title=y_axis_title,
            template='plotly_white'
        ), html.Div("Select files/columns or paste Excel data to display the graph."), (line_range_min, line_range_max)

    fig = go.Figure()

    # Color palette - Use black for publication-quality plots
    # If multiple traces, use distinguishable colors
    colors = [
        'black', '#d62728', '#2ca02c', '#1f77b4', '#9467bd',
        '#ff7f0e', '#8c564b', '#e377c2', '#bcbd22', '#17becf'
    ]

    # Unit conversion factors
    conversion_factors_map = {
        'Raw': 1.0,
        'MPa': 1e-6,   # Assumes data is in Pa
        'GPa': 1e-9,   # Assumes data is in Pa
        '%': 100.0     # Assumes data is in decimal (0-1 range)
    }

    # Initialize column_settings if not provided
    if column_settings is None:
        column_settings = {}

    # Initialize yaxis_titles if not provided
    if yaxis_titles is None:
        yaxis_titles = {}

    color_idx = 0
    yaxis_configs = {}
    analysis_cards = []
    plotted_x_values = []
    plotted_y_values = []

    def _safe_float(value):
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    def _parse_delimited_line(line: str) -> list[str]:
        stripped = line.strip()
        if '\t' in stripped:
            return [cell.strip() for cell in stripped.split('\t')]
        if ',' in stripped:
            return [cell.strip() for cell in stripped.split(',')]
        if ';' in stripped:
            return [cell.strip() for cell in stripped.split(';')]
        return [cell for cell in stripped.split() if cell]

    def _series_summary(title: str, x_values, y_values) -> html.Div:
        x_arr = np.asarray(x_values, dtype=float)
        y_arr = np.asarray(y_values, dtype=float)
        finite_mask = np.isfinite(x_arr) & np.isfinite(y_arr)
        x_arr = x_arr[finite_mask]
        y_arr = y_arr[finite_mask]
        if x_arr.size == 0:
            return html.Div([
                html.Div(title, style={'fontWeight': '700', 'fontSize': '14px', 'marginBottom': '4px'}),
                html.Div("No valid numeric points", style={'fontSize': '13px', 'color': '#64748b'})
            ], style={'padding': '12px', 'background': '#fff', 'border': '1px solid #e2e8f0', 'borderRadius': '10px'})

        rows = [
            html.Div(f"Points: {x_arr.size}", style={'fontSize': '13px'}),
            html.Div(f"X range: {x_arr.min():.6g} to {x_arr.max():.6g}", style={'fontSize': '13px'}),
            html.Div(f"Y range: {y_arr.min():.6g} to {y_arr.max():.6g}", style={'fontSize': '13px'}),
        ]
        if x_arr.size == 2:
            dx = x_arr[1] - x_arr[0]
            dy = y_arr[1] - y_arr[0]
            if np.isclose(dx, 0.0):
                rows.append(html.Div(f"Line: x = {x_arr[0]:.6g}", style={'fontSize': '13px', 'fontWeight': '600'}))
                rows.append(html.Div("Slope: undefined (vertical line)", style={'fontSize': '13px', 'fontWeight': '600'}))
                rows.append(html.Div(f"Root / x-intercept: x = {x_arr[0]:.6g}", style={'fontSize': '13px'}))
            else:
                slope = dy / dx
                intercept = y_arr[0] - slope * x_arr[0]
                rows.append(html.Div(f"Slope: {slope:.6g}", style={'fontSize': '13px', 'fontWeight': '600'}))
                rows.append(html.Div(f"Equation: y = {slope:.6g}x + {intercept:.6g}", style={'fontSize': '13px', 'fontWeight': '600'}))
                rows.append(html.Div(f"Y-intercept: {intercept:.6g}", style={'fontSize': '13px'}))
                if np.isclose(slope, 0.0):
                    root_text = "none" if not np.isclose(intercept, 0.0) else "all x"
                else:
                    root_text = f"{(-intercept / slope):.6g}"
                rows.append(html.Div(f"Root / x-intercept: {root_text}", style={'fontSize': '13px'}))
        elif x_arr.size > 2:
            overall_dx = x_arr[-1] - x_arr[0]
            if np.isclose(overall_dx, 0.0):
                rows.append(html.Div("Overall slope: undefined", style={'fontSize': '13px', 'fontWeight': '600'}))
            else:
                overall_slope = (y_arr[-1] - y_arr[0]) / overall_dx
                rows.append(html.Div(f"Overall slope (first-last): {overall_slope:.6g}", style={'fontSize': '13px', 'fontWeight': '600'}))
            segment_slopes = []
            for idx in range(len(x_arr) - 1):
                dx = x_arr[idx + 1] - x_arr[idx]
                dy = y_arr[idx + 1] - y_arr[idx]
                slope_text = "undefined" if np.isclose(dx, 0.0) else f"{(dy / dx):.6g}"
                segment_slopes.append(f"{idx + 1}-{idx + 2}: {slope_text}")
            if segment_slopes:
                rows.append(html.Div("Segment slopes: " + ", ".join(segment_slopes[:6]), style={'fontSize': '13px'}))

        return html.Div([
            html.Div(title, style={'fontWeight': '700', 'fontSize': '14px', 'marginBottom': '6px', 'color': '#102a43'}),
            *rows,
        ], style={'padding': '12px', 'background': '#fff', 'border': '1px solid #e2e8f0', 'borderRadius': '10px'})

    def _resolve_line_range(default_x_values=None) -> tuple[float, float] | None:
        values = np.asarray(default_x_values if default_x_values is not None else [], dtype=float)
        finite_values = values[np.isfinite(values)]
        left = float(line_range_min) if line_range_min not in (None, '') else (float(finite_values.min()) if finite_values.size else 0.0)
        right = float(line_range_max) if line_range_max not in (None, '') else (float(finite_values.max()) if finite_values.size else 1.0)
        if np.isclose(left, right):
            return None
        return (left, right) if left < right else (right, left)

    def _two_point_line_geometry(x_values, y_values):
        x_arr = np.asarray(x_values, dtype=float)
        y_arr = np.asarray(y_values, dtype=float)
        finite_mask = np.isfinite(x_arr) & np.isfinite(y_arr)
        x_arr = x_arr[finite_mask]
        y_arr = y_arr[finite_mask]
        if x_arr.size != 2 or y_arr.size != 2:
            return None
        dx = x_arr[1] - x_arr[0]
        dy = y_arr[1] - y_arr[0]
        if np.isclose(dx, 0.0):
            return {
                'kind': 'vertical',
                'x_const': float(x_arr[0]),
                'points': (x_arr, y_arr),
            }
        slope = dy / dx
        intercept = y_arr[0] - slope * x_arr[0]
        return {
            'kind': 'line',
            'slope': float(slope),
            'intercept': float(intercept),
            'points': (x_arr, y_arr),
        }

    def _build_intersection_card(intersections: list[dict]) -> html.Div:
        rows = [
            html.Div(
                f"{item['a']} x {item['b']}: ({item['x']:.6g}, {item['y']:.6g})",
                style={'fontSize': '13px'}
            )
            for item in intersections
        ]
        return html.Div([
            html.Div("Line Intersections", style={'fontWeight': '700', 'fontSize': '14px', 'marginBottom': '6px', 'color': '#102a43'}),
            *rows,
        ], style={'padding': '12px', 'background': '#fff', 'border': '1px solid #e2e8f0', 'borderRadius': '10px'})

    def _build_line_pair_card(line_a: dict, line_b: dict) -> html.Div:
        rows = []
        if line_a['kind'] == 'line' and line_b['kind'] == 'line':
            if np.isclose(line_a['slope'], line_b['slope']):
                relation = 'parallel' if not np.isclose(line_a['intercept'], line_b['intercept']) else 'coincident'
                rows.append(html.Div(f"Relation: {relation}", style={'fontSize': '13px'}))
                if relation == 'parallel':
                    distance = abs(line_b['intercept'] - line_a['intercept']) / np.sqrt(line_a['slope'] ** 2 + 1.0)
                    rows.append(html.Div(f"Distance between lines: {distance:.6g}", style={'fontSize': '13px'}))
            else:
                angle = np.degrees(np.arctan(abs((line_b['slope'] - line_a['slope']) / (1 + line_a['slope'] * line_b['slope']))))
                rows.append(html.Div(f"Angle between lines: {angle:.6g} deg", style={'fontSize': '13px'}))
                rows.append(html.Div("Relation: perpendicular", style={'fontSize': '13px'}) if np.isclose(line_a['slope'] * line_b['slope'], -1.0) else html.Div("Relation: intersecting", style={'fontSize': '13px'}))
        elif line_a['kind'] == 'vertical' and line_b['kind'] == 'vertical':
            relation = 'coincident' if np.isclose(line_a['x_const'], line_b['x_const']) else 'parallel'
            rows.append(html.Div(f"Relation: {relation}", style={'fontSize': '13px'}))
            if relation == 'parallel':
                rows.append(html.Div(f"Distance between lines: {abs(line_b['x_const'] - line_a['x_const']):.6g}", style={'fontSize': '13px'}))
        else:
            non_vertical = line_a if line_a['kind'] == 'line' else line_b
            rows.append(html.Div("Relation: intersecting", style={'fontSize': '13px'}))
            angle = 90.0 - np.degrees(np.arctan(non_vertical['slope']))
            rows.append(html.Div(f"Angle between lines: {abs(angle):.6g} deg", style={'fontSize': '13px'}))

        return html.Div([
            html.Div("Line Pair Analysis", style={'fontWeight': '700', 'fontSize': '14px', 'marginBottom': '6px', 'color': '#102a43'}),
            html.Div(f"Line A: {line_a['name']}", style={'fontSize': '13px'}),
            html.Div(f"Line B: {line_b['name']}", style={'fontSize': '13px'}),
            *rows,
        ], style={'padding': '12px', 'background': '#fff', 'border': '1px solid #e2e8f0', 'borderRadius': '10px'})

    def _build_root_markers(line_items: list[dict], visible_range: tuple[float, float] | None = None) -> list[dict]:
        markers = []
        for item in line_items:
            name = item['name']
            if item['kind'] == 'vertical':
                x_pos = float(item['x_const'])
                if visible_range and not (visible_range[0] <= x_pos <= visible_range[1]):
                    continue
                markers.append({
                    'label': 'Root',
                    'series': name,
                    'x': x_pos,
                    'y': 0.0,
                    'value_text': f"x = {x_pos:.6g}",
                })
                continue

            slope = item['slope']
            intercept = item['intercept']
            if np.isclose(slope, 0.0):
                if not np.isclose(intercept, 0.0):
                    continue
                x_pos = 0.0
                value_text = "all x"
            else:
                x_pos = float(-intercept / slope)
                value_text = f"x = {x_pos:.6g}"

            if visible_range and not (visible_range[0] <= x_pos <= visible_range[1]):
                continue
            markers.append({
                'label': 'Root',
                'series': name,
                'x': x_pos,
                'y': 0.0,
                'value_text': value_text,
            })
        return markers

    def _expand_range_for_root(current_range: tuple[float, float] | None, geometry: dict) -> tuple[float, float] | None:
        if current_range is None:
            return None
        left, right = current_range
        if geometry['kind'] == 'vertical':
            root_x = geometry['x_const']
        else:
            slope = geometry['slope']
            intercept = geometry['intercept']
            if np.isclose(slope, 0.0):
                return current_range
            root_x = -intercept / slope
        return (min(left, root_x), max(right, root_x))

    def _sample_marker_indices(length: int, count: int) -> np.ndarray:
        if length <= 0:
            return np.array([], dtype=int)
        if count >= length:
            return np.arange(length, dtype=int)
        return np.unique(np.linspace(0, length - 1, count, dtype=int))

    def _build_pasted_series(pasted_text: str) -> tuple[list[dict], list[str]]:
        if not (pasted_text or '').strip():
            return [], []
        blocks = []
        current = []
        for raw_line in pasted_text.replace('\r', '').split('\n'):
            if raw_line.strip():
                current.append(raw_line)
            elif current:
                blocks.append(current)
                current = []
        if current:
            blocks.append(current)

        series = []
        errors = []
        dataset_counter = 1
        for block in blocks:
            rows = [_parse_delimited_line(line) for line in block if line.strip()]
            rows = [row for row in rows if row]
            if len(rows) < 2:
                continue
            width = max(len(row) for row in rows)
            rows = [row + [''] * (width - len(row)) for row in rows]
            first_numeric = [_safe_float(cell) for cell in rows[0]]
            has_header = any(value is None for value in first_numeric)
            header = rows[0] if has_header else None
            data_rows = rows[1:] if has_header else rows

            numeric_rows = []
            for row in data_rows:
                numeric_row = [_safe_float(cell) for cell in row]
                if numeric_row[0] is None:
                    continue
                numeric_rows.append(numeric_row)

            if len(numeric_rows) < 2 or width < 2:
                errors.append(f"Dataset {dataset_counter}: could not find at least two numeric rows with x/y values.")
                dataset_counter += 1
                continue

            x_values = [row[0] for row in numeric_rows]
            for col_idx in range(1, width):
                y_values = [row[col_idx] for row in numeric_rows]
                finite_pairs = [
                    (x_val, y_val)
                    for x_val, y_val in zip(x_values, y_values)
                    if x_val is not None and y_val is not None
                ]
                if len(finite_pairs) < 2:
                    continue
                x_series = np.array([pair[0] for pair in finite_pairs], dtype=float)
                y_series = np.array([pair[1] for pair in finite_pairs], dtype=float)
                if header and col_idx < len(header) and header[col_idx]:
                    name = header[col_idx]
                elif width == 2:
                    name = f"Pasted Line {dataset_counter}"
                else:
                    name = f"Pasted Line {dataset_counter}.{col_idx}"
                series.append({'name': name, 'x': x_series, 'y': y_series})
            dataset_counter += 1
        return series, errors

    # STEP 1: Load x-axis data ONCE from the FIRST file
    # All traces will use this same x-axis data
    x_data = None
    x_source_file = None
    x_col = None
    first_file_path = list(files_and_columns.keys())[0] if files_and_columns else None

    if first_file_path:
        try:
            ds_x = GenericTextDataSource(Path(first_file_path))
            if ds_x.load():
                x_source_file = Path(first_file_path).name

                # Determine x-axis column name
                if x_axis_column.startswith('col_'):
                    # Legacy index-based format - convert to column name
                    col_idx = int(x_axis_column.split('_')[1])
                    all_cols = list(ds_x._data.columns)
                    x_col = all_cols[col_idx] if col_idx < len(all_cols) else all_cols[0]
                else:
                    # New format - use column name directly
                    available_cols = list(ds_x._data.columns)
                    if x_axis_column in available_cols:
                        x_col = x_axis_column
                    else:
                        print(f"Error: X-axis column '{x_axis_column}' not found in first file {x_source_file}")
                        x_col = available_cols[0] if available_cols else 'col_0'

                x_data = ds_x._data[x_col]
        except Exception as e:
            print(f"Error loading x-axis from {first_file_path}: {e}")

    can_plot_file_data = x_data is not None and len(x_data) > 0
    if files_and_columns and not can_plot_file_data:
        print("Warning: No valid shared x-axis data available for file-based traces")
    line_range = _resolve_line_range(x_data if can_plot_file_data else None)
    effective_line_range = line_range
    line_geometries = []

    # STEP 2: For each file, plot its y-columns against the SHARED x-axis
    for file_path, columns in files_and_columns.items():
        if not can_plot_file_data:
            break
        # Load data source
        try:
            ds = GenericTextDataSource(Path(file_path))
            if not ds.load() or not columns:
                continue

            file_name = Path(file_path).name
            print(f"File: {file_name}, Y-columns: {columns} (using x-axis from {x_source_file})")

            # Get column settings for this file
            file_settings = column_settings.get(file_path, {})

            # Add traces for each column
            for col in columns:
                if col not in ds._data.columns or col == x_col:
                    continue

                try:
                    # Get y-axis assignment for this column
                    col_setting = file_settings.get(col, {})
                    yaxis_name = col_setting.get('yaxis', 'y1')

                    # Get unit conversion based on which y-axis this column is assigned to
                    if yaxis_name == 'y1':
                        unit_conversion = yaxis1_units
                        yaxis_plotly = 'y'
                    else:  # y2
                        unit_conversion = yaxis2_units
                        yaxis_plotly = yaxis_name

                    # Get unit conversion factor
                    conversion_factor = conversion_factors_map.get(unit_conversion, 1.0)

                    print(f"  {file_name}[{col}]: Y-Axis={yaxis_name}, Unit={unit_conversion} (factor={conversion_factor})")

                    # Legend name - use custom label if provided and not empty, otherwise column name
                    legend_label = col_setting.get('legend', col)
                    trace_name = legend_label if legend_label else col
                    color = colors[color_idx % len(colors)]

                    # Apply unit conversion based on y-axis assignment
                    y_data = ds._data[col] * conversion_factor

                    # Check if data lengths match
                    if len(x_data) != len(y_data):
                        print(f"Warning: Data length mismatch in {file_name}: x_data={len(x_data)}, {col}={len(y_data)}. Skipping.")
                        continue

                    n_points = len(x_data)
                    if n_points == 0:
                        print(f"Warning: No data points for {file_name} - {col}. Skipping.")
                        continue

                    trace_x = np.asarray(x_data, dtype=float)
                    trace_y = np.asarray(y_data, dtype=float)
                    geometry = _two_point_line_geometry(trace_x, trace_y)
                    mode = 'lines'
                    if extend_two_point_lines and geometry and line_range:
                        trace_range = effective_line_range or line_range
                        if show_roots_intercepts:
                            trace_range = _expand_range_for_root(trace_range, geometry)
                            effective_line_range = trace_range
                        if geometry['kind'] == 'line':
                            trace_x = np.linspace(trace_range[0], trace_range[1], 200, dtype=float)
                            trace_y = geometry['slope'] * trace_x + geometry['intercept']
                            line_geometries.append({'name': trace_name, **geometry})
                        else:
                            y_min = float(np.nanmin(y_data))
                            y_max = float(np.nanmax(y_data))
                            pad = max(abs(y_max - y_min) * 0.2, 1.0)
                            trace_x = np.array([geometry['x_const'], geometry['x_const']], dtype=float)
                            trace_y = np.array([y_min - pad, y_max + pad], dtype=float)
                            line_geometries.append({'name': trace_name, **geometry})
                    elif geometry:
                        line_geometries.append({'name': trace_name, **geometry})

                    fig.add_trace(go.Scatter(
                        x=trace_x,
                        y=trace_y,
                        mode=mode,
                        name=trace_name,
                        line=dict(width=3.0, color=color),  # Thicker lines
                        yaxis=yaxis_plotly,  # Assign to column's selected y-axis
                        customdata=np.array([[file_name, col, idx + 1] for idx in range(len(trace_x))], dtype=object),
                        hovertemplate=(
                            "Series=%{fullData.name}<br>"
                            f"File=%{{customdata[0]}}<br>"
                            f"Column=%{{customdata[1]}}<br>"
                            f"{x_axis_title}=%{{x:.6g}}<br>"
                            f"{y_axis_title}=%{{y:.6g}}<br>"
                            "Point=%{customdata[2]}<extra></extra>"
                        ),
                    ))
                    plotted_x_values.extend(np.asarray(trace_x, dtype=float).tolist())
                    if yaxis_plotly == 'y':
                        plotted_y_values.extend(np.asarray(trace_y, dtype=float).tolist())

                    color_idx += 1
                    analysis_cards.append(_series_summary(trace_name, x_data, y_data))

                except Exception as e:
                    print(f"Error adding trace for {file_name} - {col}: {e}")
                    continue

        except Exception:
            # Skip files that fail to load
            continue

    # Configure y-axes (y1, y2, y3) based on yaxis_titles
    # Y1 (primary, left side)
    yaxis_configs['yaxis'] = dict(
        title=yaxis_titles.get('y1', y_axis_title),
        side='left'
    )

    # Y2 (secondary, right side)
    if 'y2' in yaxis_titles or any(
        file_settings.get(col, {}).get('yaxis') == 'y2'
        for file_settings in column_settings.values()
        for col in file_settings
    ):
        yaxis_configs['yaxis2'] = dict(
            title=yaxis_titles.get('y2', 'Y2'),
            side='right',
            overlaying='y',
            position=1.0
        )

    # Legend position mapping
    legend_positions = {
        'top-left': {'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
        'top-right': {'yanchor': 'top', 'y': 0.99, 'xanchor': 'right', 'x': 0.99},
        'bottom-left': {'yanchor': 'bottom', 'y': 0.01, 'xanchor': 'left', 'x': 0.01},
        'bottom-right': {'yanchor': 'bottom', 'y': 0.01, 'xanchor': 'right', 'x': 0.99}
    }
    legend_config = legend_positions.get(legend_position, legend_positions['top-left'])
    legend_config['bgcolor'] = 'rgba(255, 255, 255, 0.8)'
    legend_config['font'] = dict(size=22)  # Larger legend text
    if legend_title:
        legend_config['title'] = dict(text=legend_title, font=dict(size=24, family='Arial Black'))

    # Update layout with publication-quality settings (matching matplotlib style)
    layout_config = {
        'xaxis': dict(
            title=dict(text=x_axis_title, font=dict(size=24, family='Arial')),  # Larger axis title
            tickfont=dict(size=22, family='Arial'),  # Larger tick labels
            showgrid=show_grid,
            gridcolor='rgba(128, 128, 128, 0.2)',
            # Axis styling - match matplotlib
            mirror='allticks',  # Show ticks on all sides
            ticks='inside',  # Inward ticks (matplotlib: direction='in')
            ticklen=10,  # Longer major ticks
            tickwidth=2.5,  # Thicker major ticks
            tickcolor='black',
            # Minor ticks
            minor=dict(
                ticks='inside',
                ticklen=6,  # Longer minor ticks
                tickwidth=1.5,  # Thicker minor ticks
                tickcolor='black',
                showgrid=False
            ),
            showline=True,  # Show border line
            linecolor='black',
            linewidth=2.5,  # Thicker border
        ),
        'hovermode': 'x unified',
        'template': 'plotly_white',
        'plot_bgcolor': 'white',  # Clean white background
        'paper_bgcolor': 'white',  # Clean white paper
        'showlegend': show_legend,
        'legend': legend_config,
        'margin': dict(l=80, r=120 if len(yaxis_configs) > 1 else 60, t=40, b=80),
        'font': dict(size=22, family='Arial')  # Larger default font
    }

    # Add y-axis configurations with matplotlib-style settings
    if yaxis_configs:
        # Update each y-axis config with publication-quality styling
        for yaxis_key, yaxis_cfg in yaxis_configs.items():
            # Update title to be a dict with text and font
            if 'title' in yaxis_cfg:
                yaxis_cfg['title'] = dict(text=yaxis_cfg['title'], font=dict(size=24, family='Arial'))  # Larger axis title
            yaxis_cfg['tickfont'] = dict(size=22, family='Arial')  # Larger tick labels
            yaxis_cfg['showgrid'] = show_grid
            yaxis_cfg['gridcolor'] = 'rgba(128, 128, 128, 0.2)'
            # Matplotlib-style axis settings
            yaxis_cfg['mirror'] = 'allticks'
            yaxis_cfg['ticks'] = 'inside'
            yaxis_cfg['ticklen'] = 10  # Longer major ticks
            yaxis_cfg['tickwidth'] = 2.5  # Thicker major ticks
            yaxis_cfg['tickcolor'] = 'black'
            yaxis_cfg['minor'] = dict(
                ticks='inside',
                ticklen=6,  # Longer minor ticks
                tickwidth=1.5,  # Thicker minor ticks
                tickcolor='black',
                showgrid=False
            )
            yaxis_cfg['linecolor'] = 'black'
            yaxis_cfg['linewidth'] = 2.5  # Thicker border
            yaxis_cfg['showline'] = True  # Show border line
        layout_config.update(yaxis_configs)
    else:
        # Use custom y_axis_title when sharing single axis
        layout_config['yaxis'] = dict(
            title=dict(text=y_axis_title, font=dict(size=24, family='Arial')),  # Larger axis title
            tickfont=dict(size=22, family='Arial'),  # Larger tick labels
            showgrid=show_grid,
            gridcolor='rgba(128, 128, 128, 0.2)',
            # Matplotlib-style axis settings
            mirror='allticks',
            ticks='inside',
            ticklen=10,  # Longer major ticks
            tickwidth=2.5,  # Thicker major ticks
            tickcolor='black',
            minor=dict(
                ticks='inside',
                ticklen=6,  # Longer minor ticks
                tickwidth=1.5,  # Thicker minor ticks
                tickcolor='black',
                showgrid=False
            ),
            linecolor='black',
            linewidth=2.5,  # Thicker border
            showline=True  # Show border line
        )

    pasted_series, pasted_errors = _build_pasted_series(pasted_data)
    for series in pasted_series:
        color = colors[color_idx % len(colors)]
        trace_x = np.asarray(series['x'], dtype=float)
        trace_y = np.asarray(series['y'], dtype=float)
        geometry = _two_point_line_geometry(trace_x, trace_y)
        mode = 'lines+markers'
        if extend_two_point_lines and geometry and line_range:
            trace_range = effective_line_range or line_range
            if show_roots_intercepts:
                trace_range = _expand_range_for_root(trace_range, geometry)
                effective_line_range = trace_range
            if geometry['kind'] == 'line':
                trace_x = np.linspace(trace_range[0], trace_range[1], 200, dtype=float)
                trace_y = geometry['slope'] * trace_x + geometry['intercept']
                mode = 'lines'
                line_geometries.append({'name': series['name'], **geometry})
            else:
                y_min = float(np.nanmin(series['y']))
                y_max = float(np.nanmax(series['y']))
                pad = max(abs(y_max - y_min) * 0.2, 1.0)
                trace_x = np.array([geometry['x_const'], geometry['x_const']], dtype=float)
                trace_y = np.array([y_min - pad, y_max + pad], dtype=float)
                mode = 'lines'
                line_geometries.append({'name': series['name'], **geometry})
        elif geometry:
            line_geometries.append({'name': series['name'], **geometry})

        fig.add_trace(go.Scatter(
            x=trace_x,
            y=trace_y,
            mode='lines' if mode != 'lines+markers' else 'lines',
            name=series['name'],
            line=dict(width=3.0, color=color),
            yaxis='y',
            customdata=np.array([[idx + 1] for idx in range(len(trace_x))], dtype=object),
            hovertemplate=(
                "Series=%{fullData.name}<br>"
                f"{x_axis_title}=%{{x:.6g}}<br>"
                f"{y_axis_title}=%{{y:.6g}}<br>"
                "Point=%{customdata[0]}<extra></extra>"
            ),
        ))
        if mode == 'lines+markers':
            marker_indices = np.array([], dtype=int)
            if pasted_point_mode == 'all_points':
                marker_indices = np.arange(len(trace_x), dtype=int)
            elif pasted_point_mode == 'sampled_points':
                marker_indices = _sample_marker_indices(len(trace_x), max(2, int(pasted_marker_count)))

            if marker_indices.size:
                fig.add_trace(go.Scatter(
                    x=trace_x[marker_indices],
                    y=trace_y[marker_indices],
                    mode='markers',
                    name=f"{series['name']} points",
                    marker=dict(size=7, color=color),
                    yaxis='y',
                    showlegend=False,
                    customdata=np.array([[int(idx) + 1] for idx in marker_indices], dtype=object),
                    hovertemplate=(
                        "Point<br>"
                        f"{x_axis_title}=%{{x:.6g}}<br>"
                        f"{y_axis_title}=%{{y:.6g}}<br>"
                        "Index=%{customdata[0]}<extra></extra>"
                    ),
                ))
        plotted_x_values.extend(np.asarray(trace_x, dtype=float).tolist())
        plotted_y_values.extend(np.asarray(trace_y, dtype=float).tolist())
        analysis_cards.append(_series_summary(series['name'], series['x'], series['y']))
        color_idx += 1

    finite_x = np.asarray(plotted_x_values, dtype=float)
    finite_x = finite_x[np.isfinite(finite_x)]
    finite_y = np.asarray(plotted_y_values, dtype=float)
    finite_y = finite_y[np.isfinite(finite_y)]
    if extend_two_point_lines and (effective_line_range or line_range):
        active_range = effective_line_range or line_range
        layout_config['xaxis']['range'] = [active_range[0], active_range[1]]
    elif finite_x.size:
        x_min_vis = float(finite_x.min())
        x_max_vis = float(finite_x.max())
        x_pad = max((x_max_vis - x_min_vis) * 0.06, 1e-6) if not np.isclose(x_min_vis, x_max_vis) else max(abs(x_min_vis) * 0.08, 1.0)
        layout_config['xaxis']['range'] = [x_min_vis - x_pad, x_max_vis + x_pad]
    if finite_y.size:
        y_min_vis = float(finite_y.min())
        y_max_vis = float(finite_y.max())
        y_pad = max((y_max_vis - y_min_vis) * 0.08, 1e-6) if not np.isclose(y_min_vis, y_max_vis) else max(abs(y_min_vis) * 0.08, 1.0)
        layout_config['yaxis']['range'] = [y_min_vis - y_pad, y_max_vis + y_pad]

    intersections = []
    for idx, line_a in enumerate(line_geometries):
        for line_b in line_geometries[idx + 1:]:
            if line_a['kind'] == 'vertical' and line_b['kind'] == 'vertical':
                continue
            if line_a['kind'] == 'vertical':
                x_pos = line_a['x_const']
                if line_b['kind'] == 'line':
                    y_pos = line_b['slope'] * x_pos + line_b['intercept']
                else:
                    continue
            elif line_b['kind'] == 'vertical':
                x_pos = line_b['x_const']
                y_pos = line_a['slope'] * x_pos + line_a['intercept']
            else:
                if np.isclose(line_a['slope'], line_b['slope']):
                    continue
                x_pos = (line_b['intercept'] - line_a['intercept']) / (line_a['slope'] - line_b['slope'])
                y_pos = line_a['slope'] * x_pos + line_a['intercept']

            if line_range and not (line_range[0] <= x_pos <= line_range[1]):
                continue
            intersections.append({'a': line_a['name'], 'b': line_b['name'], 'x': float(x_pos), 'y': float(y_pos)})

    if show_intersections and intersections:
        fig.add_trace(go.Scatter(
            x=[item['x'] for item in intersections],
            y=[item['y'] for item in intersections],
            mode='markers',
            name='Intersections',
            marker=dict(size=11, color='#b91c1c', symbol='diamond'),
            customdata=np.array([[item['a'], item['b']] for item in intersections], dtype=object),
            hovertemplate=(
                "Intersection<br>"
                "Line A=%{customdata[0]}<br>"
                "Line B=%{customdata[1]}<br>"
                f"{x_axis_title}=%{{x:.6g}}<br>"
                f"{y_axis_title}=%{{y:.6g}}<extra></extra>"
            ),
        ))
        analysis_cards.insert(0, _build_intersection_card(intersections))

    root_markers = _build_root_markers(
        line_geometries,
        (effective_line_range or line_range) if extend_two_point_lines and (effective_line_range or line_range) else layout_config.get('xaxis', {}).get('range')
    )
    if show_roots_intercepts and root_markers:
        fig.add_trace(go.Scatter(
            x=[item['x'] for item in root_markers],
            y=[item['y'] for item in root_markers],
            mode='markers',
            name='Roots',
            marker=dict(size=11, color='#0b5d52', symbol='circle', line=dict(color='#063b34', width=1.5)),
            customdata=np.array([[item['series'], item['label'], item['value_text']] for item in root_markers], dtype=object),
            hovertemplate=(
                "%{customdata[1]}<br>"
                "Series=%{customdata[0]}<br>"
                f"{x_axis_title}=%{{x:.6g}}<br>"
                f"{y_axis_title}=%{{y:.6g}}<br>"
                "Value=%{customdata[2]}<extra></extra>"
            ),
        ))

    if len(line_geometries) >= 2:
        analysis_cards.insert(1 if (show_intersections and intersections) else 0, _build_line_pair_card(line_geometries[0], line_geometries[1]))

    fig.update_layout(**layout_config)

    if pasted_errors:
        analysis_cards.insert(0, html.Div([
            html.Div("Paste Parsing", style={'fontWeight': '700', 'fontSize': '14px', 'marginBottom': '6px', 'color': '#9f1239'}),
            *[html.Div(error, style={'fontSize': '13px'}) for error in pasted_errors]
        ], style={'padding': '12px', 'background': '#fff1f2', 'border': '1px solid #fecdd3', 'borderRadius': '10px'}))

    if not analysis_cards:
        analysis = html.Div("No plotted series yet.", style={'fontSize': '14px', 'color': '#64748b'})
    else:
        analysis = html.Div([
            html.Div("Series Analysis", style={'fontWeight': '700', 'fontSize': '18px', 'marginBottom': '10px', 'color': '#102a43'}),
            html.Div(analysis_cards, style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(240px, 1fr))', 'gap': '10px'})
        ], style={'padding': '12px 14px', 'background': '#f8fafc', 'border': '1px solid #e2e8f0', 'borderRadius': '12px'})

    resolved_range = effective_line_range or line_range
    return fig, analysis, (resolved_range[0], resolved_range[1]) if resolved_range else (line_range_min, line_range_max)
