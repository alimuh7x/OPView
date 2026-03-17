"""
Formula panel callback manager for OPView.
"""

from __future__ import annotations

import copy
import time

import numpy as np
import pandas as pd
from dash import ALL, MATCH, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from dash.dcc import send_data_frame

from .base import BaseCallbackManager
from utils.formula_parser import extract_formula_variables
from utils.formula_parser import evaluate_formula


def _new_formula_row_id() -> str:
    """Generate a unique row identifier."""
    return f"formula_{int(time.time() * 1000)}"


def _default_formula_row(expression: str = "sin(x)") -> dict:
    """Return a default formula trace row."""
    return {
        'id': _new_formula_row_id(),
        'expression': expression,
        'label': expression,
        'color': 'black',
        'dash': 'solid',
        'width': 3.0,
    }


def _default_panel_state(panel_number: int) -> dict:
    """Return a default panel state."""
    return {
        'panel_number': panel_number,
        'x_min': -10.0,
        'x_max': 10.0,
        'points': 400,
        'plot_title': 'Formula Plot',
        'x_axis_title': 'x',
        'y_axis_title': 'f(x)',
        'show_grid': True,
        'show_legend': True,
        'show_derivative': False,
        'show_second_derivative': False,
        'show_antiderivative': False,
        'show_tangent': False,
        'show_normal': False,
        'show_root_markers': True,
        'show_extrema_markers': True,
        'show_intersection_markers': True,
        'show_area_shading': False,
        'example_formula': 'sin(x)',
        'analysis_formula': '',
        'analysis_x0': 0.0,
        'interval_min': -2.0,
        'interval_max': 2.0,
        'threshold_value': 0.0,
        'params': {},
        'formulas': [_default_formula_row()],
    }


def _default_param_state() -> dict:
    """Return a default parameter configuration."""
    return {
        'value': 1.0,
        'min': -10.0,
        'max': 10.0,
        'step': 0.1,
    }


def _sync_panel_params(panel_state: dict) -> None:
    """Ensure parameter state matches currently used variables."""
    formulas = panel_state.get('formulas') or []
    existing = panel_state.get('params') or {}
    discovered = {}

    for formula in formulas:
        for param_name in extract_formula_variables(formula.get('expression', '')):
            discovered[param_name] = {
                **_default_param_state(),
                **(existing.get(param_name, {}) or {}),
            }

    panel_state['params'] = discovered


