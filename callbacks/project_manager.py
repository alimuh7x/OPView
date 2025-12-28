"""
Project callback manager for OPView.

Manages callbacks related to project folder selection and VTK file management.
Extracted from OPView.py Phase 13.
"""

import base64
from pathlib import Path
from dash import Output, Input, State, html
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager


class ProjectCallbackManager(BaseCallbackManager):
    """
    Manages project folder selection and file upload callbacks.

    Registers callbacks for:
    - VTK file uploads to comparison directory
    - Project folder selection and loading
    - Folder action UI updates
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
        self._register_vtk_upload()
        self._register_folder_actions()
        self._register_project_folder_selection()
        self._register_project_checkbox_controls()
        self._register_dynamic_project_updates()
        self._register_sidebar_add_project()

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
            # Import dependencies at runtime to avoid circular imports
            import OPView
            from utils.vtk_utils import list_comparison_files
            from config import comparison_data_dir, ALLOWED_VTK_EXTENSIONS

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

            # Get comparison directory
            target_dir = comparison_data_dir()
            target_path = target_dir / Path(filename).name

            # Clear reader cache for this file
            OPView.reader_cache.pop(str(target_path), None)

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
                list_comparison_files(target_dir)
            )

        self._track_callback(handle_vtk_upload)

    def _register_folder_actions(self):
        """Register callback to update folder actions based on active tab."""
        @self.app.callback(
            Output('vtk-folder-actions', 'children'),
            Input('vtk-folder-tabs', 'value'),
            prevent_initial_call=True  # Prevent firing on initial page load
        )
        def update_folder_actions(active_tab):
            """Update folder actions when switching between tabs."""
            from comparisonmgr.callbacks import _comparison_upload

            if active_tab == 'comparison':
                return _comparison_upload()
            return None

        self._track_callback(update_folder_actions)

    def _register_project_folder_selection(self):
        """
        Register callback for project folder selection.

        NOTE: Input changed from 'project-folder-dropdown' to 'project-checkboxes' in Phase 14.
        Old dropdown removed from top section; checkboxes now in sidebar.
        """
        @self.app.callback(
            Output('loaded-project-folders', 'data'),
            Output('selected-project-folder', 'data'),
            Output('vtk-upload-feedback', 'children', allow_duplicate=True),
            Output('projects-store', 'data'),
            Input('project-checkboxes', 'value'),  # Changed from project-folder-dropdown (Phase 14)
            State('active-tab', 'data'),
            prevent_initial_call='initial_duplicate'
        )
        def handle_project_folder_selection(selected_folders, active_tab):
            """Handle project folder selection for multi-project browsing.

            - `project-folder-dropdown` loads one or more project folders.
            - Comparison can pick files from any loaded project without clearing selections.
            """
            # Import dependencies at runtime
            import OPView

            # Use app_context if available, otherwise fall back to legacy globals
            use_context = OPView.app_context is not None

            # Normalize
            if not selected_folders:
                selected_folders = []
            if isinstance(selected_folders, str):
                selected_folders = [selected_folders]

            # Get discovered folders from context or global
            folders_dict = OPView.app_context.discovered_project_folders if use_context else OPView.discovered_project_folders
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
                OPView.app_context.loaded_project_names = loaded_names
                OPView.app_context.loaded_project_vtk_files_by_project = files_by_project_dict
                OPView.app_context.loaded_project_vtk_files = all_files_sorted
            else:
                OPView.loaded_project_names = loaded_names
                OPView.loaded_project_vtk_files_by_project = files_by_project_dict
                OPView.loaded_project_vtk_files = all_files_sorted

            # Choose active project (first loaded) for legacy paths and defaults.
            active_name = selected_folders[0] if selected_folders else None
            if not active_name:
                if use_context:
                    OPView.app_context.current_project_vtk_path = None
                else:
                    OPView.current_project_vtk_path = None
                msg = html.Div("No project loaded. Load one or more projects to enable Dash tabs and Comparison pickers.",
                               className='vtk-upload-feedback vtk-upload-feedback--error')
                return selected_folders, None, msg, {'names': loaded_names, 'active': None, 'files_by_project': files_by_project_dict}

            folder_info = folders_dict[active_name]

            # Update the VTK path to point to selected folder
            vtk_path = folder_info['vtk_path'] if folder_info.get('has_vtk') else None
            if use_context:
                OPView.app_context.current_project_vtk_path = vtk_path
            else:
                OPView.current_project_vtk_path = vtk_path

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
                print(f"VTK Files (loaded union): {len(all_files_sorted)}")
                print(f"✓ VTK data directory updated to: {vtk_path}")
            if folder_info.get('has_textdata'):
                print(f"TextData Path: {folder_info['textdata_path']}")
                print(f"TextData Files: {folder_info['textdata_file_count']}")
            print(f"{'='*60}\n")

            # No UI feedback message (console output still active for debugging)
            feedback_msg = None

            # Store the selected folder data
            folder_data = {
                'name': active_name,
                'path': str(folder_info['path']),
                'vtk_path': str(folder_info['vtk_path']) if folder_info['has_vtk'] else None,
                'textdata_path': str(folder_info['textdata_path']) if folder_info['has_textdata'] else None,
                'loaded': selected_folders,
            }

            return selected_folders, folder_data, feedback_msg, {'names': loaded_names, 'active': active_name, 'files_by_project': files_by_project_dict}

        self._track_callback(handle_project_folder_selection)

    def _register_project_checkbox_controls(self):
        """Register Select All / Deselect All callbacks for project checkboxes."""
        @self.app.callback(
            Output('project-checkboxes', 'value'),
            Input('select-all-projects-btn', 'n_clicks'),
            Input('deselect-all-projects-btn', 'n_clicks'),
            State('project-checkboxes', 'options'),
            prevent_initial_call=True
        )
        def handle_project_checkbox_controls(select_clicks, deselect_clicks, options):
            """
            Handle Select All / Deselect All button clicks.

            Args:
                select_clicks: Number of clicks on Select All button
                deselect_clicks: Number of clicks on Deselect All button
                options: Current checkbox options list

            Returns:
                List of selected project values
            """
            from dash import ctx
            from dash.exceptions import PreventUpdate

            triggered = ctx.triggered_id

            if triggered == 'select-all-projects-btn':
                # Select all available projects
                return [opt['value'] for opt in (options or [])]
            elif triggered == 'deselect-all-projects-btn':
                # Deselect all projects
                return []

            raise PreventUpdate

        self._track_callback(handle_project_checkbox_controls)

    def _register_dynamic_project_updates(self):
        """Register callback to add custom folders to project sidebar."""
        @self.app.callback(
            Output('project-checkboxes', 'options', allow_duplicate=True),
            Output('project-checkboxes', 'value', allow_duplicate=True),
            Input('comparison-files-store', 'data'),
            State('project-checkboxes', 'options'),
            State('project-checkboxes', 'value'),
            prevent_initial_call=True
        )
        def update_project_list_from_custom_folders(files, current_options, current_values):
            """Sync the sidebar project list with registered projects (including dynamic ones)."""
            import OPView
            from dash import no_update
            
            # Access the global registry of projects
            if OPView.app_context:
                all_projects = OPView.app_context.discovered_project_folders
            else:
                all_projects = OPView.discovered_project_folders
                
            # Current options in the UI
            current_options = current_options or []
            existing_values = {opt['value'] for opt in current_options}
            
            updated = False
            
            # Check for any registered project not in the list
            # We want to maintain order if possible, but sets are robust for check
            
            # Rebuild options list from registry to ensure it's clean and sorted
            # But we want to preserve existing UI state? 
            # Actually, rebuilding completely is safer to remove stale entries if needed,
            # but appending is smoother.
            
            # Let's iterate over registered projects and add missing ones (Dynamic ones)
            sorted_project_names = sorted(all_projects.keys())
            
            # If we just replace existing options, we might lose order or interfere with selection?
            # Safe strategy: Add missing ones.
            
            for proj_name in sorted_project_names:
                if proj_name not in existing_values:
                    current_options.append({'label': proj_name, 'value': proj_name})
                    # Auto-select the NEW project
                    if current_values is None:
                        current_values = []
                    if proj_name not in current_values:
                        current_values.append(proj_name)
                    updated = True
            
            if not updated:
                return no_update, no_update
                
            return current_options, current_values

        self._track_callback(update_project_list_from_custom_folders)

    def _register_sidebar_add_project(self):
        """Register callback for sidebar 'Add Project' button."""
        @self.app.callback(
            Output('comparison-files-store', 'data', allow_duplicate=True),
            Input('sidebar-add-project-btn', 'n_clicks'),
            State('comparison-files-store', 'data'),
            prevent_initial_call=True
        )
        def handle_sidebar_add_project(n_clicks, current_files):
            """Handle adding a project folder from the sidebar."""
            if not n_clicks:
                from dash.exceptions import PreventUpdate
                raise PreventUpdate

            from utils.project_scanner import _scan_vtk_dir
            from pathlib import Path
            import os
            import sys

            # 1. Open Dialog
            path = None
            try:
                # Try easygui first (Tkinter based)
                import easygui
                path = easygui.diropenbox(title="Select Project Folder containing VTK files")
            except Exception:
                pass

            # Fallback to plyer if easygui fails or returns None (though diropenbox returns None on cancel)
            if not path:
                try:
                    from plyer import filechooser
                    selection = filechooser.choose_dir(title="Select Project Folder containing VTK files")
                    if selection and len(selection) > 0:
                        path = selection[0]
                except Exception as e:
                    print(f"File selection failed: {e}")
                    # If both fail, we can't do much without client-side interaction
                    from dash.exceptions import PreventUpdate
                    raise PreventUpdate

            if not path:
                from dash.exceptions import PreventUpdate
                raise PreventUpdate

            # 2. Register Global Project
            import OPView
            p_obj = Path(path)
            
            # Smart naming: If folder is 'VTK', use parent name.
            if p_obj.name.lower() == 'vtk':
                project_name = p_obj.parent.name
                # If we selected .../Project/VTK, scanning it works.
                scan_path = p_obj
                root_path = p_obj.parent
            else:
                project_name = p_obj.name
                scan_path = p_obj
                root_path = p_obj

            new_files = _scan_vtk_dir(scan_path)
            if not new_files:
                return current_files

            # Create project entry
            project_entry = {
                'path': str(root_path),
                'vtk_path': str(scan_path),
                'has_vtk': True,
                'vtk_file_count': len(new_files),
                'has_textdata': False,
                'textdata_path': None,
                'textdata_file_count': 0
            }
            
            # Update global registries
            if OPView.app_context:
                OPView.app_context.discovered_project_folders[project_name] = project_entry
            else:
                OPView.discovered_project_folders[project_name] = project_entry
                
            print(f"[PROJECT_MGR] Registered dynamic project: {project_name} -> {root_path}", flush=True)

            # 3. Append to Store
            current_files = current_files or []
            existing_paths = set()
            for f in current_files:
                if isinstance(f, str):
                    existing_paths.add(f)
                else:
                    existing_paths.add(f.get('path'))

            updated_files = list(current_files)
            for f in new_files:
                if f not in existing_paths:
                    updated_files.append(f)
                    
            return updated_files

        self._track_callback(handle_sidebar_add_project)
