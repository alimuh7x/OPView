"""
Calculation notebook callback manager for OPView.
"""

from __future__ import annotations

import copy
import json

import base64

from dash import ClientsideFunction, Input, Output, State, ctx, dcc

from .base import BaseCallbackManager
from ui.calculation_notebook import (
    NOTEBOOK_DOWNLOAD_ID,
    NOTEBOOK_SNIPPETS,
    build_notebook_results,
    default_notebook_state,
)
from utils.notebook_eval import evaluate_notebook_rows


class NotebookCallbackManager(BaseCallbackManager):
    """Manage callbacks for the calculation notebook tab."""

    def register(self) -> None:
        self._register_notebook_updates()
        self._register_vars_for_js()
        self._register_side_plot()
        self._register_save_load()
        self._register_insert_example()
        self._register_monaco_sync()
        self._register_fn_panel_toggle()

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
        """Clientside callback: when Dash updates notebook-textarea (insert/load/clear),
        push the new value into the Monaco editor so it stays in sync."""
        self.app.clientside_callback(
            """
            function(value) {
                if (window._syncToMonaco) window._syncToMonaco(value || '');
                return window.dash_clientside.no_update;
            }
            """,
            Output("notebook-monaco-sync-dummy", "data"),
            Input("notebook-textarea", "value"),
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

    def _register_notebook_updates(self):
        @self.app.callback(
            Output("notebook-state", "data"),
            Output("notebook-textarea", "value"),
            Output("notebook-results", "children"),
            Output("notebook-debug", "children"),
            Input("notebook-clear-confirm-provider", "submit_n_clicks"),
            Input("notebook-live-text", "value"),
            State("notebook-state", "data"),
            prevent_initial_call=False,
        )
        def update_notebook(clear_clicks, live_text, notebook_state):
            state = copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            trigger = ctx.triggered_id

            if trigger == "notebook-clear-confirm-provider":
                text = ""
            else:
                text = live_text or ""

            raw_lines = text.splitlines()
            rows = [{"id": f"line_{index}", "expression": line} for index, line in enumerate(raw_lines)]
            evaluated_rows, variables, array_variables = evaluate_notebook_rows(rows)

            result_lines = []
            for row in evaluated_rows:
                if row.get("error"):
                    result_lines.append(f"Error: {row['error']}")
                elif row.get("result"):
                    result_lines.append(f"-> {row['result']}")
                else:
                    result_lines.append("")

            state["text"] = text
            state["variables"] = variables
            state["array_variables"] = array_variables

            debug_lines = [
                f"trigger={trigger}",
                f"live_text_len={len(live_text or '')}",
                f"state_text_len(before)={len((notebook_state or {}).get('text', '') if notebook_state else '')}",
                f"raw_lines={len(raw_lines)}",
                f"result_lines={len(result_lines)}",
                f"variables={sorted(variables.keys())}",
                f"array_variables={sorted(array_variables.keys())}",
                f"text_preview={(text[:120] + '...') if len(text) > 120 else text!r}",
                f"results_preview={result_lines[:5]!r}",
            ]
            print("[NotebookDebug] " + " | ".join(debug_lines))

            return state, text, build_notebook_results(result_lines), "\n".join(debug_lines)

        self._track_callback(update_notebook)

    def _register_side_plot(self):
        """Update the notebook side plot when arrays or variable selection changes."""

        @self.app.callback(
            Output("notebook-side-plot", "figure"),
            Output("nb-plot-x-var", "options"),
            Output("nb-plot-y-vars", "options"),
            Input("notebook-state", "data"),
            Input("nb-plot-x-var", "value"),
            Input("nb-plot-y-vars", "value"),
            Input("nb-plot-type", "value"),
            prevent_initial_call=False,
        )
        def update_side_plot(notebook_state, x_var, y_vars, plot_type):
            import numpy as np
            import plotly.graph_objects as go
            from ui.calculation_notebook import _empty_nb_figure

            nb = notebook_state or {}
            array_vars = nb.get("array_variables", {})
            arr_options = [{"label": k, "value": k} for k in sorted(array_vars)]
            plot_type = plot_type or "lines"

            y_vars = [v for v in (y_vars or []) if v in array_vars]
            if not y_vars:
                return _empty_nb_figure(), arr_options, arr_options

            colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                      "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

            x_data = array_vars.get(x_var) if x_var and x_var in array_vars else None
            x_label = x_var or "index"

            fig = go.Figure()
            for idx, y_name in enumerate(y_vars):
                y_arr = np.asarray(array_vars[y_name])
                color = colors[idx % len(colors)]

                if plot_type == "histogram":
                    fig.add_trace(go.Histogram(
                        x=y_arr,
                        name=y_name,
                        marker_color=color,
                        opacity=0.75,
                    ))
                elif plot_type == "bar":
                    if x_data is not None and len(x_data) == len(y_arr):
                        x_plot = np.asarray(x_data)
                    else:
                        x_plot = list(range(len(y_arr)))
                    fig.add_trace(go.Bar(
                        x=x_plot, y=y_arr,
                        name=y_name,
                        marker_color=color,
                    ))
                else:
                    if x_data is not None and len(x_data) == len(y_arr):
                        x_plot = np.asarray(x_data)
                    else:
                        x_plot = list(range(len(y_arr)))
                    fig.add_trace(go.Scatter(
                        x=x_plot, y=y_arr,
                        mode=plot_type,
                        name=y_name,
                        line=dict(color=color, width=2),
                        marker=dict(color=color, size=6),
                    ))

            x_axis_title = x_label if plot_type != "histogram" else y_vars[0] if len(y_vars) == 1 else "value"
            fig.update_layout(
                xaxis_title=x_axis_title,
                yaxis_title="count" if plot_type == "histogram" else (", ".join(y_vars) if len(y_vars) == 1 else "value"),
                barmode="group" if plot_type == "bar" else None,
                xaxis=dict(showgrid=True, gridcolor="rgba(200,210,220,0.5)", zeroline=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(200,210,220,0.5)", zeroline=False),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=50, r=10, t=30, b=50),
                showlegend=len(y_vars) > 1,
                legend=dict(orientation="v", x=0.01, y=0.99, xanchor="left", yanchor="top"),
            )
            return fig, arr_options, arr_options

        self._track_callback(update_side_plot)

    def _register_save_load(self):
        """Save notebook to .txt and load from .txt."""

        @self.app.callback(
            Output(NOTEBOOK_DOWNLOAD_ID, "data"),
            Input("notebook-save-btn", "n_clicks"),
            State("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def save_notebook(n_clicks, notebook_state):
            text = (notebook_state or {}).get("text", "")
            return dcc.send_string(text, filename="notebook.txt")

        self._track_callback(save_notebook)

        @self.app.callback(
            Output("notebook-textarea", "value", allow_duplicate=True),
            Output("notebook-live-text", "value", allow_duplicate=True),
            Input("notebook-load-upload", "contents"),
            prevent_initial_call=True,
        )
        def load_notebook(contents):
            if not contents:
                from dash import no_update
                return no_update, no_update
            _header, encoded = contents.split(",", 1)
            text = base64.b64decode(encoded).decode("utf-8", errors="replace")
            return text, text

        self._track_callback(load_notebook)

    @staticmethod
    def _parse_side_plot_hint(snippet: str):
        """Extract // Side plot: X=..., Y=..., Type=... from a snippet."""
        import re
        m = re.search(r"//.*?Side plot:\s*(.*)", snippet)
        if not m:
            return None, None, None
        hint = m.group(1)
        xm = re.search(r"X=(\w+)", hint)
        ym = re.search(r"Y=(\w+)", hint)
        tm = re.search(r"Type=(\w+)", hint, re.IGNORECASE)
        return (
            xm.group(1) if xm else None,
            [ym.group(1)] if ym else None,
            tm.group(1).lower() if tm else None,
        )

    def _register_insert_example(self):
        """Load a pre-built snippet example into the notebook textarea."""
        from dash import no_update

        @self.app.callback(
            Output("notebook-textarea", "value", allow_duplicate=True),
            Output("notebook-live-text", "value", allow_duplicate=True),
            Output("nb-plot-x-var", "value", allow_duplicate=True),
            Output("nb-plot-y-vars", "value", allow_duplicate=True),
            Output("nb-plot-type", "value", allow_duplicate=True),
            Input("notebook-insert-example-btn", "n_clicks"),
            State("notebook-example-select", "value"),
            State("notebook-textarea", "value"),
            prevent_initial_call=True,
        )
        def insert_example(n_clicks, selected, current_text):
            if not selected or selected not in NOTEBOOK_SNIPPETS:
                return no_update, no_update, no_update, no_update, no_update
            snippet = NOTEBOOK_SNIPPETS[selected]
            existing = (current_text or "").rstrip()
            if existing:
                new_text = existing + "\n\n" + snippet
            else:
                new_text = snippet
            x_var, y_vars, plot_type = self._parse_side_plot_hint(snippet)
            return (
                new_text,
                new_text,
                x_var if x_var else no_update,
                y_vars if y_vars else no_update,
                plot_type if plot_type else no_update,
            )

        self._track_callback(insert_example)
