"""
Calculation notebook callback manager for OPView.
"""

from __future__ import annotations

import copy
import json
import re

import base64
import numpy as np

from dash import ALL, ClientsideFunction, Input, Output, State, ctx, dcc
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager
from ui.calculation_notebook import (
    NOTEBOOK_DOWNLOAD_ID,
    NOTEBOOK_SNIPPETS,
    build_notebook_results,
    build_cells_for_column,
    default_notebook_state,
    default_notebook_cell,
    default_cell,
    new_cell_id,
)
from utils.notebook_eval import evaluate_notebook_rows, evaluate_cell
from utils.notebook_persistence import deserialize_notebook_cells, serialize_notebook_cells


def _auto_update_enabled(value) -> bool:
    """Return True when the notebook auto-update checkbox is enabled."""
    return "auto" in (value or [])


class NotebookCallbackManager(BaseCallbackManager):
    """Manage callbacks for the calculation notebook tab."""

    @staticmethod
    def _find_example_target_cell(cells: list[dict]) -> dict | None:
        """Prefer inserting examples into an empty code cell before markdown."""
        empty_code = next(
            (c for c in cells if c.get("type") == "code" and not (c.get("source", "") or "").strip()),
            None,
        )
        if empty_code is not None:
            return empty_code
        return next((c for c in cells if not (c.get("source", "") or "").strip()), None)

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

    @staticmethod
    def _is_control_flow_row(expression: str) -> bool:
        expression = str(expression or "").lstrip()
        return bool(re.match(r"^(for|if|elif|else)\b", expression))

    @staticmethod
    def _inline_matrix_payload(value) -> dict | None:
        try:
            matrix = np.asarray(value, dtype=float)
        except (TypeError, ValueError):
            return None
        if matrix.ndim != 2:
            return None
        rows, cols = matrix.shape
        if rows == 0 or cols == 0 or rows > 6 or cols > 6:
            return None
        return {
            "kind": "matrix",
            "matrix": [[NotebookCallbackManager._format_matrix_number(v) for v in row] for row in matrix.tolist()],
            "row_span": rows,
            "shape": f"{rows}x{cols}",
        }

    @staticmethod
    def _format_matrix_number(value: float) -> str:
        f = float(value)
        if not np.isfinite(f):
            return str(f)
        if f == int(f) and abs(f) < 1e15:
            return str(int(f))
        return f"{f:.3g}"

    def register(self) -> None:
        self._register_notebook_updates()
        self._register_cell_ops()
        self._register_markdown_preview()
        self._register_md_panel_toggle()
        self._register_auto_update_state()
        self._register_vars_for_js()
        self._register_plots_panel()
        self._register_save_load()
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

    def _register_markdown_preview(self) -> None:
        """Switch markdown cells explicitly between preview and edit modes."""
        self.app.clientside_callback(
            """
            function(preview_n_clicks_list, edit_n_clicks_list) {
                var ctx = window.dash_clientside.callback_context;
                if (!ctx || !ctx.triggered || !ctx.triggered.length) return window.dash_clientside.no_update;
                var trig = ctx.triggered[0];
                if (trig.value === 0 || trig.value === null) return window.dash_clientside.no_update;
                var trigger = trig.prop_id;
                var m = trigger.match(/"index"\\s*:\\s*"([^"]+)"/);
                if (!m) return window.dash_clientside.no_update;
                var cellId = m[1];
                if (trigger.indexOf('"type":"nb-cell-edit"') !== -1) {
                    if (!window._showMarkdownEditor) return window.dash_clientside.no_update;
                    window._showMarkdownEditor(cellId);
                    return window.dash_clientside.no_update;
                }
                if (window._renderMarkdownCell && window._cellEditors && window._cellEditors[cellId]) {
                    var source = window._cellEditors[cellId].getValue();
                    window._renderMarkdownCell(cellId, source);
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output("notebook-markdown-preview-dummy", "data"),
            Input({"type": "nb-cell-preview", "index": ALL}, "n_clicks"),
            Input({"type": "nb-cell-edit", "index": ALL}, "n_clicks"),
            prevent_initial_call=True,
        )

    def _register_md_panel_toggle(self) -> None:
        """Toggle the markdown help panel open/closed."""
        self.app.clientside_callback(
            """
            function(open_n, close_n) {
                var panel = document.getElementById('notebook-md-panel');
                if (!panel) return window.dash_clientside.no_update;
                var ctx = window.dash_clientside.callback_context;
                if (!ctx || !ctx.triggered || ctx.triggered.length === 0) {
                    return window.dash_clientside.no_update;
                }
                var trigger_id = ctx.triggered[0].prop_id.split('.')[0];
                if (trigger_id === 'notebook-md-help-btn') {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                } else {
                    panel.style.display = 'none';
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output("notebook-md-panel-dummy", "data"),
            Input("notebook-md-help-btn", "n_clicks"),
            Input("notebook-md-close-btn", "n_clicks"),
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
                if (window._nbApplyInlineResultZones) {
                    window._nbApplyInlineResultZones(state || {});
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

            result_lines = self._build_result_lines(evaluated_rows, array_variables)
            execution_blocks = self._build_execution_blocks(evaluated_rows, array_variables)

            state["text"] = text
            state["variables"] = variables
            state["array_variables"] = array_variables
            state["execution_blocks"] = execution_blocks
            state["plot_specs"] = NotebookCallbackManager._parse_plot_calls(text, array_variables, variables)

            return state, text, build_notebook_results(result_lines), monaco_sync

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

    # ── Cell-based notebook operations ───────────────────────────────────────

    def _register_cell_ops(self):
        """Register all cell-level callbacks: run, add, delete, move, render."""
        from dash import no_update, html as _html
        import copy as _copy

        # ── 1. Render cells container from store ─────────────────────────────
        @self.app.callback(
            Output("notebook-cells-column-left", "children"),
            Output("notebook-cells-column-right", "children"),
            Input("notebook-cells-store", "data"),
            prevent_initial_call=True,
        )
        def render_cells(cells_data):
            cells = cells_data or [default_notebook_cell()]
            return build_cells_for_column(cells, "left"), build_cells_for_column(cells, "right")

        self._track_callback(render_cells)

        # ── 2. Sync Monaco sources → store BEFORE structural ops ─────────────
        #    This clientside callback fires first, collecting Monaco values,
        #    then structural callbacks fire using nb-op-sync as Input.
        self.app.clientside_callback(
            """
            function() {
                var ctx = window.dash_clientside.callback_context;
                if (!ctx.triggered || ctx.triggered.length === 0) {
                    return window.dash_clientside.no_update;
                }
                var t = ctx.triggered[0];
                // Ignore re-mount fires: buttons initialise with n_clicks=0,
                // which Dash fires as a change when inserter strips are re-rendered.
                if (t.value === 0 || t.value === null) {
                    return window.dash_clientside.no_update;
                }
                var sources = {};
                if (window._cellEditors) {
                    Object.keys(window._cellEditors).forEach(function(id) {
                        try { sources[id] = window._cellEditors[id].getValue(); } catch(e) {}
                    });
                }
                return {sources: sources, trigger: t.prop_id, ts: Date.now()};
            }
            """,
            Output("nb-op-sync", "data"),
            Input({"type": "nb-add-code",        "index": ALL}, "n_clicks"),
            Input({"type": "nb-add-markdown",    "index": ALL}, "n_clicks"),
            Input({"type": "nb-add-plot",        "index": ALL}, "n_clicks"),
            Input({"type": "nb-cell-delete",     "index": ALL}, "n_clicks"),
            Input({"type": "nb-cell-up",         "index": ALL}, "n_clicks"),
            Input({"type": "nb-cell-down",       "index": ALL}, "n_clicks"),
            Input({"type": "nb-cell-move-left",  "index": ALL}, "n_clicks"),
            Input({"type": "nb-cell-move-right", "index": ALL}, "n_clicks"),
            Input("notebook-clear-confirm-provider", "submit_n_clicks"),
            Input("notebook-insert-example-btn", "n_clicks"),
            prevent_initial_call=True,
        )

        # ── 3. Structural ops: use nb-op-sync as Input ───────────────────────
        @self.app.callback(
            Output("notebook-cells-store", "data"),
            Output("notebook-state", "data", allow_duplicate=True),
            Input("nb-op-sync", "data"),
            State("notebook-cells-store", "data"),
            State("notebook-state", "data"),
            State("notebook-example-select", "value"),
            prevent_initial_call=True,
        )
        def handle_structural_op(op_sync, cells, notebook_state, selected_snippet):
            if not op_sync:
                raise PreventUpdate
            trigger = op_sync.get("trigger", "") or ""
            sources = op_sync.get("sources", {}) or {}
            cells = _copy.deepcopy(cells or [default_notebook_cell()])

            # Apply latest Monaco sources to cells
            for cell in cells:
                cid = cell["id"]
                if cid in sources:
                    cell["source"] = sources[cid]

            # Parse trigger to determine action and which cell_id
            # trigger format: '{"index":"cell-xxx","type":"nb-add-code"}.n_clicks'
            action = None
            target_cell_id = None

            if '"type":"nb-add-code"' in trigger or '"type": "nb-add-code"' in trigger:
                action = "add-code"
            elif '"type":"nb-add-markdown"' in trigger or '"type": "nb-add-markdown"' in trigger:
                action = "add-markdown"
            elif '"type":"nb-add-plot"' in trigger or '"type": "nb-add-plot"' in trigger:
                action = "add-plot"
            elif '"type":"nb-cell-delete"' in trigger or '"type": "nb-cell-delete"' in trigger:
                action = "delete"
            elif '"type":"nb-cell-up"' in trigger or '"type": "nb-cell-up"' in trigger:
                action = "move-up"
            elif '"type":"nb-cell-down"' in trigger or '"type": "nb-cell-down"' in trigger:
                action = "move-down"
            elif '"type":"nb-cell-move-left"' in trigger or '"type": "nb-cell-move-left"' in trigger:
                action = "move-left"
            elif '"type":"nb-cell-move-right"' in trigger or '"type": "nb-cell-move-right"' in trigger:
                action = "move-right"
            elif "notebook-clear-confirm-provider" in trigger:
                action = "clear"
            elif "notebook-insert-example-btn" in trigger:
                action = "insert-example"

            # Extract cell id from trigger string
            import re as _re
            m = _re.search(r'"index"\s*:\s*"([^"]+)"', trigger)
            if m:
                target_cell_id = m.group(1)

            if action == "clear":
                new_cells = [default_notebook_cell()]
                new_state = default_notebook_state()
                new_state["cells"] = new_cells
                return new_cells, new_state

            if action == "insert-example":
                if selected_snippet and selected_snippet in NOTEBOOK_SNIPPETS:
                    snippet = NOTEBOOK_SNIPPETS[selected_snippet]
                    if selected_snippet == "Quick Start":
                        intro_cell = default_cell(cell_type="markdown", source=(
                            "# Quick Start\n"
                            "Run one expression per line. Results appear on the right.\n"
                            "Use Shift+Enter or Run, then edit these examples or add your own markdown and code cells."
                        ))
                        code_cell = default_cell(cell_type="code", source=snippet)
                        cells = []
                        cells.extend([intro_cell, code_cell])
                    else:
                        empty_cell = NotebookCallbackManager._find_example_target_cell(cells)
                        if empty_cell is not None:
                            empty_cell["type"] = "code"
                            empty_cell["source"] = snippet
                            empty_cell["outputs"] = []
                            empty_cell["dirty"] = False
                        else:
                            cells.append(default_cell(source=snippet))
                nb_state = _copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
                nb_state["cells"] = cells
                return cells, nb_state

            cell_ids = [c["id"] for c in cells]

            if action in ("add-code", "add-markdown", "add-plot") and target_cell_id == "__start__":
                cell_type = "code" if action == "add-code" else "markdown" if action == "add-markdown" else "plot"
                new_c = default_cell(cell_type=cell_type)
                cells.insert(0, new_c)

            elif action in ("add-code", "add-markdown", "add-plot") and target_cell_id:
                cell_type = "code" if action == "add-code" else "markdown" if action == "add-markdown" else "plot"
                new_c = default_cell(cell_type=cell_type)
                try:
                    idx = cell_ids.index(target_cell_id)
                    cells.insert(idx + 1, new_c)
                except ValueError:
                    cells.append(new_c)

            elif action == "delete" and target_cell_id:
                cells = [c for c in cells if c["id"] != target_cell_id]
                if not cells:
                    cells = [default_notebook_cell()]

            elif action == "move-up" and target_cell_id:
                try:
                    idx = cell_ids.index(target_cell_id)
                    if idx > 0:
                        cells[idx - 1], cells[idx] = cells[idx], cells[idx - 1]
                except ValueError:
                    pass

            elif action == "move-down" and target_cell_id:
                try:
                    idx = cell_ids.index(target_cell_id)
                    if idx < len(cells) - 1:
                        cells[idx], cells[idx + 1] = cells[idx + 1], cells[idx]
                except ValueError:
                    pass

            elif action == "move-left" and target_cell_id:
                for cell in cells:
                    if cell["id"] == target_cell_id:
                        cell["column"] = "left"
                        break

            elif action == "move-right" and target_cell_id:
                for cell in cells:
                    if cell["id"] == target_cell_id:
                        cell["column"] = "right"
                        break

            # Rebuild accumulated state
            nb_state = _copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            nb_state["cells"] = cells
            return cells, nb_state

        self._track_callback(handle_structural_op)

        # ── 4. Run a single cell ──────────────────────────────────────────────
        self.app.clientside_callback(
            r"""
            function() {
                var ctx = window.dash_clientside.callback_context;
                var trigger = ctx.triggered && ctx.triggered.length > 0
                    ? ctx.triggered[0].prop_id : null;
                if (!trigger) return window.dash_clientside.no_update;
                var m = trigger.match(/"index"\s*:\s*"([^"]+)"/);
                var cellId = m ? m[1] : null;
                if (!cellId) return window.dash_clientside.no_update;
                var source = '';
                if (window._cellEditors && window._cellEditors[cellId]) {
                    source = window._cellEditors[cellId].getValue();
                }
                return {cell_id: cellId, source: source, ts: Date.now()};
            }
            """,
            Output("nb-cell-run-trigger", "data"),
            Input({"type": "nb-cell-run", "index": ALL}, "n_clicks"),
            Input("notebook-run-btn", "n_clicks"),
            prevent_initial_call=True,
        )

        @self.app.callback(
            Output("notebook-state", "data", allow_duplicate=True),
            Output({"type": "nb-cell-results", "index": ALL}, "children"),
            Input("nb-cell-run-trigger", "data"),
            State("notebook-cells-store", "data"),
            State("notebook-state", "data"),
            State({"type": "nb-cell-results", "index": ALL}, "id"),
            prevent_initial_call=True,
        )
        def run_cell_callback(trigger_data, cells, notebook_state, result_ids):
            if not trigger_data:
                raise PreventUpdate

            trigger_cell_id = trigger_data.get("cell_id")
            trigger_source  = trigger_data.get("source", "")

            cells = cells or [default_notebook_cell()]
            nb_state = _copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()

            # Build accumulated context top-to-bottom
            all_scalars: dict = {}
            all_arrays: dict  = {}
            all_full: dict    = {}

            cells_updated = _copy.deepcopy(cells)

            if trigger_cell_id:
                # Run only from start to this cell (to get correct context)
                found = False
                for cell in cells_updated:
                    cid = cell["id"]
                    if cell.get("type") != "code":
                        continue
                    source = trigger_source if cid == trigger_cell_id else cell.get("source", "")
                    result_rows, sv, av, fv = evaluate_cell(source, context=dict(all_full))
                    # Update accumulated context
                    all_full.update(fv)
                    all_scalars.update(sv)
                    all_arrays.update(av)
                    # Build result lines for this cell
                    result_lines = self._build_result_lines(result_rows, av)
                    cell["outputs"] = result_lines
                    cell["execution_blocks"] = self._build_execution_blocks(result_rows, av)
                    cell["dirty"] = False
                    if cid == trigger_cell_id:
                        found = True
                        break
                if not found:
                    raise PreventUpdate
            else:
                # Run all cells (triggered by "Run All" button)
                for cell in cells_updated:
                    if cell.get("type") != "code":
                        continue
                    source = cell.get("source", "")
                    result_rows, sv, av, fv = evaluate_cell(source, context=dict(all_full))
                    all_full.update(fv)
                    all_scalars.update(sv)
                    all_arrays.update(av)
                    result_lines = self._build_result_lines(result_rows, av)
                    cell["outputs"] = result_lines
                    cell["execution_blocks"] = self._build_execution_blocks(result_rows, av)
                    cell["dirty"] = False

            # Update notebook state
            nb_state["variables"] = all_scalars
            nb_state["array_variables"] = all_arrays
            nb_state["cells"] = cells_updated
            # Rebuild plot specs from all cells combined
            all_text = "\n".join(c.get("source", "") for c in cells_updated if c.get("type") == "code")
            nb_state["plot_specs"] = NotebookCallbackManager._parse_plot_calls(all_text, all_arrays, all_scalars)

            # Build outputs for all result divs
            outputs = []
            for id_dict in result_ids:
                cid = id_dict.get("index")
                cell_match = next((c for c in cells_updated if c["id"] == cid), None)
                if cell_match:
                    outputs.append(build_notebook_results(cell_match.get("outputs", [])))
                else:
                    outputs.append(no_update)

            return nb_state, outputs

        self._track_callback(run_cell_callback)

        # ── 5. Auto-run active cell on Monaco change ──────────────────────────
        #    Uses existing notebook-run-text textarea mechanism with per-cell IDs.
        #    JS pushes to {"type":"nb-cell-text","index":cell_id} on change.
        @self.app.callback(
            Output("notebook-state", "data", allow_duplicate=True),
            Output({"type": "nb-cell-results", "index": ALL}, "children", allow_duplicate=True),
            Input({"type": "nb-cell-text", "index": ALL}, "value"),
            State("notebook-cells-store", "data"),
            State("notebook-state", "data"),
            State({"type": "nb-cell-results", "index": ALL}, "id"),
            State({"type": "nb-cell-text", "index": ALL}, "id"),
            prevent_initial_call=True,
        )
        def auto_run_cell(text_values, cells, notebook_state, result_ids, text_ids):
            if not text_values or not text_ids:
                raise PreventUpdate
            from dash import ctx as _ctx
            triggered = _ctx.triggered_id
            if not triggered or not isinstance(triggered, dict):
                raise PreventUpdate

            trigger_cell_id = triggered.get("index")
            # Find source for triggered cell
            trigger_source = ""
            for id_dict, val in zip(text_ids, text_values):
                if id_dict.get("index") == trigger_cell_id:
                    trigger_source = val or ""
                    break

            cells = cells or [default_notebook_cell()]
            nb_state = _copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()

            # Evaluate from start up to and including the changed cell
            all_full: dict = {}
            all_scalars: dict = {}
            all_arrays: dict  = {}
            cells_updated = _copy.deepcopy(cells)

            for cell in cells_updated:
                cid = cell["id"]
                if cell.get("type") != "code":
                    continue
                source = trigger_source if cid == trigger_cell_id else cell.get("source", "")
                result_rows, sv, av, fv = evaluate_cell(source, context=dict(all_full))
                all_full.update(fv)
                all_scalars.update(sv)
                all_arrays.update(av)
                result_lines = self._build_result_lines(result_rows, av)
                cell["outputs"] = result_lines
                cell["execution_blocks"] = self._build_execution_blocks(result_rows, av)
                if cid == trigger_cell_id:
                    break

            nb_state["variables"] = all_scalars
            nb_state["array_variables"] = all_arrays
            nb_state["cells"] = cells_updated

            outputs = []
            for id_dict in result_ids:
                cid = id_dict.get("index")
                cell_match = next((c for c in cells_updated if c["id"] == cid), None)
                if cell_match:
                    outputs.append(build_notebook_results(cell_match.get("outputs", [])))
                else:
                    outputs.append(no_update)

            return nb_state, outputs

        self._track_callback(auto_run_cell)

    @staticmethod
    def _build_result_lines(result_rows: list, array_variables: dict) -> list:
        """Convert evaluated_rows into the result_lines format for build_notebook_results."""
        result_lines = []
        skip_rows = 0
        for row in result_rows:
            if skip_rows > 0:
                skip_rows -= 1
                continue
            expression = str(row.get("expression", "") or "").lstrip()
            source_span = max(1, int(row.get("source_span", 1) or 1))
            if NotebookCallbackManager._is_control_flow_row(expression) and not row.get("error"):
                result_lines.append({"name": "", "value": "", "count": "", "error": False})
                continue
            result_line = NotebookCallbackManager._result_render_rule(row, array_variables)
            result_line["row_span"] = max(int(result_line.get("row_span", 1) or 1), source_span)
            source_line = NotebookCallbackManager._source_line_number(row)
            if source_line is not None:
                result_line["source_line"] = source_line
            if source_span > 1:
                result_line["source_span"] = source_span
                skip_rows = source_span - 1
            result_lines.append(result_line)
        return result_lines

    @staticmethod
    def _source_line_number(row: dict) -> int | None:
        """Return a 1-based source line number parsed from the evaluator row id."""
        row_id = str(row.get("id", "") or "")
        match = re.match(r"^line_(\d+)$", row_id)
        if not match:
            return None
        return int(match.group(1)) + 1

    @staticmethod
    def _result_render_rule(row: dict, array_variables: dict) -> dict:
        """Return the normalized output rule payload for one evaluated row."""
        expression = str(row.get("expression", "") or "").lstrip()
        source_span = max(1, int(row.get("source_span", 1) or 1))
        label = NotebookCallbackManager._result_label(expression)
        raw_result = row.get("raw_result")

        if row.get("error"):
            return {
                "kind": "error",
                "name": label,
                "value": f"Error: {row['error']}",
                "count": "",
                "error": True,
                "row_span": source_span,
            }

        if not row.get("result"):
            return {
                "kind": "empty",
                "name": "",
                "value": "",
                "count": "",
                "error": False,
                "row_span": source_span,
            }

        result_line = {
            "kind": "scalar",
            "name": label,
            "value": row["result"],
            "count": len(array_variables[label]) if label in array_variables else "",
            "error": False,
            "row_span": source_span,
        }

        inline_matrix = NotebookCallbackManager._inline_matrix_payload(raw_result)
        if inline_matrix:
            result_line.update(inline_matrix)
            result_line["kind"] = "matrix"
            result_line["count"] = inline_matrix["shape"]
            result_line["row_span"] = max(source_span, int(inline_matrix["row_span"]))
            return result_line

        if isinstance(raw_result, np.ndarray) and raw_result.ndim == 2:
            result_line["kind"] = "matrix_summary"
            result_line["count"] = f"{raw_result.shape[0]}x{raw_result.shape[1]}"
            return result_line

        if isinstance(raw_result, np.ndarray) and raw_result.ndim == 1:
            result_line["kind"] = "vector"

        return result_line

    @staticmethod
    def _build_execution_blocks(result_rows: list, array_variables: dict) -> list[dict]:
        """Convert evaluated rows into block-aligned source/result payloads."""
        blocks: list[dict] = []
        skip_rows = 0
        for row in result_rows:
            if skip_rows > 0:
                skip_rows -= 1
                continue
            source_span = max(1, int(row.get("source_span", 1) or 1))
            expression = str(row.get("expression", "") or "")
            block = {
                "source": expression,
                "source_span": source_span,
                "name": NotebookCallbackManager._result_label(expression),
                "value": "",
                "count": "",
                "result_kind": "empty",
                "result_span": 1,
                "error": bool(row.get("error")),
            }
            if row.get("error"):
                block["result_kind"] = "error"
                block["value"] = f"Error: {row['error']}"
            elif row.get("result"):
                block["value"] = row["result"]
                block["result_kind"] = "text"
                if block["name"] in array_variables:
                    block["count"] = len(array_variables[block["name"]])
                inline_matrix = NotebookCallbackManager._inline_matrix_payload(row.get("raw_result"))
                if inline_matrix:
                    block["result_kind"] = "matrix"
                    block["matrix"] = inline_matrix["matrix"]
                    block["count"] = inline_matrix["shape"]
                    block["result_span"] = int(inline_matrix["row_span"])
                    block["value"] = inline_matrix["shape"] + " matrix"
                else:
                    block["result_span"] = 1
            blocks.append(block)
            if source_span > 1:
                skip_rows = source_span - 1
        return blocks

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
        if not y_vars:
            fig.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=20, r=20, t=30, b=20),
                annotations=[dict(
                    text="Choose Y variable(s) to render this plot cell",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=13, color="#94a3b8", family="'Inter','Segoe UI',system-ui,sans-serif"),
                )],
                title=spec.get("title") or None,
            )
            return fig
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
            title=spec.get("title") or None,
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
        """Keep inline plot notebook items in sync and render their figures."""
        @self.app.callback(
            Output("notebook-cells-store", "data", allow_duplicate=True),
            Output("notebook-state", "data", allow_duplicate=True),
            Input({"type": "nb-plot-item-x", "index": ALL}, "value"),
            Input({"type": "nb-plot-item-y", "index": ALL}, "value"),
            Input({"type": "nb-plot-item-type", "index": ALL}, "value"),
            Input({"type": "nb-plot-item-title", "index": ALL}, "value"),
            Input({"type": "nb-plot-item-xlabel", "index": ALL}, "value"),
            Input({"type": "nb-plot-item-ylabel", "index": ALL}, "value"),
            State({"type": "nb-plot-item-x", "index": ALL}, "id"),
            State("notebook-cells-store", "data"),
            State("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def sync_plot_item_specs(x_values, y_values, type_values, title_values, xlabel_values, ylabel_values, x_ids, cells, notebook_state):
            if not x_ids:
                raise PreventUpdate
            updated_cells = copy.deepcopy(cells or [default_notebook_cell()])
            lookup = {cell.get("id"): cell for cell in updated_cells}
            for i, id_dict in enumerate(x_ids):
                cell_id = id_dict.get("index")
                if cell_id not in lookup:
                    continue
                plot_cell = lookup[cell_id]
                plot_cell["plot_spec"] = {
                    "x_var": x_values[i] if i < len(x_values) else None,
                    "y_vars": y_values[i] if i < len(y_values) and y_values[i] else [],
                    "plot_type": type_values[i] if i < len(type_values) and type_values[i] else "lines",
                    "title": title_values[i] if i < len(title_values) and title_values[i] else "",
                    "x_title": xlabel_values[i] if i < len(xlabel_values) and xlabel_values[i] else "",
                    "y_title": ylabel_values[i] if i < len(ylabel_values) and ylabel_values[i] else "",
                }
            nb_state = copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            nb_state["cells"] = updated_cells
            return updated_cells, nb_state

        self._track_callback(sync_plot_item_specs)

        @self.app.callback(
            Output({"type": "nb-plot-item-x", "index": ALL}, "options"),
            Output({"type": "nb-plot-item-y", "index": ALL}, "options"),
            Input("notebook-state", "data"),
            State({"type": "nb-plot-item-x", "index": ALL}, "id"),
            prevent_initial_call=True,
        )
        def update_plot_item_options(notebook_state, x_ids):
            if not x_ids:
                raise PreventUpdate
            nb = notebook_state or {}
            array_vars = nb.get("array_variables", {})
            options = [{"label": key, "value": key} for key in sorted(array_vars.keys())]
            return [options] * len(x_ids), [options] * len(x_ids)

        self._track_callback(update_plot_item_options)

        @self.app.callback(
            Output({"type": "nb-plot-item-graph", "index": ALL}, "figure"),
            Input("notebook-state", "data"),
            State("notebook-cells-store", "data"),
            State({"type": "nb-plot-item-graph", "index": ALL}, "id"),
            prevent_initial_call=False,
        )
        def update_plot_item_figures(notebook_state, cells, graph_ids):
            if not graph_ids:
                raise PreventUpdate
            nb = notebook_state or {}
            array_vars = nb.get("array_variables", {})
            cell_lookup = {cell.get("id"): cell for cell in (cells or [])}
            figures = []
            for id_dict in graph_ids:
                cell_id = id_dict.get("index")
                plot_cell = cell_lookup.get(cell_id, {})
                spec = plot_cell.get("plot_spec", {}) or {}
                y_vars = [name for name in spec.get("y_vars", []) if name in array_vars]
                if not y_vars:
                    figures.append(self._build_plot_figure(
                        {
                            "x_var": spec.get("x_var"),
                            "y_vars": [],
                            "plot_type": spec.get("plot_type") or "lines",
                            "title": spec.get("title"),
                            "x_title": spec.get("x_title"),
                            "y_title": spec.get("y_title"),
                        },
                        {},
                        14,
                        2.0,
                    ))
                    continue
                plot_spec = {
                    "x_var": spec.get("x_var"),
                    "y_vars": y_vars,
                    "plot_type": spec.get("plot_type") or "lines",
                    "title": spec.get("title"),
                    "x_title": spec.get("x_title"),
                    "y_title": spec.get("y_title"),
                }
                figures.append(self._build_plot_figure(plot_spec, array_vars, 14, 2.0))
            return figures

        self._track_callback(update_plot_item_figures)

        @self.app.callback(
            Output("notebook-cells-store", "data", allow_duplicate=True),
            Output("notebook-state", "data", allow_duplicate=True),
            Input("nb-item-order-input", "value"),
            State("notebook-cells-store", "data"),
            State("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def reorder_notebook_items(order_value, cells, notebook_state):
            if not order_value:
                raise PreventUpdate
            try:
                order = json.loads(order_value)
            except (TypeError, ValueError, json.JSONDecodeError):
                raise PreventUpdate
            if not isinstance(order, list) or not order:
                raise PreventUpdate
            existing = list(cells or [default_notebook_cell()])
            lookup = {cell.get("id"): cell for cell in existing}
            ordered_cells = [lookup[cell_id] for cell_id in order if cell_id in lookup]
            for cell in existing:
                if cell.get("id") not in order:
                    ordered_cells.append(cell)
            nb_state = copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            nb_state["cells"] = ordered_cells
            return ordered_cells, nb_state

        self._track_callback(reorder_notebook_items)

        @self.app.callback(
            Output("notebook-cells-store", "data", allow_duplicate=True),
            Output("notebook-state", "data", allow_duplicate=True),
            Input("nb-item-width-input", "value"),
            State("notebook-cells-store", "data"),
            State("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def resize_notebook_item(width_value, cells, notebook_state):
            if not width_value:
                raise PreventUpdate
            try:
                payload = json.loads(width_value)
            except (TypeError, ValueError, json.JSONDecodeError):
                raise PreventUpdate
            cell_id = payload.get("id")
            width = payload.get("width")
            print(f"[debug][notebook-resize] raw payload={payload}")
            if not cell_id or width is None:
                print(f"[debug][notebook-resize] skipping invalid payload cell_id={cell_id} width={width}")
                raise PreventUpdate
            updated_cells = copy.deepcopy(cells or [default_notebook_cell()])
            for cell in updated_cells:
                if cell.get("id") == cell_id:
                    cell["panel_width"] = int(width)
                    print(f"[debug][notebook-resize] updated cell={cell_id} panel_width={cell['panel_width']}")
                    break
            else:
                print(f"[debug][notebook-resize] no cell found for cell_id={cell_id}")
                raise PreventUpdate
            nb_state = copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            nb_state["cells"] = updated_cells
            print(f"[debug][notebook-resize] notebook state cell count={len(updated_cells)}")
            return updated_cells, nb_state

        self._track_callback(resize_notebook_item)

        @self.app.callback(
            Output("notebook-state", "data", allow_duplicate=True),
            Input("nb-column-split-input", "value"),
            State("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def resize_notebook_columns(split_value, notebook_state):
            if not split_value:
                raise PreventUpdate
            try:
                payload = json.loads(split_value)
            except (TypeError, ValueError, json.JSONDecodeError):
                raise PreventUpdate
            left_pct = payload.get("left_pct")
            print(f"[debug][notebook-column-split] raw payload={payload}")
            if left_pct is None:
                print("[debug][notebook-column-split] missing left_pct")
                raise PreventUpdate
            nb_state = copy.deepcopy(notebook_state) if notebook_state else default_notebook_state()
            nb_state.setdefault("layout", {})
            nb_state["layout"]["left_column_width_pct"] = int(left_pct)
            print(f"[debug][notebook-column-split] saved left_column_width_pct={nb_state['layout']['left_column_width_pct']}")
            return nb_state

        self._track_callback(resize_notebook_columns)

        @self.app.callback(
            Output("notebook-cells-column-left", "style"),
            Output("notebook-cells-column-right", "style"),
            Input("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def sync_notebook_column_styles(notebook_state):
            left_pct = max(12, min(88, int(((notebook_state or {}).get("layout") or {}).get("left_column_width_pct", 50))))
            left_style = {"width": f"{left_pct}%", "minWidth": "0", "display": "flex", "flexDirection": "column"}
            right_style = {"width": f"{100 - left_pct}%", "minWidth": "0", "display": "flex", "flexDirection": "column"}
            print(f"[debug][notebook-column-split] apply left={left_style['width']} right={right_style['width']}")
            return left_style, right_style

        self._track_callback(sync_notebook_column_styles)

    def _register_save_load(self):
        """Save notebook to .json and load from .json or legacy .txt."""

        self.app.clientside_callback(
            """
            function(n_clicks, cells) {
                if (!n_clicks) return window.dash_clientside.no_update;
                var snapshot = Array.isArray(cells) ? JSON.parse(JSON.stringify(cells)) : [];
                if (window._cellEditors) {
                    snapshot.forEach(function(cell) {
                        if (!cell || !cell.id) return;
                        var editor = window._cellEditors[cell.id];
                        if (editor) {
                            try {
                                cell.source = editor.getValue();
                            } catch (e) {}
                        }
                    });
                }
                return {cells: snapshot, ts: Date.now()};
            }
            """,
            Output("notebook-save-sync", "data"),
            Input("notebook-save-btn", "n_clicks"),
            State("notebook-cells-store", "data"),
            prevent_initial_call=True,
        )

        @self.app.callback(
            Output(NOTEBOOK_DOWNLOAD_ID, "data"),
            Input("notebook-save-sync", "data"),
            State("notebook-save-sync", "data"),
            State("notebook-state", "data"),
            prevent_initial_call=True,
        )
        def save_notebook(save_sync, _save_sync_state, notebook_state):
            if not save_sync:
                raise PreventUpdate
            cells = save_sync.get("cells") or (notebook_state or {}).get("cells") or [default_notebook_cell()]
            payload = serialize_notebook_cells(cells, (notebook_state or {}).get("layout"))
            return dcc.send_string(json.dumps(payload, indent=2), filename="notebook.json")

        self._track_callback(save_notebook)

        @self.app.callback(
            Output("notebook-cells-store", "data", allow_duplicate=True),
            Output("notebook-state", "data", allow_duplicate=True),
            Input("notebook-load-upload", "contents"),
            Input("notebook-load-upload", "filename"),
            prevent_initial_call=True,
        )
        def load_notebook(contents, filename):
            from dash import no_update
            if not contents:
                return no_update, no_update
            _header, encoded = contents.split(",", 1)
            raw = base64.b64decode(encoded).decode("utf-8", errors="replace")

            cells: list
            if filename and filename.endswith(".json"):
                try:
                    payload = json.loads(raw)
                    if isinstance(payload, dict) and "cells" in payload:
                        cells = []
                        for c in deserialize_notebook_cells(payload):
                            restored_cell = {
                                "id": c.get("id") or new_cell_id(),
                                "type": c.get("type", "code"),
                                "column": c.get("column", "left"),
                                "panel_width": c.get("panel_width"),
                                "source": c.get("source", ""),
                                "outputs": [],
                                "dirty": False,
                            }
                            if restored_cell["type"] == "plot":
                                restored_cell["plot_spec"] = dict(c.get("plot_spec") or {})
                            cells.append(restored_cell)
                    else:
                        cells = [default_cell(source=raw)]
                except Exception:
                    cells = [default_cell(source=raw)]
            else:
                # Legacy .txt: put entire text into a single code cell
                cells = [default_cell(source=raw)]

            if not cells:
                cells = [default_notebook_cell()]
            new_state = default_notebook_state()
            if filename and filename.endswith(".json"):
                try:
                    payload_layout = (payload or {}).get("layout") if isinstance(payload, dict) else None
                    if isinstance(payload_layout, dict):
                        new_state["layout"]["left_column_width_pct"] = int(payload_layout.get("left_column_width_pct", 50))
                except Exception:
                    print("[debug][notebook-load] failed to restore layout; using default split")
            new_state["cells"] = cells
            print(f"[debug][notebook-load] restored left_column_width_pct={new_state['layout']['left_column_width_pct']}")
            return cells, new_state

        self._track_callback(load_notebook)

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
