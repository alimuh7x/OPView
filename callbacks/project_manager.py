"""
Project callback manager for OPView.

Manages callbacks related to project folder selection and VTK file management.
"""

import base64
from pathlib import Path
from dash import Output, Input, State, html, dcc
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager


class ProjectCallbackManager(BaseCallbackManager):
    """
    Manages project folder selection and file upload callbacks.
    """

    def __init__(self, app, context):
        """
        Initialize project callback manager.

        Args:
            app: Dash application instance
            context: AppContext instance
        """
        super().__init__(app, context)

    def register(self) -> None:
        """Register all project-related callbacks."""
        self._register_project_folder_selection()
        self._register_vtk_upload()
        self._register_folder_actions()

    def _register_project_folder_selection(self):
        """Register callback for project folder selection."""
        @self.app.callback(
            Output('loaded-project-folders', 'data'),
            Output('selected-project-folder', 'data'),
            Output('vtk-upload-feedback', 'children', allow_duplicate=True),
            Output('projects-store', 'data'),
            Input('project-folder-dropdown', 'value'),
            State('active-tab', 'data'),
            prevent_initial_call=True
        )
        def handle_project_folder_selection(selected_folders, active_tab):
            """Handle project folder selection for multi-project browsing."""
            # Import required functions from OPView.py
            from OPView import (
                _load_project_folders, discovered_project_folders,
                loaded_project_names, current_project_vtk_path,
                loaded_project_vtk_files_by_project
            )

            # Delegate to existing function
            return _load_project_folders(selected_folders, active_tab)

        self._track_callback(handle_project_folder_selection)

    def _register_vtk_upload(self):
        """Register callback for VTK file upload."""
        @self.app.callback(
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
            from config import ALLOWED_VTK_EXTENSIONS, comparison_data_dir
            from OPView import reader_cache, list_comparison_files

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

        self._track_callback(handle_vtk_upload)

    def _register_folder_actions(self):
        """Register callback to update folder actions based on active tab."""
        @self.app.callback(
            Output('vtk-folder-actions', 'children'),
            Input('vtk-folder-tabs', 'value')
        )
        def update_folder_actions(active_tab):
            """Update folder actions when switching between tabs."""
            if active_tab == 'comparison':
                return dcc.Upload(
                    id='vtk-file-upload',
                    accept='.vtk,.vti,.vtp,.vtr,.vts',
                    multiple=False,
                    className='vtk-file-upload',
                    children=html.Span("Add VTK File", className='vtk-file-upload__text')
                )
            return None

        self._track_callback(update_folder_actions)
