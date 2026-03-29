"""
Calculation notebook callback manager for OPView.
"""

from __future__ import annotations

import copy
import json
import re

import base64

from dash import ALL, ClientsideFunction, Input, Output, State, ctx, dcc
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager
from ui.calculation_notebook import (
    NOTEBOOK_DOWNLOAD_ID,
    NOTEBOOK_SNIPPETS,
    build_notebook_results,
    default_notebook_state,
)
from utils.notebook_eval import evaluate_notebook_rows


def _auto_update_enabled(value) -> bool:
    """Return True when the notebook auto-update checkbox is enabled."""
    return "auto" in (value or [])


class NotebookCallbackManager(BaseCallbackManager):
    """Manage callbacks for the calculation notebook tab."""

    @staticmethod
    def _result_label(expression: str) -> str:
        raw = (expression or "").strip()
        if not raw:
            return ""
        stripped = raw
        for marker in ("//", "#"):
            idx = stripped.find(marker)
            if idx != -1:
                stripped = stripped[:idx]
        stripped = stripped.strip()
        if not stripped:
            return ""
        if "=" in stripped and not re.search(r"(==|!=|<=|>=)", stripped):
            lhs = stripped.split("=", 1)[0].strip()
            if lhs.isidentifier():
                return lhs
        return stripped

    def register(self) -> None:
        self._register_notebook_updates()
        self._register_auto_update_state()
        self._register_vars_for_js()
        self._register_plots_panel()
        self._register_save_load()
        self._register_insert_example()
        self._register_monaco_sync()
        self._register_monaco_var_decorations()
        self._register_fn_panel_toggle()
        self._register_settings_modal()
        self._register_floating_chat()

    def _register_fn_panel_toggle(self) -> None:
        """Toggle the floating functions reference panel open/closed."""
        self.app.clientside_callback(
            """
            function(open_n, close_n) {
                var panel = document.getElementById('notebook-fn-panel');
                if (!panel) return window.dash_clientside.no_update;
                var ctx = window.dash_clientside.callback_context;
                if (!ctx || !ctx.triggered || ctx.triggered.length === 0)
                    return window.dash_clientside.no_update;
                var trigger_id = ctx.triggered[0].prop_id.split('.')[0];
                if (trigger_id === 'notebook-fn-btn') {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                } else {
                    panel.style.display = 'none';
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output("notebook-fn-dummy", "data"),
            Input("notebook-fn-btn", "n_clicks"),
            Input("notebook-fn-close-btn", "n_clicks"),
            prevent_initial_call=True,
        )

    def _register_monaco_sync(self) -> None:
        """Clientside callback: sync Monaco only on explicit external actions
        (clear / load / insert) via the notebook-external-sync store.
        NOT triggered by normal typing, so Monaco is never accidentally reset."""
        self.app.clientside_callback(
            """
            function(value) {
                if (value !== null && value !== undefined && window._syncToMonaco)
                    window._syncToMonaco(value);
                return window.dash_clientside.no_update;
            }
            """,
            Output("notebook-monaco-sync-dummy", "data"),
            Input("notebook-external-sync", "data"),
            prevent_initial_call=True,
        )

    def _register_monaco_var_decorations(self) -> None:
        """Refresh Monaco variable decorations and inspector from notebook-state."""
        self.app.clientside_callback(
            """
            function(state) {
                if (window._nbRefreshVarsFromState) {
                    window._nbRefreshVarsFromState(state || {});
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output("notebook-var-refresh-dummy", "data"),
            Input("notebook-state", "data"),
            prevent_initial_call=False,
        )

    def _register_vars_for_js(self):
        """Push notebook variable names to a hidden input so JS autocomplete can read them."""
        @self.app.callback(
            Output("notebook-vars-for-js", "value"),
            Input("notebook-state", "data"),
            prevent_initial_call=False,
        )
        def push_vars_to_js(notebook_state):
            state = notebook_state or {}
            names = sorted(set(state.get("variables", {}).keys()) | set(state.get("array_variables", {}).keys()))
            return json.dumps(names)

        self._track_callback(push_vars_to_js)

    def _register_auto_update_state(self):
        """Mirror the auto-update checklist into a simple hidden input for Monaco."""
        @self.app.callback(
            Output("notebook-auto-update-state", "value"),
            Input("notebook-auto-update", "value"),
            prevent_initial_call=False,
        )
        def sync_auto_update_state(value):
            return "on" if _auto_update_enabled(value) else "off"

        self._track_callback(sync_auto_update_state)

    def _register_notebook_updates(self):
        from dash import no_update

        @self.app.callback(
            Output("notebook-state", "data"),
            Output("notebook-textarea", "value"),
            Output("notebook-results", "children"),
            Output("notebook-debug", "children"),
            Output("notebook-external-sync", "data"),
            Input("notebook-run-text", "value"),
            State("notebook-state", "data"),
            prevent_initial_call=False,
        )
        def update_notebook(run_text, notebook_state):
            state = copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            trigger = ctx.triggered_id
            text = run_text or ""
            monaco_sync = no_update  # typing / explicit run — never reset Monaco from server side

            raw_lines = text.splitlines()
            rows = [{"id": f"line_{index}", "expression": line} for index, line in enumerate(raw_lines)]
            evaluated_rows, variables, array_variables = evaluate_notebook_rows(rows)

            result_lines = []
            for row in evaluated_rows:
                if row.get("error"):
                    result_lines.append({
                        "name": self._result_label(str(row.get("expression", "") or "")),
                        "value": f"Error: {row['error']}",
                        "count": "",
                        "error": True,
                    })
                elif row.get("result"):
                    label = self._result_label(str(row.get("expression", "") or ""))
                    result_lines.append({
                        "name": label,
                        "value": row["result"],
                        "count": len(array_variables[label]) if label in array_variables else "",
                        "error": False,
                    })
                else:
                    result_lines.append({"name": "", "value": "", "count": "", "error": False})

            state["text"] = text
            state["variables"] = variables
            state["array_variables"] = array_variables
            state["plot_specs"] = NotebookCallbackManager._parse_plot_calls(text, array_variables, variables)

            debug_lines = [
                f"trigger={trigger}",
                f"run_text_len={len(run_text or '')}",
                f"raw_lines={len(raw_lines)}",
                f"result_lines={len(result_lines)}",
                f"variables={sorted(variables.keys())}",
            ]
            print("[NotebookDebug] " + " | ".join(debug_lines))

            return state, text, build_notebook_results(result_lines), "\n".join(debug_lines), monaco_sync

        self._track_callback(update_notebook)

        @self.app.callback(
            Output("notebook-textarea", "value", allow_duplicate=True),
            Output("notebook-live-text", "value", allow_duplicate=True),
            Output("notebook-run-text", "value", allow_duplicate=True),
            Output("notebook-external-sync", "data", allow_duplicate=True),
            Input("notebook-clear-confirm-provider", "submit_n_clicks"),
            prevent_initial_call=True,
        )
        def clear_notebook(_submit_n_clicks):
            return "", "", "", ""

        self._track_callback(clear_notebook)

    # ── plot() call parsing (Python side) ────────────────────────────────────

    @staticmethod
    def _split_top_level(s: str) -> list:
        depth, current, parts = 0, "", []
        for c in s:
            if c in "([{": depth += 1
            elif c in ")]}": depth -= 1
            if c == "," and depth == 0:
                parts.append(current); current = ""
            else:
                current += c
        if current.strip():
            parts.append(current)
        return parts

    @staticmethod
    def _parse_y_names(arg: str) -> list:
        arg = arg.strip()
        if arg.startswith("["):
            inner = arg[1:arg.rfind("]")]
            return [s.strip() for s in inner.split(",") if s.strip()]
        return [arg] if arg else []

    @classmethod
    def _parse_plot_calls(cls, text: str, array_variables: dict, variables: dict) -> list:
        """Parse plot() calls from notebook text."""
        import re
        specs = []
        for line in text.splitlines():
            if line and line[0] in (" ", "\t"):
                continue  # skip indented block body lines
            raw = line.strip()
            clean = re.sub(r"//.*$", "", raw).strip()
            clean = re.sub(r"#.*$", "", clean).strip()

            # plot(...) call
            m = re.match(r"^plot\s*\((.+)\)$", clean)
            if m:
                args = cls._split_top_level(m.group(1))
                x_var, y_vars, plot_type, title, x_title, y_title = None, [], "lines", None, None, None
                positional = []
                for arg in args:
                    kv = re.match(r"^(\w+)\s*=\s*(.+)$", arg.strip())
                    if kv:
                        k, v = kv.group(1), kv.group(2).strip().strip("\"'")
                        if k == "type":                           plot_type = v
                        elif k == "title":                        title = v
                        elif k in ("xlabel", "x_title"):          x_title = v
                        elif k in ("ylabel", "y_title"):          y_title = v
                    else:
                        positional.append(arg.strip())
                if len(positional) == 1:
                    y_vars = cls._parse_y_names(positional[0])
                elif len(positional) >= 2:
                    x_var = positional[0]
                    y_vars = cls._parse_y_names(positional[1])
                    if len(positional) >= 3:
                        plot_type = positional[2].strip().strip("\"'")
                if y_vars:
                    specs.append(dict(x_var=x_var, y_vars=y_vars, plot_type=plot_type,
                                      title=title, x_title=x_title, y_title=y_title))
                continue

        return specs

    @staticmethod
    def _build_plot_figure(spec: dict, array_vars: dict, font_sz: int, lw: float):
        import numpy as np
        import plotly.graph_objects as go

        x_var = spec.get("x_var")
        y_vars = [v for v in spec.get("y_vars", []) if v in array_vars]
        plot_type = spec.get("plot_type") or "lines"
        x_title = spec.get("x_title") or (x_var or "index")
        y_title = spec.get("y_title") or ("count" if plot_type == "histogram" else
                                           (y_vars[0] if len(y_vars) == 1 else "value"))
        marker_sz = max(4, int(lw * 3))
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                  "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        x_data = array_vars.get(x_var) if x_var and x_var in array_vars else None

        fig = go.Figure()
        for idx, y_name in enumerate(y_vars):
            y_arr = np.asarray(array_vars[y_name])
            color = colors[idx % len(colors)]
            if plot_type == "histogram":
                fig.add_trace(go.Histogram(x=y_arr, name=y_name, marker_color=color, opacity=0.75))
            elif plot_type == "bar":
                x_plot = np.asarray(x_data) if x_data is not None and len(x_data) == len(y_arr) else list(range(len(y_arr)))
                fig.add_trace(go.Bar(x=x_plot, y=y_arr, name=y_name, marker_color=color))
            else:
                x_plot = np.asarray(x_data) if x_data is not None and len(x_data) == len(y_arr) else list(range(len(y_arr)))
                fig.add_trace(go.Scatter(x=x_plot, y=y_arr, mode=plot_type, name=y_name,
                                         line=dict(color=color, width=lw),
                                         marker=dict(color=color, size=marker_sz)))

        fig.update_layout(
            xaxis_title=x_title, yaxis_title=y_title,
            barmode="group" if plot_type == "bar" else None,
            font=dict(size=font_sz, family="'Inter','Segoe UI',system-ui,sans-serif"),
            xaxis=dict(title_font=dict(size=font_sz + 2), tickfont=dict(size=font_sz),
                       showgrid=True, gridcolor="rgba(200,210,220,0.5)",
                       zeroline=True, zerolinecolor="rgba(100,116,139,0.45)", zerolinewidth=2),
            yaxis=dict(title_font=dict(size=font_sz + 2), tickfont=dict(size=font_sz),
                       showgrid=True, gridcolor="rgba(200,210,220,0.5)",
                       zeroline=True, zerolinecolor="rgba(100,116,139,0.45)", zerolinewidth=2),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=60, r=10, t=30, b=60),
            showlegend=len(y_vars) > 1,
            legend=dict(orientation="v", x=0.01, y=0.99, xanchor="left", yanchor="top",
                        font=dict(size=font_sz)),
        )
        return fig

    def _register_plots_panel(self):
        """Render plot() call results as cards in the plots panel."""
        @self.app.callback(
            Output("nb-selector-specs", "data"),
            Input("nb-plot-new-btn", "n_clicks"),
            Input({"type": "nb-plot-card-remove-btn", "index": ALL}, "n_clicks"),
            Input({"type": "nb-plot-card-x", "index": ALL}, "value"),
            Input({"type": "nb-plot-card-y", "index": ALL}, "value"),
            Input({"type": "nb-plot-card-type", "index": ALL}, "value"),
            Input({"type": "nb-plot-card-xlabel", "index": ALL}, "value"),
            Input({"type": "nb-plot-card-ylabel", "index": ALL}, "value"),
            State({"type": "nb-plot-card-x", "index": ALL}, "id"),
            State("nb-selector-specs", "data"),
            prevent_initial_call=True,
        )
        def manage_selector_specs(new_n, remove_clicks, x_values, y_values, type_values, xlabel_values, ylabel_values, x_ids, current_specs):
            from dash import ctx as _ctx

            specs = list(current_specs or [])
            triggered = _ctx.triggered_id

            if triggered == "nb-plot-new-btn":
                next_id = max([spec.get("id", -1) for spec in specs] + [-1]) + 1
                specs.append(dict(
                    id=next_id, x_var=None, y_vars=[], plot_type="lines",
                    title=None, x_title=None, y_title=None,
                ))
                return specs

            if isinstance(triggered, dict) and triggered.get("type") == "nb-plot-card-remove-btn":
                remove_id = triggered.get("index")
                specs = [spec for spec in specs if spec.get("id") != remove_id]
                if not specs:
                    specs = [dict(id=0, x_var=None, y_vars=[], plot_type="lines",
                                  title=None, x_title=None, y_title=None)]
                return specs

            if not x_ids:
                raise PreventUpdate

            rebuilt = []
            for i, id_dict in enumerate(x_ids):
                plot_id = id_dict.get("index")
                rebuilt.append(dict(
                    id=plot_id,
                    x_var=x_values[i] if i < len(x_values) else None,
                    y_vars=(y_values[i] if i < len(y_values) and y_values[i] else []),
                    plot_type=(type_values[i] if i < len(type_values) and type_values[i] else "lines"),
                    title=None,
                    x_title=(xlabel_values[i] or None) if i < len(xlabel_values) else None,
                    y_title=(ylabel_values[i] or None) if i < len(ylabel_values) else None,
                ))
            return rebuilt

        self._track_callback(manage_selector_specs)

        # ── Notebook-driven plots (from plot() calls) — triggered by notebook-state only ──
        @self.app.callback(
            Output("notebook-auto-plots", "children"),
            Input("notebook-state", "data"),
            State("nb-global-font-size", "value"),
            State("nb-global-line-width", "value"),
            prevent_initial_call=False,
        )
        def render_notebook_plots(notebook_state, font_size, line_width):
            from dash import html as _html
            nb = notebook_state or {}
            notebook_specs = list(nb.get("plot_specs", []))
            array_vars = nb.get("array_variables", {})
            font_sz = int(font_size) if font_size else 14
            lw = float(line_width) if line_width is not None else 2.0

            valid_specs = [
                (spec, i) for i, spec in enumerate(notebook_specs)
                if any(v in array_vars for v in spec.get("y_vars", []))
            ]
            cards = []
            for i, (spec, _orig_i) in enumerate(valid_specs):
                y_vars = [v for v in spec.get("y_vars", []) if v in array_vars]
                x_var = spec.get("x_var")
                display_title = spec.get("title") or f"plot({', '.join(filter(None, ([x_var] if x_var else []) + y_vars))})"
                fig = self._build_plot_figure(spec, array_vars, font_sz, lw)
                cards.append(_html.Div(
                    [
                        _html.Div(
                            [
                                _html.Span("📊 ", style={"color": "#001f41"}),
                                _html.Span("Notebook",
                                           style={"fontSize": "10px", "fontWeight": "700",
                                                  "textTransform": "uppercase", "letterSpacing": "0.07em",
                                                  "color": "#001f41", "background": "rgba(0,31,65,0.08)",
                                                  "padding": "2px 6px", "borderRadius": "999px",
                                                  "marginRight": "8px"}),
                                _html.Span(display_title,
                                           style={"fontFamily": "'JetBrains Mono','Fira Code',monospace",
                                                  "fontSize": "12px", "color": "#334155", "fontWeight": "600"}),
                            ],
                            style={"padding": "6px 10px", "background": "rgba(0,31,65,0.04)",
                                   "borderBottom": "1px solid rgba(0,31,65,0.10)",
                                   "borderRadius": "8px 8px 0 0"},
                        ),
                        dcc.Graph(
                            id={"type": "nb-plot-card", "index": i},
                            figure=fig,
                            config={
                                "displayModeBar": True, "scrollZoom": True,
                                "toImageButtonOptions": {"format": "png", "filename": f"plot_{i+1}",
                                                         "height": 900, "width": 1400, "scale": 3},
                            },
                            style={"height": "320px"},
                        ),
                    ],
                    style={"border": "1px solid rgba(0,31,65,0.15)", "borderRadius": "8px",
                           "marginBottom": "12px", "overflow": "hidden",
                           "boxShadow": "0 2px 8px rgba(0,31,65,0.06)"},
                ))
            return cards

        self._track_callback(render_notebook_plots)

        # ── Quick plots (user-created) — triggered by selector-specs only ──
        @self.app.callback(
            Output("notebook-plots-panel", "children"),
            Input("nb-selector-specs", "data"),
            State("notebook-state", "data"),
            State("nb-global-font-size", "value"),
            State("nb-global-line-width", "value"),
            prevent_initial_call=False,
        )
        def render_quick_plots(selector_specs, notebook_state, font_size, line_width):
            from dash import html as _html
            import plotly.graph_objects as _go
            nb = notebook_state or {}
            selector_specs = list(selector_specs or [])
            array_vars = nb.get("array_variables", {})
            options = [{"label": k, "value": k} for k in sorted(array_vars.keys())]
            font_sz = int(font_size) if font_size else 14
            lw = float(line_width) if line_width is not None else 2.0

            def quick_placeholder_figure(message: str):
                fig = _go.Figure()
                fig.update_layout(
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=20, b=20),
                    annotations=[dict(text=message, x=0.5, y=0.5, xref="paper", yref="paper",
                                      showarrow=False,
                                      font=dict(size=13, color="#94a3b8",
                                                family="'Inter','Segoe UI',system-ui,sans-serif"))],
                )
                return fig

            cards = []
            for idx, spec in enumerate(selector_specs, start=1):
                plot_id = spec.get("id", idx - 1)
                y_vars = [v for v in spec.get("y_vars", []) if v in array_vars]
                x_var = spec.get("x_var")
                has_valid_plot = bool(y_vars)
                fig = self._build_plot_figure(spec, array_vars, font_sz, lw) if has_valid_plot else \
                    quick_placeholder_figure("Choose Y to start plotting")

                cards.append(_html.Div(
                    [
                        _html.Div(
                            [
                                _html.Div(
                                    [
                                        _html.Span("📊 ", style={"color": "#7c3aed"}),
                                        _html.Span("Quick",
                                                   style={"fontSize": "10px", "fontWeight": "700",
                                                          "textTransform": "uppercase",
                                                          "letterSpacing": "0.07em", "color": "#7c3aed",
                                                          "background": "rgba(124,58,237,0.10)",
                                                          "padding": "2px 6px", "borderRadius": "999px",
                                                          "marginRight": "8px"}),
                                        _html.Span(f"Quick Plot {idx}",
                                                   style={"fontFamily": "'JetBrains Mono','Fira Code',monospace",
                                                          "fontSize": "12px", "color": "#334155", "fontWeight": "600"}),
                                    ],
                                    style={"display": "flex", "alignItems": "center", "flexWrap": "wrap"},
                                ),
                                _html.Button(
                                    "✕",
                                    id={"type": "nb-plot-card-remove-btn", "index": plot_id},
                                    n_clicks=0,
                                    title="Remove plot card",
                                    style={
                                        "fontSize": "12px", "padding": "2px 7px",
                                        "background": "rgba(239,68,68,0.08)",
                                        "border": "1px solid rgba(239,68,68,0.18)",
                                        "borderRadius": "6px", "cursor": "pointer",
                                        "color": "#dc2626", "fontWeight": "700",
                                    },
                                ),
                            ],
                            style={
                                "padding": "6px 10px",
                                "background": "rgba(124,58,237,0.05)",
                                "borderBottom": "1px solid rgba(124,58,237,0.12)",
                                "display": "flex",
                                "justifyContent": "space-between",
                                "alignItems": "center",
                                "gap": "8px",
                            },
                        ),
                        _html.Div(
                            [
                                _html.Div("X", style={"fontSize": "11px", "fontWeight": "700",
                                                      "color": "#475467", "whiteSpace": "nowrap"}),
                                dcc.Dropdown(
                                    id={"type": "nb-plot-card-x", "index": plot_id},
                                    placeholder="x axis (opt.)",
                                    options=options,
                                    value=x_var,
                                    clearable=True,
                                    style={"fontSize": "12px", "flex": "1 1 90px", "minWidth": "84px"},
                                ),
                                _html.Div("Y", style={"fontSize": "11px", "fontWeight": "700",
                                                      "color": "#475467", "whiteSpace": "nowrap"}),
                                dcc.Dropdown(
                                    id={"type": "nb-plot-card-y", "index": plot_id},
                                    placeholder="y variable(s)",
                                    options=options,
                                    value=spec.get("y_vars") or [],
                                    multi=True,
                                    style={"fontSize": "12px", "flex": "2 1 120px", "minWidth": "100px"},
                                ),
                                dcc.Dropdown(
                                    id={"type": "nb-plot-card-type", "index": plot_id},
                                    options=[
                                        {"label": "Lines", "value": "lines"},
                                        {"label": "Markers", "value": "markers"},
                                        {"label": "L+M", "value": "lines+markers"},
                                        {"label": "Bar", "value": "bar"},
                                        {"label": "Hist", "value": "histogram"},
                                    ],
                                    value=spec.get("plot_type") or "lines",
                                    clearable=False,
                                    style={"fontSize": "12px", "flex": "0 0 95px", "minWidth": "90px"},
                                ),
                            ],
                            style={
                                "display": "flex", "alignItems": "center", "flexWrap": "wrap",
                                "gap": "6px", "padding": "10px", "borderBottom": "1px solid rgba(124,58,237,0.10)",
                                "background": "rgba(248,250,252,0.7)",
                            },
                        ),
                        _html.Div(
                            [
                                _html.Div("X label", style={"fontSize": "11px", "fontWeight": "700",
                                                             "color": "#475467", "whiteSpace": "nowrap"}),
                                dcc.Input(
                                    id={"type": "nb-plot-card-xlabel", "index": plot_id},
                                    type="text",
                                    placeholder="X axis title…",
                                    value=spec.get("x_title") or "",
                                    debounce=True,
                                    style={"fontSize": "12px", "flex": "1 1 100px", "minWidth": "80px",
                                           "padding": "4px 8px", "borderRadius": "6px",
                                           "border": "1px solid #e2e8f0", "outline": "none"},
                                ),
                                _html.Div("Y label", style={"fontSize": "11px", "fontWeight": "700",
                                                             "color": "#475467", "whiteSpace": "nowrap",
                                                             "marginLeft": "10px"}),
                                dcc.Input(
                                    id={"type": "nb-plot-card-ylabel", "index": plot_id},
                                    type="text",
                                    placeholder="Y axis title…",
                                    value=spec.get("y_title") or "",
                                    debounce=True,
                                    style={"fontSize": "12px", "flex": "1 1 100px", "minWidth": "80px",
                                           "padding": "4px 8px", "borderRadius": "6px",
                                           "border": "1px solid #e2e8f0", "outline": "none"},
                                ),
                            ],
                            style={
                                "display": "flex", "alignItems": "center", "flexWrap": "wrap",
                                "gap": "6px", "padding": "8px 10px",
                                "borderBottom": "1px solid rgba(124,58,237,0.10)",
                                "background": "rgba(248,250,252,0.4)",
                            },
                        ),
                        dcc.Graph(
                            id={"type": "nb-plot-card", "index": f"quick-{plot_id}"},
                            figure=fig,
                            config={
                                "displayModeBar": True,
                                "scrollZoom": True,
                                "toImageButtonOptions": {
                                    "format": "png", "filename": f"quick_plot_{idx}",
                                    "height": 900, "width": 1400, "scale": 3,
                                },
                            },
                            style={"height": "320px"},
                        ),
                    ],
                    style={
                        "border": "1px solid rgba(124,58,237,0.18)",
                        "borderRadius": "8px",
                        "marginBottom": "12px",
                        "overflow": "hidden",
                        "boxShadow": "0 2px 8px rgba(124,58,237,0.06)",
                    },
                ))
            return cards

        self._track_callback(render_quick_plots)

        # ── Update dropdown options when notebook variables change (no re-render, no value change) ──
        @self.app.callback(
            Output({"type": "nb-plot-card-x", "index": ALL}, "options"),
            Output({"type": "nb-plot-card-y", "index": ALL}, "options"),
            Input("notebook-state", "data"),
            State({"type": "nb-plot-card-x", "index": ALL}, "id"),
            prevent_initial_call=True,
        )
        def update_quick_plot_options(notebook_state, x_ids):
            if not x_ids:
                raise PreventUpdate
            nb = notebook_state or {}
            array_vars = nb.get("array_variables", {})
            options = [{"label": k, "value": k} for k in sorted(array_vars.keys())]
            return [options] * len(x_ids), [options] * len(x_ids)

        self._track_callback(update_quick_plot_options)

        # ── Update only figures when font/linewidth changes (no structural re-render) ──
        @self.app.callback(
            Output({"type": "nb-plot-card", "index": ALL}, "figure"),
            Input("nb-global-font-size", "value"),
            Input("nb-global-line-width", "value"),
            State("notebook-state", "data"),
            State("nb-selector-specs", "data"),
            State({"type": "nb-plot-card", "index": ALL}, "id"),
            prevent_initial_call=True,
        )
        def update_figures_on_settings(font_size, line_width, notebook_state, selector_specs, graph_ids):
            if not graph_ids:
                raise PreventUpdate
            nb = notebook_state or {}
            notebook_specs = list(nb.get("plot_specs", []))
            selector_specs = list(selector_specs or [])
            array_vars = nb.get("array_variables", {})
            font_sz = int(font_size) if font_size else 14
            lw = float(line_width) if line_width is not None else 2.0

            valid_notebook_specs = [
                (spec, True) for spec in notebook_specs
                if any(v in array_vars for v in spec.get("y_vars", []))
            ]
            spec_by_quick_id = {spec.get("id"): spec for spec in selector_specs}

            from dash import no_update as _nu
            figures = []
            for id_dict in graph_ids:
                idx = id_dict.get("index")
                if isinstance(idx, str) and idx.startswith("quick-"):
                    plot_id = int(idx.split("-")[1])
                    spec = spec_by_quick_id.get(plot_id)
                    if spec and any(v in array_vars for v in spec.get("y_vars", [])):
                        figures.append(self._build_plot_figure(spec, array_vars, font_sz, lw))
                    else:
                        figures.append(_nu)
                else:
                    i = int(idx) if idx is not None else -1
                    if 0 <= i < len(valid_notebook_specs):
                        spec, _ = valid_notebook_specs[i]
                        figures.append(self._build_plot_figure(spec, array_vars, font_sz, lw))
                    else:
                        figures.append(_nu)
            return figures

        self._track_callback(update_figures_on_settings)

    def _register_save_load(self):
        """Save notebook to .txt and load from .txt."""

        @self.app.callback(
            Output(NOTEBOOK_DOWNLOAD_ID, "data"),
            Input("notebook-save-btn", "n_clicks"),
            State("notebook-live-text", "value"),
            State("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def save_notebook(n_clicks, live_text, notebook_state):
            text = live_text if live_text is not None else (notebook_state or {}).get("text", "")
            return dcc.send_string(text, filename="notebook.txt")

        self._track_callback(save_notebook)

        @self.app.callback(
            Output("notebook-textarea", "value", allow_duplicate=True),
            Output("notebook-live-text", "value", allow_duplicate=True),
            Output("notebook-run-text", "value", allow_duplicate=True),
            Output("notebook-external-sync", "data", allow_duplicate=True),
            Input("notebook-load-upload", "contents"),
            prevent_initial_call=True,
        )
        def load_notebook(contents):
            if not contents:
                from dash import no_update
                return no_update, no_update, no_update, no_update
            _header, encoded = contents.split(",", 1)
            text = base64.b64decode(encoded).decode("utf-8", errors="replace")
            return text, text, text, text

        self._track_callback(load_notebook)

    def _register_insert_example(self):
        """Load a pre-built snippet example into the notebook textarea."""
        from dash import no_update

        @self.app.callback(
            Output("notebook-textarea", "value", allow_duplicate=True),
            Output("notebook-live-text", "value", allow_duplicate=True),
            Output("notebook-run-text", "value", allow_duplicate=True),
            Output("notebook-external-sync", "data", allow_duplicate=True),
            Input("notebook-insert-example-btn", "n_clicks"),
            State("notebook-example-select", "value"),
            State("notebook-live-text", "value"),
            prevent_initial_call=True,
        )
        def insert_example(n_clicks, selected, current_text):
            if not selected or selected not in NOTEBOOK_SNIPPETS:
                return no_update, no_update, no_update, no_update
            snippet = NOTEBOOK_SNIPPETS[selected]
            existing = (current_text or "").rstrip()
            new_text = existing + "\n\n" + snippet if existing else snippet
            return new_text, new_text, new_text, new_text

        self._track_callback(insert_example)

    def _register_settings_modal(self):
        """Open/close AI settings modal and save API key to ~/.opview_settings.json."""
        import os
        from dash import no_update
        from config.settings_store import save as _settings_save, apply_env as _apply_env

        # Open modal
        @self.app.callback(
            Output("nb-settings-modal", "style"),
            Output("nb-settings-provider", "value"),
            Output("nb-settings-apikey", "value"),
            Output("nb-settings-apikey", "placeholder"),
            Output("nb-settings-key-label", "children"),
            Input("nb-settings-open-btn", "n_clicks"),
            Input("nb-settings-close-btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def toggle_modal(open_clicks, close_clicks):
            from dash import ctx as _ctx
            from config.settings_store import load as _load
            _visible = {"display": "flex", "position": "fixed", "inset": "0",
                        "background": "rgba(0,0,0,0.45)", "zIndex": "9999",
                        "justifyContent": "center", "alignItems": "center"}
            _hidden  = {"display": "none"}
            if _ctx.triggered_id == "nb-settings-open-btn":
                settings = _load()
                provider = settings.get("AI_PROVIDER", "anthropic")
                key_map = {
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openai":    "OPENAI_API_KEY",
                    "gemini":    "GEMINI_API_KEY",
                }
                if provider == "github":
                    return _visible, provider, "", "Auto-detected from gh auth token", "GitHub PAT (optional)"
                key = settings.get(key_map.get(provider, "ANTHROPIC_API_KEY"), "")
                return _visible, provider, key, "Paste your API key here…", "API Key"
            return _hidden, no_update, no_update, no_update, no_update

        self._track_callback(toggle_modal)

        # Save settings
        @self.app.callback(
            Output("nb-settings-status", "children"),
            Output("nb-settings-modal", "style", allow_duplicate=True),
            Input("nb-settings-save-btn", "n_clicks"),
            State("nb-settings-provider", "value"),
            State("nb-settings-apikey", "value"),
            prevent_initial_call=True,
        )
        def save_settings(n_clicks, provider, api_key):
            if provider != "github" and (not api_key or not api_key.strip()):
                return "Enter an API key first.", no_update
            _hidden = {"display": "none"}
            key = api_key.strip()
            all_keys = {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": "",
                        "GEMINI_API_KEY": "", "GITHUB_TOKEN": ""}
            key_map = {"anthropic": "ANTHROPIC_API_KEY",
                       "openai":    "OPENAI_API_KEY",
                       "gemini":    "GEMINI_API_KEY",
                       "github":    "GITHUB_TOKEN"}
            env_key = key_map.get(provider, "ANTHROPIC_API_KEY")
            all_keys[env_key] = key  # may be empty for github (uses gh auth token)
            all_keys["AI_PROVIDER"] = provider
            _settings_save(all_keys)
            # Update env vars
            for k, v in all_keys.items():
                if k == "AI_PROVIDER":
                    continue
                if v:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
            return "Saved.", _hidden

        self._track_callback(save_settings)

    def _register_floating_chat(self):
        """Global floating AI chat widget — toggle, user bubble, clear."""
        import re
        from dash import html, no_update

        _placeholder = [html.Div("Ask me anything…", className="fchat-placeholder")]

        def _fchat_render_history(history, ts_base):
            """Render history as DOM items for floating chat."""
            items = []
            for msg in (history or []):
                is_user = msg["role"] == "user"
                bubble_cls = "fchat-bubble-user" if is_user else "fchat-bubble-ai"
                items.append(html.Div(msg["content"], className=bubble_cls))
            return items

        # Toggle is handled entirely by JS (see notebook_live_sync.js watchFChatToggle)
        # No Python round-trip needed for open/close.

        # ── Show user bubble immediately + set pending ─────────────────────
        @self.app.callback(
            Output("fchat-messages", "children"),
            Output("fchat-pending", "value"),
            Output("fchat-input", "value"),
            Input("fchat-send-btn", "n_clicks"),
            Input("fchat-input", "n_submit"),
            Input("fchat-clear-btn", "n_clicks"),
            State("fchat-input", "value"),
            State("fchat-history", "value"),
            State("fchat-send-btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def fchat_show_user(send_n, n_submit, clear_n, user_input, history_json, ts):
            from dash import ctx as _ctx
            import json as _json
            if _ctx.triggered_id == "fchat-clear-btn":
                return _placeholder, "", ""
            if not user_input or not user_input.strip():
                raise PreventUpdate
            user_text = user_input.strip()
            history = _json.loads(history_json or "[]")
            items = _fchat_render_history(history, ts or 0)
            items.append(html.Div(user_text, className="fchat-bubble-user"))
            items.append(html.Div("…", **{"data-thinking": "1"},
                                  className="fchat-thinking"))
            return items, _json.dumps({"text": user_text, "ts": ts or 0}), ""

        self._track_callback(fchat_show_user)

        # ── Clear history ─────────────────────────────────────────────────
        @self.app.callback(
            Output("fchat-history", "value", allow_duplicate=True),
            Output("fchat-code-map", "value", allow_duplicate=True),
            Input("fchat-clear-btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def fchat_clear(n):
            return "[]", "{}"

        self._track_callback(fchat_clear)
