"""
Design Showcase tab — canonical visual reference for AGENTS.md UI standards.

This tab answers one question:
"If a new OPView tab is created by following AGENTS.md exactly, how should it look?"
"""

from __future__ import annotations

import math

import plotly.graph_objects as go
from dash import dcc, html


SECTION_TITLE_STYLE = {
    "fontSize": "14px",
    "fontWeight": "700",
    "letterSpacing": "0.04em",
    "textTransform": "uppercase",
    "color": "#355070",
    "marginBottom": "10px",
}

LOAD_HEADER_STYLE = {
    "fontSize": "13px",
    "fontWeight": "700",
    "color": "#1e3a5f",
    "paddingBottom": "6px",
    "borderBottom": "1px solid #dbe3ef",
    "marginBottom": "10px",
}

LABEL_STYLE = {
    "fontSize": "12px",
    "color": "#64748b",
    "marginBottom": "3px",
    "fontWeight": "500",
}

COMPONENT_LABEL_STYLE = {
    "fontSize": "12px",
    "fontWeight": "700",
    "color": "#355070",
    "minWidth": "28px",
    "paddingTop": "6px",
}

SUB_LABEL_STYLE = {
    "fontSize": "11px",
    "color": "#94a3b8",
    "fontStyle": "italic",
}

INPUT_STYLE = {
    "width": "100%",
    "fontSize": "13px",
    "padding": "8px 11px",
    "borderRadius": "7px",
    "border": "1.5px solid #d1dce8",
    "background": "linear-gradient(180deg, #ffffff 0%, #fafbfc 100%)",
    "minHeight": "32px",
    "boxSizing": "border-box",
}

BIG_DROPDOWN_STYLE = {
    "fontSize": "13px",
    "width": "100%",
    "minWidth": "0",
}

SMALL_DROPDOWN_STYLE = {
    "fontSize": "12px",
    "flex": "1 1 170px",
    "minWidth": "145px",
}

STEPPER_BUTTON_STYLE = {
    "width": "34px",
    "minWidth": "34px",
    "minHeight": "36px",
    "border": "1px solid #b8c7de",
    "background": "#f8fbff",
    "color": "#355070",
    "fontSize": "18px",
    "fontWeight": "700",
    "cursor": "pointer",
    "padding": "0",
    "lineHeight": "1",
    "flex": "0 0 auto",
}

PANEL_STYLE = {
    "background": "#ffffff",
    "border": "1px solid #dbe3ef",
    "padding": "16px 18px",
    "marginBottom": "16px",
}

PAGE_SECTION_STYLE = {
    "padding": "0 20px",
    "marginBottom": "16px",
}


def _debug(message: str) -> None:
    print(f"[debug][design-showcase] {message}", flush=True)


def _label(text: str) -> html.Div:
    return html.Div(text, style=LABEL_STYLE)


def _sub_header(text: str) -> html.Div:
    return html.Div(text, style=LOAD_HEADER_STYLE)


def _field(label: str, control) -> html.Div:
    return html.Div(
        [_label(label), control],
        style={"display": "flex", "flexDirection": "column", "marginBottom": "12px"},
    )


def _panel(title: str, subtitle: str, children: list[html.Div], extra_style: dict | None = None) -> html.Div:
    style = {**PANEL_STYLE, **(extra_style or {})}
    return html.Div(
        [
            html.Div(title, style=SECTION_TITLE_STYLE),
            html.Div(subtitle, style={**SUB_LABEL_STYLE, "fontSize": "12px", "marginBottom": "12px"}),
            *children,
        ],
        style=style,
    )


def _stepper(id_prefix: str, value: float) -> html.Div:
    return html.Div(
        [
            html.Button("−", id=f"{id_prefix}-minus", n_clicks=0, style={**STEPPER_BUTTON_STYLE, "borderRadius": "10px 0 0 10px"}),
            dcc.Input(
                id=f"{id_prefix}-input",
                type="number",
                value=value,
                debounce=True,
                step="any",
                style={
                    **INPUT_STYLE,
                    "minWidth": "150px",
                    "minHeight": "36px",
                    "borderRadius": "0",
                    "borderLeft": "none",
                    "borderRight": "none",
                    "padding": "0 11px",
                },
            ),
            html.Button("+", id=f"{id_prefix}-plus", n_clicks=0, style={**STEPPER_BUTTON_STYLE, "borderRadius": "0 10px 10px 0"}),
        ],
        style={"display": "flex", "alignItems": "stretch", "width": "100%", "minHeight": "36px"},
    )


