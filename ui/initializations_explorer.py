"""
UI for the Initializations Explorer tab.
"""

from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from utils.initializations_explorer import build_quasi_random_summary, simulate_quasi_random_nuclei_2d


PANEL_STYLE = {
    "background": "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
    "border": "1px solid #dbe3ef",
    "borderRadius": "16px",
    "boxShadow": "0 10px 28px rgba(15, 23, 42, 0.06)",
    "padding": "16px 18px",
}

SECTION_TITLE_STYLE = {
    "fontSize": "14px",
    "fontWeight": "700",
    "letterSpacing": "0.04em",
    "textTransform": "uppercase",
    "color": "#355070",
    "marginBottom": "10px",
}


def _axis_tick_step(size: int) -> int:
    """Return a readable integer tick step for the given domain size."""
    if size <= 12:
        return 1
    if size <= 24:
        return 2
    if size <= 40:
        return 5
    if size <= 80:
        return 10
    return 20


def default_quasi_random_settings() -> dict:
    """Return default explorer settings."""
    return {
        "method": "quasi-random-nuclei",
        "nx": 50,
        "ny": 50,
        "offset_x": 0,
        "offset_y": 0,
        "spacing_x": 5,
        "spacing_y": 5,
        "deviation_x": 0,
        "deviation_y": 0,
        "threshold": 0.0,
        "seed": 1,
    }


def _slider_block(component_id: str, label: str, min_value: float, max_value: float, value: float, step: float = 1) -> html.Div:
    return html.Div(
        [
            html.Div(label, style={"fontSize": "13px", "fontWeight": "700", "color": "#4a5568", "marginBottom": "6px"}),
            dcc.Slider(
                id=component_id,
                min=min_value,
                max=max_value,
                step=step,
                value=value,
                tooltip={"placement": "bottom", "always_visible": True},
            ),
        ],
        style={"marginBottom": "18px"},
    )


def _build_stats(data: dict) -> html.Div:
    card_style = {
        "background": "#ffffff",
        "border": "1px solid #dde6f2",
        "borderRadius": "12px",
        "padding": "12px 14px",
        "minWidth": "120px",
    }
    return html.Div(
        [
            html.Div(
                [
                    html.Div("Final nuclei", style={"fontSize": "12px", "color": "#667085", "marginBottom": "4px"}),
                    html.Div(str(data["final_count"]), style={"fontSize": "28px", "fontWeight": "800", "color": "#0f2942"}),
                ],
                style=card_style,
            ),
            html.Div(
                [
                    html.Div("Effective origin", style={"fontSize": "12px", "color": "#667085", "marginBottom": "4px"}),
                    html.Div(f"{data['origin'][0]}, {data['origin'][1]}", style={"fontSize": "24px", "fontWeight": "800", "color": "#355070"}),
                ],
                style=card_style,
            ),
        ],
        style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
    )


def build_quasi_random_figure(settings: dict, reroll_count: int = 0) -> tuple[go.Figure, html.Div, html.Div]:
    """Build the Plotly figure, stats, and explanation."""
    effective_seed = int(settings["seed"]) + int(reroll_count) * 9973
    data = simulate_quasi_random_nuclei_2d(
        nx=settings["nx"],
        ny=settings["ny"],
        offset=(settings["offset_x"], settings["offset_y"]),
        spacing=(settings["spacing_x"], settings["spacing_y"]),
        deviation=(settings["deviation_x"], settings["deviation_y"]),
        threshold=settings["threshold"],
        seed=effective_seed,
    )

    figure = go.Figure()
    if data["final_points"]:
        figure.add_trace(
            go.Scatter(
                x=[point["x"] for point in data["final_points"]],
                y=[point["y"] for point in data["final_points"]],
                mode="markers",
                marker={
                    "size": 11,
                    "color": "#f59e0b",
                    "line": {"width": 1.5, "color": "#9a6700"},
                },
                customdata=[
                    [point["base_x"], point["base_y"], point["dx"], point["dy"]]
                    for point in data["final_points"]
                ],
                hovertemplate=(
                    "Final nucleus<br>"
                    "x=%{x}, y=%{y}<br>"
                    "base=(%{customdata[0]}, %{customdata[1]})<br>"
                    "shift=(%{customdata[2]}, %{customdata[3]})<extra></extra>"
                ),
                name="Final nuclei",
            )
        )

    figure.update_layout(
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
        height=620,
        plot_bgcolor="#fbfcfe",
        paper_bgcolor="#ffffff",
        showlegend=False,
    )
    figure.update_xaxes(
        range=[-0.5, settings["nx"] - 0.5],
        dtick=_axis_tick_step(settings["nx"]),
        gridcolor="rgba(53, 80, 112, 0.10)",
        zeroline=False,
        title={"text": "x", "font": {"size": 18}},
        tickfont={"size": 16},
        constrain="domain",
    )
    figure.update_yaxes(
        range=[-0.5, settings["ny"] - 0.5],
        dtick=_axis_tick_step(settings["ny"]),
        gridcolor="rgba(53, 80, 112, 0.10)",
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
        title={"text": "y", "font": {"size": 18}},
        tickfont={"size": 16},
    )
    figure.add_shape(
        type="rect",
        x0=-0.5,
        y0=-0.5,
        x1=settings["nx"] - 0.5,
        y1=settings["ny"] - 0.5,
        line={"color": "#355070", "width": 2},
    )

    explanation = html.Div(
        [
            html.Div("How to read this", style=SECTION_TITLE_STYLE),
            html.P(
                build_quasi_random_summary(data),
                style={"margin": 0, "fontSize": "14px", "lineHeight": "1.6", "color": "#4b5563"},
            ),
        ],
        style={**PANEL_STYLE, "marginTop": "14px"},
    )

    return figure, _build_stats(data), explanation


