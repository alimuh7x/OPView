"""
Project callback manager for OPView.

Manages callbacks related to project folder selection.
Extracted from OPView.py Phase 13.
"""

import os
from pathlib import Path
from dash import Output, Input, State, html, ALL, no_update, ctx
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager


class ProjectCallbackManager(BaseCallbackManager):
    """
    Manages project folder selection callbacks.

    Registers callbacks for:
    - Project folder selection and loading
    - Folder action UI updates
    - Dynamic project updates
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
        # Removed: self._register_vtk_upload() - Upload feature removed per user request
        self._register_folder_actions()
        self._register_project_folder_selection()
        # Removed: self._register_project_checkbox_controls() - Select/Deselect All buttons removed per user request
        self._register_dynamic_project_updates()
        self._register_sidebar_add_project()
        self._register_sidebar_path_modal()
        self._register_project_filter_by_tab()
        self._register_clear_comparison_on_project()

    # Removed: _register_vtk_upload() - Upload feature removed per user request

    def _register_folder_actions(self):
        """Register callback to update folder actions based on active tab."""
        @self.app.callback(
            Output('vtk-folder-actions', 'children'),
            Input('vtk-folder-tabs', 'value'),
            prevent_initial_call=True  # Prevent firing on initial page load
        )
        def update_folder_actions(active_tab):
            """Update folder actions when switching between tabs."""
            # Removed: Upload button no longer shown on comparison tab
            return None

        self._track_callback(update_folder_actions)

    def _register_project_folder_selection(self):
        """
        Register callback for project folder selection.

        NOTE: Updated to hierarchical checkboxes in Phase 19.
        Uses pattern-matched IDs to collect selections from all project groups.
        """
        @self.app.callback(
            Output('loaded-vtk-folders', 'data'),
            Output('loaded-textdata-folders', 'data'),
            Output('selected-project-folder', 'data'),
            Output('project-feedback', 'children', allow_duplicate=True),
            Output('projects-store', 'data'),
            Input({'type': 'project-vtk-checklist', 'project': ALL}, 'value'),  # Pattern-matched for hierarchical checkboxes
            State('active-tab', 'data'),
            State('loaded-vtk-folders', 'data'),
            State('loaded-textdata-folders', 'data'),
            prevent_initial_call='initial_duplicate'
        )
        def handle_project_folder_selection(all_vtk_selections, active_tab, current_vtk_loaded, current_text_loaded):
            """Handle VTK folder selections from hierarchical project checkboxes.

            Merges selections from all project group checklists into a single list.
            Each group contributes its selected VTK folders to the final selection.

            Uses folder-type routing: inspects folder metadata (has_vtk, has_textdata)
            to determine which store each folder should go to, instead of relying on
            the active_tab State which can be stale during tab transitions.
            """
            # Merge all selected values from different project groups
            selected_folders = []
            for group_selection in all_vtk_selections:
                if group_selection:
                    selected_folders.extend(group_selection)

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

            # If selection hasn't changed, do nothing (avoid rebuilds on tab switches/DOM rehydration)
            prev_vtk = current_vtk_loaded or []
            prev_text = current_text_loaded or []
            prev_all = sorted(list(prev_vtk) + list(prev_text))
            curr_all = sorted(selected_folders)
            if prev_all == curr_all:
                raise PreventUpdate

            # Smart PreventUpdate: Only prevent if input is empty BUT stores have existing data
            # This indicates a DOM rebuild/transition, not a genuine user action to uncheck all
            if not selected_folders:
                # Check if we have existing state in stores
                if (current_vtk_loaded and len(current_vtk_loaded) > 0) or \
                   (current_text_loaded and len(current_text_loaded) > 0):
                    # We have existing selections but input is empty - this is a rebuild/transition
                    raise PreventUpdate
                # If stores are also empty, let callback proceed (genuine "uncheck all" action)

            # Split selections by folder type (VTK vs TextData)
            # This replaces tab-based routing with folder-type routing
            vtk_folders = []
            textdata_folders = []
            for folder_name in selected_folders:
                info = folders_dict.get(folder_name) or {}
                if info.get('has_vtk'):
                    vtk_folders.append(folder_name)
                if info.get('has_textdata'):
                    textdata_folders.append(folder_name)

            # Process VTK folders: build loaded files union for comparison pickers
            loaded_vtk_paths = []
            loaded_names = []
            for name in vtk_folders:
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
            # Prefer VTK folder if available, otherwise use first selected folder
            active_name = vtk_folders[0] if vtk_folders else (selected_folders[0] if selected_folders else None)
            if not active_name:
                if use_context:
                    OPView.app_context.current_project_vtk_path = None
                else:
                    OPView.current_project_vtk_path = None
                msg = html.Div("No project loaded. Load one or more projects to enable Dash tabs and Comparison pickers.",
                               className='project-feedback project-feedback--error')
                return (
                    vtk_folders,           # loaded-vtk-folders
                    textdata_folders,      # loaded-textdata-folders
                    None,
                    msg,
                    {'names': loaded_names, 'active': None, 'files_by_project': files_by_project_dict},
                )

            folder_info = folders_dict[active_name]

            # Update the VTK path to point to selected folder
            vtk_path = folder_info['vtk_path'] if folder_info.get('has_vtk') else None
            if use_context:
                OPView.app_context.current_project_vtk_path = vtk_path
            else:
                OPView.current_project_vtk_path = vtk_path

            # Initialize dataset registry for panel-based auto-detection
            # Works in both context and legacy modes
            if vtk_path:
                from config.dataset_registry import DatasetRegistry
                from config.tabs import TAB_CONFIGS

                registry = DatasetRegistry(Path(vtk_path), TAB_CONFIGS)
                registry.detect(verbose=False)  # Silent mode for faster UI response

                # Store registry in both context (if available) and global
                if use_context:
                    OPView.app_context.dataset_registry = registry
                else:
                    OPView.dataset_registry = registry  # Store in legacy global

                # Assign unconfigured datasets to pre-created auto slots.
                # This allows auto datasets to work without registering new callbacks at runtime.
                unconfigured = [ds for ds in registry.all_datasets if ds.module_id == "unconfigured"]
                OPView.auto_dataset_to_slot = {}
                OPView.auto_slot_to_dataset = {}
                for slot_id, ds in zip(OPView.AUTO_PANEL_SLOTS, unconfigured):
                    OPView.auto_dataset_to_slot[ds.dataset_id] = slot_id
                    OPView.auto_slot_to_dataset[slot_id] = ds.dataset_id
                if use_context and OPView.app_context is not None:
                    OPView.app_context.auto_dataset_to_slot = OPView.auto_dataset_to_slot
                    OPView.app_context.auto_slot_to_dataset = OPView.auto_slot_to_dataset
                if bool(os.environ.get("OPVIEW_DEBUG")):
                    print(
                        f"[OPVIEW_DEBUG] assigned auto slots: {len(OPView.auto_dataset_to_slot)} "
                        f"of {len(unconfigured)} unconfigured datasets",
                        flush=True,
                    )

                configured_count = len([ds for ds in registry.all_datasets if ds.module_id != "unconfigured"])
                unconfigured_count = len([ds for ds in registry.all_datasets if ds.module_id == "unconfigured"])
                print(f"Dataset registry: {len(registry)} datasets ({configured_count} configured, {unconfigured_count} auto-detected)")

                # NOTE: Do NOT create/register new ViewerPanels (callbacks) during this callback.
                # Dash's front-end callback graph is established at page load; registering callbacks
                # later (from inside a running callback) leads to "auto" panels that render once
                # but do not respond to dropdown/range changes without a full refresh.
                #
                # Auto panels are handled by mapping datasets to pre-created slots (see above).
                if bool(os.environ.get("OPVIEW_DEBUG")):
                    print(
                        f"[OPVIEW_DEBUG] project_manager detected {unconfigured_count} unconfigured datasets "
                        f"(auto datasets mapped onto slots)",
                        flush=True,
                    )

            # Main tabs are initialized at startup (no VTK reads). Selecting projects only
            # updates `projects-store`; panels react instantly without requiring a refresh.

            # Compact logging for faster UI response
            vtk_info = f"{folder_info.get('vtk_file_count', 0)} VTK" if folder_info.get('has_vtk') else ""
            textdata_info = f"{folder_info.get('textdata_file_count', 0)} TextData" if folder_info.get('has_textdata') else ""
            file_summary = ", ".join(filter(None, [vtk_info, textdata_info]))
            print(f"Project loaded: {active_name} ({file_summary})")

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

            return vtk_folders, textdata_folders, folder_data, feedback_msg, {'names': loaded_names, 'active': active_name, 'files_by_project': files_by_project_dict}

        self._track_callback(handle_project_folder_selection)

    # =============================================================================
    # REMOVED: _register_project_checkbox_controls() - Select/Deselect All buttons removed ✅
    # =============================================================================
    # Select All / Deselect All buttons removed from UI per user request
    # =============================================================================

    def _register_dynamic_project_updates(self):
        """Register callback to add custom folders to project sidebar."""
        @self.app.callback(
            Output('project-checkboxes-container', 'children', allow_duplicate=True),
            Input('comparison-files-store', 'data'),
            State('vtk-folder-tabs', 'value'),
            State('loaded-vtk-folders', 'data'),
            State('loaded-textdata-folders', 'data'),
            prevent_initial_call=True
        )
        def update_project_list_from_custom_folders(_files, active_tab, loaded_vtk_folders, loaded_textdata_folders):
            """No-op placeholder kept to avoid missing-output errors; filtering is handled elsewhere."""
            from dash import no_update
            return no_update

        self._track_callback(update_project_list_from_custom_folders)

    def _register_sidebar_add_project(self):
        """Register callback for sidebar 'Add Project' button."""
        @self.app.callback(
            Output('comparison-files-store', 'data', allow_duplicate=True),
            Output('loaded-vtk-folders', 'data', allow_duplicate=True),
            Output('loaded-textdata-folders', 'data', allow_duplicate=True),
            Output('project-checkboxes-container', 'children', allow_duplicate=True),
            Input('sidebar-add-project-btn', 'n_clicks'),
            Input('sidebar-path-submit-btn', 'n_clicks'),
            State('comparison-files-store', 'data'),
            State('loaded-vtk-folders', 'data'),
            State('loaded-textdata-folders', 'data'),
            State('vtk-folder-tabs', 'value'),
            State('sidebar-path-input', 'value'),
            prevent_initial_call=True
        )
        def handle_sidebar_add_project(n_clicks, path_submit_clicks, current_files, loaded_vtk_folders, loaded_textdata_folders, active_tab, manual_path):
            """Handle adding a project folder from the sidebar."""
            trig = ctx.triggered_id
            if not trig:
                from dash.exceptions import PreventUpdate
                raise PreventUpdate

            from utils.project_scanner import _scan_vtk_dir
            from pathlib import Path
            import os
            import sys
            from utils.project_scanner import group_projects_by_parent
            from utils.path_utils import choose_folder
            from dash import html, dcc

            # 1. Get path from dialog or pasted input
            if trig == 'sidebar-path-submit-btn':
                path = (manual_path or '').strip()
                if not path:
                    from dash.exceptions import PreventUpdate
                    raise PreventUpdate
            else:
                path = choose_folder(title="Select Project Folder containing VTK files")

            if not path:
                from dash.exceptions import PreventUpdate
                raise PreventUpdate

            # 2. Register Global Project
            import OPView
            p_obj = Path(path)

            # Detect structure: parent may contain VTK and/or TextData
            def _find_textdata_folder(base: Path):
                variants = ["TextData", "Textdata", "textdata", "TEXTDATA"]
                for v in variants:
                    candidate = base / v
                    if candidate.exists() and candidate.is_dir():
                        return candidate
                return None

            entries = {}
            def _store_entry(name, info):
                entries[name] = info

            def _add_parent_with_children(root: Path):
                project_name_local = root.name
                vtk_dir = root / "VTK"
                text_dir = _find_textdata_folder(root)
                has_vtk = vtk_dir.exists() and vtk_dir.is_dir()
                has_text = text_dir is not None

                # Parent entry
                _store_entry(project_name_local, {
                    'path': root,
                    'has_vtk': has_vtk,
                    'has_textdata': has_text,
                    'vtk_path': vtk_dir if has_vtk else None,
                    'textdata_path': text_dir,
                    'vtk_file_count': -1,
                    'textdata_file_count': -1,
                    'is_subdirectory': False,
                    'parent_folder': None
                })
                if has_vtk:
                    _store_entry(f"{project_name_local}/VTK", {
                        'path': vtk_dir,
                        'has_vtk': True,
                        'has_textdata': False,
                        'vtk_path': vtk_dir,
                        'textdata_path': None,
                        'vtk_file_count': -1,
                        'textdata_file_count': 0,
                        'is_subdirectory': True,
                        'parent_folder': project_name_local
                    })
                if has_text:
                    _store_entry(f"{project_name_local}/TextData", {
                        'path': text_dir,
                        'has_vtk': False,
                        'has_textdata': True,
                        'vtk_path': None,
                        'textdata_path': text_dir,
                        'vtk_file_count': 0,
                        'textdata_file_count': -1,
                        'is_subdirectory': True,
                        'parent_folder': project_name_local
                    })
                return project_name_local, vtk_dir if has_vtk else None

            # If user picked VTK or TextData folder directly, normalize to parent project
            project_name = None
            vtk_path = None
            if p_obj.name.lower() in ('vtk', 'textdata', 'textdata', 'textdata'):
                parent = p_obj.parent
                project_name, vtk_path = _add_parent_with_children(parent)
            else:
                project_name, vtk_path = _add_parent_with_children(p_obj)

            # Scan VTK files for comparison store (optional)
            new_files = _scan_vtk_dir(Path(vtk_path)) if vtk_path and Path(vtk_path).exists() else []

            # Update global registries
            registry_target = OPView.app_context.discovered_project_folders if OPView.app_context else OPView.discovered_project_folders
            registry_target.update(entries)

            print(f"Project added: {project_name} ({len(new_files)} VTK files, textdata={'yes' if entries.get(f'{project_name}/TextData') else 'no'})")

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

            # Rebuild hierarchical UI based on active tab and current loaded folders
            loaded_vtk_folders = loaded_vtk_folders or []
            loaded_textdata_folders = loaded_textdata_folders or []
            loaded_folders = loaded_vtk_folders if active_tab in ['current', 'comparison'] else loaded_textdata_folders
            all_projects = registry_target
            filtered = {}
            if active_tab in ['current', 'comparison']:
                filtered = {n: info for n, info in all_projects.items() if info.get('has_vtk', False)}
            elif active_tab == 'custom-graph':
                filtered = {n: info for n, info in all_projects.items() if info.get('has_textdata', False)}
            else:
                filtered = all_projects

            grouped_projects = group_projects_by_parent(filtered)
            if not grouped_projects:
                children = [html.Div("No projects found", className='project-empty')]
            else:
                children = []
                for proj_name, vtk_folders in grouped_projects.items():
                    folder_values = [opt['value'] for opt in vtk_folders]
                    selected_values = [f for f in loaded_folders if f in folder_values]
                    children.append(
                        html.Div([
                            html.Label(proj_name, className='project-group-header'),
                            dcc.Checklist(
                                id={'type': 'project-vtk-checklist', 'project': proj_name},
                                options=vtk_folders,
                                value=selected_values,
                                className='vtk-folder-checklist',
                                labelStyle={'display': 'flex', 'alignItems': 'center'},
                                inputStyle={'marginRight': '8px'}
                            )
                        ], className='project-group')
                    )

            return updated_files, loaded_vtk_folders, loaded_textdata_folders, children

        self._track_callback(handle_sidebar_add_project)

    def _register_sidebar_path_modal(self):
        """Open/close modal for manual project path input."""
        @self.app.callback(
            Output('sidebar-path-modal', 'opened'),
            Output('sidebar-path-input', 'value'),
            Input('sidebar-add-project-path-btn', 'n_clicks'),
            Input('sidebar-path-cancel-btn', 'n_clicks'),
            Input('sidebar-path-submit-btn', 'n_clicks'),
            State('sidebar-path-modal', 'opened'),
            prevent_initial_call=True
        )
        def toggle_sidebar_path_modal(open_clicks, cancel_clicks, submit_clicks, opened):
            trig = ctx.triggered_id
            if trig == 'sidebar-add-project-path-btn':
                return True, no_update
            if trig in ('sidebar-path-cancel-btn', 'sidebar-path-submit-btn'):
                return False, ''
            raise PreventUpdate

        self._track_callback(toggle_sidebar_path_modal)

    def _register_project_filter_by_tab(self):
        """Register callback to filter project list based on active tab (hierarchical UI)."""
        @self.app.callback(
            Output('project-checkboxes-container', 'children', allow_duplicate=True),
            Input('vtk-folder-tabs', 'value'),
            State('loaded-vtk-folders', 'data'),
            State('loaded-textdata-folders', 'data'),
            prevent_initial_call='initial_duplicate'  # Run on initial load to filter based on default tab
        )
        def filter_projects_by_tab(active_tab, loaded_vtk_folders, loaded_textdata_folders):
            """Filter and rebuild hierarchical project checkboxes based on active tab, preserving selections.

            - Single View (current) & Multi View (comparison): Show folders with VTK files
            - Custom Graph (custom-graph): Show folders with text/CSV files

            Args:
                active_tab: The active tab value ('current', 'comparison', or 'custom-graph')
                loaded_folders: Currently selected folder paths from store (for restoring checkbox state)

            Returns:
                Rebuilt hierarchical checkbox structure with filtered projects and restored selections
            """
            import OPView
            from utils.project_scanner import group_projects_by_parent
            from dash import html, dcc

            # Get loaded folders from store (for restoring checkbox state)
            # Always merge selections from BOTH stores when rebuilding checkboxes
            # This ensures state persists across tab switches
            vtk_selections = loaded_vtk_folders or []
            textdata_selections = loaded_textdata_folders or []
            loaded_folders = list(set(vtk_selections + textdata_selections))

            # Get all discovered projects
            if OPView.app_context:
                all_projects = OPView.app_context.discovered_project_folders
            else:
                all_projects = OPView.discovered_project_folders

            # Show ALL folders on ALL tabs (no filtering)
            # This prevents checkbox state loss when switching tabs
            # Users can check both VTK and TextData folders simultaneously
            filtered_projects = all_projects

            # Build hierarchical structure from filtered projects
            grouped_projects = group_projects_by_parent(filtered_projects)

            if not grouped_projects:
                return [html.Div("No projects found", className='project-empty')]

            # Rebuild hierarchical checkbox groups WITH RESTORED VALUES
            groups = []
            for project_name, vtk_folders in grouped_projects.items():
                # Extract folder values (full paths) for this group
                folder_values = [opt['value'] for opt in vtk_folders]

                # Find which folders in this group are currently loaded (restore from store)
                selected_values = [f for f in loaded_folders if f in folder_values]

                groups.append(
                    html.Div([
                        # Project header (no checkbox)
                        html.Label(project_name, className='project-group-header'),
                        # VTK folder checkboxes (indented) WITH RESTORED STATE
                        dcc.Checklist(
                            id={'type': 'project-vtk-checklist', 'project': project_name},
                            options=vtk_folders,
                            value=selected_values,  # ← CHANGED: Restore from store instead of []
                            className='vtk-folder-checklist',
                            labelStyle={'display': 'flex', 'alignItems': 'center'},
                            inputStyle={'marginRight': '8px'}
                        )
                    ], className='project-group')
                )

            return groups

        self._track_callback(filter_projects_by_tab)

    def _register_clear_comparison_on_project(self):
        """Clear comparison selections only when the project selection actually changes."""
        @self.app.callback(
            Output({'type': 'comparison-selected-files-store', 'group': ALL}, 'data', allow_duplicate=True),
            Output({'type': 'comparison-controls-store', 'group': ALL}, 'data', allow_duplicate=True),
            Output('comparison-clear-flag-global', 'data', allow_duplicate=True),
            Input('selected-project-folder', 'data'),
            State('comparison-clear-flag-global', 'data'),
            State({'type': 'comparison-selected-files-store', 'group': ALL}, 'id'),
            State({'type': 'comparison-controls-store', 'group': ALL}, 'id'),
            prevent_initial_call=True
        )
        def clear_comparison_on_project(selected_project, last_project, sel_ids, ctrl_ids):
            # If no comparison components are mounted yet, do nothing.
            if not sel_ids and not ctrl_ids:
                raise PreventUpdate

            # Only clear if the project actually changed.
            if selected_project == last_project:
                raise PreventUpdate

            sel_out = [[] for _ in (sel_ids or [])]
            ctrl_out = [{} for _ in (ctrl_ids or [])]
            return sel_out, ctrl_out, selected_project

        self._track_callback(clear_comparison_on_project)