def _sample_figure() -> go.Figure:
    _debug("_sample_figure:start")
    xs = [i * 0.1 for i in range(100)]
    ys_a = [math.sin(x) * math.exp(-x * 0.1) for x in xs]
    ys_b = [math.cos(x) * math.exp(-x * 0.1) for x in xs]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys_a, mode="lines", name="sin · decay", line={"color": "#001f41", "width": 2}))
    fig.add_trace(go.Scatter(x=xs, y=ys_b, mode="lines", name="cos · decay", line={"color": "#b60021", "width": 2, "dash": "dash"}))
    fig.update_layout(
        margin={"l": 40, "r": 20, "t": 30, "b": 40},
        paper_bgcolor="white",
        plot_bgcolor="#f8fafc",
        font={"family": "Roboto Condensed", "size": 12, "color": "#0f1b2b"},
        legend={"orientation": "h", "y": -0.15},
        xaxis={"title": "Time (s)", "gridcolor": "#e2e8f0"},
        yaxis={"title": "Amplitude", "gridcolor": "#e2e8f0"},
        title={"text": "Sample Decay Curves", "font": {"size": 14, "color": "#355070"}},
    )
    _debug("_sample_figure:done")
    return fig


def _typography_section() -> html.Div:
    print("[debug][design-showcase] _typography_section:start", flush=True)
    panel = _panel(
        "Typography",
        "AGENTS.md typography scale rendered as a direct visual reference.",
        [
            html.H1(
                "App Title — 1.5rem / 700",
                className="app-title",
                style={"background": "#001f41", "padding": "8px 16px", "display": "inline-block"},
            ),
            html.Div(style={"height": "10px"}),
            html.Div("Dataset / Panel Big Title — 1.2rem / 700", className="dataset-title", style={"marginBottom": "6px"}),
            html.Div("Sidebar Tab Label — 1.1rem / 600", style={"fontSize": "1.1rem", "fontWeight": "600", "color": "#1e3a5f", "marginBottom": "6px"}),
            html.Div("Section Title — 14px / 700 / UPPERCASE", style=SECTION_TITLE_STYLE),
            html.Div("Sub-section Header — 13px / 700", style={**LOAD_HEADER_STYLE, "border": "none", "paddingBottom": "0"}),
            html.Div("Body base — 16.5px, Roboto Condensed", style={"fontSize": "16.5px", "marginBottom": "4px"}),
            html.Div("Field Label — 12px / 500", style=LABEL_STYLE),
            html.Div("Component Label — 12px / 700", style=COMPONENT_LABEL_STYLE),
            html.Div("Sub-label / hint text — 11px italic", style=SUB_LABEL_STYLE),
            html.Div(
                [
                    html.Span("22", style={"fontSize": "22px", "fontWeight": "700", "color": "#1e3a5f"}),
                    html.Span("  Summary stat value", style={**SUB_LABEL_STYLE, "marginLeft": "4px"}),
                ]
            ),
        ],
    )
    print("[debug][design-showcase] _typography_section:done", flush=True)
    return panel


def _single_field_controls_section() -> html.Div:
    _debug("_single_field_controls_section:start")
    panel = _panel(
        "Single-Field Controls",
        "Default rule: label on top, control below, one field per block.",
        [
            _field("Project Name", dcc.Input(id="showcase-input-1", type="text", placeholder="e.g. OpenPhase_Run_01", style={**INPUT_STYLE})),
            _field("Time Step (s)", dcc.Input(id="showcase-input-2", type="number", value=0.001, step="any", style={**INPUT_STYLE})),
            _field("Scalar Field", dcc.Dropdown(
                id="showcase-dd-big-1",
                options=[
                    {"label": "von Mises Stress", "value": "von_mises"},
                    {"label": "Pressure", "value": "pressure"},
                    {"label": "σ_xx — Normal Stress X", "value": "sxx"},
                ],
                value="von_mises",
                clearable=False,
                style=BIG_DROPDOWN_STYLE,
            )),
            _field("Trigger Type", dcc.Dropdown(
                id="showcase-dd-big-2",
                options=[
                    {"label": "USER", "value": "USER"},
                    {"label": "TIME", "value": "TIME"},
                    {"label": "TIMESTEP", "value": "TIMESTEP"},
                ],
                value="USER",
                clearable=False,
                style=BIG_DROPDOWN_STYLE,
            )),
        ],
    )
    _debug("_single_field_controls_section:done")
    return panel


