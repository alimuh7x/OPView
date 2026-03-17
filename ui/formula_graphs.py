"""
Formula graph UI builders for the Formula Plot tab.
"""

from __future__ import annotations

from typing import Dict, List

from dash import dcc, html
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import cumulative_trapezoid, trapezoid
from scipy.interpolate import CubicSpline

from utils.formula_parser import FormulaValidationError, evaluate_formula, extract_formula_variables


FORMULA_EXAMPLES = [
    {"label": "Sine Wave", "value": "sin(x)"},
    {"label": "Damped Sine", "value": "a*exp(-b*x) * sin(c*x)"},
    {"label": "Parabola", "value": "x**2"},
    {"label": "Cubic", "value": "x**3 - 3*x"},
    {"label": "Gaussian", "value": "a*exp(-(x**2)/b)"},
    {"label": "Logistic", "value": "1 / (1 + exp(-a*x))"},
]

TRACE_COLORS = [
    {"label": "Black", "value": "black"},
    {"label": "Red", "value": "#d62728"},
    {"label": "Blue", "value": "#1f77b4"},
    {"label": "Green", "value": "#2ca02c"},
    {"label": "Orange", "value": "#ff7f0e"},
    {"label": "Purple", "value": "#9467bd"},
]

TRACE_DASHES = [
    {"label": "Solid", "value": "solid"},
    {"label": "Dash", "value": "dash"},
    {"label": "Dot", "value": "dot"},
    {"label": "Dash Dot", "value": "dashdot"},
]


def _default_formula_row(row_id: str, expression: str = "sin(x)") -> Dict:
    """Return a default formula row state."""
    return {
        "id": row_id,
        "expression": expression,
        "label": expression,
        "color": "black",
        "dash": "solid",
        "width": 3.0,
    }


def _default_param_state() -> Dict:
    """Return default settings for a detected parameter."""
    return {
        "value": 1.0,
        "min": -10.0,
        "max": 10.0,
        "step": 0.1,
    }


def _as_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalise_interval(start: float, end: float, x_min: float, x_max: float) -> tuple[float, float]:
    left = _as_float(start, x_min)
    right = _as_float(end, x_max)
    left = max(min(left, x_max), x_min)
    right = max(min(right, x_max), x_min)
    if left > right:
        left, right = right, left
    if np.isclose(left, right):
        right = min(x_max, left + max((x_max - x_min) * 0.01, 1e-6))
    return left, right


def _filter_real_values(values) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array[np.isfinite(array)]


def _dedupe_points(values, tolerance: float = 1e-7) -> list[float]:
    result = []
    for value in sorted(_filter_real_values(values)):
        if not result or abs(value - result[-1]) > tolerance:
            result.append(float(value))
    return result


def _safe_spline(x_values: np.ndarray, y_values: np.ndarray) -> CubicSpline | None:
    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
    if np.count_nonzero(finite_mask) < 4:
        return None
    x_valid = x_values[finite_mask]
    y_valid = y_values[finite_mask]
    if np.unique(x_valid).size < 4:
        return None
    return CubicSpline(x_valid, y_valid, extrapolate=False)


def _solve_spline_roots(x_values: np.ndarray, y_values: np.ndarray, limit: int = 12) -> list[float]:
    spline = _safe_spline(x_values, y_values)
    roots = []
    if spline is not None:
        roots = _dedupe_points(spline.roots(extrapolate=False))
    if roots:
        return roots[:limit]

    roots = []
    for idx in np.where(np.diff(np.signbit(y_values)))[0]:
        x0, x1 = x_values[idx], x_values[idx + 1]
        y0, y1 = y_values[idx], y_values[idx + 1]
        if not np.isfinite([y0, y1]).all():
            continue
        if np.isclose(y0, y1):
            roots.append(float(x0))
            continue
        roots.append(float(x0 - y0 * (x1 - x0) / (y1 - y0)))
    return _dedupe_points(roots)[:limit]


def _find_extrema(x_values: np.ndarray, y_values: np.ndarray, limit: int = 16) -> tuple[list[dict], CubicSpline | None]:
    spline = _safe_spline(x_values, y_values)
    if spline is None:
        return [], None

    first = spline.derivative()
    second = spline.derivative(2)
    extrema = []
    for x_pos in _dedupe_points(first.roots(extrapolate=False)):
        y_pos = float(spline(x_pos))
        curvature = float(second(x_pos))
        point_type = "minimum" if curvature > 0 else "maximum" if curvature < 0 else "stationary"
        extrema.append({"x": float(x_pos), "y": y_pos, "type": point_type})
    extrema.sort(key=lambda item: item["x"])
    return extrema[:limit], spline


