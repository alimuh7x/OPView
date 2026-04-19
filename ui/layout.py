"""
App layout builder for OPView.

Extracted from OPView.py Phase 11 - provides the main application layout.
"""

from dash import html, dcc
import dash_mantine_components as dmc
from config import TAB_CONFIGS
from ui.floating_chat import build_floating_chat


def build_app_layout(
    discovered_project_folders,
    comparison_files,
    initial_active_tab,
    build_tab_children_func,
    build_comparison_content_func,
    allowed_comparison_groups_func,
    get_project_folder_options_func,
    group_projects_by_parent_func,
    default_vtk_folder_label="VTK",
    server_session_id=None
):
    """Build the main application layout.

    Args:
        discovered_project_folders: Dict of discovered project folders
        comparison_files: List of comparison file names
        initial_active_tab: Initial active tab ID
        build_tab_children_func: Function to build tab children
        build_comparison_content_func: Function to build comparison content
        allowed_comparison_groups_func: Function to get allowed comparison groups
        get_project_folder_options_func: Function to get project folder options (legacy)
        group_projects_by_parent_func: Function to group VTK folders by parent project
        default_vtk_folder_label: Label for default VTK folder
        server_session_id: Unique server session ID for detecting server restarts

    Returns:
        Dash layout component
    """
    import time
    _layout_start = time.time()
    print(f"    [layout] Starting layout build...")

    result = dmc.MantineProvider(
        html.Div(
            id='app-container',
            children=[
                # Server session tracking (for detecting server restarts)
                dcc.Store(
                    id='server-session-id',
                    data={'id': server_session_id} if server_session_id else None,
                    storage_type='memory'  # Don't persist - always fetch from server
                ),
                html.Div(id='session-check-dummy', style={'display': 'none'}),  # Session checker dummy output
                dcc.Store(id='active-tab', data=None),  # Currently active tab (memory only - resets on refresh)
                dcc.Store(id='open-tabs', data=[]),  # Track which tabs are open (memory only - resets on refresh)
                # Multi View has its own panel state (separate from Single View).
                dcc.Store(id='comparison-active-tab', data=None),  # Active comparison panel (memory only)
                dcc.Store(id='comparison-open-tabs', data=[]),  # Open comparison panels (memory only)
                dcc.Store(id='comparison-files-store', data=comparison_files),
                dcc.Store(id='comparison-clear-flag-global', data=None),  # Track last cleared project
                dcc.Store(id='comparison-png-export-trigger', data=None),  # PNG export trigger (memory only)
                html.Div(id='comparison-png-export-dummy', style={'display': 'none'}),  # PNG export dummy output
                html.Div(id='panel-visibility-dummy', style={'display': 'none'}),  # Panel visibility clientside callback dummy
                html.Div(id='comparison-panel-visibility-dummy', style={'display': 'none'}),  # Comparison panel visibility dummy
                dcc.Store(id='loaded-vtk-folders', data=[]),
                dcc.Store(id='loaded-textdata-folders', data=[]),
                dcc.Store(id='selected-project-folder', data=None),
                dcc.Store(id='projects-store', data={'names': [], 'active': None, 'files_by_project': {}}, storage_type='session'),
                dcc.Store(id='graphs-multifile-panels', data={}),  # Graph panels state (memory - resets on refresh)
                dcc.Location(id='url', refresh=False),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Img(src='/assets/OP_Logo_main.png', className='app-logo', alt='OP logo'),
                                html.H1([
                                    "OPV",
                                    html.Span("iew", className='app-title-sub'),
                                ], className='app-title')
                            ], className='app-title-card')
                        ], className='top-left'),
                        html.Div([
                            html.A("Documentation", href='/docs', target='_blank', className='doc-link')
                        ], className='top-right')
                ], className='top-bar')
            ], className='app-header'),

