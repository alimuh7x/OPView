"""
Tab callback manager for OPView.

Manages callbacks related to tab navigation and rendering.
"""

from dash import Output, Input, State, ctx, ALL, no_update
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager


class TabCallbackManager(BaseCallbackManager):
    """
    Manages tab navigation and rendering callbacks.
    """

    def __init__(self, app, context, ui_manager=None):
        """
        Initialize tab callback manager.

        Args:
            app: Dash application instance
            context: AppContext instance
            ui_manager: UIManager instance (optional, for future use)
        """
        super().__init__(app, context)
        self.ui_manager = ui_manager

    def register(self) -> None:
        """Register all tab-related callbacks."""
        # OLD: self._register_set_active_tab()  # Removed - used old tab buttons
        self._register_render_tab_content()
        # Dynamic tab management callbacks
        self._register_panel_dropdown_update()  # NEW: Update panel dropdown based on detected datasets
        self._register_add_tab_from_dropdown()
        self._register_render_tab_headers()
        self._register_activate_tab_from_header()
        self._register_close_tab()
        # Multi View has its own panel system (separate from Single View)
        self._register_comparison_panel_dropdown_update()
        self._register_add_comparison_tab_from_dropdown()
        self._register_render_comparison_tab_headers()
        self._register_activate_comparison_tab_from_header()
        self._register_close_comparison_tab()
        self._register_toggle_module_selector()  # Show/hide module/graphs selectors based on active tab
        self._register_populate_custom_graph_selector()  # Folder/file dropdowns for Custom Graph tab
        # self._register_clear_comparison_on_tab_switch()  # REMOVED: Was clearing valid user selections on tab switch

    # =========================================================================
    # OLD CALLBACK - Removed (Phase 14 - Dynamic Tab Management) ✅
    # =========================================================================
    # _register_set_active_tab() removed - used old tab buttons
    # Replaced by _register_activate_tab_from_header() for dynamic tab headers
    # =========================================================================

    def _comparison_group_for_dataset_id(self, dataset_id: str):
        """Return the comparison group (filename prefix) for a dataset id."""
        from pathlib import Path

        if not dataset_id:
            return None

        resolved_id = dataset_id
        if str(resolved_id).startswith("auto-slot-"):
            try:
                import OPView
                resolved_id = getattr(OPView, "auto_slot_to_dataset", {}).get(resolved_id) or resolved_id
            except Exception:
                pass

        registry = None
        if self.context and getattr(self.context, "dataset_registry", None):
            registry = self.context.dataset_registry
        else:
            import OPView
            registry = getattr(OPView, "dataset_registry", None)

        glob_pat = ""
        if registry:
            info = registry.get_by_id(resolved_id)
            if info and getattr(info, "file_glob", None):
                glob_pat = info.file_glob

        if not glob_pat and str(resolved_id).startswith("auto-"):
            # Best-effort fallback for unconfigured datasets.
            name = str(resolved_id).replace("auto-", "", 1)
            return (name[:1].upper() + name[1:]) if name else None

        base = Path(glob_pat).name
        stem = base.split(".")[0]
        stem = stem.split("*", 1)[0].rstrip("_")
        if not stem:
            return None
        return stem.split("_", 1)[0]

    def _get_comparison_groups_for_open_tabs(self, open_tabs):
        """
        Map dataset IDs from open_tabs to their corresponding comparison file groups.

        This enables Multi View to only show panels for explicitly added datasets,
        matching the behavior of Single View.

        Args:
            open_tabs: List of dataset IDs (e.g., ['phase-field-phase', 'mechanics-stresses'])

        Returns:
            Set of comparison group names (e.g., {'PhaseField', 'Stresses'})
        """
        if not open_tabs:
            return set()

        groups = set()

        for dataset_id in open_tabs:
            group = self._comparison_group_for_dataset_id(dataset_id)
            if group:
                groups.add(group)

        return groups

    def _register_comparison_panel_dropdown_update(self):
        """Update Multi View panel dropdown when project loads."""
        @self.app.callback(
            Output('comparison-panel-selector-dropdown', 'options'),
            Output('comparison-detection-status', 'children'),
            Input('selected-project-folder', 'data'),
            prevent_initial_call=True
        )
        def update_comparison_panel_dropdown(project_data):
            from dash import html

            if not project_data:
                return [], html.Span("No project loaded", className='detection-status-text', style={'color': '#888'})

            registry = None
            if self.context and self.context.dataset_registry:
                registry = self.context.dataset_registry
            else:
                import OPView
                if hasattr(OPView, 'dataset_registry') and OPView.dataset_registry:
                    registry = OPView.dataset_registry

            if not registry:
                return [], html.Span("No datasets detected", className='detection-status-text', style={'color': '#888'})

            value_map = {}
            try:
                if self.context and getattr(self.context, "auto_dataset_to_slot", None):
                    value_map = self.context.auto_dataset_to_slot or {}
                else:
                    import OPView
                    value_map = getattr(OPView, "auto_dataset_to_slot", {}) or {}
            except Exception:
                value_map = {}

            grouped = []
            for module in registry.tab_configs:
                module_id = module.get('id', '')
                datasets_in_module = [d for d in registry.all_datasets if d.module_id == module_id]
                if not datasets_in_module:
                    continue
                grouped.append({'label': f"─── {module.get('label', module_id)} ───", 'value': f"__group_{module_id}", 'disabled': True})
                for d in datasets_in_module:
                    grouped.append({'label': f"  {d.label}", 'value': d.dataset_id})

            unconfigured = [d for d in registry.all_datasets if d.module_id == "unconfigured"]
            if unconfigured:
                grouped.append({'label': '─── Other Files ───', 'value': '__group_unconfigured', 'disabled': True})
                for d in unconfigured:
                    grouped.append({'label': f"  {d.label}", 'value': value_map.get(d.dataset_id, d.dataset_id)})

            status_msg = registry.get_status_message()
            status_color = '#4CAF50' if len(registry) > 0 else '#888'
            status_element = html.Span(
                status_msg,
                className='detection-status-text',
                style={'color': status_color}
            )

            return grouped, status_element

        self._track_callback(update_comparison_panel_dropdown)

    def _register_panel_dropdown_update(self):
        """Register callback to update panel dropdown when project loads."""
        @self.app.callback(
            Output('panel-selector-dropdown', 'options'),
            Output('detection-status', 'children'),
            Input('selected-project-folder', 'data'),
            prevent_initial_call=True
        )
        def update_panel_dropdown(project_data):
            """
            Populate panel dropdown with detected datasets from the loaded project.

            When a project is selected, the dataset registry is populated in the
            project_manager callback. This callback reads that registry and builds
            the dropdown options showing only available data types.
            """
            from dash import html

            # Check if project is loaded
            if not project_data:
                return [], html.Span("No project loaded", className='detection-status-text', style={'color': '#888'})

            # Get registry from context or legacy global
            registry = None
            if self.context and self.context.dataset_registry:
                registry = self.context.dataset_registry
            else:
                # Fall back to legacy global variable
                import OPView
                if hasattr(OPView, 'dataset_registry') and OPView.dataset_registry:
                    registry = OPView.dataset_registry

            if not registry:
                return [], html.Span("No datasets detected", className='detection-status-text', style={'color': '#888'})

            # Build grouped dropdown options, mapping unconfigured datasets onto pre-created slot ids.
            value_map = {}
            try:
                if self.context and getattr(self.context, "auto_dataset_to_slot", None):
                    value_map = self.context.auto_dataset_to_slot or {}
                else:
                    import OPView
                    value_map = getattr(OPView, "auto_dataset_to_slot", {}) or {}
            except Exception:
                value_map = {}

            options = []
            for ds in registry.all_datasets:
                value = ds.dataset_id
                if ds.module_id == "unconfigured":
                    value = value_map.get(ds.dataset_id, ds.dataset_id)
                options.append({'label': ds.label, 'value': value})

            # Re-group using the registry helper but with our mapped values.
            # Keep the original grouped layout by reusing module ordering.
            if True:
                grouped = []
                # configured modules in TAB_CONFIGS order
                for module in registry.tab_configs:
                    module_id = module.get('id', '')
                    datasets_in_module = [d for d in registry.all_datasets if d.module_id == module_id]
                    if not datasets_in_module:
                        continue
                    grouped.append({'label': f"─── {module.get('label', module_id)} ───", 'value': f"__group_{module_id}", 'disabled': True})
                    for d in datasets_in_module:
                        grouped.append({'label': f"  {d.label}", 'value': d.dataset_id})
                # unconfigured section
                unconfigured = [d for d in registry.all_datasets if d.module_id == "unconfigured"]
                if unconfigured:
                    grouped.append({'label': '─── Other Files ───', 'value': '__group_unconfigured', 'disabled': True})
                    for d in unconfigured:
                        grouped.append({'label': f"  {d.label}", 'value': value_map.get(d.dataset_id, d.dataset_id)})
                options = grouped

            # Build status message
            status_msg = registry.get_status_message()
            status_color = '#4CAF50' if len(registry) > 0 else '#888'

            status_element = html.Span(
                status_msg,
                className='detection-status-text',
                style={'color': status_color}
            )

            return options, status_element

        self._track_callback(update_panel_dropdown)

    def _register_render_tab_content(self):
        """Register callback to render active tab content."""
        @self.app.callback(
            Output('tab-content', 'children'),
            Output('tab-content', 'style'),
            Output('comparison-content', 'children'),
            Output('comparison-content', 'style'),
            Output('graphs-content', 'style'),
            Input('active-tab', 'data'),
            Input('open-tabs', 'data'),
            Input('comparison-active-tab', 'data'),
            Input('comparison-open-tabs', 'data'),
            Input('comparison-files-store', 'data'),
            Input('selected-project-folder', 'data'),
            Input('loaded-vtk-folders', 'data'),
            Input('vtk-folder-tabs', 'value'),
            State({'type': 'comparison-controls-store', 'group': ALL}, 'data'),
            State({'type': 'comparison-controls-store', 'group': ALL}, 'id'),
            State({'type': 'comparison-selected-files-store', 'group': ALL}, 'data'),
            State({'type': 'comparison-selected-files-store', 'group': ALL}, 'id'),
            prevent_initial_call=True
        )
        def render_active_tab(active_tab, open_tabs, comparison_active_tab, comparison_open_tabs,
                              comparison_files, _active_project, _loaded_vtk_projects, active_folder,
                              group_controls_data, group_controls_ids,
                              selected_group_data, selected_group_ids):
            """Render content for the active tab."""
            # Import dependencies
            from dash import html
            from OPView import build_tab_children
            from comparisonmgr.ui_builders import build_comparison_group_content

            # Determine what triggered this callback
            triggered = ctx.triggered_id

            # === HANDLE CUSTOM GRAPH TAB ===
            if active_folder == 'custom-graph':
                # Graph panels are managed independently by GraphsCallbackManager.
                return (
                    no_update,                   # tab-content children
                    {'display': 'none'},         # tab-content style - HIDE VTK content
                    no_update,                   # comparison-content children - don't update
                    {'display': 'none'},         # comparison-content style - HIDE comparison
                    {'display': 'block'},        # graphs-content style - SHOW graphs
                )

            # === HANDLE COMPARISON TAB ===
            if active_folder == 'comparison':
                # Multi View has its own panels; start empty until user adds one.
                if not comparison_open_tabs or not comparison_active_tab:
                    return (
                        no_update,                   # tab-content children
                        {'display': 'none'},         # tab-content - HIDE VTK modules
                        html.Div("Add a panel from the dropdown to use Multi View",
                                className='dataset-empty',
                                style={'padding': '40px', 'text-align': 'center'}),
                        {'display': 'block'},        # comparison-content - SHOW placeholder
                        {'display': 'none'},         # graphs-content - HIDE
                    )

                # Build comparison content for all open comparison panels and hide inactive ones.
                stored_by_group = {}
                if group_controls_data and group_controls_ids:
                    for store_id, store_data in zip(group_controls_ids, group_controls_data):
                        if not isinstance(store_id, dict) or not store_data:
                            continue
                        grp = store_id.get('group')
                        if grp is not None:
                            stored_by_group[grp] = store_data

                selected_by_group = {}
                if selected_group_data and selected_group_ids:
                    for store_id, store_data in zip(selected_group_ids, selected_group_data):
                        if not isinstance(store_id, dict):
                            continue
                        grp = store_id.get('group')
                        if grp is not None:
                            selected_by_group[grp] = store_data or []

                panels = []
                for tab_id in comparison_open_tabs or []:
                    groups = sorted(self._get_comparison_groups_for_open_tabs([tab_id]))
                    group = groups[0] if groups else None
                    if not group:
                        content = [html.Div(f"Failed to resolve comparison group for: {tab_id}", className='dataset-empty')]
                    else:
                        content = build_comparison_group_content(group, comparison_files or [], stored_by_group, selected_by_group)
                    panels.append(
                        html.Div(
                            content,
                            id={'type': 'comparison-panel', 'tab': tab_id},
                            style={'display': 'block'} if tab_id == comparison_active_tab else {'display': 'none'},
                        )
                    )

                return (
                    no_update,                   # tab-content children
                    {'display': 'none'},         # tab-content - HIDE VTK modules
                    panels,                      # comparison-content children
                    {'display': 'block'},        # comparison-content - SHOW
                    {'display': 'none'},         # graphs-content - HIDE
                )

            # === HANDLE VTK TAB (current) ===
            # Show placeholder if no modules open on VTK tab
            if not open_tabs or not active_tab:
                return (
                    html.Div("Add a module from the dropdown to get started",
                            className='dataset-empty',
                            style={'padding': '40px', 'text-align': 'center'}),
                    {'display': 'block'},         # tab-content - SHOW placeholder
                    no_update,                    # comparison-content children - don't update
                    {'display': 'none'},          # comparison-content - HIDE
                    {'display': 'none'},          # graphs-content - HIDE
                )

            # Build VTK tab content for all open panels and hide inactive ones.
            # This preserves per-panel control + dcc.Store state when switching tabs.
            if active_tab:
                panels = []
                for tab_id in open_tabs or []:
                    try:
                        content = build_tab_children(tab_id)
                    except Exception as e:
                        content = [html.Div(f"Failed to render panel: {tab_id} ({e})", className='dataset-empty')]
                    panels.append(
                        html.Div(
                            content,
                            id={'type': 'tab-panel', 'tab': tab_id},
                            style={'display': 'block'} if tab_id == active_tab else {'display': 'none'},
                        )
                    )
                return (
                    panels,                      # tab-content children
                    {'display': 'block'},        # tab-content - SHOW VTK modules
                    no_update,                   # comparison-content children - don't update
                    {'display': 'none'},         # comparison-content - HIDE
                    {'display': 'none'},         # graphs-content - HIDE
                )

            # Fallback - should not reach here
            raise PreventUpdate

        self._track_callback(render_active_tab)

    def _register_add_tab_from_dropdown(self):
        """Register callback to add tab when selected from panel dropdown."""
        @self.app.callback(
            Output('open-tabs', 'data'),
            Output('active-tab', 'data', allow_duplicate=True),
            Output('panel-selector-dropdown', 'value'),  # Changed from module-selector-dropdown
            Input('panel-selector-dropdown', 'value'),   # Changed from module-selector-dropdown
            State('open-tabs', 'data'),
            prevent_initial_call=True
        )
        def add_tab_from_dropdown(selected_dataset, open_tabs):
            """
            Add selected dataset panel to open tabs and activate it.

            Changed from module-based to dataset-based selection.
            Each selection now adds ONE panel for a specific dataset.
            """
            if not selected_dataset:
                raise PreventUpdate

            # Skip group headers (disabled options used for visual grouping)
            if selected_dataset.startswith('__group_'):
                raise PreventUpdate

            # Create new list (Dash requires new object to detect changes)
            new_open_tabs = open_tabs.copy() if open_tabs else []

            # Add tab if not already open (dataset_id now instead of module_id)
            # Note: Auto-detected panels are now created when project loads (in project_manager),
            # so they exist with callbacks registered before user can select them
            if selected_dataset not in new_open_tabs:
                new_open_tabs.append(selected_dataset)

            # Set as active tab and clear dropdown
            return new_open_tabs, selected_dataset, None

        self._track_callback(add_tab_from_dropdown)

    def _register_add_comparison_tab_from_dropdown(self):
        """Add a Multi View panel when selected from the comparison dropdown."""
        @self.app.callback(
            Output('comparison-open-tabs', 'data'),
            Output('comparison-active-tab', 'data', allow_duplicate=True),
            Output('comparison-panel-selector-dropdown', 'value'),
            Input('comparison-panel-selector-dropdown', 'value'),
            State('comparison-open-tabs', 'data'),
            prevent_initial_call=True
        )
        def add_comparison_tab_from_dropdown(selected_dataset, open_tabs):
            if not selected_dataset:
                raise PreventUpdate
            if str(selected_dataset).startswith('__group_'):
                raise PreventUpdate

            new_open_tabs = open_tabs.copy() if open_tabs else []
            if selected_dataset not in new_open_tabs:
                new_open_tabs.append(selected_dataset)

            return new_open_tabs, selected_dataset, None

        self._track_callback(add_comparison_tab_from_dropdown)

    def _register_render_tab_headers(self):
        """Register callback to render dynamic tab headers."""
        @self.app.callback(
            Output('dynamic-tab-headers', 'children'),
            Input('open-tabs', 'data'),
            Input('active-tab', 'data'),  # Changed from State to Input - updates when active tab changes
            prevent_initial_call=True  # Prevent firing on initial page load
        )
        def render_tab_headers(open_tabs, active_tab):
            """
            Render horizontal tab headers with close buttons.

            Changed to use dataset_id instead of module_id.
            Looks up dataset info from registry to get labels and icons.
            """
            from dash import html

            if not open_tabs:
                return []

            # Get dataset registry from context or legacy global
            registry = None
            if self.context and self.context.dataset_registry:
                registry = self.context.dataset_registry
            else:
                # Fall back to legacy global variable
                import OPView
                if hasattr(OPView, 'dataset_registry') and OPView.dataset_registry:
                    registry = OPView.dataset_registry

            headers = []
            for tab_id in open_tabs:
                is_active = (tab_id == active_tab)

                # Get dataset info from registry
                if registry:
                    dataset_info = registry.get_by_id(tab_id)
                    if not dataset_info:
                        # Slot-based auto dataset: map slot id -> dataset id
                        try:
                            import OPView
                            dataset_id = getattr(OPView, "auto_slot_to_dataset", {}).get(tab_id)
                            if dataset_id:
                                dataset_info = registry.get_by_id(dataset_id)
                        except Exception:
                            dataset_info = None
                    if dataset_info:
                        label = dataset_info.label
                    else:
                        # Fallback if not found in registry
                        label = tab_id.replace('-', ' ').title()
                else:
                    # No registry available - use fallback
                    label = tab_id.replace('-', ' ').title()

                headers.append(
                    html.Div([
                        html.Span(label, className='tab-label'),
                        html.Button(
                            '×',
                            id={'type': 'close-tab-btn', 'tab': tab_id},
                            className='tab-close-btn'
                        )
                    ],
                    id={'type': 'tab-header', 'tab': tab_id},
                    className='tab-header active' if is_active else 'tab-header')
                )

            return headers

        self._track_callback(render_tab_headers)

    def _register_render_comparison_tab_headers(self):
        """Render Multi View tab headers with close buttons."""
        @self.app.callback(
            Output('comparison-tab-headers', 'children'),
            Input('comparison-open-tabs', 'data'),
            Input('comparison-active-tab', 'data'),
            prevent_initial_call=True
        )
        def render_comparison_tab_headers(open_tabs, active_tab):
            from dash import html

            if not open_tabs:
                return []

            registry = None
            if self.context and self.context.dataset_registry:
                registry = self.context.dataset_registry
            else:
                import OPView
                if hasattr(OPView, 'dataset_registry') and OPView.dataset_registry:
                    registry = OPView.dataset_registry

            headers = []
            for tab_id in open_tabs:
                is_active = (tab_id == active_tab)

                label = None
                if registry:
                    dataset_info = registry.get_by_id(tab_id)
                    if not dataset_info:
                        try:
                            import OPView
                            dataset_id = getattr(OPView, "auto_slot_to_dataset", {}).get(tab_id)
                            if dataset_id:
                                dataset_info = registry.get_by_id(dataset_id)
                        except Exception:
                            dataset_info = None
                    if dataset_info:
                        label = dataset_info.label
                if not label:
                    label = str(tab_id).replace('-', ' ').title()

                headers.append(
                    html.Div([
                        html.Span(label, className='tab-label'),
                        html.Button(
                            '×',
                            id={'type': 'comparison-close-tab-btn', 'tab': tab_id},
                            className='tab-close-btn'
                        )
                    ],
                    id={'type': 'comparison-tab-header', 'tab': tab_id},
                    className='tab-header active' if is_active else 'tab-header')
                )

            return headers

        self._track_callback(render_comparison_tab_headers)

    def _register_activate_tab_from_header(self):
        """Register callback to activate tab when header is clicked."""
        @self.app.callback(
            Output('active-tab', 'data', allow_duplicate=True),
            Input({'type': 'tab-header', 'tab': ALL}, 'n_clicks'),
            State('active-tab', 'data'),
            prevent_initial_call=True
        )
        def activate_tab_from_header(n_clicks, current_tab):
            """Set active tab when header is clicked."""
            if not ctx.triggered_id:
                raise PreventUpdate

            # Prevent firing when header is just created (n_clicks=None)
            if not n_clicks or all(nc is None for nc in n_clicks):
                raise PreventUpdate

            new_active = ctx.triggered_id['tab']
            return new_active

        self._track_callback(activate_tab_from_header)

    def _register_activate_comparison_tab_from_header(self):
        """Activate Multi View tab when its header is clicked."""
        @self.app.callback(
            Output('comparison-active-tab', 'data', allow_duplicate=True),
            Input({'type': 'comparison-tab-header', 'tab': ALL}, 'n_clicks'),
            State('comparison-active-tab', 'data'),
            prevent_initial_call=True
        )
        def activate_comparison_tab_from_header(n_clicks, current_tab):
            if not ctx.triggered_id:
                raise PreventUpdate
            if not n_clicks or all(nc is None for nc in n_clicks):
                raise PreventUpdate
            return ctx.triggered_id['tab']

        self._track_callback(activate_comparison_tab_from_header)

    def _register_close_tab(self):
        """Register callback to close tab when X button is clicked."""
        @self.app.callback(
            Output('open-tabs', 'data', allow_duplicate=True),
            Output('active-tab', 'data', allow_duplicate=True),
            Input({'type': 'close-tab-btn', 'tab': ALL}, 'n_clicks'),
            State('open-tabs', 'data'),
            State('active-tab', 'data'),
            prevent_initial_call=True
        )
        def close_tab(n_clicks, open_tabs, active_tab):
            """Remove tab from open tabs when X button clicked."""
            if not ctx.triggered_id:
                raise PreventUpdate

            # Prevent firing when button is just created (n_clicks=None)
            if not n_clicks or all(nc is None or nc == 0 for nc in n_clicks):
                raise PreventUpdate

            tab_id = ctx.triggered_id['tab']

            # Create new list (Dash requires new object to detect changes)
            new_open_tabs = open_tabs.copy() if open_tabs else []

            # Remove from open tabs
            if tab_id in new_open_tabs:
                new_open_tabs.remove(tab_id)

            # If closed tab was active, switch to first remaining tab (or None)
            new_active = active_tab
            if active_tab == tab_id:
                new_active = new_open_tabs[0] if new_open_tabs else None

            return new_open_tabs, new_active

        self._track_callback(close_tab)

    def _register_close_comparison_tab(self):
        """Close a Multi View tab when X is clicked."""
        @self.app.callback(
            Output('comparison-open-tabs', 'data', allow_duplicate=True),
            Output('comparison-active-tab', 'data', allow_duplicate=True),
            Input({'type': 'comparison-close-tab-btn', 'tab': ALL}, 'n_clicks'),
            State('comparison-open-tabs', 'data'),
            State('comparison-active-tab', 'data'),
            prevent_initial_call=True
        )
        def close_comparison_tab(n_clicks, open_tabs, active_tab):
            if not ctx.triggered_id:
                raise PreventUpdate
            if not n_clicks or all(nc is None or nc == 0 for nc in n_clicks):
                raise PreventUpdate

            tab_id = ctx.triggered_id['tab']
            new_open_tabs = open_tabs.copy() if open_tabs else []
            if tab_id in new_open_tabs:
                new_open_tabs.remove(tab_id)

            new_active = active_tab
            if active_tab == tab_id:
                new_active = new_open_tabs[0] if new_open_tabs else None

            return new_open_tabs, new_active

        self._track_callback(close_comparison_tab)

    def _register_toggle_module_selector(self):
        """Register callback to show/hide panel and graphs selectors based on active top-level tab."""
        @self.app.callback(
            Output('sidebar-panel-selector', 'style'),  # Single View
            Output('sidebar-comparison-panel-selector', 'style'),  # Multi View
            Output('sidebar-graphs-selector', 'style'),
            Input('vtk-folder-tabs', 'value'),
            prevent_initial_call=True
        )
        def toggle_sidebar_selectors(active_folder):
            """Show appropriate selector based on active tab."""
            if active_folder == 'custom-graph':
                # On Custom Graph tab: hide modules, show custom graph selector.
                return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
            if active_folder == 'comparison':
                # On Multi View: show comparison panel selector, hide Single View selector.
                return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
            else:
                # On Single View: show panel selector, hide others.
                return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}

        self._track_callback(toggle_sidebar_selectors)

    def _register_populate_custom_graph_selector(self):
        """Populate the Custom Graph folder/file dropdowns in the sidebar."""
        @self.app.callback(
            Output('graphs-folder-selector', 'options'),
            Output('graphs-file-selector', 'options'),
            Output('graphs-file-selector', 'disabled'),
            Output('graphs-folder-selector', 'value', allow_duplicate=True),
            Output('graphs-file-selector', 'value', allow_duplicate=True),
            Input('loaded-textdata-folders', 'data'),
            Input('vtk-folder-tabs', 'value'),
            Input('graphs-folder-selector', 'value'),
            prevent_initial_call=True
        )
        def populate_custom_graph_selector(loaded_projects, active_folder, selected_folder):
            from pathlib import Path
            from ui import get_textdata_files

            if active_folder != 'custom-graph':
                raise PreventUpdate

            textdata_files = get_textdata_files(loaded_projects)
            grouped = {}
            for f in textdata_files:
                p = Path(f)
                project_name = p.parent.parent.name if p.parent.name == 'TextData' else 'Unknown'
                grouped.setdefault(project_name, []).append(str(f))

            folder_options = [{'label': name, 'value': name} for name in sorted(grouped.keys())]

            if not selected_folder or selected_folder not in grouped:
                return folder_options, [], True, None, None

            file_options = []
            for file_str in sorted(grouped[selected_folder]):
                p = Path(file_str)
                file_options.append({'label': p.name, 'value': file_str})

            return folder_options, file_options, False, no_update, None

        self._track_callback(populate_custom_graph_selector)

    # =========================================================================
    # REMOVED CALLBACK: _register_clear_comparison_on_tab_switch (2025-01-14)
    # =========================================================================
    # This callback cleared all Multi View selections when entering the tab,
    # which destroyed valid user work when switching between Custom Graph and
    # Multi View. Since the three tabs (Single View, Multi View, Custom Graph)
    # use different data types and stores, there's no risk of stale state.
    # =========================================================================
    # def _register_clear_comparison_on_tab_switch(self):
    #     """Clear comparison selections when switching into Multi View to avoid stale state."""
    #     @self.app.callback(
    #         Output({'type': 'comparison-selected-files-store', 'group': ALL}, 'data', allow_duplicate=True),
    #         Output({'type': 'comparison-controls-store', 'group': ALL}, 'data', allow_duplicate=True),
    #         Input('vtk-folder-tabs', 'value'),
    #         State({'type': 'comparison-selected-files-store', 'group': ALL}, 'id'),
    #         State({'type': 'comparison-controls-store', 'group': ALL}, 'id'),
    #         prevent_initial_call=True
    #     )
    #     def clear_comparison_on_tab(value, sel_ids, ctrl_ids):
    #         if value != 'comparison':
    #             raise PreventUpdate
    #         if not sel_ids and not ctrl_ids:
    #             raise PreventUpdate
    #         sel_out = [[] for _ in (sel_ids or [])]
    #         ctrl_out = [{} for _ in (ctrl_ids or [])]
    #         return sel_out, ctrl_out
    #
    #     self._track_callback(clear_comparison_on_tab)