def _multi_field_rows_section() -> html.Div:
    _debug("_multi_field_rows_section:start")
    bc_options = [
        {"label": "NONE", "value": "NONE"},
        {"label": "Stress", "value": "Stress"},
        {"label": "Strain", "value": "Strain"},
        {"label": "Strain Rate", "value": "StrainRate"},
    ]
    panel = _panel(
        "Multi-Field Rows",
        "Table-like layout when one item has several related fields.",
        [
            _sub_header("Small dropdowns — inline in a multi-field row"),
            html.Div(
                [
                    html.Span("Component", style={**LABEL_STYLE, "minWidth": "60px"}),
                    html.Span("Type", style={**LABEL_STYLE, "flex": "1", "paddingTop": "0"}),
                    html.Span("Value", style={**LABEL_STYLE, "width": "140px"}),
                ],
                style={"display": "flex", "gap": "6px", "marginBottom": "4px"},
            ),
            *[
                html.Div(
                    [
                        html.Span(comp, style=COMPONENT_LABEL_STYLE),
                        dcc.Dropdown(
                            id=f"showcase-dd-small-{i}",
                            options=bc_options,
                            value="NONE" if i > 0 else "Stress",
                            clearable=False,
                            style=SMALL_DROPDOWN_STYLE,
                        ),
                        dcc.Input(
                            id=f"showcase-input-bc-{i}",
                            type="number",
                            value=350e6 if i == 0 else 0.0,
                            debounce=True,
                            step="any",
                            style={**INPUT_STYLE, "width": "140px", "flexShrink": "0"},
                        ),
                    ],
                    style={"display": "flex", "gap": "6px", "alignItems": "flex-start", "marginBottom": "4px"},
                )
                for i, comp in enumerate(["XX", "YY", "ZZ"])
            ],
        ],
    )
    _debug("_multi_field_rows_section:done")
    return panel


def _stepper_section() -> html.Div:
    _debug("_stepper_section:start")
    panel = _panel(
        "Stepper Inputs",
        "Decimal-preserving stepper inputs using the AGENTS.md size and radius standards.",
        [
            _field("Young's Modulus (Pa)", _stepper("showcase-stepper-1", 200e9)),
            _field("Poisson Ratio", _stepper("showcase-stepper-2", 0.3)),
            _field("Timestep Size", _stepper("showcase-stepper-3", 0.001)),
            html.Div(style={"height": "8px"}),
            html.Div(
                [
                    html.Div([_label("Min"), _stepper("showcase-stepper-4", 0.0)], style={"flex": "1 1 200px"}),
                    html.Div([_label("Max"), _stepper("showcase-stepper-5", 100.0)], style={"flex": "1 1 200px"}),
                ],
                style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
            ),
        ],
    )
    _debug("_stepper_section:done")
    return panel