def _find_intersections(
    x_values: np.ndarray,
    y_values_a: np.ndarray,
    y_values_b: np.ndarray,
    limit: int = 12,
) -> list[dict]:
    diff = y_values_a - y_values_b
    roots = _solve_spline_roots(x_values, diff, limit=limit)
    spline_a = _safe_spline(x_values, y_values_a)
    intersections = []
    for x_pos in roots:
        if spline_a is not None:
            y_pos = float(spline_a(x_pos))
        else:
            y_pos = float(np.interp(x_pos, x_values, y_values_a))
        intersections.append({"x": x_pos, "y": y_pos})
    return intersections


def _build_formula_rows(panel_id: str, formulas: List[Dict]) -> List[html.Div]:
    """Build editable rows for multiple formulas."""
    rows = []
    for formula in formulas:
        row_id = formula["id"]
        rows.append(
            html.Div([
                html.Div([
                    html.Label("Formula", className='multifile-mini-label', style={'fontSize': '14px'}),
                    dcc.Input(
                        id={'type': 'formula-row-expression', 'panel': panel_id, 'row': row_id},
                        type='text',
                        value=formula.get('expression', ''),
                        debounce=True,
                        placeholder='Example: sin(x)',
                        style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                    ),
                ], style={'flex': '2'}),
                html.Div([
                    html.Label("Legend", className='multifile-mini-label', style={'fontSize': '14px'}),
                    dcc.Input(
                        id={'type': 'formula-row-label', 'panel': panel_id, 'row': row_id},
                        type='text',
                        value=formula.get('label', ''),
                        debounce=True,
                        placeholder='Trace label',
                        style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                    ),
                ], style={'flex': '1'}),
                html.Div([
                    html.Label("Color", className='multifile-mini-label', style={'fontSize': '14px'}),
                    dcc.Dropdown(
                        id={'type': 'formula-row-color', 'panel': panel_id, 'row': row_id},
                        options=TRACE_COLORS,
                        value=formula.get('color', 'black'),
                        clearable=False,
                        style={'fontSize': '14px'}
                    ),
                ], style={'flex': '0.8'}),
                html.Div([
                    html.Label("Line", className='multifile-mini-label', style={'fontSize': '14px'}),
                    dcc.Dropdown(
                        id={'type': 'formula-row-dash', 'panel': panel_id, 'row': row_id},
                        options=TRACE_DASHES,
                        value=formula.get('dash', 'solid'),
                        clearable=False,
                        style={'fontSize': '14px'}
                    ),
                ], style={'flex': '0.8'}),
                html.Div([
                    html.Label("Width", className='multifile-mini-label', style={'fontSize': '14px'}),
                    dcc.Input(
                        id={'type': 'formula-row-width', 'panel': panel_id, 'row': row_id},
                        type='number',
                        min=1,
                        max=8,
                        step=0.5,
                        value=formula.get('width', 3.0),
                        debounce=True,
                        style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                    ),
                ], style={'flex': '0.6'}),
                html.Button(
                    '×',
                    id={'type': 'formula-row-remove-btn', 'panel': panel_id, 'row': row_id},
                    className='graph-close-btn',
                    title='Remove formula',
                    style={
                        'background': 'none',
                        'border': 'none',
                        'color': '#999',
                        'fontSize': '24px',
                        'cursor': 'pointer',
                        'padding': '0 8px',
                        'alignSelf': 'flex-end',
                    }
                ),
            ], style={'display': 'flex', 'gap': '12px', 'alignItems': 'flex-end', 'marginBottom': '10px'})
        )
    return rows


