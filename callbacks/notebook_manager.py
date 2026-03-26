"""
Calculation notebook callback manager for OPView.
"""

from __future__ import annotations

import copy

from dash import Input, Output, State, ctx

from .base import BaseCallbackManager
from ui.calculation_notebook import build_notebook_results, default_notebook_state
from utils.notebook_eval import evaluate_notebook_rows


class NotebookCallbackManager(BaseCallbackManager):
    """Manage callbacks for the calculation notebook tab."""

    def register(self) -> None:
        self._register_notebook_updates()

    def _register_notebook_updates(self):
        @self.app.callback(
            Output("notebook-state", "data"),
            Output("notebook-textarea", "value"),
            Output("notebook-results", "children"),
            Output("notebook-debug", "children"),
            Input("notebook-clear-btn", "n_clicks"),
            Input("notebook-live-text", "value"),
            State("notebook-state", "data"),
            prevent_initial_call=False,
        )
        def update_notebook(clear_clicks, live_text, notebook_state):
            state = copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            trigger = ctx.triggered_id

            if trigger == "notebook-clear-btn":
                text = ""
            else:
                text = live_text or ""

            raw_lines = text.splitlines()
            rows = [{"id": f"line_{index}", "expression": line} for index, line in enumerate(raw_lines)]
            evaluated_rows, variables = evaluate_notebook_rows(rows)

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

            debug_lines = [
                f"trigger={trigger}",
                f"live_text_len={len(live_text or '')}",
                f"state_text_len(before)={len((notebook_state or {}).get('text', '') if notebook_state else '')}",
                f"raw_lines={len(raw_lines)}",
                f"result_lines={len(result_lines)}",
                f"variables={sorted(variables.keys())}",
                f"text_preview={(text[:120] + '...') if len(text) > 120 else text!r}",
                f"results_preview={result_lines[:5]!r}",
            ]
            print("[NotebookDebug] " + " | ".join(debug_lines))

            return state, text, build_notebook_results(result_lines), "\n".join(debug_lines)

        self._track_callback(update_notebook)