class FormulaCallbackManager(BaseCallbackManager):
    """Manages callbacks for formula plotting panels."""

    def register(self) -> None:
        self._register_add_formula_panel()
        self._register_add_formula_row()
        self._register_apply_example_formula()
        self._register_remove_formula_row()
        self._register_sync_formula_panels()
        self._register_sync_parameter_controls()
        self._register_reset_formula_params()
        self._register_export_formula_csv()
        self._register_update_formula_graph()
        self._register_close_formula_panel()

    def _register_add_formula_panel(self):
        @self.app.callback(
            Output('formula-panels', 'data'),
            Output('formula-panels-container', 'children'),
            Input('formula-add-panel-btn', 'n_clicks'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def add_formula_panel(n_clicks, panels_state):
            from ui.formula_graphs import build_formula_panel

            if ctx.triggered_id != 'formula-add-panel-btn':
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state or {})
            panel_id = f'formula_{int(time.time() * 1000)}'
            panels_state[panel_id] = _default_panel_state(len(panels_state) + 1)

            panels = [
                build_formula_panel(pid, panels_state[pid])
                for pid in sorted(panels_state.keys())
            ]
            return panels_state, panels

        self._track_callback(add_formula_panel)

    def _register_add_formula_row(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-add-row-btn', 'panel': ALL}, 'n_clicks'),
            State({'type': 'formula-example', 'panel': ALL}, 'value'),
            State({'type': 'formula-example', 'panel': ALL}, 'id'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def add_formula_row(n_clicks, example_values, example_ids, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not ctx.triggered_id:
                raise PreventUpdate
            if not n_clicks or all(nc is None or nc == 0 for nc in n_clicks):
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state or {})
            panel_id = ctx.triggered_id['panel']
            panel_state = panels_state.get(panel_id)
            if not panel_state:
                raise PreventUpdate

            selected_example = panel_state.get('example_formula', 'sin(x)')
            for example_id, example_value in zip(example_ids, example_values):
                if example_id.get('panel') == panel_id and example_value:
                    selected_example = example_value
                    break

            panel_state['example_formula'] = selected_example
            formulas = list(panel_state.get('formulas') or [])
            formulas.append(_default_formula_row(selected_example))
            panel_state['formulas'] = formulas
            _sync_panel_params(panel_state)

            panels = [
                build_formula_panel(pid, panels_state[pid])
                for pid in sorted(panels_state.keys())
            ]
            return panels_state, panels

        self._track_callback(add_formula_row)

    def _register_apply_example_formula(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-example', 'panel': ALL}, 'value'),
            State({'type': 'formula-example', 'panel': ALL}, 'id'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def apply_example_formula(example_values, example_ids, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not panels_state:
                raise PreventUpdate
            if not ctx.triggered_id:
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state)
            target_panel = ctx.triggered_id['panel']
            changed = False
            for example_id, value in zip(example_ids, example_values):
                panel_id = example_id['panel']
                if panel_id != target_panel:
                    continue
                if panel_id not in panels_state or value is None:
                    continue

                panel_state = panels_state[panel_id]
                if panel_state.get('example_formula') == value:
                    continue
                panel_state['example_formula'] = value
                formulas = panel_state.get('formulas') or []
                if formulas:
                    old_expression = formulas[0].get('expression')
                    old_label = formulas[0].get('label')
                    formulas[0]['expression'] = value
                    if not old_label or old_label == old_expression:
                        formulas[0]['label'] = value
                _sync_panel_params(panel_state)
                changed = True

            if not changed:
                raise PreventUpdate

            panels = [
                build_formula_panel(pid, panels_state[pid])
                for pid in sorted(panels_state.keys())
            ]
            return panels_state, panels

        self._track_callback(apply_example_formula)

    def _register_remove_formula_row(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-row-remove-btn', 'panel': ALL, 'row': ALL}, 'n_clicks'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def remove_formula_row(n_clicks, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not ctx.triggered_id:
                raise PreventUpdate
            if not n_clicks or all(nc is None or nc == 0 for nc in n_clicks):
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state or {})
            panel_id = ctx.triggered_id['panel']
            row_id = ctx.triggered_id['row']
            panel_state = panels_state.get(panel_id)
            if not panel_state:
                raise PreventUpdate

            formulas = [
                formula for formula in (panel_state.get('formulas') or [])
                if formula.get('id') != row_id
            ]
            if not formulas:
                formulas = [_default_formula_row(panel_state.get('example_formula', 'sin(x)'))]
            panel_state['formulas'] = formulas
            _sync_panel_params(panel_state)

            panels = [
                build_formula_panel(pid, panels_state[pid])
                for pid in sorted(panels_state.keys())
            ]
            return panels_state, panels

        self._track_callback(remove_formula_row)

    def _register_sync_formula_panels(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-row-expression', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-label', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-color', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-dash', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-width', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-x-min', 'panel': ALL}, 'value'),
            Input({'type': 'formula-x-max', 'panel': ALL}, 'value'),
            Input({'type': 'formula-points', 'panel': ALL}, 'value'),
            Input({'type': 'formula-plot-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-x-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-y-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-display-options', 'panel': ALL}, 'value'),
            Input({'type': 'formula-analysis-formula', 'panel': ALL}, 'value'),
            Input({'type': 'formula-analysis-x0', 'panel': ALL}, 'value'),
            Input({'type': 'formula-interval-min', 'panel': ALL}, 'value'),
            Input({'type': 'formula-interval-max', 'panel': ALL}, 'value'),
            Input({'type': 'formula-threshold', 'panel': ALL}, 'value'),
            Input({'type': 'formula-param-slider', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-value', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-min', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-max', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-step', 'panel': ALL, 'param': ALL}, 'value'),
            State({'type': 'formula-row-expression', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-label', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-color', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-dash', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-width', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-x-min', 'panel': ALL}, 'id'),
            State({'type': 'formula-x-max', 'panel': ALL}, 'id'),
            State({'type': 'formula-points', 'panel': ALL}, 'id'),
            State({'type': 'formula-plot-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-x-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-y-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-display-options', 'panel': ALL}, 'id'),
            State({'type': 'formula-analysis-formula', 'panel': ALL}, 'id'),
            State({'type': 'formula-analysis-x0', 'panel': ALL}, 'id'),
            State({'type': 'formula-interval-min', 'panel': ALL}, 'id'),
            State({'type': 'formula-interval-max', 'panel': ALL}, 'id'),
            State({'type': 'formula-threshold', 'panel': ALL}, 'id'),
            State({'type': 'formula-param-slider', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-value', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-min', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-max', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-step', 'panel': ALL, 'param': ALL}, 'id'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def sync_formula_panels(
            formula_expressions, formula_labels, formula_colors, formula_dashes, formula_widths,
            x_mins, x_maxs, points_values, plot_titles, x_titles, y_titles, display_options,
            analysis_formula_values, analysis_x0_values, interval_min_values, interval_max_values, threshold_values,
            param_slider_values, param_input_values, param_min_values, param_max_values, param_step_values,
            expression_ids, label_ids, color_ids, dash_ids, width_ids,
            x_min_ids, x_max_ids, points_ids, plot_title_ids, x_title_ids, y_title_ids, display_ids,
            analysis_formula_ids, analysis_x0_ids, interval_min_ids, interval_max_ids, threshold_ids,
            param_slider_ids, param_input_ids, param_min_ids, param_max_ids, param_step_ids,
            panels_state
        ):
            from dash import no_update
            from ui.formula_graphs import build_formula_panel

            if not panels_state:
                raise PreventUpdate

            # Dash callbacks react more reliably when store updates return a fresh object
            # instead of mutating the existing nested state in place.
            panels_state = copy.deepcopy(panels_state)
            triggered = ctx.triggered_id if isinstance(ctx.triggered_id, dict) else None
            triggered_type = triggered.get('type') if triggered else None

            for component_id, value in zip(expression_ids, formula_expressions):
                panel_id = component_id['panel']
                row_id = component_id['row']
                for formula in panels_state.get(panel_id, {}).get('formulas', []):
                    if formula.get('id') == row_id and value is not None:
                        formula['expression'] = value

            for component_id, value in zip(label_ids, formula_labels):
                panel_id = component_id['panel']
                row_id = component_id['row']
                for formula in panels_state.get(panel_id, {}).get('formulas', []):
                    if formula.get('id') == row_id and value is not None:
                        formula['label'] = value

            for component_id, value in zip(color_ids, formula_colors):
                panel_id = component_id['panel']
                row_id = component_id['row']
                for formula in panels_state.get(panel_id, {}).get('formulas', []):
                    if formula.get('id') == row_id and value is not None:
                        formula['color'] = value

            for component_id, value in zip(dash_ids, formula_dashes):
                panel_id = component_id['panel']
                row_id = component_id['row']
                for formula in panels_state.get(panel_id, {}).get('formulas', []):
                    if formula.get('id') == row_id and value is not None:
                        formula['dash'] = value

            for component_id, value in zip(width_ids, formula_widths):
                panel_id = component_id['panel']
                row_id = component_id['row']
                for formula in panels_state.get(panel_id, {}).get('formulas', []):
                    if formula.get('id') == row_id and value is not None:
                        formula['width'] = value

            for panel_state in panels_state.values():
                _sync_panel_params(panel_state)

            for ids, values, key in (
                (x_min_ids, x_mins, 'x_min'),
                (x_max_ids, x_maxs, 'x_max'),
                (points_ids, points_values, 'points'),
                (plot_title_ids, plot_titles, 'plot_title'),
                (x_title_ids, x_titles, 'x_axis_title'),
                (y_title_ids, y_titles, 'y_axis_title'),
            ):
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    if panel_id in panels_state and value is not None:
                        panels_state[panel_id][key] = value

            for component_id, value in zip(display_ids, display_options):
                panel_id = component_id['panel']
                if panel_id in panels_state:
                    opts = value or []
                    panels_state[panel_id]['show_legend'] = 'legend' in opts
                    panels_state[panel_id]['show_grid'] = 'grid' in opts
                    panels_state[panel_id]['show_derivative'] = 'derivative' in opts
                    panels_state[panel_id]['show_second_derivative'] = 'second_derivative' in opts
                    panels_state[panel_id]['show_antiderivative'] = 'antiderivative' in opts
                    panels_state[panel_id]['show_tangent'] = 'tangent' in opts
                    panels_state[panel_id]['show_normal'] = 'normal' in opts
                    panels_state[panel_id]['show_root_markers'] = 'root_markers' in opts
                    panels_state[panel_id]['show_extrema_markers'] = 'extrema_markers' in opts
                    panels_state[panel_id]['show_intersection_markers'] = 'intersection_markers' in opts
                    panels_state[panel_id]['show_area_shading'] = 'area_shading' in opts

            for ids, values, key in (
                (analysis_formula_ids, analysis_formula_values, 'analysis_formula'),
                (analysis_x0_ids, analysis_x0_values, 'analysis_x0'),
                (interval_min_ids, interval_min_values, 'interval_min'),
                (interval_max_ids, interval_max_values, 'interval_max'),
                (threshold_ids, threshold_values, 'threshold_value'),
            ):
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    if panel_id in panels_state and value is not None:
                        panels_state[panel_id][key] = value

            param_updates = []
            if triggered_type == 'formula-param-slider':
                param_updates.append((param_slider_ids, param_slider_values, 'value'))
            elif triggered_type == 'formula-param-value':
                param_updates.append((param_input_ids, param_input_values, 'value'))
            else:
                # Fallback for non-parameter triggers and initial mixed updates.
                param_updates.extend([
                    (param_slider_ids, param_slider_values, 'value'),
                ])

            param_updates.extend([
                (param_min_ids, param_min_values, 'min'),
                (param_max_ids, param_max_values, 'max'),
                (param_step_ids, param_step_values, 'step'),
            ])

            for ids, values, field in param_updates:
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    param_name = component_id['param']
                    panel_state = panels_state.get(panel_id)
                    if not panel_state or value is None:
                        continue
                    panel_state.setdefault('params', {})
                    panel_state['params'].setdefault(param_name, _default_param_state())
                    panel_state['params'][param_name][field] = value

            structure_trigger_types = {
                'formula-row-expression',
                'formula-row-label',
                'formula-param-min',
                'formula-param-max',
                'formula-param-step',
            }

            if triggered_type in structure_trigger_types:
                panels = [
                    build_formula_panel(pid, panels_state[pid])
                    for pid in sorted(panels_state.keys())
                ]
                return panels_state, panels

            return panels_state, no_update

        self._track_callback(sync_formula_panels)

    def _register_sync_parameter_controls(self):
        @self.app.callback(
            Output({'type': 'formula-param-slider', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-param-slider', 'panel': MATCH, 'param': MATCH}, 'min'),
            Output({'type': 'formula-param-slider', 'panel': MATCH, 'param': MATCH}, 'max'),
            Output({'type': 'formula-param-slider', 'panel': MATCH, 'param': MATCH}, 'step'),
            Output({'type': 'formula-param-value', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-param-min', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-param-max', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-param-step', 'panel': MATCH, 'param': MATCH}, 'value'),
            Input('formula-panels', 'data'),
            State({'type': 'formula-param-slider', 'panel': MATCH, 'param': MATCH}, 'id'),
            prevent_initial_call=False
        )
        def sync_parameter_controls(panels_state, component_id):
            if not component_id:
                raise PreventUpdate

            panel_state = (panels_state or {}).get(component_id['panel'], {})
            params = panel_state.get('params') or {}
            settings = {
                **_default_param_state(),
                **(params.get(component_id['param'], {}) or {}),
            }

            try:
                current_min = float(settings['min'])
                current_max = float(settings['max'])
                current_step = abs(float(settings['step'])) or 0.1
                current_value = float(settings['value'])
            except (TypeError, ValueError):
                defaults = _default_param_state()
                current_min = defaults['min']
                current_max = defaults['max']
                current_step = defaults['step']
                current_value = defaults['value']

            if current_min >= current_max:
                current_max = current_min + max(current_step, 0.1)
            current_value = min(max(current_value, current_min), current_max)

            return (
                current_value,
                current_min,
                current_max,
                current_step,
                current_value,
                current_min,
                current_max,
                current_step,
            )

        self._track_callback(sync_parameter_controls)

    def _register_reset_formula_params(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Input({'type': 'formula-reset-params-btn', 'panel': ALL}, 'n_clicks'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def reset_formula_params(n_clicks, panels_state):
            if not ctx.triggered_id:
                raise PreventUpdate
            if not n_clicks or all(nc is None or nc == 0 for nc in n_clicks):
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state or {})
            panel_id = ctx.triggered_id['panel']
            panel_state = panels_state.get(panel_id)
            if not panel_state:
                raise PreventUpdate

            params = {}
            for param_name in (panel_state.get('params') or {}).keys():
                params[param_name] = _default_param_state()
            panel_state['params'] = params
            return panels_state

        self._track_callback(reset_formula_params)

    def _register_export_formula_csv(self):
        @self.app.callback(
            Output({'type': 'formula-download', 'panel': MATCH}, 'data'),
            Input({'type': 'formula-export-btn', 'panel': MATCH}, 'n_clicks'),
            State('formula-panels', 'data'),
            State({'type': 'formula-export-btn', 'panel': MATCH}, 'id'),
            prevent_initial_call=True
        )
        def export_formula_csv(n_clicks, panels_state, button_id):
            if not n_clicks or not button_id:
                raise PreventUpdate

            panel_state = (panels_state or {}).get(button_id['panel'], {})
            formulas = panel_state.get('formulas') or []
            if not formulas:
                raise PreventUpdate

            x_min = float(panel_state.get('x_min', -10.0))
            x_max = float(panel_state.get('x_max', 10.0))
            points = int(panel_state.get('points', 400))
            x_values = pd.Series(np.linspace(x_min, x_max, points), name='x')
            param_values = {
                name: float((settings or {}).get('value', 1.0))
                for name, settings in (panel_state.get('params') or {}).items()
            }

            data = {'x': x_values}
            for formula in formulas:
                expression = (formula.get('expression') or '').strip()
                if not expression:
                    continue
                label = (formula.get('label') or expression).strip()
                data[label] = evaluate_formula(expression, x_values.to_numpy(), param_values)

            df = pd.DataFrame(data)
            filename = f"{button_id['panel']}_formula_samples.csv"
            return send_data_frame(df.to_csv, filename, index=False)

        self._track_callback(export_formula_csv)

    def _register_update_formula_graph(self):
        @self.app.callback(
            Output({'type': 'formula-plot', 'panel': MATCH}, 'figure'),
            Output({'type': 'formula-analysis', 'panel': MATCH}, 'children'),
            Input('formula-panels', 'data'),
            State({'type': 'formula-plot', 'panel': MATCH}, 'id'),
            prevent_initial_call=False
        )
        def update_formula_graph(panels_state, plot_id):
            from ui.formula_graphs import build_formula_figure

            if not plot_id:
                raise PreventUpdate

            panel_state = (panels_state or {}).get(plot_id['panel'], {})
            figure, summary = build_formula_figure(panel_state)
            return figure, summary

        self._track_callback(update_formula_graph)

    def _register_close_formula_panel(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-close-btn', 'panel': ALL}, 'n_clicks'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def close_formula_panel(n_clicks, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not ctx.triggered_id:
                raise PreventUpdate
            if not n_clicks or all(nc is None or nc == 0 for nc in n_clicks):
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state or {})
            panel_to_remove = ctx.triggered_id['panel']
            panels_state.pop(panel_to_remove, None)

            for index, panel_id in enumerate(sorted(panels_state.keys()), start=1):
                panels_state[panel_id]['panel_number'] = index

            panels = [
                build_formula_panel(pid, panels_state[pid])
                for pid in sorted(panels_state.keys())
            ]
            return panels_state, panels

        self._track_callback(close_formula_panel)