# =============================================================================
# PROJECT SELECTION - Moved to sidebar checkboxes (Phase 14) ✅
# =============================================================================
# Project folder selection dropdown previously at this location.
# Now implemented as checkboxes in sidebar (see line ~124).
# Callback: callbacks/project_manager.py:137 (_register_project_folder_selection)
# Controls: callbacks/project_manager.py:269 (_register_project_checkbox_controls)
# =============================================================================

                html.Div([
                    html.Div([
                        html.Span(default_vtk_folder_label, className='vtk-folder-badge'),
                        html.Span("Tabs", className='vtk-folder-heading-text')
                    ], className='vtk-folder-heading'),
                    dcc.Tabs(
                        id='vtk-folder-tabs',
                        value='current',
                        className='vtk-tabs',
                        children=[
                            dcc.Tab(
                                label='Single View',
                                value='current',
                                className='vtk-tab',
                                selected_className='vtk-tab--selected'
                            ),
                            dcc.Tab(
                                label='Multi View',
                                value='comparison',
                                className='vtk-tab',
                                selected_className='vtk-tab--selected'
                            ),
                            dcc.Tab(
                                label='Custom Graph',
                                value='custom-graph',
                                className='vtk-tab',
                                selected_className='vtk-tab--selected'
                            ),
                        ]
                    ),
                    html.Div(id='vtk-folder-actions', className='vtk-folder-actions'),
                    html.Div(id='project-feedback', className='project-feedback')

                ], className='vtk-folder-row'),

