"""
Calculation notebook UI for OPView.
"""

from __future__ import annotations

from dash import dcc, html


NOTEBOOK_ROWS = 28
NOTEBOOK_LINE_HEIGHT = "34px"
RESULTS_GUTTER_WIDTH = "220px"
FUNCTIONS_CARD_WIDTH = "360px"
NOTEBOOK_SHEET_WIDTH = "1280px"

NOTEBOOK_HELP = [
    {
        "title": "Trig",
        "items": ["sin(x)", "cos(x)", "tan(x)", "asin(x)", "acos(x)", "atan(x)"],
        "note": "Angles are in radians.",
    },
    {
        "title": "Math",
        "items": ["abs(x)", "sqrt(x)", "exp(x)", "log(x)", "floor(x)", "ceil(x)", "round(x)"],
    },
    {
        "title": "Engineering",
        "items": [
            "cfl_dt(dx,u,cfl=1)",
            "diffusion_dt(dx,D,f=0.5)",
            "fourier_number(D,dt,dx)",
            "peclet(u,L,D)",
            "cell_size(L,N)",
            "domain_points(L,dx)",
            "von_mises(s11,s22,s33,s12=0,s23=0,s13=0)",
        ],
        "note": "For plane stress use von_mises(sxx, syy, 0, txy, 0, 0).",
    },
    {
        "title": "Constitutive",
        "items": [
            "shear_modulus(E,nu)",
            "lame_lambda(E,nu)",
            "hooke_1d(E,eps)",
            "hooke_3d(E,nu,exx,eyy,ezz,exy=0,eyz=0,exz=0)",
            "plane_strain(E,nu,exx,eyy,exy=0)",
            "plane_stress(E,nu,exx,eyy,exy=0)",
            "plane_stress_ezz(nu,exx,eyy)",
        ],
        "note": "Stress-state functions return compact objects like {sxx: ..., syy: ..., txy: ...}.",
    },
    {
        "title": "Vectors",
        "items": ["dot(a,b)", "cross(a,b)", "norm(v)", "normalize(v)", "length(v)"],
        "note": "Use vector syntax like v = [1, 2, 3].",
    },
    {
        "title": "Matrices",
        "items": ["A @ B", "det(M)", "inv(M)", "transpose(M)", "trace(M)", "rank(M)", "eig(M)"],
        "note": "Use matrix syntax like A = [[1, 2], [3, 4]]. eig(M) currently supports 1x1 and 2x2.",
    },
    {
        "title": "Builders",
        "items": ["eye(n)", "zeros(m,n)", "ones(m,n)", "shape(M)"],
    },
    {
        "title": "Consts",
        "items": ["pi", "e"],
    },
    {
        "title": "Units",
        "items": ["nm", "um", "mm", "cm", "m", "Pa", "kPa", "MPa", "GPa", "s", "min", "h"],
        "note": "Examples: 10*mm, 210*GPa, 5*min",
    },
    {
        "title": "Comments",
        "items": ["# comment", "// comment"],
        "note": "Inline comments are ignored during evaluation.",
    },
]

GRID_HELP_TITLES = {"Trig", "Math", "Vectors", "Matrices", "Builders", "Consts", "Units"}

NOTEBOOK_EXAMPLES = [
    "v = [1, 2, 3]",
    "A = [[1, 2], [3, 4]]",
    "dot(v, [4, 5, 6])",
    "A @ [[5, 6], [7, 8]]",
    "vm = von_mises(200*MPa, 120*MPa, 0, 40*MPa, 0, 0)",
    "ps = plane_stress(210*GPa, 0.3, 1e-3, 0, 0)",
]


def default_notebook_state() -> dict:
    """Return default notebook state."""
    return {
        "text": "",
        "variables": {},
    }


def build_notebook_results(result_lines: list[str] | None = None) -> list[html.Div]:
    """Build the result gutter lines."""
    result_lines = result_lines or []
    rows = max(NOTEBOOK_ROWS, len(result_lines))
    children = []
    for index in range(rows):
        text = result_lines[index] if index < len(result_lines) else ""
        children.append(
            html.Div(
                text,
                style={
                    "height": NOTEBOOK_LINE_HEIGHT,
                    "lineHeight": NOTEBOOK_LINE_HEIGHT,
                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                    "fontSize": "19px",
                    "fontWeight": "600",
                    "color": "#0b5d52" if text and not text.startswith("Error:") else "#b42318" if text else "#98a2b3",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "paddingLeft": "2px",
                },
                title=text,
            )
        )
    return children