def build_initializations_explorer() -> html.Div:
    """Build the Initializations Explorer tab."""
    defaults = default_quasi_random_settings()
    initial_figure, initial_stats, initial_explanation = build_quasi_random_figure(defaults)

    controls = html.Div(
        [
            html.Div("Method", style=SECTION_TITLE_STYLE),
            dcc.Dropdown(
                id="initializations-method-selector",
                options=[{"label": "QuasiRandomNuclei", "value": "quasi-random-nuclei"}],
                value=defaults["method"],
                clearable=False,
                style={"marginBottom": "18px"},
            ),
            html.Div("Domain", style=SECTION_TITLE_STYLE),
            _slider_block("initializations-nx", "Nx", 8, 120, defaults["nx"]),
            _slider_block("initializations-ny", "Ny", 8, 120, defaults["ny"]),
            html.Div("Origin / Spacing", style=SECTION_TITLE_STYLE),
            _slider_block("initializations-offset-x", "offsetX", 0, 60, defaults["offset_x"]),
            _slider_block("initializations-offset-y", "offsetY", 0, 60, defaults["offset_y"]),
            _slider_block("initializations-spacing-x", "spacingX", 1, 120, defaults["spacing_x"]),
            _slider_block("initializations-spacing-y", "spacingY", 1, 120, defaults["spacing_y"]),
            html.Div("Deviation / Filter", style=SECTION_TITLE_STYLE),
            _slider_block("initializations-deviation-x", "deviationX", 0, 20, defaults["deviation_x"]),
            _slider_block("initializations-deviation-y", "deviationY", 0, 20, defaults["deviation_y"]),
            _slider_block("initializations-threshold", "threshold", 0, 1, defaults["threshold"], step=0.01),
            _slider_block("initializations-seed", "seed", 1, 200, defaults["seed"]),
            html.Div(
                [
                    html.Button("Reroll Same Settings", id="initializations-reroll-btn", className="graphs-add-panel-btn", n_clicks=0),
                    html.Button("Regular", id="initializations-preset-regular-btn", className="graphs-add-panel-btn", n_clicks=0, style={"background": "#f8fbff", "color": "#355070"}),
                    html.Button("More Random", id="initializations-preset-random-btn", className="graphs-add-panel-btn", n_clicks=0, style={"background": "#f8fbff", "color": "#355070"}),
                ],
                style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginTop": "8px"},
            ),
        ],
        style={**PANEL_STYLE, "width": "360px", "minWidth": "360px"},
    )

    plot_panel = html.Div(
        [
            dcc.Graph(
                id="initializations-figure",
                figure=initial_figure,
                config={"displaylogo": False},
                style={"height": "640px"},
            ),
            html.Div(id="initializations-explanation", children=initial_explanation),
        ],
        style={"flex": "1", "minWidth": "0"},
    )

    return html.Div(
        [
            html.Div(
                "Interactive explorer for OpenPhase initialization methods. Start with QuasiRandomNuclei and adjust sliders to understand how spacing, offset, deviation, threshold, and seed change the final nuclei pattern.",
                style={"fontSize": "14px", "color": "#667085", "marginBottom": "14px"},
            ),
            html.Div(
                [
                    controls,
                    html.Div(
                        [
                            html.Div(id="initializations-stats", children=initial_stats, style={"marginBottom": "14px"}),
                            plot_panel,
                        ],
                        style={"flex": "1", "minWidth": "0"},
                    ),
                ],
                style={"display": "flex", "gap": "18px", "alignItems": "flex-start", "flexWrap": "wrap"},
            ),
        ],
        style={"padding": "6px 4px 18px 4px"},
    )