def _buttons_icons_section() -> html.Div:
    _debug("_buttons_icons_section:start")
    panel = _panel(
        "Buttons and Icons",
        "Standard buttons, icon-only buttons, and shared asset-based add/remove controls.",
        [
            _sub_header("Standard .btn class"),
            html.Div(
                [
                    html.Button("Apply", id="showcase-btn-apply", n_clicks=0, className="btn btn-danger"),
                    html.Button("Reset", id="showcase-btn-reset", n_clicks=0, className="btn"),
                    html.Button("Export", id="showcase-btn-export", n_clicks=0, className="btn"),
                ],
                style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginBottom": "16px"},
            ),
            _sub_header("Icon-only .icon-btn class"),
            html.Div(
                [
                    html.Button(html.Img(src="/assets/bar-chart.png", style={"width": "14px", "height": "14px"}), id="showcase-icon-btn-1", n_clicks=0, className="icon-btn", title="Chart"),
                    html.Button(html.Img(src="/assets/download.png", style={"width": "14px", "height": "14px"}), id="showcase-icon-btn-2", n_clicks=0, className="icon-btn", title="Download"),
                    html.Button(html.Img(src="/assets/Reset.png", style={"width": "14px", "height": "14px"}), id="showcase-icon-btn-3", n_clicks=0, className="icon-btn", title="Reset"),
                ],
                style={"display": "flex", "gap": "6px", "marginBottom": "16px"},
            ),
            _sub_header("Image icon buttons (CSS classes)"),
            html.Div(
                [
                    html.Button("", id="showcase-add-btn", n_clicks=0, className="opview-image-add-btn", style={"width": "40px", "height": "32px", "backgroundPosition": "center", "paddingLeft": "0"}),
                    html.Button("", id="showcase-remove-btn", n_clicks=0, className="opview-image-close-btn", style={"width": "26px", "height": "26px"}),
                ],
                style={"display": "flex", "gap": "8px", "alignItems": "center", "marginBottom": "16px"},
            ),
            _sub_header("Compact reset .reset-btn"),
            html.Div(
                [
                    html.Button(
                        html.Img(src="/assets/Reset.png", style={"width": "14px", "height": "14px"}),
                        id="showcase-reset-btn",
                        n_clicks=0,
                        className="btn reset-btn",
                    ),
                ]
            ),
        ],
    )
    _debug("_buttons_icons_section:done")
    return panel


def _panels_section() -> html.Div:
    _debug("_panels_section:start")
    panel = html.Div(
        [
            html.Div("Panel and Container Sizes", style=SECTION_TITLE_STYLE),
            html.Div("Fixed, flexible, and wide panels using the documented OPView size rules.", style={**SUB_LABEL_STYLE, "fontSize": "12px", "marginBottom": "12px"}),
            html.Div(
                [
                    html.Div(
                        [
                            _sub_header("Sidebar panel — 240px"),
                            html.Div("Fixed-width sidebar panel", style={"fontSize": "13px", "color": "#64748b"}),
                            html.Div(style={"height": "8px"}),
                            _field("Option", dcc.Dropdown(
                                id="showcase-panel-dd",
                                options=[{"label": f"Item {i}", "value": i} for i in range(1, 6)],
                                value=1,
                                clearable=False,
                                style=BIG_DROPDOWN_STYLE,
                            )),
                        ],
                        style={**PANEL_STYLE, "flex": "0 0 240px", "minWidth": "240px", "maxWidth": "240px"},
                    ),
                    html.Div(
                        [
                            _sub_header("Feature panel — flex: 1 1 300px"),
                            html.Div("Default feature panel footprint.", style={"fontSize": "13px", "color": "#64748b", "marginBottom": "10px"}),
                            html.Div(
                                [
                                    _field("Alpha", dcc.Input(id="showcase-fp-1", type="number", value=1.0, style={**INPUT_STYLE})),
                                    _field("Beta", dcc.Input(id="showcase-fp-2", type="number", value=0.5, style={**INPUT_STYLE})),
                                    _field("Gamma", dcc.Input(id="showcase-fp-3", type="number", value=0.25, style={**INPUT_STYLE})),
                                ],
                                style={"display": "flex", "gap": "10px", "flexWrap": "wrap"},
                            ),
                        ],
                        style={**PANEL_STYLE, "flex": "1 1 300px", "minWidth": "200px"},
                    ),
                    html.Div(
                        [
                            _sub_header("Wide panel — flex: 1 1 400px"),
                            html.Div("Used for notebook and larger graph-driven content.", style={"fontSize": "13px", "color": "#64748b"}),
                        ],
                        style={**PANEL_STYLE, "flex": "1 1 400px", "minWidth": "200px"},
                    ),
                ],
                style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
            ),
        ],
        style={**PANEL_STYLE},
    )
    _debug("_panels_section:done")
    return panel


