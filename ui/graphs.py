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
            'x_axis_column': None  # Which column to use as x-axis (column name)
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

    # Panel layout - Two column design: Graph (left) | Controls (right)
    # Panel layout - Hybrid Design (Top Data, Right Settings)
    return html.Div([
        # Header with close button
        html.Div([
            html.Div([
                html.H3(f"Graph Panel {panel_num}", className='dataset-title')
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
            ], style={'marginBottom': '12px'}),

            # Columns Selection (Grid)
            html.Div([
                html.Div(file_sections, className='multifile-columns-grid'),
            ], style={'display': 'block' if file_sections else 'none', 'marginBottom': '4px'}),
        ], className='multifile-top-controls'),

        # MAIN CONTENT AREA (Split View)
        html.Div([
            # LEFT: GRAPH
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
                )
            ], className='multifile-graph-area'),

            # RIGHT: SETTINGS SIDEBAR
            html.Div([
                html.H4("Settings", className='multifile-settings-header', style={'fontSize': '16px'}),

                # X-Axis Settings
                html.Div([
                     html.Label("X-Axis", className='multifile-sublabel', style={'fontSize': '15px'}),
                     html.Div([
                        html.Label("Column:", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Dropdown(
                            id={'type': 'multifile-x-axis-column', 'panel': panel_id},
                            options=_build_x_axis_column_options(panel_state.get('files', [])),
                            value=panel_state.get('x_axis_column'),
                            clearable=False,
                            style={'fontSize': '14px', 'marginBottom': '8px'}
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

            ], className='multifile-settings-sidebar'),
        ], className='multifile-main-content'),

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
                          yaxis2_units: str = 'Raw') -> go.Figure:
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
        Plotly figure with all traces and configured axes
    """
    from data.sources import GenericTextDataSource

    if not files_and_columns:
        # Return empty figure
        return go.Figure().update_layout(
            title="Select files and columns to display the graph",
            xaxis_title=x_axis_title,
            yaxis_title=y_axis_title,
            template='plotly_white'
        )

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
    file_idx = 0
    yaxis_configs = {}

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
                print(f"X-axis source: {x_source_file}[{x_col}], length={len(x_data)}")
        except Exception as e:
            print(f"Error loading x-axis from {first_file_path}: {e}")

    if x_data is None or len(x_data) == 0:
        print("Error: No x-axis data available")
        return go.Figure()

    # STEP 2: For each file, plot its y-columns against the SHARED x-axis
    for file_path, columns in files_and_columns.items():
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

                    fig.add_trace(go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode='lines',  # Lines only, no markers
                        name=trace_name,
                        line=dict(width=3.0, color=color),  # Thicker lines
                        yaxis=yaxis_plotly  # Assign to column's selected y-axis
                    ))

                    color_idx += 1

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

    fig.update_layout(**layout_config)

    return fig