## -------------------------------------------------------------------------------
                html.Div([
                    html.Div([
                        # Projects Section
                        html.Div([
                            html.Span("PROJECTS", className='sidebar-projects-title'),
                            # Hierarchical project checkboxes (grouped by project)
                            html.Div(
                                id='project-checkboxes-container',
                                children=[
                                    html.Div([
                                        # Project header (no checkbox)
                                        html.Label(project_name, className='project-group-header'),
                                        # VTK folder checkboxes (indented)
                                        dcc.Checklist(
                                            id={'type': 'project-vtk-checklist', 'project': project_name},
                                            options=vtk_folders,
                                            value=[],
                                            className='vtk-folder-checklist',
                                            labelStyle={'display': 'flex', 'alignItems': 'center'},
                                            inputStyle={'marginRight': '8px'}
                                        )
                                    ], className='project-group')
                                    for project_name, vtk_folders in group_projects_by_parent_func(discovered_project_folders).items()
                                ] if group_projects_by_parent_func(discovered_project_folders) else [
                                    html.Div("No projects found", className='project-empty')
                                ],
                                className='hierarchical-project-checkboxes'
                            ),

                            html.Div([
                                html.Button(
                                    "📂 Add Project Folder",
                                    id='sidebar-add-project-btn',
                                    n_clicks=0,
                                    className='sidebar-add-project-btn',
                                    style={'marginTop': '10px', 'width': '100%'}
                                ),
                                html.Button(
                                    "Paste Project Path",
                                    id='sidebar-add-project-path-btn',
                                    n_clicks=0,
                                    className='sidebar-add-project-btn',
                                    style={'marginTop': '8px', 'width': '100%'}
                                ),
                            ], className='sidebar-add-project-container'),
                        ], id='sidebar-projects-section', className='sidebar-projects-section'),

                        # Graphs Section - REMOVED (Phase 18 - Two-column layout) ✅
                        # Controls moved into each graph panel's right column
                        html.Div([], id='sidebar-graphs-selector', style={'display': 'none'}),

                        # Placeholders — analysis/tools are separate apps (calculationNotebook / OPPre).
                        html.Div([], id='sidebar-initializations-section', style={'display': 'none'}),
                        html.Div([], id='sidebar-mechanical-loads-section', style={'display': 'none'}),
                        html.Div([], id='sidebar-notebook-section', style={'display': 'none'}),

                    ], className='sidebar'),
                    html.Div([
                        html.Div(
                            [
                                html.Div([
                                    html.Span("ADD PANEL", className='sidebar-title'),
                                    dcc.Dropdown(
                                        id='panel-selector-dropdown',
                                        options=[],
                                        placeholder="Select a data type",
                                        className='panel-selector-dropdown',
                                        clearable=True,
                                        searchable=False,
                                        maxHeight=560
                                    ),
                                    html.Div(
                                        id='detection-status',
                                        children=[
                                            html.Span("No project loaded", className='detection-status-text')
                                        ],
                                        className='detection-status',
                                        style={'fontSize': '0.85em', 'color': '#65d36e'}
                                    )
                                ], id='sidebar-panel-selector', className='main-panel-selector-card'),
                                html.Div([
                                    html.Span("ADD PANEL", className='sidebar-title'),
                                    dcc.Dropdown(
                                        id='comparison-panel-selector-dropdown',
                                        options=[],
                                        placeholder="Select a data type to compare...",
                                        className='panel-selector-dropdown',
                                        clearable=True,
                                        searchable=False,
                                        maxHeight=560
                                    ),
                                    html.Div(
                                        id='comparison-detection-status',
                                        children=[
                                            html.Span("No project loaded", className='detection-status-text')
                                        ],
                                        className='detection-status',
                                        style={'fontSize': '0.85em', 'color': '#65d36e'}
                                    )
                                ], id='sidebar-comparison-panel-selector', className='main-panel-selector-card', style={'display': 'none'}),
                            ],
                            className='main-panel-selector-shell'
                        ),
                        html.Div(
                            html.Div(
                                id='dynamic-tab-headers',
                                children=[],
                                className='inner-tab-headers'
                            ),
                            id='single-view-inner-tabs-row',
                            className='inner-tabs-row',
                            style={'display': 'block'}
                        ),
                        html.Div(
                            html.Div(
                                id='comparison-tab-headers',
                                children=[],
                                className='inner-tab-headers'
                            ),
                            id='comparison-inner-tabs-row',
                            className='inner-tabs-row',
                            style={'display': 'none'}
                        ),
                        # Tab content area
                        html.Div(
                            id='tab-content',
                            children=[html.Div("Add a module from the dropdown to get started", className='dataset-empty', style={'padding': '40px', 'text-align': 'center'})]
                        ),
                        html.Div(
                            id='comparison-content',
                            children=[],  # Empty initially - lazy loaded by callback
                            style={'display': 'none'}
                        ),
                        html.Div(
                            id='graphs-content',
                            children=[
                                html.Div([
                                    html.Button(
                                        "Add or Select Text File",
                                        id='graphs-add-file-panel-btn',
                                        className='graphs-add-panel-btn opview-image-add-btn',
                                        n_clicks=0
                                    ),
                                    html.Button(
                                        "Add Data",
                                        id='graphs-add-data-panel-btn',
                                        className='graphs-add-panel-btn opview-image-add-btn',
                                        n_clicks=0
                                    ),
                                    html.Button(
                                        "Notebook Plot",
                                        id='graphs-add-notebook-panel-btn',
                                        className='graphs-add-panel-btn opview-image-add-btn',
                                        n_clicks=0
                                    ),
                                ], style={'display': 'flex', 'gap': '10px', 'flexWrap': 'wrap'}),
                                html.Div(id='graphs-multifile-container', className='multifile-panels-container'),
                            ],
                            style={'display': 'none'}
                        ),
                        html.Div(
                            id='formula-content',
                            children=[],
                            style={'display': 'none'}
                        ),
                        html.Div(
                            id='notebook-content',
                            children=[],
                            style={'display': 'none'}
                        ),
                        html.Div(
                            id='initializations-content',
                            children=[],
                            style={'display': 'none'}
                        ),
                        html.Div(
                            id='mechanical-loads-content',
                            children=[],
                            style={'display': 'none'}
                        ),
                    ], className='main-panel')
                ], className='layout-shell'),
                build_floating_chat(),
                dmc.Modal(
                    id='sidebar-path-modal',
                    title="Select Path",
                    opened=False,
                    centered=True,
                    size="md",
                    children=[
                        dcc.Input(
                            id='sidebar-path-input',
                            type='text',
                            placeholder="Paste folder path here",
                            style={'width': '100%'}
                        ),
                        html.Div([
                            html.Button(
                                "Cancel",
                                id='sidebar-path-cancel-btn',
                                n_clicks=0,
                                className='btn'
                            ),
                            html.Button(
                                "Add",
                                id='sidebar-path-submit-btn',
                                n_clicks=0,
                                className='btn btn-danger',
                                style={'marginLeft': '8px'}
                            ),
                        ], style={'display': 'flex', 'justifyContent': 'flex-end', 'marginTop': '12px'})
                    ],
                )
            ]
        )
    )

    print(f"    [layout] Layout built in {time.time()-_layout_start:.3f}s")
    return result