def build_calculation_notebook(state: dict | None = None) -> html.Div:
    """Build the calculation notebook tab content."""
    state = state or default_notebook_state()
    text = state.get("text", "")

    return html.Div(
        [
            html.Div(
                [
                    html.Button(
                        "Clear Notebook",
                        id="notebook-clear-btn",
                        className="graphs-add-panel-btn",
                        n_clicks=0,
                        style={
                            "background": "#0f2942",
                            "border": "1px solid #173b5c",
                            "boxShadow": "none",
                            "padding": "8px 14px",
                            "fontSize": "13px",
                        },
                    ),
                ],
                style={"display": "flex", "gap": "10px", "marginBottom": "10px"},
            ),
            html.Div(
                "Write formulas and assignments on the left. Results appear line by line on the right, variables carry downward, and comments are ignored.",
                style={"fontSize": "13px", "color": "#667085", "marginBottom": "14px"},
            ),
            html.Div(
                [
                    dcc.Textarea(
                        id="notebook-textarea",
                        value=text,
                        placeholder="x = 5\ny = 5\nz = x^2 - y",
                        style={
                            "flex": "1",
                            "height": "76vh",
                            "minHeight": "76vh",
                            "padding": "18px 18px",
                            "fontSize": "20px",
                            "lineHeight": NOTEBOOK_LINE_HEIGHT,
                            "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                            "border": "none",
                            "outline": "none",
                            "resize": "none",
                            "backgroundColor": "transparent",
                            "backgroundImage": "repeating-linear-gradient(to bottom, transparent 0px, transparent 33px, #eef2f6 33px, #eef2f6 34px)",
                            "backgroundPosition": "0 18px",
                            "backgroundAttachment": "local",
                            "color": "#0f172a",
                            "whiteSpace": "pre",
                            "overflowY": "auto",
                        },
                    ),
                    dcc.Input(
                        id="notebook-live-text",
                        type="text",
                        value=text,
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                build_notebook_results([]),
                                id="notebook-results",
                            ),
                            html.Div(
                                id="notebook-debug",
                                style={
                                    "marginTop": "14px",
                                    "paddingTop": "10px",
                                    "borderTop": "1px dashed #d0d5dd",
                                    "fontFamily": "monospace",
                                    "fontSize": "12px",
                                    "color": "#667085",
                                    "whiteSpace": "pre-wrap",
                                },
                            ),
                        ],
                        style={
                            "width": RESULTS_GUTTER_WIDTH,
                            "minWidth": RESULTS_GUTTER_WIDTH,
                            "padding": "18px 14px 18px 8px",
                            "borderLeft": "1px solid rgba(15, 23, 42, 0.045)",
                            "background": "linear-gradient(180deg, rgba(252,253,255,0.78) 0%, rgba(248,250,252,0.68) 100%)",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Functions",
                                style={
                                    "fontSize": "13px",
                                    "fontWeight": "700",
                                    "letterSpacing": "0.04em",
                                    "textTransform": "uppercase",
                                    "color": "#475467",
                                    "marginBottom": "10px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                section["title"],
                                                style={
                                                    "fontSize": "12px",
                                                    "fontWeight": "700",
                                                    "textTransform": "uppercase",
                                                    "letterSpacing": "0.04em",
                                                    "color": "#667085",
                                                    "marginBottom": "8px",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        item,
                                                        style={
                                                            "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                                                            "fontSize": "12px",
                                                            "color": "#102a43",
                                                            "background": "rgba(255,255,255,0.96)",
                                                            "border": "1px solid rgba(226,232,240,0.95)",
                                                            "borderRadius": "999px",
                                                            "padding": "7px 12px",
                                                            "textAlign": "center",
                                                            "boxShadow": "0 1px 2px rgba(15, 23, 42, 0.04)",
                                                        },
                                                    )
                                                    for item in section["items"]
                                                ]
                                                if section["title"] in GRID_HELP_TITLES
                                                else [html.Div(item) for item in section["items"]],
                                                style={
                                                    "display": "grid",
                                                    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                                                    "gap": "8px 8px",
                                                }
                                                if section["title"] in GRID_HELP_TITLES
                                                else {
                                                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                                                    "fontSize": "13px",
                                                    "lineHeight": "1.65",
                                                    "color": "#102a43",
                                                    "background": "rgba(255,255,255,0.55)",
                                                    "border": "1px solid rgba(148,163,184,0.16)",
                                                    "borderRadius": "12px",
                                                    "padding": "8px 10px",
                                                    "display": "grid",
                                                    "gap": "1px",
                                                },
                                            ),
                                            html.Div(
                                                section.get("note", ""),
                                                style={
                                                    "fontSize": "12px",
                                                    "color": "#667085",
                                                    "lineHeight": "1.45",
                                                    "marginTop": "6px",
                                                    "display": "block" if section.get("note") else "none",
                                                },
                                            ),
                                        ],
                                        style={"marginBottom": "12px"},
                                    )
                                    for section in NOTEBOOK_HELP
                                ],
                                style={"display": "grid", "gap": "2px"},
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        "Examples",
                                        style={
                                            "fontSize": "12px",
                                            "fontWeight": "700",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.04em",
                                            "color": "#667085",
                                            "marginTop": "8px",
                                            "marginBottom": "6px",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                example,
                                                style={
                                                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                                                    "fontSize": "13px",
                                                    "color": "#102a43",
                                                    "padding": "4px 0",
                                                },
                                            )
                                            for example in NOTEBOOK_EXAMPLES
                                        ],
                                        style={
                                            "display": "grid",
                                            "gap": "1px",
                                            "background": "rgba(255,255,255,0.55)",
                                            "border": "1px solid rgba(148,163,184,0.16)",
                                            "borderRadius": "12px",
                                            "padding": "8px 10px",
                                        },
                                    ),
                                ]
                            ),
                        ],
                        style={
                            "width": FUNCTIONS_CARD_WIDTH,
                            "minWidth": FUNCTIONS_CARD_WIDTH,
                            "padding": "18px 16px",
                            "borderLeft": "1px solid rgba(15, 23, 42, 0.05)",
                            "background": "linear-gradient(180deg, rgba(244,247,251,0.92) 0%, rgba(238,243,248,0.86) 100%)",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "stretch",
                    "width": "100%",
                    "maxWidth": NOTEBOOK_SHEET_WIDTH,
                    "minHeight": "76vh",
                    "background": "#fffdf8",
                    "border": "1px solid rgba(148, 163, 184, 0.22)",
                    "borderRadius": "18px",
                    "boxShadow": "0 14px 34px rgba(15, 23, 42, 0.06)",
                    "overflow": "hidden",
                    "position": "relative",
                },
            ),
        ],
        style={"padding": "18px 24px", "width": "100%"},
    )