def _build_parameter_controls(panel_id: str, params: Dict[str, Dict]) -> html.Div:
    """Build slider + numeric controls for detected parameters."""
    if not params:
        return html.Div(
            "No extra parameters detected. Use symbols like a, b, or c in your formulas to get controls.",
            style={'fontSize': '13px', 'color': '#666'}
        )

    controls = []
    for name in sorted(params.keys()):
        settings = {**_default_param_state(), **(params.get(name) or {})}
        try:
            settings['min'] = float(settings['min'])
            settings['max'] = float(settings['max'])
            settings['step'] = abs(float(settings['step'])) or 0.1
            settings['value'] = float(settings['value'])
        except (TypeError, ValueError):
            settings = _default_param_state()
        if settings['min'] >= settings['max']:
            settings['max'] = settings['min'] + max(settings['step'], 0.1)
        settings['value'] = min(max(settings['value'], settings['min']), settings['max'])
        controls.append(
            html.Div([
                html.Label(name, className='multifile-mini-label', style={'fontSize': '15px', 'fontWeight': '700'}),
                dcc.Slider(
                    id={'type': 'formula-param-slider', 'panel': panel_id, 'param': name},
                    min=settings['min'],
                    max=settings['max'],
                    step=settings['step'],
                    value=settings['value'],
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
                html.Div([
                    html.Div([
                        html.Label("Value", className='multifile-mini-label'),
                        dcc.Input(
                            id={'type': 'formula-param-value', 'panel': panel_id, 'param': name},
                            type='number',
                            value=settings['value'],
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '13px'}
                        ),
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Label("Min", className='multifile-mini-label'),
                        dcc.Input(
                            id={'type': 'formula-param-min', 'panel': panel_id, 'param': name},
                            type='number',
                            value=settings['min'],
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '13px'}
                        ),
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Label("Max", className='multifile-mini-label'),
                        dcc.Input(
                            id={'type': 'formula-param-max', 'panel': panel_id, 'param': name},
                            type='number',
                            value=settings['max'],
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '13px'}
                        ),
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Label("Step", className='multifile-mini-label'),
                        dcc.Input(
                            id={'type': 'formula-param-step', 'panel': panel_id, 'param': name},
                            type='number',
                            value=settings['step'],
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '13px'}
                        ),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '8px', 'marginTop': '8px'}),
            ], style={'marginBottom': '14px', 'paddingBottom': '12px', 'borderBottom': '1px solid #e8eaef'})
        )

    return html.Div(controls)


def _build_table(title: str, columns: list[str], rows: list[list[str]]) -> html.Div:
    if not rows:
        return html.Div()
    return html.Div([
        html.Div(title, style={'fontWeight': '700', 'marginBottom': '6px'}),
        html.Table([
            html.Thead(html.Tr([html.Th(column, style={'textAlign': 'left', 'padding': '6px 8px'}) for column in columns])),
            html.Tbody([
                html.Tr([html.Td(cell, style={'padding': '6px 8px', 'borderTop': '1px solid #eceff3'}) for cell in row])
                for row in rows
            ])
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '13px'})
    ], style={'marginTop': '12px'})