def _graph_section() -> html.Div:
    print("[debug][design-showcase] _graph_section:start", flush=True)
    panel = _panel(
        "Graph Area",
        "Reference graph shell for a typical OPView tab: controls on one side, Plotly graph on the other.",
        [
            html.Div(
                [
                    html.Div(
                        [
                            _field("X Axis", dcc.Dropdown(
                                id="showcase-graph-x",
                                options=[{"label": "Time (s)", "value": "time"}, {"label": "Timestep", "value": "step"}],
                                value="time",
                                clearable=False,
                                style=BIG_DROPDOWN_STYLE,
                            )),
                            _field("Y Axis", dcc.Dropdown(
                                id="showcase-graph-y",
                                options=[{"label": "sin · decay", "value": "sin"}, {"label": "cos · decay", "value": "cos"}, {"label": "Both", "value": "both"}],
                                value="both",
                                clearable=False,
                                style=BIG_DROPDOWN_STYLE,
                            )),
                            _field("Line width", _stepper("showcase-graph-lw", 2.0)),
                            html.Button("Refresh", id="showcase-graph-refresh", n_clicks=0, className="btn btn-danger", style={"width": "100%"}),
                        ],
                        style={"flex": "0 0 200px", "minWidth": "180px", "display": "flex", "flexDirection": "column"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="showcase-graph",
                                figure=_sample_figure(),
                                style={"height": "320px"},
                                config={"displayModeBar": True},
                            ),
                        ],
                        style={"flex": "1 1 400px", "minWidth": "300px"},
                    ),
                ],
                style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
            )
        ],
    )
    print("[debug][design-showcase] _graph_section:done", flush=True)
    return panel


def _colors_section() -> html.Div:
    _debug("_colors_section:start")
    colors = [
        ("#001f41", "Primary — buttons, sidebar, graph accents"),
        ("#b60021", "Accent — active states"),
        ("#95041a", "Hover — button hover"),
        ("#9f051d", "Accent dark"),
        ("#355070", "Section titles, component labels"),
        ("#1e3a5f", "Sub-headers, stat values"),
        ("#64748b", "Field labels, muted text"),
        ("#94a3b8", "Sub-labels, hints"),
        ("#d1dce8", "Input borders"),
        ("#dbe3ef", "Panel borders"),
    ]
    panel = _panel(
        "Colors and Tokens",
        "Color palette and token examples taken directly from AGENTS.md.",
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(style={"width": "40px", "height": "40px", "background": color, "border": "1px solid #dbe3ef", "borderRadius": "6px", "flexShrink": "0"}),
                            html.Div(
                                [
                                    html.Div(color, style={"fontFamily": "monospace", "fontSize": "12px", "fontWeight": "700", "color": "#0f1b2b"}),
                                    html.Div(label, style={"fontSize": "11px", "color": "#64748b"}),
                                ]
                            ),
                        ],
                        style={"display": "flex", "gap": "10px", "alignItems": "center"},
                    )
                    for color, label in colors
                ],
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fill, minmax(260px, 1fr))", "gap": "10px"},
            ),
        ],
    )
    _debug("_colors_section:done")
    return panel


def build_design_showcase() -> html.Div:
    """Build the full design showcase tab layout."""
    print("[debug][design-showcase] build_design_showcase: building layout", flush=True)

    layout = html.Div(
        [
            html.Div(
                [
                    html.Div("Design Showcase", className="dataset-title", style={"marginBottom": "4px"}),
                    html.Div(
                        "Canonical AGENTS.md output — this is the visual reference for how a new OPView tab should look when built by the rulebook.",
                        style={**SUB_LABEL_STYLE, "fontSize": "13px"},
                    ),
                ],
                style={"padding": "16px 20px 8px 20px", "borderBottom": "1px solid #dbe3ef", "marginBottom": "16px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            _typography_section(),
                            _single_field_controls_section(),
                            _stepper_section(),
                        ],
                        style={"flex": "1 1 380px", "minWidth": "320px"},
                    ),
                    html.Div(
                        [
                            _multi_field_rows_section(),
                            _buttons_icons_section(),
                        ],
                        style={"flex": "1 1 380px", "minWidth": "320px"},
                    ),
                ],
                style={"display": "flex", "gap": "16px", "flexWrap": "wrap", **PAGE_SECTION_STYLE},
            ),
            html.Div([_panels_section()], style=PAGE_SECTION_STYLE),
            html.Div([_graph_section()], style=PAGE_SECTION_STYLE),
            html.Div([_colors_section()], style={**PAGE_SECTION_STYLE, "paddingBottom": "32px"}),
        ],
        style={"overflowY": "auto", "height": "100%", "background": "#f0f4f8"},
    )

    print("[debug][design-showcase] build_design_showcase: layout built", flush=True)
    return layout
