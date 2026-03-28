"""
Formula panel callback manager for OPView.
"""

from __future__ import annotations

import copy
import time

import numpy as np
import pandas as pd
import plotly.io as pio
from dash import ALL, MATCH, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from dash.dcc import send_bytes, send_data_frame

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
        'visible': True,
    }


PRESET_PARAM_DEFAULTS = {
    'sin(x)': {},
    'a*exp(-b*x) * sin(c*x)': {
        'a': {'value': 1.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
        'b': {'value': 0.15, 'min': 0.0, 'max': 2.0, 'step': 0.01},
        'c': {'value': 2.0, 'min': 0.1, 'max': 10.0, 'step': 0.1},
    },
    'a*exp(-((x-b)**2)/(2*c**2))': {
        'a': {'value': 1.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
        'b': {'value': 0.0, 'min': -10.0, 'max': 10.0, 'step': 0.1},
        'c': {'value': 1.5, 'min': 0.1, 'max': 10.0, 'step': 0.1},
    },
    '1 / (1 + exp(-a*(x-b)))': {
        'a': {'value': 1.0, 'min': 0.1, 'max': 10.0, 'step': 0.1},
        'b': {'value': 0.0, 'min': -10.0, 'max': 10.0, 'step': 0.1},
    },
    'a*exp(-x/tau) + c': {
        'a': {'value': 1.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
        'tau': {'value': 2.0, 'min': 0.1, 'max': 20.0, 'step': 0.1},
        'c': {'value': 0.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
    },
    'a*(1-exp(-x/tau)) + c': {
        'a': {'value': 1.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
        'tau': {'value': 2.0, 'min': 0.1, 'max': 20.0, 'step': 0.1},
        'c': {'value': 0.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
    },
    'a / (1 + exp(-(x-b)/c)) + d': {
        'a': {'value': 1.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
        'b': {'value': 0.0, 'min': -10.0, 'max': 10.0, 'step': 0.1},
        'c': {'value': 1.0, 'min': 0.1, 'max': 10.0, 'step': 0.1},
        'd': {'value': 0.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
    },
    'a*exp(-q/(r*x))': {
        'a': {'value': 1.0, 'min': 0.0, 'max': 10.0, 'step': 0.1},
        'q': {'value': 1.0, 'min': 0.1, 'max': 10.0, 'step': 0.1},
        'r': {'value': 1.0, 'min': 0.1, 'max': 10.0, 'step': 0.1},
    },
    'a/(x-b) + c': {
        'a': {'value': 1.0, 'min': -10.0, 'max': 10.0, 'step': 0.1},
        'b': {'value': 0.0, 'min': -10.0, 'max': 10.0, 'step': 0.1},
        'c': {'value': 0.0, 'min': -10.0, 'max': 10.0, 'step': 0.1},
    },
}


PRESET_PANEL_DEFAULTS = {
    'a*exp(-q/(r*x))': {
        'x_min': 200.0,
        'x_max': 1600.0,
        'points': 600,
        'x_axis_title': 'Temperature',
        'y_axis_title': 'Rate',
        'interval_min': 300.0,
        'interval_max': 1200.0,
        'analysis_x0': 800.0,
    },
}

PRESET_2D_DEFAULTS = {
    'periodic_surface': {
        'expression_2d': 'sin(x)*cos(y)',
        'label_2d': 'sin(x)*cos(y)',
        'x_min': -5.0, 'x_max': 5.0, 'y_min': -5.0, 'y_max': 5.0,
        'x_points_2d': 80, 'y_points_2d': 80,
        'x_axis_title': 'x', 'y_axis_title': 'y', 'z_axis_title': 'f(x,y)',
        'surface_colorscale': 'Viridis',
    },
    'gaussian_hill': {
        'expression_2d': 'a*exp(-((x-x0)**2 + (y-y0)**2)/(2*sigma**2))',
        'label_2d': 'Gaussian hill',
        'x_min': -6.0, 'x_max': 6.0, 'y_min': -6.0, 'y_max': 6.0,
        'x_points_2d': 100, 'y_points_2d': 100,
        'x_axis_title': 'x', 'y_axis_title': 'y', 'z_axis_title': 'height',
        'surface_colorscale': 'Plasma',
        'params': {
            'a': {'value': 1.0, 'min': 0.0, 'max': 5.0, 'step': 0.1},
            'x0': {'value': 0.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
            'y0': {'value': 0.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
            'sigma': {'value': 1.5, 'min': 0.1, 'max': 5.0, 'step': 0.1},
        },
    },
    'saddle': {
        'expression_2d': 'x**2 - y**2',
        'label_2d': 'Saddle surface',
        'x_min': -4.0, 'x_max': 4.0, 'y_min': -4.0, 'y_max': 4.0,
        'x_points_2d': 90, 'y_points_2d': 90,
        'x_axis_title': 'x', 'y_axis_title': 'y', 'z_axis_title': 'z',
        'surface_colorscale': 'RdBu',
    },
    'paraboloid': {
        'expression_2d': 'a*(x**2 + y**2) + c',
        'label_2d': 'Paraboloid',
        'x_min': -4.0, 'x_max': 4.0, 'y_min': -4.0, 'y_max': 4.0,
        'x_points_2d': 90, 'y_points_2d': 90,
        'x_axis_title': 'x', 'y_axis_title': 'y', 'z_axis_title': 'z',
        'surface_colorscale': 'Cividis',
        'params': {
            'a': {'value': 1.0, 'min': -2.0, 'max': 2.0, 'step': 0.1},
            'c': {'value': 0.0, 'min': -5.0, 'max': 5.0, 'step': 0.1},
        },
    },
    'radial_decay': {
        'expression_2d': 'a*exp(-sqrt(x**2 + y**2)/tau)',
        'label_2d': 'Radial decay',
        'x_min': -8.0, 'x_max': 8.0, 'y_min': -8.0, 'y_max': 8.0,
        'x_points_2d': 100, 'y_points_2d': 100,
        'x_axis_title': 'x', 'y_axis_title': 'y', 'z_axis_title': 'z',
        'surface_colorscale': 'Turbo',
        'params': {
            'a': {'value': 1.0, 'min': 0.0, 'max': 5.0, 'step': 0.1},
            'tau': {'value': 2.5, 'min': 0.1, 'max': 10.0, 'step': 0.1},
        },
    },
}


def _default_panel_state(panel_number: int) -> dict:
    """Return a default panel state."""
    return {
        'panel_type': '1d',
        'panel_number': panel_number,
        'x_min': -10.0,
        'x_max': 10.0,
        'points': 400,
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
        'show_monotonicity_regions': True,
        'show_concavity_regions': True,
        'example_formula': 'sin(x)',
        'analysis_formula': '',
        'analysis_x0': 0.0,
        'interval_min': -2.0,
        'interval_max': 2.0,
        'threshold_value': None,
        'click_mode': 'focus',
        'pending_interval_start': None,
        'params': {},
        'formulas': [_default_formula_row()],
    }


def _default_panel_state_2d(panel_number: int) -> dict:
    """Return a default 2D panel state."""
    return {
        'panel_type': '2d',
        'panel_number': panel_number,
        'preset_2d': 'periodic_surface',
        'expression_2d': 'sin(x)*cos(y)',
        'label_2d': 'sin(x)*cos(y)',
        'x_min': -5.0,
        'x_max': 5.0,
        'y_min': -5.0,
        'y_max': 5.0,
        'x_points_2d': 80,
        'y_points_2d': 80,
        'x_axis_title': 'x',
        'y_axis_title': 'y',
        'z_axis_title': 'f(x,y)',
        'surface_colorscale': 'Viridis',
        'display_mode_2d': 'surface',
        'contour_levels_2d': 12,
        'contour_style_2d': 'filled',
        'auto_z_range_2d': True,
        'z_min_2d': None,
        'z_max_2d': None,
        'probe_x_2d': 0.0,
        'probe_y_2d': 0.0,
        'params': {},
    }


def _default_param_state() -> dict:
    """Return a default parameter configuration."""
    return {
        'value': 1.0,
        'min': -10.0,
        'max': 10.0,
        'step': 0.1,
        'use_notebook': False,
    }


def _safe_float(value, fallback: float) -> float:
    """Convert callback values to float without crashing on empty/text input."""
    try:
        if value in (None, ""):
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _safe_int(value, fallback: int) -> int:
    """Convert callback values to int without crashing on empty/text input."""
    try:
        if value in (None, ""):
            return fallback
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _sync_panel_params(panel_state: dict) -> None:
    """Ensure parameter state matches currently used variables."""
    existing = panel_state.get('params') or {}
    discovered = {}
    if panel_state.get('panel_type', '1d') == '2d':
        for param_name in extract_formula_variables(panel_state.get('expression_2d', ''), coordinate_names=('x', 'y')):
            discovered[param_name] = {
                **_default_param_state(),
                **(existing.get(param_name, {}) or {}),
            }
    else:
        formulas = panel_state.get('formulas') or []
        for formula in formulas:
            for param_name in extract_formula_variables(formula.get('expression', '')):
                discovered[param_name] = {
                    **_default_param_state(),
                    **(existing.get(param_name, {}) or {}),
                }

    panel_state['params'] = discovered


def _apply_preset_defaults(panel_state: dict, expression: str) -> None:
    """Apply known parameter defaults for the selected preset."""
    _sync_panel_params(panel_state)
    defaults = PRESET_PARAM_DEFAULTS.get((expression or '').strip(), {})
    if not defaults:
        return

    params = panel_state.get('params') or {}
    for param_name, config in defaults.items():
        params[param_name] = {
            **_default_param_state(),
            **params.get(param_name, {}),
            **config,
        }
    panel_state['params'] = params

    panel_defaults = PRESET_PANEL_DEFAULTS.get((expression or '').strip(), {})
    for key, value in panel_defaults.items():
        panel_state[key] = value


def _apply_2d_preset_defaults(panel_state: dict, preset_id: str) -> None:
    """Apply defaults for a 2D preset."""
    preset = PRESET_2D_DEFAULTS.get(preset_id)
    if not preset:
        return

    panel_state.update({k: v for k, v in preset.items() if k != 'params'})
    panel_state['preset_2d'] = preset_id
    _sync_panel_params(panel_state)
    if preset.get('params'):
        params = panel_state.get('params') or {}
        for param_name, config in preset['params'].items():
            params[param_name] = {
                **_default_param_state(),
                **params.get(param_name, {}),
                **config,
            }
        panel_state['params'] = params


class FormulaCallbackManager(BaseCallbackManager):
    """Manages callbacks for formula plotting panels."""

    def register(self) -> None:
        self._register_add_formula_panel()
        self._register_add_formula_row()
        self._register_apply_example_formula()
        self._register_remove_formula_row()
        self._register_formula_steppers()
        self._register_sync_formula_panels()
        self._register_sync_formula_panels_2d()
        self._register_sync_parameter_controls()
        self._register_sync_parameter_controls_2d()
        self._register_graph_click_selection()
        self._register_analysis_jump()
        self._register_reset_formula_params()
        self._register_export_formula_csv()
        self._register_export_formula_png()
        self._register_update_formula_graph()
        self._register_update_formula_graph_2d()
        self._register_update_formula_slices_2d()
        self._register_close_formula_panel()

    def _register_add_formula_panel(self):
        @self.app.callback(
            Output('formula-panels', 'data'),
            Output('formula-panels-container', 'children'),
            Input('formula-add-panel-1d-btn', 'n_clicks'),
            Input('formula-add-panel-2d-btn', 'n_clicks'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def add_formula_panel(n_clicks_1d, n_clicks_2d, panels_state):
            from ui.formula_graphs import build_formula_panel

            if ctx.triggered_id not in {'formula-add-panel-1d-btn', 'formula-add-panel-2d-btn'}:
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state or {})
            panel_id = f'formula_{int(time.time() * 1000)}'
            if ctx.triggered_id == 'formula-add-panel-2d-btn':
                panels_state[panel_id] = _default_panel_state_2d(len(panels_state) + 1)
                _apply_2d_preset_defaults(panels_state[panel_id], panels_state[panel_id].get('preset_2d', 'periodic_surface'))
            else:
                panels_state[panel_id] = _default_panel_state(len(panels_state) + 1)
                _apply_preset_defaults(panels_state[panel_id], panels_state[panel_id].get('example_formula', 'sin(x)'))

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
            if panel_state.get('panel_type', '1d') != '1d':
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
            _apply_preset_defaults(panel_state, selected_example)

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
                if panel_state.get('panel_type', '1d') != '1d':
                    continue
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
                _apply_preset_defaults(panel_state, value)
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
            if panel_state.get('panel_type', '1d') != '1d':
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

    def _register_formula_steppers(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-stepper-btn', 'panel': ALL, 'field': ALL, 'row': ALL, 'direction': ALL}, 'n_clicks'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def apply_formula_stepper(n_clicks, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not ctx.triggered_id or not panels_state:
                raise PreventUpdate
            if not n_clicks or all(value is None or value == 0 for value in n_clicks):
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state or {})
            panel_id = ctx.triggered_id['panel']
            field = ctx.triggered_id['field']
            row_id = ctx.triggered_id['row']
            direction = ctx.triggered_id['direction']

            panel_state = panels_state.get(panel_id)
            if not panel_state:
                raise PreventUpdate

            delta = -1 if direction == 'minus' else 1

            if field == 'x_min':
                current = float(panel_state.get('x_min', -10.0))
                panel_state['x_min'] = current + delta * 1.0
            elif field == 'x_max':
                current = float(panel_state.get('x_max', 10.0))
                panel_state['x_max'] = current + delta * 1.0
            elif field == 'points':
                current = int(panel_state.get('points', 400))
                panel_state['points'] = max(50, min(5000, current + delta * 50))
            elif field == 'width':
                for formula in panel_state.get('formulas', []):
                    if formula.get('id') != row_id:
                        continue
                    current = float(formula.get('width', 3.0))
                    formula['width'] = max(1.0, min(8.0, round(current + delta * 0.5, 2)))
                    break
            else:
                raise PreventUpdate

            panels = [
                build_formula_panel(pid, panels_state[pid])
                for pid in sorted(panels_state.keys())
            ]
            return panels_state, panels

        self._track_callback(apply_formula_stepper)

    def _register_sync_formula_panels(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-row-expression', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-label', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-color', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-dash', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-width', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-row-visible', 'panel': ALL, 'row': ALL}, 'value'),
            Input({'type': 'formula-x-min', 'panel': ALL}, 'value'),
            Input({'type': 'formula-x-max', 'panel': ALL}, 'value'),
            Input({'type': 'formula-points', 'panel': ALL}, 'value'),
            Input({'type': 'formula-x-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-y-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-display-options', 'panel': ALL}, 'value'),
            Input({'type': 'formula-analysis-formula', 'panel': ALL}, 'value'),
            Input({'type': 'formula-analysis-x0', 'panel': ALL}, 'value'),
            Input({'type': 'formula-interval-min', 'panel': ALL}, 'value'),
            Input({'type': 'formula-interval-max', 'panel': ALL}, 'value'),
            Input({'type': 'formula-threshold', 'panel': ALL}, 'value'),
            Input({'type': 'formula-click-mode', 'panel': ALL}, 'value'),
            Input({'type': 'formula-param-slider', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-value', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-min', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-max', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-step', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-param-nb-toggle', 'panel': ALL, 'param': ALL}, 'n_clicks'),
            Input('notebook-state', 'data'),
            State({'type': 'formula-row-expression', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-label', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-color', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-dash', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-width', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-row-visible', 'panel': ALL, 'row': ALL}, 'id'),
            State({'type': 'formula-x-min', 'panel': ALL}, 'id'),
            State({'type': 'formula-x-max', 'panel': ALL}, 'id'),
            State({'type': 'formula-points', 'panel': ALL}, 'id'),
            State({'type': 'formula-x-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-y-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-display-options', 'panel': ALL}, 'id'),
            State({'type': 'formula-analysis-formula', 'panel': ALL}, 'id'),
            State({'type': 'formula-analysis-x0', 'panel': ALL}, 'id'),
            State({'type': 'formula-interval-min', 'panel': ALL}, 'id'),
            State({'type': 'formula-interval-max', 'panel': ALL}, 'id'),
            State({'type': 'formula-threshold', 'panel': ALL}, 'id'),
            State({'type': 'formula-click-mode', 'panel': ALL}, 'id'),
            State({'type': 'formula-param-slider', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-value', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-min', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-max', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-step', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-param-nb-toggle', 'panel': ALL, 'param': ALL}, 'id'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def sync_formula_panels(
            formula_expressions, formula_labels, formula_colors, formula_dashes, formula_widths, formula_visible_values,
            x_mins, x_maxs, points_values, x_titles, y_titles, display_options,
            analysis_formula_values, analysis_x0_values, interval_min_values, interval_max_values, threshold_values, click_mode_values,
            param_slider_values, param_input_values, param_min_values, param_max_values, param_step_values,
            param_nb_toggle_clicks, notebook_state,
            expression_ids, label_ids, color_ids, dash_ids, width_ids, visible_ids,
            x_min_ids, x_max_ids, points_ids, x_title_ids, y_title_ids, display_ids,
            analysis_formula_ids, analysis_x0_ids, interval_min_ids, interval_max_ids, threshold_ids, click_mode_ids,
            param_slider_ids, param_input_ids, param_min_ids, param_max_ids, param_step_ids,
            param_nb_toggle_ids,
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
                        current = _safe_float(formula.get('width', 3.0), 3.0)
                        formula['width'] = max(1.0, min(8.0, _safe_float(value, current)))

            for component_id, value in zip(visible_ids, formula_visible_values):
                panel_id = component_id['panel']
                row_id = component_id['row']
                for formula in panels_state.get(panel_id, {}).get('formulas', []):
                    if formula.get('id') == row_id:
                        formula['visible'] = 'visible' in (value or [])

            for panel_state in panels_state.values():
                _sync_panel_params(panel_state)

            for component_id, value in zip(x_min_ids, x_mins):
                panel_id = component_id['panel']
                if panel_id in panels_state and value is not None:
                    current = _safe_float(panels_state[panel_id].get('x_min', -10.0), -10.0)
                    panels_state[panel_id]['x_min'] = _safe_float(value, current)

            for component_id, value in zip(x_max_ids, x_maxs):
                panel_id = component_id['panel']
                if panel_id in panels_state and value is not None:
                    current = _safe_float(panels_state[panel_id].get('x_max', 10.0), 10.0)
                    panels_state[panel_id]['x_max'] = _safe_float(value, current)

            for component_id, value in zip(points_ids, points_values):
                panel_id = component_id['panel']
                if panel_id in panels_state and value is not None:
                    current = _safe_int(panels_state[panel_id].get('points', 400), 400)
                    panels_state[panel_id]['points'] = max(10, min(5000, _safe_int(value, current)))
            for ids, values, key in (
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
                    panels_state[panel_id]['show_monotonicity_regions'] = 'monotonicity_regions' in opts
                    panels_state[panel_id]['show_concavity_regions'] = 'concavity_regions' in opts

            for ids, values, key in (
                (analysis_formula_ids, analysis_formula_values, 'analysis_formula'),
                (analysis_x0_ids, analysis_x0_values, 'analysis_x0'),
                (interval_min_ids, interval_min_values, 'interval_min'),
                (interval_max_ids, interval_max_values, 'interval_max'),
                (click_mode_ids, click_mode_values, 'click_mode'),
            ):
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    if panel_id in panels_state and value is not None:
                        panels_state[panel_id][key] = value

            for component_id, value in zip(threshold_ids, threshold_values):
                panel_id = component_id['panel']
                if panel_id in panels_state:
                    panels_state[panel_id]['threshold_value'] = value

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
                    current = _safe_float(
                        panel_state['params'][param_name].get(field, _default_param_state()[field]),
                        _default_param_state()[field]
                    )
                    panel_state['params'][param_name][field] = _safe_float(value, current)

            # Handle NB toggle: flip use_notebook for the clicked parameter
            if triggered_type == 'formula-param-nb-toggle' and triggered:
                panel_id = triggered['panel']
                param_name = triggered['param']
                panel_state = panels_state.get(panel_id)
                if panel_state:
                    panel_state.setdefault('params', {})
                    panel_state['params'].setdefault(param_name, _default_param_state())
                    current_use_nb = panel_state['params'][param_name].get('use_notebook', False)
                    new_use_nb = not current_use_nb
                    panel_state['params'][param_name]['use_notebook'] = new_use_nb
                    # Pre-fill value from notebook when binding
                    nb_vars = (notebook_state or {}).get('variables', {})
                    if new_use_nb and param_name in nb_vars:
                        try:
                            panel_state['params'][param_name]['value'] = float(nb_vars[param_name])
                        except (TypeError, ValueError):
                            pass

            # Inject notebook variables for display in panel UI
            nb_vars = (notebook_state or {}).get('variables', {})
            for pid in panels_state:
                panels_state[pid]['_notebook_vars'] = nb_vars

            structure_trigger_types = {
                'formula-row-expression',
                'formula-row-label',
                'formula-param-min',
                'formula-param-max',
                'formula-param-step',
                'formula-param-nb-toggle',
                'notebook-state',
            }

            if triggered_type in structure_trigger_types or (isinstance(ctx.triggered_id, str) and ctx.triggered_id == 'notebook-state'):
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
            State('notebook-state', 'data'),
            prevent_initial_call=False
        )
        def sync_parameter_controls(panels_state, component_id, notebook_state):
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

            # Override value from notebook if use_notebook is set
            if settings.get('use_notebook'):
                nb_vars = (notebook_state or {}).get('variables', {})
                param_name = component_id['param']
                if param_name in nb_vars:
                    try:
                        nb_value = float(nb_vars[param_name])
                        # Expand slider range to accommodate notebook value if needed
                        current_min = min(current_min, nb_value)
                        current_max = max(current_max, nb_value)
                        current_value = nb_value
                    except (TypeError, ValueError):
                        pass

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

    def _register_sync_formula_panels_2d(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-2d-expression', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-label', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-preset', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-x-min', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-x-max', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-y-min', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-y-max', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-x-points', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-y-points', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-x-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-y-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-z-title', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-display-mode', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-contour-levels', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-contour-style', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-auto-z-range', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-z-min', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-z-max', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-probe-x', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-probe-y', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-colorscale', 'panel': ALL}, 'value'),
            Input({'type': 'formula-2d-param-slider', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-2d-param-value', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-2d-param-min', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-2d-param-max', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-2d-param-step', 'panel': ALL, 'param': ALL}, 'value'),
            Input({'type': 'formula-2d-param-nb-toggle', 'panel': ALL, 'param': ALL}, 'n_clicks'),
            State({'type': 'formula-2d-expression', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-label', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-preset', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-x-min', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-x-max', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-y-min', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-y-max', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-x-points', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-y-points', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-x-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-y-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-z-title', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-display-mode', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-contour-levels', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-contour-style', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-auto-z-range', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-z-min', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-z-max', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-probe-x', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-probe-y', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-colorscale', 'panel': ALL}, 'id'),
            State({'type': 'formula-2d-param-slider', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-2d-param-value', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-2d-param-min', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-2d-param-max', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-2d-param-step', 'panel': ALL, 'param': ALL}, 'id'),
            State({'type': 'formula-2d-param-nb-toggle', 'panel': ALL, 'param': ALL}, 'id'),
            State('formula-panels', 'data'),
            State('notebook-state', 'data'),
            prevent_initial_call=True
        )
        def sync_formula_panels_2d(
            expressions, labels, presets, x_mins, x_maxs, y_mins, y_maxs, x_points, y_points,
            x_titles, y_titles, z_titles, display_modes, contour_levels, contour_styles, auto_z_ranges, z_mins, z_maxs, probe_xs, probe_ys, colorscales,
            param_slider_values, param_input_values, param_min_values, param_max_values, param_step_values,
            nb_toggle_clicks,
            expression_ids, label_ids, preset_ids, x_min_ids, x_max_ids, y_min_ids, y_max_ids, x_points_ids, y_points_ids,
            x_title_ids, y_title_ids, z_title_ids, display_ids, contour_level_ids, contour_style_ids, auto_z_range_ids, z_min_ids, z_max_ids, probe_x_ids, probe_y_ids, colorscale_ids,
            param_slider_ids, param_input_ids, param_min_ids, param_max_ids, param_step_ids,
            nb_toggle_ids,
            panels_state, notebook_state
        ):
            from ui.formula_graphs import build_formula_panel

            if not panels_state:
                raise PreventUpdate

            panels_state = copy.deepcopy(panels_state)
            triggered = ctx.triggered_id if isinstance(ctx.triggered_id, dict) else None
            triggered_type = triggered.get('type') if triggered else None

            if triggered_type == 'formula-2d-preset':
                for component_id, value in zip(preset_ids, presets):
                    panel_id = component_id['panel']
                    panel_state = panels_state.get(panel_id)
                    if panel_state and panel_state.get('panel_type') == '2d' and value:
                        _apply_2d_preset_defaults(panel_state, value)

            for ids, values, key in (
                (expression_ids, expressions, 'expression_2d'),
                (label_ids, labels, 'label_2d'),
                (x_title_ids, x_titles, 'x_axis_title'),
                (y_title_ids, y_titles, 'y_axis_title'),
                (z_title_ids, z_titles, 'z_axis_title'),
                (colorscale_ids, colorscales, 'surface_colorscale'),
            ):
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    panel_state = panels_state.get(panel_id)
                    if panel_state and panel_state.get('panel_type') == '2d' and value is not None:
                        panel_state[key] = value

            for ids, values, key, fallback in (
                (x_min_ids, x_mins, 'x_min', -5.0),
                (x_max_ids, x_maxs, 'x_max', 5.0),
                (y_min_ids, y_mins, 'y_min', -5.0),
                (y_max_ids, y_maxs, 'y_max', 5.0),
            ):
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    panel_state = panels_state.get(panel_id)
                    if panel_state and panel_state.get('panel_type') == '2d' and value is not None:
                        panel_state[key] = _safe_float(value, panel_state.get(key, fallback))

            for ids, values, key in (
                (x_points_ids, x_points, 'x_points_2d'),
                (y_points_ids, y_points, 'y_points_2d'),
            ):
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    panel_state = panels_state.get(panel_id)
                    if panel_state and panel_state.get('panel_type') == '2d' and value is not None:
                        panel_state[key] = max(20, min(200, _safe_int(value, panel_state.get(key, 80))))

            for component_id, value in zip(display_ids, display_modes):
                panel_id = component_id['panel']
                panel_state = panels_state.get(panel_id)
                if panel_state and panel_state.get('panel_type') == '2d' and value is not None:
                    panel_state['display_mode_2d'] = value

            for ids, values, key, fallback in (
                (contour_level_ids, contour_levels, 'contour_levels_2d', 12),
                (probe_x_ids, probe_xs, 'probe_x_2d', 0.0),
                (probe_y_ids, probe_ys, 'probe_y_2d', 0.0),
                (z_min_ids, z_mins, 'z_min_2d', 0.0),
                (z_max_ids, z_maxs, 'z_max_2d', 1.0),
            ):
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    panel_state = panels_state.get(panel_id)
                    if panel_state and panel_state.get('panel_type') == '2d' and value is not None:
                        if key == 'contour_levels_2d':
                            panel_state[key] = max(3, min(50, _safe_int(value, panel_state.get(key, fallback))))
                        else:
                            panel_state[key] = _safe_float(value, panel_state.get(key, fallback))

            for component_id, value in zip(contour_style_ids, contour_styles):
                panel_id = component_id['panel']
                panel_state = panels_state.get(panel_id)
                if panel_state and panel_state.get('panel_type') == '2d' and value is not None:
                    panel_state['contour_style_2d'] = value

            for component_id, value in zip(auto_z_range_ids, auto_z_ranges):
                panel_id = component_id['panel']
                panel_state = panels_state.get(panel_id)
                if panel_state and panel_state.get('panel_type') == '2d':
                    panel_state['auto_z_range_2d'] = 'auto' in (value or [])

            for panel_state in panels_state.values():
                if panel_state.get('panel_type') == '2d':
                    _sync_panel_params(panel_state)

            param_updates = []
            if triggered_type == 'formula-2d-param-slider':
                param_updates.append((param_slider_ids, param_slider_values, 'value'))
            elif triggered_type == 'formula-2d-param-value':
                param_updates.append((param_input_ids, param_input_values, 'value'))
            else:
                param_updates.extend([
                    (param_min_ids, param_min_values, 'min'),
                    (param_max_ids, param_max_values, 'max'),
                    (param_step_ids, param_step_values, 'step'),
                ])

            for ids, values, key in param_updates:
                for component_id, value in zip(ids, values):
                    panel_id = component_id['panel']
                    param_name = component_id['param']
                    panel_state = panels_state.get(panel_id)
                    if not panel_state or panel_state.get('panel_type') != '2d':
                        continue
                    params = panel_state.setdefault('params', {})
                    current = {**_default_param_state(), **(params.get(param_name, {}) or {})}
                    if key == 'value':
                        current['value'] = _safe_float(value, current['value'])
                    elif key == 'min':
                        current['min'] = _safe_float(value, current['min'])
                    elif key == 'max':
                        current['max'] = _safe_float(value, current['max'])
                    elif key == 'step':
                        current['step'] = max(1e-6, abs(_safe_float(value, current['step'])))
                    params[param_name] = current

            # Handle NB toggle for 2D panels
            if triggered_type == 'formula-2d-param-nb-toggle' and triggered:
                panel_id = triggered['panel']
                param_name = triggered['param']
                panel_state = panels_state.get(panel_id)
                if panel_state and panel_state.get('panel_type') == '2d':
                    panel_state.setdefault('params', {})
                    panel_state['params'].setdefault(param_name, _default_param_state())
                    current_use_nb = panel_state['params'][param_name].get('use_notebook', False)
                    new_use_nb = not current_use_nb
                    panel_state['params'][param_name]['use_notebook'] = new_use_nb
                    nb_vars = (notebook_state or {}).get('variables', {})
                    if new_use_nb and param_name in nb_vars:
                        try:
                            panel_state['params'][param_name]['value'] = float(nb_vars[param_name])
                        except (TypeError, ValueError):
                            pass

            # Inject notebook variables for display in panel UI
            nb_vars = (notebook_state or {}).get('variables', {})
            for pid in panels_state:
                panels_state[pid]['_notebook_vars'] = nb_vars

            panels = [
                build_formula_panel(pid, panels_state[pid])
                for pid in sorted(panels_state.keys())
            ]
            return panels_state, panels

        self._track_callback(sync_formula_panels_2d)

    def _register_sync_parameter_controls_2d(self):
        @self.app.callback(
            Output({'type': 'formula-2d-param-slider', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-2d-param-slider', 'panel': MATCH, 'param': MATCH}, 'min'),
            Output({'type': 'formula-2d-param-slider', 'panel': MATCH, 'param': MATCH}, 'max'),
            Output({'type': 'formula-2d-param-slider', 'panel': MATCH, 'param': MATCH}, 'step'),
            Output({'type': 'formula-2d-param-value', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-2d-param-min', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-2d-param-max', 'panel': MATCH, 'param': MATCH}, 'value'),
            Output({'type': 'formula-2d-param-step', 'panel': MATCH, 'param': MATCH}, 'value'),
            Input('formula-panels', 'data'),
            State({'type': 'formula-2d-param-slider', 'panel': MATCH, 'param': MATCH}, 'id'),
            State('notebook-state', 'data'),
            prevent_initial_call=False
        )
        def sync_parameter_controls_2d(panels_state, component_id, notebook_state):
            if not component_id:
                raise PreventUpdate

            panel_state = (panels_state or {}).get(component_id['panel'], {})
            if panel_state.get('panel_type') != '2d':
                raise PreventUpdate
            settings = {
                **_default_param_state(),
                **((panel_state.get('params') or {}).get(component_id['param'], {}) or {}),
            }

            current_min = float(settings['min'])
            current_max = float(settings['max'])
            current_step = abs(float(settings['step'])) or 0.1
            current_value = float(settings['value'])

            if settings.get('use_notebook'):
                nb_vars = (notebook_state or {}).get('variables', {})
                param_name = component_id['param']
                if param_name in nb_vars:
                    try:
                        nb_value = float(nb_vars[param_name])
                        current_min = min(current_min, nb_value)
                        current_max = max(current_max, nb_value)
                        current_value = nb_value
                    except (TypeError, ValueError):
                        pass

            if current_min >= current_max:
                current_max = current_min + max(current_step, 0.1)
            current_value = min(max(current_value, current_min), current_max)
            return (
                current_value, current_min, current_max, current_step,
                current_value, current_min, current_max, current_step,
            )

        self._track_callback(sync_parameter_controls_2d)

    def _register_graph_click_selection(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-plot', 'panel': ALL}, 'clickData'),
            State({'type': 'formula-plot', 'panel': ALL}, 'id'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def update_from_graph_click(click_data_list, plot_ids, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not ctx.triggered_id or not panels_state:
                raise PreventUpdate

            panel_id = ctx.triggered_id['panel']
            panel_state = copy.deepcopy((panels_state or {}).get(panel_id))
            if not panel_state:
                raise PreventUpdate

            click_data = None
            for component_id, value in zip(plot_ids, click_data_list):
                if component_id.get('panel') == panel_id:
                    click_data = value
                    break

            if not click_data or not click_data.get('points'):
                raise PreventUpdate

            x_value = click_data['points'][0].get('x')
            if x_value is None:
                raise PreventUpdate

            click_mode = panel_state.get('click_mode', 'focus')
            if click_mode == 'interval':
                pending = panel_state.get('pending_interval_start')
                if pending is None:
                    panel_state['pending_interval_start'] = float(x_value)
                    panel_state['interval_min'] = float(x_value)
                    panel_state['interval_max'] = float(x_value)
                else:
                    panel_state['interval_min'] = min(float(pending), float(x_value))
                    panel_state['interval_max'] = max(float(pending), float(x_value))
                    panel_state['pending_interval_start'] = None
            else:
                panel_state['analysis_x0'] = float(x_value)

            updated = copy.deepcopy(panels_state)
            updated[panel_id] = panel_state
            panels = [
                build_formula_panel(pid, updated[pid])
                for pid in sorted(updated.keys())
            ]
            return updated, panels

        self._track_callback(update_from_graph_click)

        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-2d-plot', 'panel': ALL}, 'clickData'),
            State({'type': 'formula-2d-plot', 'panel': ALL}, 'id'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def update_from_graph_click_2d(click_data_list, plot_ids, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not ctx.triggered_id or not panels_state:
                raise PreventUpdate

            panel_id = ctx.triggered_id['panel']
            panel_state = copy.deepcopy((panels_state or {}).get(panel_id))
            if not panel_state or panel_state.get('panel_type') != '2d':
                raise PreventUpdate

            click_data = None
            for component_id, value in zip(plot_ids, click_data_list):
                if component_id.get('panel') == panel_id:
                    click_data = value
                    break

            if not click_data or not click_data.get('points'):
                raise PreventUpdate

            point = click_data['points'][0]
            x_value = point.get('x')
            y_value = point.get('y')
            if x_value is None or y_value is None:
                raise PreventUpdate

            panel_state['probe_x_2d'] = float(x_value)
            panel_state['probe_y_2d'] = float(y_value)

            updated = copy.deepcopy(panels_state)
            updated[panel_id] = panel_state
            panels = [
                build_formula_panel(pid, updated[pid])
                for pid in sorted(updated.keys())
            ]
            return updated, panels

        self._track_callback(update_from_graph_click_2d)

    def _register_analysis_jump(self):
        @self.app.callback(
            Output('formula-panels', 'data', allow_duplicate=True),
            Output('formula-panels-container', 'children', allow_duplicate=True),
            Input({'type': 'formula-analysis-jump', 'panel': ALL, 'x': ALL}, 'n_clicks'),
            State('formula-panels', 'data'),
            prevent_initial_call=True
        )
        def jump_to_analysis_point(n_clicks, panels_state):
            from ui.formula_graphs import build_formula_panel

            if not ctx.triggered_id or not panels_state:
                raise PreventUpdate
            if not n_clicks or all(value is None or value == 0 for value in n_clicks):
                raise PreventUpdate

            panel_id = ctx.triggered_id['panel']
            x_value = ctx.triggered_id.get('x')
            if x_value is None:
                raise PreventUpdate

            updated = copy.deepcopy(panels_state)
            if panel_id not in updated:
                raise PreventUpdate

            updated[panel_id]['analysis_x0'] = float(x_value)
            panels = [
                build_formula_panel(pid, updated[pid])
                for pid in sorted(updated.keys())
            ]
            return updated, panels

        self._track_callback(jump_to_analysis_point)

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
            if panel_state.get('panel_type', '1d') == '2d':
                _sync_panel_params(panel_state)
                preset = PRESET_2D_DEFAULTS.get(panel_state.get('preset_2d', 'periodic_surface'), {})
                for param_name, config in (preset.get('params') or {}).items():
                    panel_state['params'][param_name] = {
                        **_default_param_state(),
                        **(panel_state['params'].get(param_name, {}) or {}),
                        **config,
                    }
            else:
                _apply_preset_defaults(panel_state, panel_state.get('example_formula', 'sin(x)'))
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
            param_values = {
                name: float((settings or {}).get('value', 1.0))
                for name, settings in (panel_state.get('params') or {}).items()
            }

            if panel_state.get('panel_type', '1d') == '2d':
                from utils.formula_parser import evaluate_formula_2d

                expression = (panel_state.get('expression_2d') or '').strip()
                if not expression:
                    raise PreventUpdate
                x_values = np.linspace(float(panel_state.get('x_min', -5.0)), float(panel_state.get('x_max', 5.0)), int(panel_state.get('x_points_2d', 80)))
                y_values = np.linspace(float(panel_state.get('y_min', -5.0)), float(panel_state.get('y_max', 5.0)), int(panel_state.get('y_points_2d', 80)))
                x_grid, y_grid = np.meshgrid(x_values, y_values)
                z_grid = evaluate_formula_2d(expression, x_grid, y_grid, param_values)
                df = pd.DataFrame({'x': x_grid.ravel(), 'y': y_grid.ravel(), 'z': z_grid.ravel()})
                filename = f"{button_id['panel']}_formula_surface_samples.csv"
            else:
                formulas = panel_state.get('formulas') or []
                if not formulas:
                    raise PreventUpdate
                x_min = float(panel_state.get('x_min', -10.0))
                x_max = float(panel_state.get('x_max', 10.0))
                points = int(panel_state.get('points', 400))
                x_values = pd.Series(np.linspace(x_min, x_max, points), name='x')
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

    def _register_export_formula_png(self):
        @self.app.callback(
            Output({'type': 'formula-image-download', 'panel': MATCH}, 'data'),
            Input({'type': 'formula-export-png-btn', 'panel': MATCH}, 'n_clicks'),
            State('formula-panels', 'data'),
            State({'type': 'formula-export-png-btn', 'panel': MATCH}, 'id'),
            prevent_initial_call=True
        )
        def export_formula_png(n_clicks, panels_state, button_id):
            from ui.formula_graphs import build_formula_figure

            if not n_clicks or not button_id:
                raise PreventUpdate

            panel_state = copy.deepcopy((panels_state or {}).get(button_id['panel'], {}))
            if not panel_state:
                raise PreventUpdate

            panel_state['_panel_id'] = button_id['panel']
            figure, _, _ = build_formula_figure(panel_state)
            image_bytes = pio.to_image(figure, format='png', width=1600, height=1100, scale=2)
            return send_bytes(lambda buffer: buffer.write(image_bytes), f"{button_id['panel']}_formula_plot.png")

        self._track_callback(export_formula_png)

    def _register_update_formula_graph(self):
        @self.app.callback(
            Output({'type': 'formula-plot', 'panel': MATCH}, 'figure'),
            Output({'type': 'formula-analysis', 'panel': MATCH}, 'children'),
            Output({'type': 'formula-analysis-details', 'panel': MATCH}, 'children'),
            Input('formula-panels', 'data'),
            State({'type': 'formula-plot', 'panel': MATCH}, 'id'),
            State('notebook-state', 'data'),
            prevent_initial_call=False
        )
        def update_formula_graph(panels_state, plot_id, notebook_state):
            from ui.formula_graphs import build_formula_figure

            if not plot_id:
                raise PreventUpdate

            panel_state = copy.deepcopy((panels_state or {}).get(plot_id['panel'], {}))
            panel_state['_panel_id'] = plot_id['panel']
            panel_state['_notebook_vars'] = (notebook_state or {}).get('variables', {})
            figure, summary, details = build_formula_figure(panel_state)
            return figure, summary, details

        self._track_callback(update_formula_graph)

    def _register_update_formula_graph_2d(self):
        @self.app.callback(
            Output({'type': 'formula-2d-plot', 'panel': MATCH}, 'figure'),
            Output({'type': 'formula-2d-analysis', 'panel': MATCH}, 'children'),
            Output({'type': 'formula-2d-analysis-details', 'panel': MATCH}, 'children'),
            Input('formula-panels', 'data'),
            State({'type': 'formula-2d-plot', 'panel': MATCH}, 'id'),
            State('notebook-state', 'data'),
            prevent_initial_call=False
        )
        def update_formula_graph_2d(panels_state, plot_id, notebook_state):
            from ui.formula_graphs import build_formula_figure

            if not plot_id:
                raise PreventUpdate

            panel_state = copy.deepcopy((panels_state or {}).get(plot_id['panel'], {}))
            panel_state['_panel_id'] = plot_id['panel']
            panel_state['_notebook_vars'] = (notebook_state or {}).get('variables', {})
            figure, summary, details = build_formula_figure(panel_state)
            return figure, summary, details

        self._track_callback(update_formula_graph_2d)

    def _register_update_formula_slices_2d(self):
        @self.app.callback(
            Output({'type': 'formula-2d-x-slice', 'panel': MATCH}, 'figure'),
            Output({'type': 'formula-2d-y-slice', 'panel': MATCH}, 'figure'),
            Input('formula-panels', 'data'),
            State({'type': 'formula-2d-x-slice', 'panel': MATCH}, 'id'),
            State('notebook-state', 'data'),
            prevent_initial_call=False
        )
        def update_formula_slices_2d(panels_state, graph_id, notebook_state):
            from ui.formula_graphs import build_formula_2d_slice_figures

            if not graph_id:
                raise PreventUpdate

            panel_state = copy.deepcopy((panels_state or {}).get(graph_id['panel'], {}))
            panel_state['_panel_id'] = graph_id['panel']
            panel_state['_notebook_vars'] = (notebook_state or {}).get('variables', {})
            return build_formula_2d_slice_figures(panel_state)

        self._track_callback(update_formula_slices_2d)

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

