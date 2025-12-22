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
        self._register_set_active_tab()
        self._register_render_tab_content()

    def _register_set_active_tab(self):
        """Register callback to set active tab based on button clicks."""
        @self.app.callback(
            Output('active-tab', 'data'),
            Input({'type': 'tab-button', 'tab': ALL}, 'n_clicks'),
            State('active-tab', 'data'),
            prevent_initial_call=True
        )
        def set_active_tab(n_clicks, current_tab):
            """Set active tab when tab button is clicked."""
            trigger = ctx.triggered_id
            if isinstance(trigger, dict) and trigger.get('tab'):
                return trigger['tab']
            return current_tab

        self._track_callback(set_active_tab)

    def _register_render_tab_content(self):
        """Register callback to render active tab content."""
        @self.app.callback(
            Output('tab-content', 'children'),
            Output('tab-content', 'style'),
            Output('comparison-content', 'children'),
            Output('comparison-content', 'style'),
            Output({'type': 'tab-button', 'tab': ALL}, 'className'),
            Input('active-tab', 'data'),
            Input('comparison-files-store', 'data'),
            Input('selected-project-folder', 'data'),
            Input('loaded-project-folders', 'data'),
            Input('vtk-folder-tabs', 'value'),
            State({'type': 'comparison-controls-store', 'group': ALL}, 'data'),
            State({'type': 'comparison-controls-store', 'group': ALL}, 'id'),
            State({'type': 'comparison-selected-files-store', 'group': ALL}, 'data'),
            State({'type': 'comparison-selected-files-store', 'group': ALL}, 'id'),
        )
        def render_active_tab(active_tab, comparison_files, _active_project, _loaded_projects, active_folder,
                              group_controls_data, group_controls_ids,
                              selected_group_data, selected_group_ids):
            """Render content for the active tab."""
            # Import dependencies
            from dash import html
            from OPView import (
                build_tab_children, build_comparison_content,
                allowed_comparison_groups_for_tab, TAB_ORDER
            )

            if active_tab is None and active_folder != 'comparison':
                return (
                    html.Div("No tabs available", className='dataset-empty'),
                    {},
                    [],
                    {'display': 'none'},
                    ['custom-tab'] * len(TAB_ORDER),
                )

            classes = [
                'custom-tab active-tab' if tab_id == active_tab else 'custom-tab'
                for tab_id in TAB_ORDER
            ]

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
                    classes,
                )

            children = build_tab_children(active_tab)
            return (
                children,
                {'display': 'block'},
                no_update,
                {'display': 'none'},
                classes,
            )

        self._track_callback(render_active_tab)