def build_formula_panel(panel_id: str, panel_state: Dict | None = None) -> html.Div:
    """Build a formula plotting panel that matches existing graph panels."""
    state = {
        "panel_number": 1,
        "x_min": -10.0,
        "x_max": 10.0,
        "points": 400,
        "plot_title": "Formula Plot",
        "x_axis_title": "x",
        "y_axis_title": "f(x)",
        "show_grid": True,
        "show_legend": True,
        "show_derivative": False,
        "show_second_derivative": False,
        "show_antiderivative": False,
        "show_tangent": False,
        "show_normal": False,
        "show_root_markers": True,
        "show_extrema_markers": True,
        "show_intersection_markers": True,
        "show_area_shading": False,
        "example_formula": "sin(x)",
        "analysis_formula": "",
        "analysis_x0": 0.0,
        "interval_min": -2.0,
        "interval_max": 2.0,
        "threshold_value": 0.0,
        "params": {},
        "formulas": [_default_formula_row("formula_1", "sin(x)")],
    }
    if panel_state:
        state.update(panel_state)

    formulas = state.get("formulas") or [_default_formula_row("formula_1", "sin(x)")]
    panel_num = state.get("panel_number", 1)
    display_options = []
    for key, token in (
        ('show_legend', 'legend'),
        ('show_grid', 'grid'),
        ('show_derivative', 'derivative'),
        ('show_second_derivative', 'second_derivative'),
        ('show_antiderivative', 'antiderivative'),
        ('show_tangent', 'tangent'),
        ('show_normal', 'normal'),
        ('show_root_markers', 'root_markers'),
        ('show_extrema_markers', 'extrema_markers'),
        ('show_intersection_markers', 'intersection_markers'),
        ('show_area_shading', 'area_shading'),
    ):
        if state.get(key, False):
            display_options.append(token)

    detected_params = {}
    for formula in formulas:
        for param_name in extract_formula_variables(formula.get('expression', '')):
            detected_params[param_name] = {
                **_default_param_state(),
                **(state.get('params', {}).get(param_name, {}) or {}),
            }

    formula_options = []
    for formula in formulas:
        expression = formula.get('expression', '')
        label = (formula.get('label') or expression or 'Formula').strip()
        formula_options.append({'label': label, 'value': formula.get('id')})

    analysis_formula = state.get('analysis_formula') or (formula_options[0]['value'] if formula_options else "")
    if formula_options and analysis_formula not in {option['value'] for option in formula_options}:
        analysis_formula = formula_options[0]['value']

    return html.Div([
        html.Div([
            html.Div([
                html.H3(f"Formula Panel {panel_num}", className='dataset-title')
            ], style={'flex': '1'}),
            html.Button(
                '×',
                id={'type': 'formula-close-btn', 'panel': panel_id},
                className='graph-close-btn',
                style={
                    'background': 'none',
                    'border': 'none',
                    'color': '#999',
                    'fontSize': '28px',
                    'cursor': 'pointer',
                    'padding': '0 8px',
                    'lineHeight': '1'
                }
            )
        ], className='dataset-header', style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Label("Examples", className='multifile-label'),
                        dcc.Dropdown(
                            id={'type': 'formula-example', 'panel': panel_id},
                            options=FORMULA_EXAMPLES,
                            value=state.get('example_formula', 'sin(x)'),
                            clearable=False,
                            style={'fontSize': '14px'}
                        ),
                    ], style={'flex': '1'}),
                    html.Button(
                        "+ Add Formula",
                        id={'type': 'formula-add-row-btn', 'panel': panel_id},
                        className='graphs-add-panel-btn',
                        n_clicks=0,
                        style={'marginBottom': '0', 'alignSelf': 'flex-end'}
                    ),
                    html.Button(
                        "Reset Params",
                        id={'type': 'formula-reset-params-btn', 'panel': panel_id},
                        className='graphs-add-panel-btn',
                        n_clicks=0,
                        style={'marginBottom': '0', 'alignSelf': 'flex-end'}
                    ),
                    html.Button(
                        "Export CSV",
                        id={'type': 'formula-export-btn', 'panel': panel_id},
                        className='graphs-add-panel-btn',
                        n_clicks=0,
                        style={'marginBottom': '0', 'alignSelf': 'flex-end'}
                    ),
                ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '12px', 'alignItems': 'stretch'}),
                html.Div(_build_formula_rows(panel_id, formulas)),
                html.Div(
                    "Allowed: x, pi, e, sin, cos, tan, exp, log, sqrt, abs. Use ** for powers.",
                    style={'fontSize': '12px', 'color': '#666', 'marginTop': '4px'}
                ),
                html.Div([
                    html.Div([
                        html.Label("X Min", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Input(
                            id={'type': 'formula-x-min', 'panel': panel_id},
                            type='number',
                            value=state['x_min'],
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                        ),
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Label("X Max", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Input(
                            id={'type': 'formula-x-max', 'panel': panel_id},
                            type='number',
                            value=state['x_max'],
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                        ),
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Label("Points", className='multifile-mini-label', style={'fontSize': '14px'}),
                        dcc.Input(
                            id={'type': 'formula-points', 'panel': panel_id},
                            type='number',
                            min=50,
                            max=5000,
                            step=50,
                            value=state['points'],
                            debounce=True,
                            style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                        ),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '12px', 'marginTop': '14px'})
            ], className='multifile-top-controls'),
            html.Div([
                html.Div([
                    dcc.Graph(
                        id={'type': 'formula-plot', 'panel': panel_id},
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '700px', 'width': '1000px'}
                    ),
                    html.Div(
                        id={'type': 'formula-analysis', 'panel': panel_id},
                        children="No analysis available yet.",
                        className='hist-summary',
                        style={'margin': '12px 10px 10px 10px'}
                    ),
                    dcc.Download(id={'type': 'formula-download', 'panel': panel_id})
                ], className='multifile-graph-column'),
                html.Div([
                    html.Div([
                        html.Label("Figure", className='multifile-sublabel', style={'fontSize': '15px'}),
                        html.Div([
                            html.Label("Plot Title", className='multifile-mini-label', style={'fontSize': '14px'}),
                            dcc.Input(
                                id={'type': 'formula-plot-title', 'panel': panel_id},
                                type='text',
                                value=state['plot_title'],
                                debounce=True,
                                style={'width': '100%', 'padding': '5px', 'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                            html.Label("X-Axis Title", className='multifile-mini-label', style={'fontSize': '14px'}),
                            dcc.Input(
                                id={'type': 'formula-x-title', 'panel': panel_id},
                                type='text',
                                value=state['x_axis_title'],
                                debounce=True,
                                style={'width': '100%', 'padding': '5px', 'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                            html.Label("Y-Axis Title", className='multifile-mini-label', style={'fontSize': '14px'}),
                            dcc.Input(
                                id={'type': 'formula-y-title', 'panel': panel_id},
                                type='text',
                                value=state['y_axis_title'],
                                debounce=True,
                                style={'width': '100%', 'padding': '5px', 'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                            html.Label("Display", className='multifile-mini-label', style={'fontSize': '14px'}),
                            dcc.Checklist(
                                id={'type': 'formula-display-options', 'panel': panel_id},
                                options=[
                                    {'label': 'Legend', 'value': 'legend'},
                                    {'label': 'Grid', 'value': 'grid'},
                                    {'label': 'Derivative', 'value': 'derivative'},
                                    {'label': '2nd Derivative', 'value': 'second_derivative'},
                                    {'label': 'Integral Curve', 'value': 'antiderivative'},
                                    {'label': 'Tangent', 'value': 'tangent'},
                                    {'label': 'Normal', 'value': 'normal'},
                                    {'label': 'Root Markers', 'value': 'root_markers'},
                                    {'label': 'Extrema Markers', 'value': 'extrema_markers'},
                                    {'label': 'Intersection Markers', 'value': 'intersection_markers'},
                                    {'label': 'Area Shading', 'value': 'area_shading'},
                                ],
                                value=display_options,
                                labelStyle={'display': 'block', 'fontSize': '14px', 'marginBottom': '6px'}
                            ),
                        ], className='multifile-setting-group')
                    ], className='multifile-setting-section'),
                    html.Div([
                        html.Label("Analysis Tools", className='multifile-sublabel', style={'fontSize': '15px'}),
                        html.Div([
                            html.Label("Focus Formula", className='multifile-mini-label'),
                            dcc.Dropdown(
                                id={'type': 'formula-analysis-formula', 'panel': panel_id},
                                options=formula_options,
                                value=analysis_formula,
                                clearable=False if formula_options else True,
                                style={'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                            html.Label("X0 (tangent / normal)", className='multifile-mini-label'),
                            dcc.Input(
                                id={'type': 'formula-analysis-x0', 'panel': panel_id},
                                type='number',
                                value=state.get('analysis_x0', 0.0),
                                debounce=True,
                                style={'width': '100%', 'padding': '5px', 'fontSize': '14px', 'marginBottom': '8px'}
                            ),
                            html.Label("Integral Interval", className='multifile-mini-label'),
                            html.Div([
                                dcc.Input(
                                    id={'type': 'formula-interval-min', 'panel': panel_id},
                                    type='number',
                                    value=state.get('interval_min', state.get('x_min', -10.0)),
                                    debounce=True,
                                    style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                                ),
                                dcc.Input(
                                    id={'type': 'formula-interval-max', 'panel': panel_id},
                                    type='number',
                                    value=state.get('interval_max', state.get('x_max', 10.0)),
                                    debounce=True,
                                    style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                                ),
                            ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '8px'}),
                            html.Label("Threshold", className='multifile-mini-label'),
                            dcc.Input(
                                id={'type': 'formula-threshold', 'panel': panel_id},
                                type='number',
                                value=state.get('threshold_value', 0.0),
                                debounce=True,
                                style={'width': '100%', 'padding': '5px', 'fontSize': '14px'}
                            ),
                        ], className='multifile-setting-group')
                    ], className='multifile-setting-section'),
                    html.Div([
                        html.Label("Parameters", className='multifile-sublabel', style={'fontSize': '15px'}),
                        html.Div(
                            _build_parameter_controls(panel_id, detected_params),
                            className='multifile-setting-group'
                        )
                    ], className='multifile-setting-section')
                ], className='multifile-settings-sidebar'),
            ], className='multifile-main-content'),
        ], className='dataset-body')
    ], className='dataset-block multifile-panel', id=f'formula-{panel_id}')


def build_formula_figure(panel_state: Dict) -> tuple[go.Figure, html.Div]:
    """Build an interactive Plotly figure and a detailed analysis summary."""
    formulas = panel_state.get('formulas') or []
    params = panel_state.get('params') or {}
    plot_title = panel_state.get('plot_title', 'Formula Plot')
    x_axis_title = panel_state.get('x_axis_title', 'x')
    y_axis_title = panel_state.get('y_axis_title', 'f(x)')

    fig = go.Figure()

    try:
        x_min = float(panel_state.get('x_min', -10.0))
        x_max = float(panel_state.get('x_max', 10.0))
        points = int(panel_state.get('points', 400))
        if points < 10:
            raise FormulaValidationError("Points must be at least 10")
        if x_min >= x_max:
            raise FormulaValidationError("X Min must be smaller than X Max")

        x_values = np.linspace(x_min, x_max, points)
        interval_min, interval_max = _normalise_interval(
            panel_state.get('interval_min', x_min),
            panel_state.get('interval_max', x_max),
            x_min,
            x_max,
        )
        threshold_value = _as_float(panel_state.get('threshold_value', 0.0), 0.0)
        analysis_x0 = _as_float(panel_state.get('analysis_x0', 0.0), 0.0)
        analysis_x0 = min(max(analysis_x0, x_min), x_max)
        param_values = {
            name: float((settings or {}).get('value', 1.0))
            for name, settings in params.items()
        }

        series_results = []
        error_rows = []

        for formula in formulas:
            expression = (formula.get('expression') or '').strip()
            row_id = formula.get('id')
            label = (formula.get('label') or expression or 'Formula').strip()
            color = formula.get('color') or 'black'
            dash = formula.get('dash') or 'solid'
            width = _as_float(formula.get('width', 3.0), 3.0)

            if not expression:
                error_rows.append([label, "Please enter a formula"])
                continue

            try:
                y_values = evaluate_formula(expression, x_values, param_values)
            except Exception as exc:
                error_rows.append([label, str(exc) or "Unable to evaluate formula"])
                continue

            spline = _safe_spline(x_values, y_values)
            roots = _solve_spline_roots(x_values, y_values, limit=24)
            extrema, extrema_spline = _find_extrema(x_values, y_values, limit=24)
            threshold_crossings = _solve_spline_roots(x_values, y_values - threshold_value, limit=24)
            cumulative = cumulative_trapezoid(np.nan_to_num(y_values, nan=0.0), x_values, initial=0.0)

            series_results.append({
                'id': row_id,
                'label': label,
                'expression': expression,
                'color': color,
                'dash': dash,
                'width': width,
                'y': y_values,
                'spline': spline or extrema_spline,
                'roots': roots,
                'extrema': extrema,
                'threshold_crossings': threshold_crossings,
                'cumulative': cumulative,
            })

            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines',
                line={'width': width, 'color': color, 'dash': dash},
                name=label,
            ))

        if not series_results:
            error_message = "Please add at least one valid formula"
            if error_rows:
                fig.update_layout(
                    title=plot_title or "Formula Plot",
                    template='plotly_white',
                    xaxis_title=x_axis_title or "x",
                    yaxis_title=y_axis_title or "f(x)",
                    annotations=[{
                        'text': "No valid formulas to plot",
                        'xref': 'paper',
                        'yref': 'paper',
                        'x': 0.5,
                        'y': 0.5,
                        'showarrow': False,
                        'font': {'size': 16, 'color': '#b00020'}
                    }]
                )
                return fig, html.Div([
                    html.Div("No valid formulas to plot. See row errors below."),
                    _build_table("Formula Errors", ["Formula", "Error"], error_rows),
                ])
            raise FormulaValidationError(error_message)

        show_derivative = panel_state.get('show_derivative', False)
        show_second_derivative = panel_state.get('show_second_derivative', False)
        show_antiderivative = panel_state.get('show_antiderivative', False)
        show_tangent = panel_state.get('show_tangent', False)
        show_normal = panel_state.get('show_normal', False)
        show_root_markers = panel_state.get('show_root_markers', True)
        show_extrema_markers = panel_state.get('show_extrema_markers', True)
        show_intersection_markers = panel_state.get('show_intersection_markers', True)
        show_area_shading = panel_state.get('show_area_shading', False)

        analysis_formula_id = panel_state.get('analysis_formula') or series_results[0]['id']
        selected_series = next((item for item in series_results if item['id'] == analysis_formula_id), series_results[0])

        root_rows = []
        extrema_rows = []
        intersection_rows = []
        threshold_rows = []
        summary_blocks = []

        for series in series_results:
            spline = series['spline']
            y_values = series['y']

            finite_values = _filter_real_values(y_values)
            if finite_values.size:
                summary_blocks.append(html.Div(
                    f"{series['label']}: min={finite_values.min():.4g}, max={finite_values.max():.4g}, mean={finite_values.mean():.4g}"
                ))

            if spline is not None:
                derivative_values = spline.derivative()(x_values)
                second_derivative_values = spline.derivative(2)(x_values)
            else:
                derivative_values = np.gradient(y_values, x_values)
                second_derivative_values = np.gradient(derivative_values, x_values)

            if show_derivative:
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=derivative_values,
                    mode='lines',
                    line={'width': 2.0, 'color': series['color'], 'dash': 'dash'},
                    name=f"{series['label']} (d/dx)",
                ))

            if show_second_derivative:
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=second_derivative_values,
                    mode='lines',
                    line={'width': 1.8, 'color': series['color'], 'dash': 'dot'},
                    name=f"{series['label']} (d2/dx2)",
                ))

            if show_antiderivative:
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=series['cumulative'],
                    mode='lines',
                    line={'width': 2.0, 'color': series['color'], 'dash': 'dashdot'},
                    name=f"{series['label']} integral",
                ))

            if show_root_markers and series['roots']:
                fig.add_trace(go.Scatter(
                    x=series['roots'],
                    y=[0.0] * len(series['roots']),
                    mode='markers',
                    marker={'color': series['color'], 'size': 10, 'symbol': 'x'},
                    name=f"{series['label']} roots",
                ))

            if show_extrema_markers and series['extrema']:
                fig.add_trace(go.Scatter(
                    x=[item['x'] for item in series['extrema']],
                    y=[item['y'] for item in series['extrema']],
                    mode='markers',
                    marker={'color': series['color'], 'size': 11, 'symbol': 'diamond'},
                    name=f"{series['label']} extrema",
                ))

            for root in series['roots']:
                root_rows.append([series['label'], f"{root:.6g}", "0"])
            for item in series['extrema']:
                extrema_rows.append([series['label'], item['type'], f"{item['x']:.6g}", f"{item['y']:.6g}"])
            for crossing in series['threshold_crossings']:
                threshold_rows.append([series['label'], f"{crossing:.6g}", f"{threshold_value:.6g}"])

        intersections = []
        for idx in range(len(series_results)):
            for jdx in range(idx + 1, len(series_results)):
                left = series_results[idx]
                right = series_results[jdx]
                points_found = _find_intersections(x_values, left['y'], right['y'], limit=12)
                for point in points_found:
                    intersections.append((left['label'], right['label'], point))
                    intersection_rows.append([
                        f"{left['label']} / {right['label']}",
                        f"{point['x']:.6g}",
                        f"{point['y']:.6g}",
                    ])

        if show_intersection_markers and intersections:
            fig.add_trace(go.Scatter(
                x=[item[2]['x'] for item in intersections],
                y=[item[2]['y'] for item in intersections],
                mode='markers',
                marker={'color': '#444', 'size': 10, 'symbol': 'cross'},
                name='Intersections',
            ))

        selected_spline = selected_series['spline']
        if selected_spline is not None:
            y0 = float(selected_spline(analysis_x0))
            slope = float(selected_spline.derivative()(analysis_x0))
            second_at_x0 = float(selected_spline.derivative(2)(analysis_x0))
        else:
            y0 = float(np.interp(analysis_x0, x_values, selected_series['y']))
            slope = float(np.interp(analysis_x0, x_values, np.gradient(selected_series['y'], x_values)))
            second_at_x0 = float(np.interp(
                analysis_x0,
                x_values,
                np.gradient(np.gradient(selected_series['y'], x_values), x_values),
            ))

        if show_tangent:
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y0 + slope * (x_values - analysis_x0),
                mode='lines',
                line={'color': selected_series['color'], 'dash': 'dash', 'width': 2},
                name=f"{selected_series['label']} tangent",
            ))

        if show_normal:
            if abs(slope) < 1e-12:
                finite_selected = _filter_real_values(selected_series['y'])
                y_span = finite_selected.max() - finite_selected.min() if finite_selected.size else 2.0
                if not np.isfinite(y_span) or y_span == 0:
                    y_span = 2.0
                fig.add_trace(go.Scatter(
                    x=[analysis_x0, analysis_x0],
                    y=[y0 - y_span / 2.0, y0 + y_span / 2.0],
                    mode='lines',
                    line={'color': selected_series['color'], 'dash': 'dot', 'width': 2},
                    name=f"{selected_series['label']} normal",
                ))
            else:
                normal_slope = -1.0 / slope
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=y0 + normal_slope * (x_values - analysis_x0),
                    mode='lines',
                    line={'color': selected_series['color'], 'dash': 'dot', 'width': 2},
                    name=f"{selected_series['label']} normal",
                ))

        fig.add_trace(go.Scatter(
            x=[analysis_x0],
            y=[y0],
            mode='markers',
            marker={'color': selected_series['color'], 'size': 12, 'symbol': 'circle-open'},
            name=f"{selected_series['label']} focus point",
        ))

        interval_mask = (x_values >= interval_min) & (x_values <= interval_max)
        interval_x = x_values[interval_mask]
        interval_y = selected_series['y'][interval_mask]
        exact_integral = None
        if interval_x.size >= 2:
            if selected_spline is not None:
                anti = selected_spline.antiderivative()
                exact_integral = float(anti(interval_max) - anti(interval_min))
            else:
                exact_integral = float(trapezoid(interval_y, interval_x))
            if show_area_shading:
                fig.add_trace(go.Scatter(
                    x=np.concatenate(([interval_x[0]], interval_x, [interval_x[-1]])),
                    y=np.concatenate(([0.0], interval_y, [0.0])),
                    fill='toself',
                    fillcolor='rgba(31, 119, 180, 0.18)',
                    line={'color': 'rgba(31, 119, 180, 0.1)'},
                    name=f"{selected_series['label']} area",
                    hoverinfo='skip',
                ))

        if param_values:
            summary_blocks.insert(0, html.Div(
                "Parameters: " + ", ".join(f"{name}={value:.4g}" for name, value in sorted(param_values.items()))
            ))

        summary_blocks.append(html.Div(
            f"Focus: {selected_series['label']} at x0={analysis_x0:.4g}, y={y0:.4g}, slope={slope:.4g}, curvature={second_at_x0:.4g}"
        ))
        summary_blocks.append(html.Div(f"Interval: [{interval_min:.4g}, {interval_max:.4g}]"))
        if exact_integral is not None:
            summary_blocks.append(html.Div(
                f"Exact selected integral of {selected_series['label']} = {exact_integral:.6g}"
            ))
        summary_blocks.append(html.Div(f"Threshold crossings checked at y={threshold_value:.4g}"))

        fig.update_layout(
            title=plot_title or "Formula Plot",
            template='plotly_white',
            hovermode='x unified',
            margin=dict(l=80, r=40, t=50, b=70),
            font=dict(size=18, family='Arial'),
            showlegend=panel_state.get('show_legend', True),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        fig.update_xaxes(
            title=x_axis_title or "x",
            showgrid=panel_state.get('show_grid', True),
            gridcolor='rgba(128, 128, 128, 0.2)',
            mirror='allticks',
            ticks='inside',
            ticklen=8,
            tickwidth=2,
            tickcolor='black',
            showline=True,
            linecolor='black',
            linewidth=2,
        )
        fig.update_yaxes(
            title=y_axis_title or "f(x)",
            showgrid=panel_state.get('show_grid', True),
            gridcolor='rgba(128, 128, 128, 0.2)',
            mirror='allticks',
            ticks='inside',
            ticklen=8,
            tickwidth=2,
            tickcolor='black',
            showline=True,
            linecolor='black',
            linewidth=2,
        )
        fig.add_vrect(
            x0=interval_min,
            x1=interval_max,
            fillcolor='rgba(127, 127, 127, 0.08)',
            line_width=0,
            layer='below',
        )
        fig.add_hline(
            y=threshold_value,
            line_dash='dot',
            line_color='rgba(160, 160, 160, 0.8)',
            annotation_text='Threshold',
            annotation_position='top left',
        )

        summary = html.Div(
            summary_blocks + [
                _build_table("Formula Errors", ["Formula", "Error"], error_rows),
                _build_table("Roots", ["Formula", "x", "y"], root_rows),
                _build_table("Extrema", ["Formula", "Type", "x", "y"], extrema_rows),
                _build_table("Intersections", ["Pair", "x", "y"], intersection_rows),
                _build_table("Threshold Crossings", ["Formula", "x", "y"], threshold_rows),
            ],
            style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}
        )
        return fig, summary

    except Exception as exc:
        message = str(exc) or "Unable to render formula"
        fig.update_layout(
            title=plot_title or "Formula Plot",
            template='plotly_white',
            xaxis_title=x_axis_title or "x",
            yaxis_title=y_axis_title or "f(x)",
            annotations=[{
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 16, 'color': '#b00020'}
            }]
        )
        return fig, html.Div(message)
