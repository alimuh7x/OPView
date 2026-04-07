"""
UI for the Mechanical Loads Explorer tab.

Interactive configurator for OpenPhase MechanicalLoads: define N loads with
trigger conditions and 6-component boundary conditions, then visualize them.
"""

from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from utils.mechanical_loads_explorer import (
    BC_TYPE_OPTIONS,
    COMPONENT_LABELS,
    COMPONENT_INDEX_OPTIONS,
    TRIGGER_OPTIONS,
    VALUE_TRIGGERS,
    INDEX_TRIGGERS,
    BC_TYPE_COLORS,
    build_load_figure,
    build_opstudio_export_text,
    build_load_step_figure,
    build_loads_summary,
    build_trigger_timeline,
    default_load_structure,
    summarize_load,
)


PANEL_STYLE = {
    "background": "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
    "border": "1px solid #dbe3ef",
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

LOAD_HEADER_STYLE = {
    "fontSize": "13px",
    "fontWeight": "700",
    "color": "#1e3a5f",
    "paddingBottom": "6px",
    "borderBottom": "1px solid #dbe3ef",
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

INPUT_STYLE = {
    "width": "100%",
    "fontSize": "13px",
    "padding": "5px 8px",
    "borderRadius": "6px",
    "border": "1px solid #dbe3ef",
    "background": "#ffffff",
}

MECHANICAL_LOAD_PRESET_OPTIONS = [
    {"label": "Custom", "value": "custom"},
    {"label": "Creep", "value": "creep"},
    {"label": "Fatigue", "value": "fatigue"},
    {"label": "Stress / Strain", "value": "stress_strain"},
]

_SUB_LABEL = {
    "fontSize": "11px",
    "color": "#94a3b8",
    "marginBottom": "0",
    "fontStyle": "italic",
}


def _trigger_row(
    label: str,
    trigger_type_id: dict,
    trigger_val_id: dict,
    trigger_idx_id: dict,
    trigger_val_wrap_id: dict,
    trigger_idx_wrap_id: dict,
    default_trigger: str,
    default_trigger_val: float,
    default_trigger_idx: int,
) -> html.Div:
    """
    Build one trigger section (ON or OFF).

    Layout (stacked):
      [Label]
      [Type dropdown — full width]
      [Type dropdown — full width]
      [at value: _______] [component: [XX ▼]]
    """
    show_val = default_trigger in VALUE_TRIGGERS
    show_idx = default_trigger in INDEX_TRIGGERS
    print(
        "[mechanical-loads] _trigger_row "
        f"label={label!r} trigger_type_id={trigger_type_id!r} "
        f"default_trigger={default_trigger!r} default_trigger_val={default_trigger_val!r} "
        f"default_trigger_idx={default_trigger_idx!r} show_val={show_val!r} show_idx={show_idx!r}",
        flush=True,
    )
    return html.Div([
        html.Div(label, style=LABEL_STYLE),
        dcc.Dropdown(
            id=trigger_type_id,
            options=TRIGGER_OPTIONS,
            value=default_trigger,
            clearable=False,
            style={"fontSize": "13px", "marginBottom": "4px"},
        ),
        html.Div([
            html.Div(
                id=trigger_val_wrap_id,
                children=[
                    html.Div("Value", style=LABEL_STYLE),
                    dcc.Input(
                        id=trigger_val_id,
                        type="number",
                        value=default_trigger_val,
                        debounce=True,
                        step="any",
                        placeholder="e.g. 100",
                        style={**INPUT_STYLE, "width": "100%"},
                    ),
                ],
                style={
                    "display": "flex" if show_val else "none",
                    "flexDirection": "column",
                    "gap": "4px",
                    "alignItems": "stretch",
                    "flex": "1 1 0",
                    "minWidth": "0",
                },
            ),
            html.Div(
                id=trigger_idx_wrap_id,
                children=[
                    html.Div("Component", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id=trigger_idx_id,
                        options=COMPONENT_INDEX_OPTIONS,
                        value=default_trigger_idx,
                        clearable=False,
                        style={"fontSize": "13px", "width": "100%"},
                    ),
                ],
                style={
                    "display": "flex" if show_idx else "none",
                    "flexDirection": "column",
                    "gap": "4px",
                    "alignItems": "stretch",
                    "flex": "1 1 0",
                    "minWidth": "0",
                },
            ),
        ], style={
            "display": "flex",
            "gap": "8px",
            "alignItems": "flex-end",
            "flexWrap": "nowrap",
            "marginTop": "4px",
            "marginBottom": "4px",
        }),
    ], style={"marginBottom": "10px"})


def _bc_component_row(n: int, c: int, bc_type: str, bc_value: float) -> html.Div:
    """Build a single BC component row (label + type dropdown + value input)."""
    print(
        "[mechanical-loads] _bc_component_row "
        f"load_index={n!r} component_index={c!r} bc_type={bc_type!r} bc_value={bc_value!r}",
        flush=True,
    )
    return html.Div([
        html.Span(COMPONENT_LABELS[c], style=COMPONENT_LABEL_STYLE),
        dcc.Dropdown(
            id={"type": "ml-bc-type", "index": n * 6 + c},
            options=BC_TYPE_OPTIONS,
            value=bc_type,
            clearable=False,
            style={"fontSize": "12px", "flex": "1 1 170px", "minWidth": "145px"},
        ),
        dcc.Input(
            id={"type": "ml-bc-val", "index": n * 6 + c},
            type="number",
            value=bc_value,
            debounce=True,
            step="any",
            placeholder="0.0",
            style={**INPUT_STYLE, "width": "150px", "flexShrink": "0"},
        ),
    ], style={"display": "flex", "gap": "6px", "alignItems": "flex-start", "marginBottom": "4px"})


def build_load_card(n: int, load: dict | None = None) -> html.Div:
    """
    Build a single load configuration card for load index n.
    Uses load dict values as defaults (or default_load_structure if None).
    """
    if load is None:
        load = default_load_structure()
    print(
        "[mechanical-loads] build_load_card "
        f"load_index={n!r} load={load!r}",
        flush=True,
    )

    bc_rows = [_bc_component_row(n, c, load["bc_types"][c], load["bc_values"][c]) for c in range(6)]

    return html.Div([
        html.Div([
            html.Div(f"Load {n}", style=LOAD_HEADER_STYLE),
            html.Button(
                "",
                id={"type": "ml-remove-load-btn", "index": n},
                n_clicks=0,
                title=f"Remove load {n}",
                className="mechanical-remove-load-btn",
            ),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "gap": "10px",
            "marginBottom": "10px",
        }),

        _trigger_row(
            "Trigger ON — when should this load activate?",
            {"type": "ml-trigger-on",          "index": n},
            {"type": "ml-trigger-on-val",       "index": n},
            {"type": "ml-trigger-on-idx",       "index": n},
            {"type": "ml-trigger-on-val-wrap",  "index": n},
            {"type": "ml-trigger-on-idx-wrap",  "index": n},
            load["trigger_on"],
            load["trigger_on_val"],
            load["trigger_on_idx"],
        ),

        _trigger_row(
            "Trigger OFF — when should this load deactivate?",
            {"type": "ml-trigger-off",          "index": n},
            {"type": "ml-trigger-off-val",      "index": n},
            {"type": "ml-trigger-off-idx",      "index": n},
            {"type": "ml-trigger-off-val-wrap", "index": n},
            {"type": "ml-trigger-off-idx-wrap", "index": n},
            load["trigger_off"],
            load["trigger_off_val"],
            load["trigger_off_idx"],
        ),

        html.Div([
            html.Div("Repeat count", style=LABEL_STYLE),
            dcc.Input(
                id={"type": "ml-repeat", "index": n},
                type="number",
                value=load["repeat"],
                debounce=True,
                min=1,
                step=1,
                style={**INPUT_STYLE, "width": "130px"},
            ),
        ], style={"marginBottom": "10px"}),

        html.Div("Boundary Conditions", style={**SECTION_TITLE_STYLE, "fontSize": "12px",
                                                "marginTop": "8px", "marginBottom": "6px"}),
        html.Div([
            html.Div([
                html.Span("", style={**COMPONENT_LABEL_STYLE, "minWidth": "28px"}),
                html.Span("Type", style={**LABEL_STYLE, "flex": "1", "paddingTop": "0"}),
                html.Span("Value", style={**LABEL_STYLE, "width": "140px"}),
            ], style={"display": "flex", "gap": "6px", "marginBottom": "4px"}),
            *bc_rows,
        ]),
    ], style={**PANEL_STYLE, "marginBottom": "12px"})


def _build_stats(loads: list[dict]) -> html.Div:
    """Build summary stat cards."""
    print(f"[mechanical-loads] _build_stats loads={loads!r}", flush=True)
    items = build_loads_summary(loads)
    cards = []
    for label, value in items:
        cards.append(html.Div([
            html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": "#1e3a5f"}),
            html.Div(label, style={"fontSize": "11px", "color": "#64748b", "marginTop": "2px"}),
        ], style={
            "background": "#fcfcfc",
            "borderRadius": "2px",
            "padding": "10px 14px",
            "minWidth": "80px",
            "textAlign": "center",
        }))
    return html.Div(cards, style={"display": "flex", "gap": "10px", "flexWrap": "wrap",
                                   "marginBottom": "14px"})


def _trigger_desc(trigger: str, val: float, idx: int) -> str:
    """Return human-readable trigger description."""
    if trigger == "USER":
        return "USER (activate manually in code)"
    comp = COMPONENT_LABELS[idx] if 0 <= idx < len(COMPONENT_LABELS) else "XX"
    if trigger == "TIME":
        return f"when simulation time ≥ {val:g}"
    if trigger == "TIMESTEP":
        return f"when time step ≥ {val:g}"
    if trigger == "STRESS":
        return f"when Stress[{comp}] reaches {val:g}"
    if trigger == "STRAIN":
        return f"when Strain[{comp}] reaches {val:g}"
    return trigger


def _bc_color(bc_type: str) -> str:
    return BC_TYPE_COLORS.get(bc_type, "#e2e8f0")


def build_load_status(loads: list[dict]) -> html.Div:
    """
    Build per-load status output cards — shows each load's current configuration
    in plain language so the user can verify what is active and why.
    """
    if not loads:
        print("[mechanical-loads] build_load_status loads=[]", flush=True)
        return html.Div("No loads configured.", style={"color": "#94a3b8", "fontSize": "13px"})

    print(f"[mechanical-loads] build_load_status loads={loads!r}", flush=True)
    cards = []
    for i, load in enumerate(loads):
        on_text  = _trigger_desc(load["trigger_on"],  load["trigger_on_val"],  load["trigger_on_idx"])
        off_text = _trigger_desc(load["trigger_off"], load["trigger_off_val"], load["trigger_off_idx"])

        active_bcs = [
            (COMPONENT_LABELS[c], t, v)
            for c, (t, v) in enumerate(zip(load["bc_types"], load["bc_values"]))
            if t != "NONE"
        ]

        bc_pills = []
        for comp, bc_type, val in active_bcs:
            bc_pills.append(html.Span(
                f"{comp} = {bc_type}({val:g})",
                style={
                    "background": _bc_color(bc_type),
                    "color": "#fff" if bc_type != "NONE" else "#334155",
                    "borderRadius": "2px",
                    "padding": "2px 7px",
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "marginRight": "4px",
                    "marginBottom": "3px",
                    "display": "inline-block",
                }
            ))

        cards.append(html.Div([
            html.Div(f"Load {i}", style={
                "fontWeight": "700", "fontSize": "13px", "color": "#1e3a5f",
                "marginBottom": "6px",
            }),
            html.Div([
                html.Span("ON:  ", style={"fontWeight": "600", "color": "#10b981", "fontSize": "12px", "minWidth": "36px"}),
                html.Span(on_text, style={"fontSize": "12px", "color": "#334155"}),
            ], style={"marginBottom": "3px", "display": "flex", "gap": "4px"}),
            html.Div([
                html.Span("OFF: ", style={"fontWeight": "600", "color": "#ef4444", "fontSize": "12px", "minWidth": "36px"}),
                html.Span(off_text, style={"fontSize": "12px", "color": "#334155"}),
            ], style={"marginBottom": "6px", "display": "flex", "gap": "4px"}),
            html.Div(
                bc_pills if bc_pills else [
                    html.Span("— no active boundary conditions —",
                              style={"fontSize": "11px", "color": "#94a3b8", "fontStyle": "italic"})
                ],
                style={"display": "flex", "flexWrap": "wrap"},
            ),
        ], style={
            "background": "#f6f7f8",
            "border": "1px solid #dbe3ef",
            "borderRadius": "6px",
            "padding": "10px 14px",
            "marginBottom": "8px",
        }))

    return html.Div(cards, style={
        "display": "grid",
        "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
        "gap": "10px",
        "alignItems": "stretch",
    })


def build_mechanical_loads_explorer() -> html.Div:
    """Build the full Mechanical Loads Explorer layout (static initial render)."""
    print("[mechanical-loads] build_mechanical_loads_explorer panel_radius=10px", flush=True)
    initial_loads = [default_load_structure()]
    initial_fig      = build_load_figure(initial_loads)
    initial_step_fig = build_load_step_figure(initial_loads)
    initial_timeline = build_trigger_timeline(initial_loads)
    initial_status   = build_load_status(initial_loads)
    initial_export   = build_opstudio_export_text(initial_loads)

    return html.Div([
        dcc.Store(id="ml-num-loads", data=1),

        html.Div(
            "Configure mechanical boundary condition loads, trigger conditions, and visualize "
            "the resulting stress/strain state per Voigt component.",
            style={"fontSize": "13px", "color": "#64748b", "marginBottom": "16px"},
        ),

        html.Div([
            html.Div([
                # Preset dropdown moved to sidebar — keep hidden for Dash component ID stability
                dcc.Dropdown(
                    id="ml-preset",
                    options=MECHANICAL_LOAD_PRESET_OPTIONS,
                    value="custom",
                    clearable=False,
                    style={"display": "none"},
                ),
            ], style={"flex": "0", "minWidth": "0"}),
            html.Div([
                html.Div("dt (time per timestep)", style=LOAD_HEADER_STYLE),
                dcc.Input(
                    id="ml-dt",
                    type="number",
                    value=1.0,
                    debounce=True,
                    min=0,
                    step="any",
                    style={
                        **INPUT_STYLE,
                        "width": "220px",
                        "height": "30px",
                        "padding": "0 12px",
                        "lineHeight": "30px",
                        "boxSizing": "border-box",
                    },
                ),
            ], style={"flex": "1 1 240px", "minWidth": "220px", "maxWidth": "240px"}),
        ], style={
            "marginBottom": "16px",
            "display": "flex",
            "gap": "16px",
            "alignItems": "flex-end",
            "flexWrap": "wrap",
        }),

        html.Div([

            # ── Left panel: controls ───────────────────────────────────────────
            html.Div([
                html.Button(
                    "Add Load",
                    id="ml-add-load-btn",
                    n_clicks=0,
                    className="mechanical-add-load-btn opview-image-add-btn",
                ),
                html.Div(
                    id="ml-loads-list",
                    children=[build_load_card(0, initial_loads[0])],
                ),
            ], style={
                "width": "100%",
                "maxWidth": "420px",
                "minWidth": "280px",
                "flex": "1 1 360px",
            }),

            # ── Right panel: status + visualization ────────────────────────────
            html.Div([

                # Load Status output
                html.Div([
                    html.Div("Load Status", style=SECTION_TITLE_STYLE),
                    html.Div(
                        id="ml-load-status",
                        children=[initial_status],
                    ),
                ], style={**PANEL_STYLE, "marginBottom": "14px"}),

                html.Div([
                    html.Div("Debug", style=SECTION_TITLE_STYLE),
                    html.Pre(
                        id="ml-debug-output",
                        children="Mechanical Loads debug: waiting for events",
                        style={
                            "margin": "0",
                            "whiteSpace": "pre-wrap",
                            "fontSize": "12px",
                            "lineHeight": "1.45",
                            "color": "#0f172a",
                            "background": "#eef2ff",
                            "border": "1px solid #c7d2fe",
                            "borderRadius": "2px",
                            "padding": "12px",
                            "maxHeight": "220px",
                            "overflowY": "auto",
                        },
                    ),
                ], style={**PANEL_STYLE, "marginBottom": "14px"}),

                # Stats cards
                html.Div(id="ml-stats", children=[_build_stats(initial_loads)]),

                # BC bar chart
                html.Div([
                    html.Div("Applied Load History", style=SECTION_TITLE_STYLE),
                    dcc.Graph(
                        id="ml-figure",
                        figure=initial_fig,
                        config={"displayModeBar": False},
                    ),
                ], style={**PANEL_STYLE, "marginBottom": "14px"}),

                html.Div([
                    html.Div("Applied Load History (Timesteps)", style=SECTION_TITLE_STYLE),
                    dcc.Graph(
                        id="ml-step-figure",
                        figure=initial_step_fig,
                        config={"displayModeBar": False},
                    ),
                ], style={**PANEL_STYLE, "marginBottom": "14px"}),

                # Trigger timeline
                html.Div([
                    html.Div("Trigger Timeline", style=SECTION_TITLE_STYLE),
                    dcc.Graph(
                        id="ml-timeline",
                        figure=initial_timeline,
                        config={"displayModeBar": False},
                    ),
                ], style={**PANEL_STYLE, "marginBottom": "14px"}),

                html.Div([
                    html.Div([
                        html.Div("OPStudio Export", style={**SECTION_TITLE_STYLE, "marginBottom": "0"}),
                        dcc.Clipboard(
                            id="ml-export-copy",
                            target_id="ml-export-output",
                            title="Copy export text",
                            children="Copy",
                            style={
                                "display": "inline-flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "padding": "8px 14px",
                                "borderRadius": "8px",
                                "border": "1px solid #bfdbfe",
                                "background": "#eff6ff",
                                "color": "#1d4ed8",
                                "cursor": "pointer",
                                "fontSize": "13px",
                                "fontWeight": "600",
                            },
                        ),
                    ], style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "gap": "12px",
                        "marginBottom": "10px",
                    }),
                    dcc.Textarea(
                        id="ml-export-output",
                        value=initial_export,
                        readOnly=True,
                        style={
                            "width": "100%",
                            "minHeight": "240px",
                            "fontFamily": "monospace",
                            "fontSize": "12px",
                            "lineHeight": "1.45",
                            "padding": "12px",
                            "borderRadius": "10px",
                            "border": "1px solid #cbd5e1",
                            "background": "#f8fafc",
                            "color": "#0f172a",
                            "resize": "vertical",
                        },
                    ),
                ], style={**PANEL_STYLE, "marginBottom": "14px"}),

            ], style={"flex": "999 1 560px", "minWidth": "0", "width": "100%"}),

        ], style={
            "display": "flex",
            "gap": "18px",
            "alignItems": "flex-start",
            "flexWrap": "wrap",
            "width": "100%",
        }),
    ], style={"padding": "16px 20px"})
