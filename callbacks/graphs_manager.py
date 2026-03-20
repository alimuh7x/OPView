"""
Graphs tab callback manager for OPView.

Manages callbacks for TextData file selection and plotting.
Extracted Phase 17.
"""

from pathlib import Path
from dash import Output, Input, State, html, ALL, MATCH, ctx, no_update
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager


class GraphsCallbackManager(BaseCallbackManager):
    """
    Manages graphs tab callbacks for text file plotting.

    Registers callbacks for:
    - Adding new graph panels (1-3 files per panel)
    - Updating panels when files are selected
    - Updating graphs when columns or y-axis settings change
    - Removing graph panels when closed
    """

    def __init__(self, app, context):
        """
        Initialize graphs callback manager.

        Args:
            app: Dash application instance
            context: AppContext instance
        """
        super().__init__(app, context)

    def register(self) -> None:
        """Register all graphs-related callbacks."""
        self._register_add_multifile_panel()
        self._register_update_multifile_files()
        self._register_update_multifile_graph()
        self._register_close_multifile_panel()

    def _register_add_multifile_panel(self):
        """Register callback to add a new multi-file panel."""
        @self.app.callback(
            Output('graphs-multifile-panels', 'data'),
            Output('graphs-multifile-container', 'children'),
            Input('graphs-add-file-panel-btn', 'n_clicks'),
            Input('graphs-add-data-panel-btn', 'n_clicks'),
            State('graphs-multifile-panels', 'data'),
            State('loaded-textdata-folders', 'data'),
            prevent_initial_call=True
        )
        def add_multifile_panel(n_clicks_file, n_clicks_data, panels_state, loaded_projects):
            """Add a new multi-file panel."""
            from ui import get_textdata_files, build_multifile_panel
            import time

            if ctx.triggered_id not in {'graphs-add-file-panel-btn', 'graphs-add-data-panel-btn'}:
                raise PreventUpdate

            # Get available files
            available_files = get_textdata_files(loaded_projects)

            # Initialize panels state if None
            if panels_state is None:
                panels_state = {}

            # Generate new panel ID using timestamp to ensure uniqueness
            panel_id = f'panel_{int(time.time() * 1000)}'

            # Calculate sequential panel number for display
            panel_number = len(panels_state) + 1
            source_mode = 'data' if ctx.triggered_id == 'graphs-add-data-panel-btn' else 'file'

            # Add ONLY the new panel to state
            panels_state[panel_id] = {
                'files': [],
                'columns_by_file': {},
                'separate_yaxes': False,
                'panel_number': panel_number,  # Store display number
                'x_axis_title': 'Time',
                'y_axis_title': 'Value',
                'yaxis_titles': {},  # Separate titles for each y-axis
                'yaxis1_units': 'Raw',  # Units for Y-Axis 1
                'yaxis2_units': 'Raw',  # Units for Y-Axis 2
                'legend_position': 'top-left',
                'legend_title': '',
                'show_grid': True,
                'show_legend': True,
                'x_axis_column': None,  # Will be set to first column name when files are selected
                'pasted_data': '',
                'source_mode': source_mode,
                'extend_two_point_lines': False,
                'show_intersections': False,
                'show_roots_intercepts': False,
                'line_range_min': 0.0,
                'line_range_max': 1.0,
                'pasted_point_mode': 'line_only',
                'pasted_marker_count': 25,
            }

            # Build all panels (both existing and new)
            panels = []
            for pid in sorted(panels_state.keys()):
                state = panels_state[pid]
                panels.append(build_multifile_panel(pid, available_files, state))

            return panels_state, panels

        self._track_callback(add_multifile_panel)

    def _register_update_multifile_files(self):
        """Register callback to update panel when files or column selection changes."""
        @self.app.callback(
            Output('graphs-multifile-panels', 'data', allow_duplicate=True),
            Output('graphs-multifile-container', 'children', allow_duplicate=True),
            Input({'type': 'multifile-file-selector', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-pasted-data', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-column-selector', 'panel': ALL, 'file': ALL}, 'value'),
            Input({'type': 'multifile-column-yaxis', 'panel': ALL, 'file': ALL, 'column': ALL}, 'value'),
            Input({'type': 'multifile-column-legend', 'panel': ALL, 'file': ALL, 'column': ALL}, 'value'),
            Input({'type': 'multifile-extend-two-point-lines', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-show-intersections', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-show-roots-intercepts', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-line-range-min', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-line-range-max', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-pasted-point-mode', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-pasted-marker-count', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-legend-position', 'panel': ALL}, 'value'),
            Input({'type': 'multifile-display-options', 'panel': ALL}, 'value'),
            State({'type': 'multifile-file-selector', 'panel': ALL}, 'id'),
            State({'type': 'multifile-pasted-data', 'panel': ALL}, 'id'),
            State({'type': 'multifile-column-selector', 'panel': ALL, 'file': ALL}, 'id'),
            State({'type': 'multifile-column-yaxis', 'panel': ALL, 'file': ALL, 'column': ALL}, 'id'),
            State({'type': 'multifile-column-legend', 'panel': ALL, 'file': ALL, 'column': ALL}, 'id'),
            State({'type': 'multifile-x-axis-column', 'panel': ALL}, 'value'),
            State({'type': 'multifile-x-axis-column', 'panel': ALL}, 'id'),
            State({'type': 'multifile-x-axis-title', 'panel': ALL}, 'value'),
            State({'type': 'multifile-x-axis-title', 'panel': ALL}, 'id'),
            State({'type': 'multifile-extend-two-point-lines', 'panel': ALL}, 'id'),
            State({'type': 'multifile-show-intersections', 'panel': ALL}, 'id'),
            State({'type': 'multifile-show-roots-intercepts', 'panel': ALL}, 'id'),
            State({'type': 'multifile-line-range-min', 'panel': ALL}, 'id'),
            State({'type': 'multifile-line-range-max', 'panel': ALL}, 'id'),
            State({'type': 'multifile-pasted-point-mode', 'panel': ALL}, 'id'),
            State({'type': 'multifile-pasted-marker-count', 'panel': ALL}, 'id'),
            State({'type': 'multifile-legend-position', 'panel': ALL}, 'id'),
            State({'type': 'multifile-display-options', 'panel': ALL}, 'id'),
            State({'type': 'multifile-y-axis-title', 'panel': ALL}, 'value'),
            State({'type': 'multifile-y-axis-title', 'panel': ALL}, 'id'),
            State({'type': 'multifile-yaxis2-title', 'panel': ALL}, 'value'),
            State({'type': 'multifile-yaxis2-title', 'panel': ALL}, 'id'),
            State({'type': 'multifile-yaxis1-units', 'panel': ALL}, 'value'),
            State({'type': 'multifile-yaxis2-units', 'panel': ALL}, 'value'),
            State({'type': 'multifile-yaxis1-units', 'panel': ALL}, 'id'),
            State('graphs-multifile-panels', 'data'),
            State('loaded-textdata-folders', 'data'),
            prevent_initial_call=True
        )
        def update_multifile_files(all_file_selections, all_pasted_data, all_column_selections, all_yaxis_values, all_legend_values,
                                   all_extend_values, all_show_intersections, all_show_roots, all_line_range_mins, all_line_range_maxs,
                                   all_pasted_point_modes, all_pasted_marker_counts, all_legend_positions, all_display_options,
                                   all_file_ids, all_pasted_ids, all_column_ids, all_yaxis_ids, all_legend_ids,
                                   all_x_axis_values, all_x_axis_ids,
                                   all_x_axis_titles, all_x_axis_title_ids,
                                   all_extend_ids,
                                   all_show_intersections_ids,
                                   all_show_roots_ids,
                                   all_line_range_min_ids,
                                   all_line_range_max_ids,
                                   all_pasted_point_mode_ids,
                                   all_pasted_marker_count_ids,
                                   all_legend_position_ids,
                                   all_display_option_ids,
                                   all_y_axis_titles, all_y_axis_title_ids,
                                   all_yaxis2_titles, all_yaxis2_title_ids,
                                   all_yaxis1_units, all_yaxis2_units, all_yaxis_units_ids,
                                   panels_state, loaded_projects):
            """Update panels when file selections or column settings change."""
            from ui import get_textdata_files, build_multifile_panel

            if panels_state is None:
                raise PreventUpdate

            triggered = ctx.triggered_id
            rebuild_trigger_types = {
                'multifile-file-selector',
                'multifile-column-selector',
            }
            preserve_children = not (
                isinstance(triggered, dict) and
                triggered.get('type') in rebuild_trigger_types
            )

            # Update file selections
            for panel_id_dict, selected_files in zip(all_file_ids, all_file_selections):
                panel_id = panel_id_dict['panel']

                if panel_id in panels_state:
                    # Limit to 3 files
                    limited_files = (selected_files or [])[:3]
                    panels_state[panel_id]['files'] = limited_files

                    # Initialize structures
                    if 'columns_by_file' not in panels_state[panel_id]:
                        panels_state[panel_id]['columns_by_file'] = {}
                    if 'column_settings' not in panels_state[panel_id]:
                        panels_state[panel_id]['column_settings'] = {}

                    # Remove columns for files that were deselected
                    files_to_remove = [f for f in panels_state[panel_id]['columns_by_file'].keys() if f not in limited_files]
                    for file_path in files_to_remove:
                        panels_state[panel_id]['columns_by_file'].pop(file_path, None)
                        panels_state[panel_id]['column_settings'].pop(file_path, None)

                    # Initialize for new files
                    for file_path in limited_files:
                        if file_path not in panels_state[panel_id]['columns_by_file']:
                            panels_state[panel_id]['columns_by_file'][file_path] = []
                        if file_path not in panels_state[panel_id]['column_settings']:
                            panels_state[panel_id]['column_settings'][file_path] = {}

            for pasted_id, pasted_text in zip(all_pasted_ids, all_pasted_data):
                panel_id = pasted_id['panel']
                if panel_id in panels_state:
                    panels_state[panel_id]['pasted_data'] = pasted_text or ''

            # Update column selections from checklists
            for column_id, selected_columns in zip(all_column_ids, all_column_selections):
                panel_id = column_id['panel']
                file_path = column_id['file']

                if panel_id in panels_state:
                    if 'columns_by_file' not in panels_state[panel_id]:
                        panels_state[panel_id]['columns_by_file'] = {}
                    panels_state[panel_id]['columns_by_file'][file_path] = selected_columns or []

            # Update column y-axis assignments and legend labels
            for yaxis_val, legend_val, yaxis_id, legend_id in zip(all_yaxis_values, all_legend_values, all_yaxis_ids, all_legend_ids):
                panel_id = yaxis_id['panel']
                file_path = yaxis_id['file']
                column = yaxis_id['column']

                if panel_id in panels_state:
                    if 'column_settings' not in panels_state[panel_id]:
                        panels_state[panel_id]['column_settings'] = {}
                    if file_path not in panels_state[panel_id]['column_settings']:
                        panels_state[panel_id]['column_settings'][file_path] = {}

                    # Store y-axis assignment and legend label (allow empty strings)
                    panels_state[panel_id]['column_settings'][file_path][column] = {
                        'yaxis': yaxis_val or 'y1',
                        'legend': legend_val if legend_val is not None else column  # Preserve empty strings
                    }

            # Preserve X-axis column selections
            for x_axis_val, x_axis_id in zip(all_x_axis_values, all_x_axis_ids):
                panel_id = x_axis_id['panel']
                if panel_id in panels_state and x_axis_val is not None:
                    panels_state[panel_id]['x_axis_column'] = x_axis_val

            # Preserve X-axis title
            for x_title_val, x_title_id in zip(all_x_axis_titles, all_x_axis_title_ids):
                panel_id = x_title_id['panel']
                if panel_id in panels_state and x_title_val is not None:
                    panels_state[panel_id]['x_axis_title'] = x_title_val

            for extend_val, extend_id in zip(all_extend_values, all_extend_ids):
                panel_id = extend_id['panel']
                if panel_id in panels_state:
                    panels_state[panel_id]['extend_two_point_lines'] = 'extend' in (extend_val or [])

            for show_val, show_id in zip(all_show_intersections, all_show_intersections_ids):
                panel_id = show_id['panel']
                if panel_id in panels_state:
                    panels_state[panel_id]['show_intersections'] = 'show' in (show_val or [])

            for show_val, show_id in zip(all_show_roots, all_show_roots_ids):
                panel_id = show_id['panel']
                if panel_id in panels_state:
                    panels_state[panel_id]['show_roots_intercepts'] = 'show' in (show_val or [])

            for range_val, range_id in zip(all_line_range_mins, all_line_range_min_ids):
                panel_id = range_id['panel']
                if panel_id in panels_state and range_val is not None:
                    try:
                        panels_state[panel_id]['line_range_min'] = float(range_val)
                    except (TypeError, ValueError):
                        pass

            for range_val, range_id in zip(all_line_range_maxs, all_line_range_max_ids):
                panel_id = range_id['panel']
                if panel_id in panels_state and range_val is not None:
                    try:
                        panels_state[panel_id]['line_range_max'] = float(range_val)
                    except (TypeError, ValueError):
                        pass

            for mode_val, mode_id in zip(all_pasted_point_modes, all_pasted_point_mode_ids):
                panel_id = mode_id['panel']
                if panel_id in panels_state and mode_val is not None:
                    panels_state[panel_id]['pasted_point_mode'] = mode_val

            for count_val, count_id in zip(all_pasted_marker_counts, all_pasted_marker_count_ids):
                panel_id = count_id['panel']
                if panel_id in panels_state and count_val is not None:
                    try:
                        panels_state[panel_id]['pasted_marker_count'] = max(2, int(count_val))
                    except (TypeError, ValueError):
                        pass

            for legend_pos, legend_id in zip(all_legend_positions, all_legend_position_ids):
                panel_id = legend_id['panel']
                if panel_id in panels_state and legend_pos is not None:
                    panels_state[panel_id]['legend_position'] = legend_pos

            for options, display_id in zip(all_display_options, all_display_option_ids):
                panel_id = display_id['panel']
                if panel_id in panels_state:
                    opts = options or []
                    panels_state[panel_id]['show_legend'] = 'legend' in opts
                    panels_state[panel_id]['show_grid'] = 'grid' in opts

            # Preserve Y-axis titles
            for y_title_val, y_title_id in zip(all_y_axis_titles, all_y_axis_title_ids):
                panel_id = y_title_id['panel']
                if panel_id in panels_state and y_title_val is not None:
                    panels_state[panel_id]['y_axis_title'] = y_title_val

            for yaxis2_title_val, yaxis2_title_id in zip(all_yaxis2_titles, all_yaxis2_title_ids):
                panel_id = yaxis2_title_id['panel']
                if panel_id in panels_state and yaxis2_title_val is not None:
                    if 'yaxis_titles' not in panels_state[panel_id]:
                        panels_state[panel_id]['yaxis_titles'] = {}
                    panels_state[panel_id]['yaxis_titles']['y2'] = yaxis2_title_val

            # Preserve Y-axis units
            for yaxis1_val, yaxis2_val, yaxis_id in zip(all_yaxis1_units, all_yaxis2_units, all_yaxis_units_ids):
                panel_id = yaxis_id['panel']
                if panel_id in panels_state:
                    if yaxis1_val is not None:
                        panels_state[panel_id]['yaxis1_units'] = yaxis1_val
                    if yaxis2_val is not None:
                        panels_state[panel_id]['yaxis2_units'] = yaxis2_val

            # Rebuild all panels only when the control layout itself needs updating.
            if preserve_children:
                return panels_state, no_update

            # Rebuild all panels
            available_files = get_textdata_files(loaded_projects)
            panels = []
            for pid in sorted(panels_state.keys()):
                state = panels_state[pid]
                panels.append(build_multifile_panel(pid, available_files, state))

            return panels_state, panels

        self._track_callback(update_multifile_files)

    def _register_update_multifile_graph(self):
        """Register callback to update multi-file graph."""
        @self.app.callback(
            Output({'type': 'multifile-plot', 'panel': MATCH}, 'figure'),
            Output({'type': 'multifile-analysis', 'panel': MATCH}, 'children'),
            Output({'type': 'multifile-line-range-min', 'panel': MATCH}, 'value'),
            Output({'type': 'multifile-line-range-max', 'panel': MATCH}, 'value'),
            Input('graphs-multifile-panels', 'data'),
            Input({'type': 'multifile-x-axis-title', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-y-axis-title', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-yaxis1-title', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-yaxis2-title', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-yaxis1-units', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-yaxis2-units', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-legend-position', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-legend-title', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-x-axis-column', 'panel': MATCH}, 'value'),
            Input({'type': 'multifile-display-options', 'panel': MATCH}, 'value'),
            State({'type': 'multifile-plot', 'panel': MATCH}, 'id'),
            prevent_initial_call=False  # Allow initial render
        )
        def update_multifile_graph(panels_state, x_title, y_title,
                                   yaxis1_title, yaxis2_title,
                                   yaxis1_units, yaxis2_units,
                                   legend_position, legend_title,
                                   x_axis_column, display_options, plot_id):
            """Update the multi-file graph when columns, axes, titles, or settings change."""
            from ui import build_multifile_figure

            if not panels_state or not plot_id:
                raise PreventUpdate

            panel_id = plot_id['panel']
            panel_state = panels_state.get(panel_id, {})

            # Get files and columns from panel state
            files_and_columns = panel_state.get('columns_by_file', {})
            # Get column settings from panel state
            column_settings = panel_state.get('column_settings', {})

            # Use default titles if none provided
            x_axis_title = x_title or 'Time'
            y_axis_title = y_title or 'Value'

            # Build yaxis_titles dict
            yaxis_titles = {}
            if y_title:
                yaxis_titles['y1'] = y_title
            if yaxis2_title:
                yaxis_titles['y2'] = yaxis2_title

            # Use defaults if not provided
            legend_position = legend_position or 'top-left'
            legend_title = legend_title or ''

            # Set x_axis_column default to first column name from first file
            if not x_axis_column:
                if files_and_columns:
                    from data.sources import GenericTextDataSource
                    first_file = list(files_and_columns.keys())[0]
                    try:
                        ds = GenericTextDataSource(Path(first_file))
                        if ds.load():
                            cols = ds.get_available_columns()
                            x_axis_column = cols[0] if cols else 'col_0'
                        else:
                            x_axis_column = 'col_0'
                    except Exception:
                        x_axis_column = 'col_0'
                else:
                    x_axis_column = 'col_0'

            # Parse display options
            display_opts = display_options or []
            show_legend = 'legend' in display_opts
            show_grid = 'grid' in display_opts

            # Build figure with y-axis units
            figure, analysis, resolved_range = build_multifile_figure(
                files_and_columns,
                column_settings,  # Pass column settings (yaxis assignment per column)
                x_axis_title,
                y_axis_title,
                yaxis_titles,
                legend_position,
                legend_title,
                show_grid,
                show_legend,
                x_axis_column,
                yaxis1_units or 'Raw',
                yaxis2_units or 'Raw',
                panel_state.get('pasted_data', ''),
                panel_state.get('extend_two_point_lines', False),
                panel_state.get('show_intersections', False),
                panel_state.get('show_roots_intercepts', False),
                panel_state.get('line_range_min'),
                panel_state.get('line_range_max'),
                panel_state.get('pasted_point_mode', 'line_only'),
                panel_state.get('pasted_marker_count', 25),
            )
            resolved_min, resolved_max = resolved_range
            return figure, analysis, resolved_min, resolved_max

        self._track_callback(update_multifile_graph)

    def _register_close_multifile_panel(self):
        """Register callback to close a multi-file panel."""
        @self.app.callback(
            Output('graphs-multifile-panels', 'data', allow_duplicate=True),
            Output('graphs-multifile-container', 'children', allow_duplicate=True),
            Input({'type': 'multifile-close-btn', 'panel': ALL}, 'n_clicks'),
            State({'type': 'multifile-close-btn', 'panel': ALL}, 'id'),
            State('graphs-multifile-panels', 'data'),
            State('loaded-textdata-folders', 'data'),
            prevent_initial_call=True
        )
        def close_multifile_panel(n_clicks, all_ids, panels_state, loaded_projects):
            """Remove a multi-file panel when close button clicked."""
            if not ctx.triggered_id:
                raise PreventUpdate

            if not n_clicks or all(nc is None or nc == 0 for nc in n_clicks):
                raise PreventUpdate

            from ui import get_textdata_files, build_multifile_panel

            # Get panel to remove
            panel_to_remove = ctx.triggered_id['panel']

            # Remove from state
            if panels_state and panel_to_remove in panels_state:
                del panels_state[panel_to_remove]

            # Rebuild remaining panels
            available_files = get_textdata_files(loaded_projects)
            panels = []
            for pid in sorted(panels_state.keys()):
                state = panels_state[pid]
                panels.append(build_multifile_panel(pid, available_files, state))

            return panels_state, panels

        self._track_callback(close_multifile_panel)
