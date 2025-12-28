"""
App layout builder for OPView.

Extracted from OPView.py Phase 11 - provides the main application layout.
"""

from dash import html, dcc
import dash_mantine_components as dmc


def build_app_layout(
    discovered_project_folders,
    comparison_files,
    initial_active_tab,
    build_tab_children_func,
    build_comparison_content_func,
    allowed_comparison_groups_func,
    get_project_folder_options_func,
    default_vtk_folder_label="VTK"
):
    """Build the main application layout.

    Args:
        discovered_project_folders: Dict of discovered project folders
        comparison_files: List of comparison file names
        initial_active_tab: Initial active tab ID
        build_tab_children_func: Function to build tab children
        build_comparison_content_func: Function to build comparison content
        allowed_comparison_groups_func: Function to get allowed comparison groups
        get_project_folder_options_func: Function to get project folder options
        default_vtk_folder_label: Label for default VTK folder

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
                dcc.Store(id='active-tab', data=None),  # Currently active tab (memory only - resets on refresh)
                dcc.Store(id='open-tabs', data=[]),  # Track which tabs are open (memory only - resets on refresh)
                dcc.Store(id='comparison-files-store', data=comparison_files),
                dcc.Store(id='loaded-project-folders', data=[], storage_type='session'),
                dcc.Store(id='selected-project-folder', data=None, storage_type='session'),
                dcc.Store(id='projects-store', data={'names': [], 'active': None, 'files_by_project': {}}, storage_type='session'),
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
                            label=default_vtk_folder_label,
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
                        # Projects Section
                        html.Div([
                            html.Span("PROJECTS", className='sidebar-projects-title'),
                            dcc.Checklist(
                                id='project-checkboxes',
                                options=get_project_folder_options_func(discovered_project_folders),
                                value=[],
                                className='project-checkboxes',
                                labelStyle={'display': 'flex', 'alignItems': 'center'},
                                inputStyle={'marginRight': '8px'}
                            ),
                            html.Div([
                                html.Button(
                                    "Select All",
                                    id='select-all-projects-btn',
                                    n_clicks=0,
                                    className='project-checkbox-btn'
                                ),
                                html.Span("|", className='project-controls-separator'),
                                html.Button(
                                    "Deselect All",
                                    id='deselect-all-projects-btn',
                                    n_clicks=0,
                                    className='project-checkbox-btn'
                                ),

                            ], className='project-checkbox-controls'),
                            
                            html.Div([
                                html.Button(
                                    "➕ Add Project Folder",
                                    id='sidebar-add-project-btn',
                                    n_clicks=0,
                                    className='sidebar-add-project-btn',
                                    style={'marginTop': '10px', 'width': '100%'}
                                ),
                            ], className='sidebar-add-project-container'),
                        ], className='sidebar-projects-section'),

                        # Modules Section - Dynamic Tab Selection
                        html.Div([
                            html.Span("ADD MODULE", className='sidebar-title'),
                            dcc.Dropdown(
                                id='module-selector-dropdown',
                                options=[
                                    {'label': '⛶ Phase-Field', 'value': 'phase-field'},
                                    {'label': '⚛ Composition', 'value': 'composition'},
                                    {'label': '⚙ Mechanics', 'value': 'mechanics'},
                                    {'label': '🧪 Plasticity', 'value': 'plasticity'},
                                ],
                                placeholder="Add a module...",
                                className='module-selector-dropdown',
                                clearable=False,
                                searchable=False
                            ),
                            # Dynamic tab headers (vertical list in sidebar)
                            html.Div(
                                id='dynamic-tab-headers',
                                children=[],  # Empty initially
                                className='sidebar-tab-headers'
                            )
                        ], className='sidebar-module-selector'),
                    ], className='sidebar'),
                    html.Div([
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
                    ], className='main-panel')
                ], className='layout-shell')
            ]
        )
    )

    print(f"    [layout] Layout built in {time.time()-_layout_start:.3f}s")
    return result
