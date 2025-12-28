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
        self._register_add_tab_from_dropdown()
        self._register_render_tab_headers()
        self._register_activate_tab_from_header()
        self._register_close_tab()

    # =========================================================================
    # OLD CALLBACK - Removed (Phase 14 - Dynamic Tab Management) ✅
    # =========================================================================
    # _register_set_active_tab() removed - used old tab buttons
    # Replaced by _register_activate_tab_from_header() for dynamic tab headers
    # =========================================================================

    def _register_render_tab_content(self):
        """Register callback to render active tab content."""
        @self.app.callback(
            Output('tab-content', 'children'),
            Output('tab-content', 'style'),
            Output('comparison-content', 'children'),
            Output('comparison-content', 'style'),
            Input('active-tab', 'data'),
            Input('open-tabs', 'data'),
            Input('comparison-files-store', 'data'),
            Input('selected-project-folder', 'data'),
            Input('loaded-project-folders', 'data'),
            Input('vtk-folder-tabs', 'value'),
            State({'type': 'comparison-controls-store', 'group': ALL}, 'data'),
            State({'type': 'comparison-controls-store', 'group': ALL}, 'id'),
            State({'type': 'comparison-selected-files-store', 'group': ALL}, 'data'),
            State({'type': 'comparison-selected-files-store', 'group': ALL}, 'id'),
            prevent_initial_call=True
        )
        def render_active_tab(active_tab, open_tabs, comparison_files, _active_project, _loaded_projects, active_folder,
                              group_controls_data, group_controls_ids,
                              selected_group_data, selected_group_ids):
            """Render content for the active tab."""
            # Import dependencies
            from dash import html
            from OPView import (
                build_tab_children, build_comparison_content,
                allowed_comparison_groups_for_tab
            )

            # Show placeholder if no tabs open
            if not open_tabs or (not active_tab and active_folder != 'comparison'):
                return (
                    html.Div("Add a module from the dropdown to get started",
                            className='dataset-empty',
                            style={'padding': '40px', 'text-align': 'center'}),
                    {'display': 'block'},
                    no_update,
                    no_update,
                )

            if active_folder == 'comparison':
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

                allowed_groups = allowed_comparison_groups_for_tab(active_tab)
                return (
                    no_update,
                    {'display': 'none'},
                    build_comparison_content(comparison_files or [], stored_by_group, selected_by_group, allowed_groups),
                    {'display': 'block'},
                )

            children = build_tab_children(active_tab)
            return (
                children,
                {'display': 'block'},
                no_update,
                {'display': 'none'},
            )

        self._track_callback(render_active_tab)

    def _register_add_tab_from_dropdown(self):
        """Register callback to add tab when selected from dropdown."""
        @self.app.callback(
            Output('open-tabs', 'data'),
            Output('active-tab', 'data', allow_duplicate=True),
            Output('module-selector-dropdown', 'value'),
            Input('module-selector-dropdown', 'value'),
            State('open-tabs', 'data'),
            prevent_initial_call=True
        )
        def add_tab_from_dropdown(selected_module, open_tabs):
            """Add selected module to open tabs and activate it."""
            if not selected_module:
                raise PreventUpdate

            # Create new list (Dash requires new object to detect changes)
            new_open_tabs = open_tabs.copy() if open_tabs else []

            # Add tab if not already open
            if selected_module not in new_open_tabs:
                new_open_tabs.append(selected_module)

            # Set as active tab and clear dropdown
            return new_open_tabs, selected_module, None

        self._track_callback(add_tab_from_dropdown)

    def _register_render_tab_headers(self):
        """Register callback to render dynamic tab headers."""
        @self.app.callback(
            Output('dynamic-tab-headers', 'children'),
            Input('open-tabs', 'data'),
            Input('active-tab', 'data'),  # Changed from State to Input - updates when active tab changes
            prevent_initial_call=True  # Prevent firing on initial page load
        )
        def render_tab_headers(open_tabs, active_tab):
            """Render horizontal tab headers with close buttons."""
            from dash import html
            from OPView import TAB_CONFIGS

            if not open_tabs:
                return []

            icons = {
                "phase-field": "⛶",
                "composition": "⚛",
                "mechanics": "⚙",
                "plasticity": "🧪",
            }

            # Get labels from TAB_CONFIGS
            tab_labels = {tab['id']: tab['label'] for tab in TAB_CONFIGS}

            headers = []
            for tab_id in open_tabs:
                is_active = (tab_id == active_tab)

                headers.append(
                    html.Div([
                        html.Span(icons.get(tab_id, "•"), className='tab-icon'),
                        html.Span(tab_labels.get(tab_id, tab_id.title()), className='tab-label'),
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
