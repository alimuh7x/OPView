"""
Source-level regression tests for notebook manager review fixes.
"""
from __future__ import annotations

import pathlib
import unittest
import importlib.util
import numpy as np


NOTEBOOK_MANAGER = pathlib.Path(__file__).resolve().parents[1] / "callbacks" / "notebook_manager.py"
MONACO_NOTEBOOK = pathlib.Path(__file__).resolve().parents[1] / "assets" / "monaco_notebook.js"
LIVE_SYNC = pathlib.Path(__file__).resolve().parents[1] / "assets" / "notebook_live_sync.js"
OPVIEW_APP = pathlib.Path(__file__).resolve().parents[1] / "OPView.py"
NOTEBOOK_PERSISTENCE = pathlib.Path(__file__).resolve().parents[1] / "utils" / "notebook_persistence.py"


def _load_notebook_persistence_module():
    spec = importlib.util.spec_from_file_location("notebook_persistence_test_module", NOTEBOOK_PERSISTENCE)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load notebook persistence module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NotebookManagerSourceTests(unittest.TestCase):
    def test_notebook_json_save_payload_includes_all_cells_in_order(self):
        persistence = _load_notebook_persistence_module()
        cells = [
            {"id": "cell-a", "type": "code", "source": "x = 1", "outputs": [{"value": "1"}], "dirty": True},
            {"id": "cell-b", "type": "markdown", "source": "# Title", "outputs": [{"value": "ignored"}], "dirty": False},
        ]

        payload = persistence.serialize_notebook_cells(cells)

        self.assertEqual(payload["version"], 3)
        self.assertEqual(
            payload["cells"],
            [
                {"id": "cell-a", "type": "code", "source": "x = 1"},
                {"id": "cell-b", "type": "markdown", "source": "# Title"},
            ],
        )

    def test_notebook_json_load_normalizes_cells_for_rerun(self):
        persistence = _load_notebook_persistence_module()
        payload = {
            "version": 3,
            "cells": [
                {"id": "cell-a", "type": "code", "source": "x = 1", "outputs": [{"value": "ignored"}]},
                {"id": "cell-b", "type": "markdown", "source": "# Heading"},
            ],
        }

        cells = persistence.deserialize_notebook_cells(payload)

        self.assertEqual(
            cells,
            [
                {"id": "cell-a", "type": "code", "source": "x = 1", "outputs": [], "dirty": False},
                {"id": "cell-b", "type": "markdown", "source": "# Heading", "outputs": [], "dirty": False},
            ],
        )

    def test_save_load_code_uses_save_sync_snapshot(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        ui_source = pathlib.Path(__file__).resolve().parents[1].joinpath("ui", "calculation_notebook.py").read_text(encoding="utf-8")
        self.assertIn('State("notebook-save-sync", "data")', source)
        self.assertIn('Input("notebook-save-sync", "data")', source)
        self.assertIn('dcc.Store(id="notebook-save-sync", data=None)', ui_source)

    def test_plot_parser_strips_hash_comments(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('clean = re.sub(r"#.*$", "", clean).strip()', source)

    def test_monaco_var_refresh_callback_registered(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn("def _register_monaco_var_decorations", source)
        self.assertIn('Output("notebook-var-refresh-dummy", "data")', source)
        self.assertIn("window._nbRefreshVarsFromState", source)

    def test_monaco_sync_no_longer_dispatches_hidden_inputs(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        sync_section = source.split("window._syncToMonaco = function (val) {", 1)[1].split("};", 1)[0]
        self.assertNotIn("dispatchEvent(new Event('input'", sync_section)

    def test_monaco_requeries_hidden_inputs_after_dash_replacement(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("function getCellTextarea(cellId)", source)
        self.assertIn("document.getElementById('{\"index\":\"' + cellId + '\",\"type\":\"nb-cell-text\"}')", source)
        self.assertNotIn("document.getElementById('notebook-live-text')", source)
        self.assertNotIn("document.getElementById('notebook-run-text')", source)

    def test_monaco_boots_when_document_is_already_ready(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("if (document.readyState === 'complete' || document.readyState === 'interactive')", source)
        self.assertIn("document.addEventListener('DOMContentLoaded', bootNotebookEditors);", source)

    def test_monaco_client_debug_breadcrumbs_exist(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("function setClientDebug(message)", source)
        self.assertIn("'editor change ' + cellId +", source)
        self.assertIn("loadMonaco: editor.main loaded", source)
        self.assertIn("mutation attribute ", source)
        self.assertIn("document.getElementById('notebook-auto-update')", source)

    def test_result_grid_uses_compact_readable_typography(self):
        source = LIVE_SYNC.read_text(encoding="utf-8")

        self.assertIn('row.style.height = "30px";', source)
        self.assertIn('row.style.lineHeight = "30px";', source)
        self.assertIn('row.style.fontSize = "12px";', source)
        self.assertIn('const cellBase = "padding:0 6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;height:30px;line-height:30px;";', source)

    def test_notebook_ai_prompt_includes_collision_and_runtime_safety_rules(self):
        source = LIVE_SYNC.read_text(encoding="utf-8")

        self.assertIn("Do not overwrite existing notebook variables unless the user explicitly asks", source)
        self.assertIn("If you need a new variable, choose a unique descriptive name", source)
        self.assertIn("If required inputs are missing, say which variables are missing", source)
        self.assertIn("Current scalar variables:", source)
        self.assertIn("Current array variables:", source)
        self.assertIn("var arrayVarsCtx = '';", source)
        self.assertIn("nbState.array_variables", source)

    def test_notebook_ai_prompt_expands_typed_code_into_runnable_notebook_snippets(self):
        source = LIVE_SYNC.read_text(encoding="utf-8")

        self.assertIn("If the user gives typed code from C, C++, Java, or similar languages", source)
        self.assertIn("convert it into notebook syntax", source)
        self.assertIn("remove type keywords like double, float, int, or const", source)
        self.assertIn("return a runnable notebook snippet, not just a single rewritten line", source)
        self.assertIn("add placeholder/default assignments for any referenced variables that are missing from the current notebook context", source)

    def test_notebook_ai_prompt_includes_short_curated_function_defaults(self):
        source = LIVE_SYNC.read_text(encoding="utf-8")

        self.assertIn("Important defaults:", source)
        self.assertIn("linspace(start, stop, num=50)", source)
        self.assertIn("arange(start, stop, step=1)", source)
        self.assertIn("cfl_dt(dx, u, cfl=1)", source)
        self.assertIn("diffusion_dt(dx, D, f=0.5)", source)
        self.assertIn('plot(x, y, type=\\"line\\")', source)

    def test_auto_update_state_is_mirrored_for_monaco(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('Output("notebook-auto-update-state", "value")', source)
        self.assertIn('Input("notebook-auto-update", "value")', source)
        self.assertIn('return "on" if _auto_update_enabled(value) else "off"', source)

    def test_result_lines_include_variable_or_expression_label(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn("def _result_label(expression: str) -> str:", source)
        self.assertIn('result_lines.append({', source)
        self.assertIn('"name": label,', source)
        self.assertIn('"value": row["result"],', source)
        self.assertIn('"count": len(array_variables[label]) if label in array_variables else ""', source)

    def test_result_lines_skip_control_flow_summary_rows(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn("def _is_control_flow_row(expression: str) -> bool:", source)
        self.assertIn("str(row.get(\"expression\", \"\") or \"\").lstrip()", source)
        self.assertIn("NotebookCallbackManager._is_control_flow_row(expression)", source)
        self.assertIn('result_lines.append({"name": "", "value": "", "count": "", "error": False})', source)

    def test_small_matrix_results_become_inline_table_metadata(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        result_lines = NotebookCallbackManager._build_result_lines(
            [{"expression": "A = eye(3)", "result": "3×3 matrix", "raw_result": np.eye(3), "error": ""}],
            {},
        )

        self.assertEqual(result_lines[0]["kind"], "matrix")
        self.assertEqual(result_lines[0]["row_span"], 3)
        self.assertEqual(result_lines[0]["shape"], "3x3")
        self.assertEqual(result_lines[0]["matrix"][1][1], "1")

    def test_example_insert_prefers_empty_code_cell(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        cells = [
            {"id": "md-1", "type": "markdown", "source": "", "outputs": [], "dirty": False},
            {"id": "code-1", "type": "code", "source": "", "outputs": [], "dirty": False},
        ]

        target = NotebookCallbackManager._find_example_target_cell(cells)

        self.assertIs(target, cells[1])

    def test_start_inserter_target_is_handled_as_prepend(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('if action in ("add-code", "add-markdown") and target_cell_id == "__start__":', source)
        self.assertIn('cells.insert(0, new_c)', source)

    def test_quick_start_insert_creates_markdown_intro_before_code(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('if selected_snippet == "Quick Start":', source)
        self.assertIn('intro_cell = default_cell(', source)
        self.assertIn('cell_type="markdown"', source)
        self.assertIn('code_cell = default_cell(cell_type="code", source=snippet)', source)
        self.assertIn('cells.extend([intro_cell, code_cell])', source)

    def test_multiline_matrix_results_collapse_continuation_rows(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        result_lines = NotebookCallbackManager._build_result_lines(
            [
                {"expression": "A = [", "result": "3×3 matrix", "raw_result": np.eye(3), "error": "", "source_span": 5},
                {"expression": "    [1, 0, 0],", "result": "", "raw_result": None, "error": ""},
                {"expression": "    [0, 1, 0],", "result": "", "raw_result": None, "error": ""},
                {"expression": "    [0, 0, 1],", "result": "", "raw_result": None, "error": ""},
                {"expression": "]", "result": "", "raw_result": None, "error": ""},
            ],
            {},
        )

        self.assertEqual(len(result_lines), 1)
        self.assertEqual(result_lines[0]["row_span"], 5)
        self.assertEqual(result_lines[0]["source_span"], 5)
        self.assertEqual(result_lines[0]["matrix"][2][2], "1")

    def test_execution_blocks_preserve_source_and_matrix_shape(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        blocks = NotebookCallbackManager._build_execution_blocks(
            [
                {"expression": "x = 1", "result": "1", "raw_result": 1.0, "error": "", "source_span": 1},
                {"expression": "A = [[1,2,3],[4,5,6],[7,8,9]]", "result": "3×3 matrix", "raw_result": np.eye(3), "error": "", "source_span": 1},
            ],
            {},
        )

        self.assertEqual(blocks[0]["source"], "x = 1")
        self.assertEqual(blocks[0]["result_span"], 1)
        self.assertEqual(blocks[1]["source"], "A = [[1,2,3],[4,5,6],[7,8,9]]")
        self.assertEqual(blocks[1]["result_kind"], "matrix")
        self.assertEqual(blocks[1]["result_span"], 3)
        self.assertEqual(blocks[1]["matrix"][1][1], "1")

    def test_large_matrix_results_stay_compact(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        result_lines = NotebookCallbackManager._build_result_lines(
            [{"expression": "A = eye(7)", "result": "7×7 matrix", "raw_result": np.eye(7), "error": ""}],
            {},
        )

        self.assertEqual(result_lines[0]["kind"], "matrix_summary")
        self.assertEqual(result_lines[0]["count"], "7x7")
        self.assertEqual(result_lines[0]["value"], "7×7 matrix")

    def test_output_rule_helper_keeps_empty_and_scalar_rows_at_source_span(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        empty_rule = NotebookCallbackManager._result_render_rule(
            {"expression": "if x > 0:", "result": "", "raw_result": None, "error": "", "source_span": 3},
            {},
        )
        scalar_rule = NotebookCallbackManager._result_render_rule(
            {"expression": "x = 1", "result": "1", "raw_result": 1.0, "error": "", "source_span": 2},
            {},
        )

        self.assertEqual(empty_rule["kind"], "empty")
        self.assertEqual(empty_rule["row_span"], 3)
        self.assertEqual(scalar_rule["kind"], "scalar")
        self.assertEqual(scalar_rule["row_span"], 2)

    def test_output_rule_helper_keeps_vectors_compact_and_small_single_line_matrices_inline(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        vector_rule = NotebookCallbackManager._result_render_rule(
            {"expression": "v = [1, 2, 3]", "result": "[1, 2, 3]", "raw_result": np.array([1.0, 2.0, 3.0]), "error": "", "source_span": 1},
            {"v": [1.0, 2.0, 3.0]},
        )
        matrix_rule = NotebookCallbackManager._result_render_rule(
            {"expression": "A = eye(3)", "result": "3×3 matrix", "raw_result": np.eye(3), "error": "", "source_span": 1},
            {},
        )

        self.assertEqual(vector_rule["kind"], "vector")
        self.assertEqual(vector_rule["row_span"], 1)
        self.assertEqual(matrix_rule["kind"], "matrix")
        self.assertEqual(matrix_rule["row_span"], 3)
        self.assertEqual(matrix_rule["shape"], "3x3")

    def test_result_lines_capture_source_line_for_inline_matrix_alignment(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        result_lines = NotebookCallbackManager._build_result_lines(
            [{"id": "line_4", "expression": "A = eye(3)", "result": "3×3 matrix", "raw_result": np.eye(3), "error": "", "source_span": 1}],
            {},
        )

        self.assertEqual(result_lines[0]["source_line"], 5)

    def test_live_sync_exposes_state_refresh(self):
        source = LIVE_SYNC.read_text(encoding="utf-8")
        self.assertIn("window._nbRefreshVarsFromState = refreshVarsFromState;", source)

    def test_monaco_inline_matrix_alignment_uses_source_end_line_anchor(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("window._nbApplyInlineResultZones = function (state) {", source)
        self.assertIn("editor.changeViewZones(function (accessor) {", source)
        self.assertIn("var sourceLine = parseInt(line.source_line || (index + 1), 10);", source)
        self.assertIn("var sourceSpan = parseInt(line.source_span || 1, 10);", source)
        self.assertIn("var extraRows = Math.max(0, rowSpan - sourceSpan);", source)
        self.assertIn("var sourceEndLine = sourceLine + sourceSpan - 1;", source)
        self.assertIn("afterLineNumber: sourceEndLine,", source)
        self.assertIn("heightInPx: extraRows * 34", source)

    def test_var_refresh_callback_calls_inline_result_zone_path(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn("window._nbApplyInlineResultZones", source)

    def test_result_lines_keep_source_span_for_multiline_matrix_alignment(self):
        from callbacks.notebook_manager import NotebookCallbackManager

        result_lines = NotebookCallbackManager._build_result_lines(
            [{"id": "line_0", "expression": "A = [", "result": "3×3 matrix", "raw_result": np.eye(3), "error": "", "source_span": 2}],
            {},
        )

        self.assertEqual(result_lines[0]["source_line"], 1)
        self.assertEqual(result_lines[0]["source_span"], 2)
        self.assertEqual(result_lines[0]["row_span"], 3)

    def test_live_sync_supports_slice_assignment_targets(self):
        source = LIVE_SYNC.read_text(encoding="utf-8")
        self.assertIn("function parseSliceIndices(expr, variables, length)", source)
        self.assertIn("Slice assignment length mismatch", source)
        self.assertIn("findTopLevelColon(idx1Expr) !== -1", source)

    def test_live_sync_results_use_labels_and_single_blue(self):
        source = LIVE_SYNC.read_text(encoding="utf-8")
        self.assertIn("function resultLabel(expression)", source)
        self.assertIn('results[li] = {', source)
        self.assertIn('name: label,', source)
        self.assertIn('count: Array.isArray(value) ? value.length : ""', source)
        self.assertIn('row.style.display = "grid";', source)
        self.assertIn('const nameColWidth = Math.max(72, Math.min(220, maxLabelLen * 9 + 16));', source)
        self.assertIn('const colTemplate = nameColWidth + "px minmax(0, 1fr) 56px";', source)
        self.assertIn("if (r && r.error) acc.push(i);", source)

    def test_notebook_defaults_to_light_theme_class(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("theme:                'nb-light',", source)
        self.assertIn("container.classList.add('theme-nb-light');", source)

    def test_light_theme_editor_surface_is_pure_white(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("'editor.background':                   '#ffffff'", source)
        self.assertIn("'editor.lineHighlightBackground':      '#ffffff'", source)
        self.assertIn("'editorBracketMatch.background':       '#ffffff'", source)
        self.assertNotIn("'editor.background':                   '#fffdf8'", source)

    def test_theme_selector_logic_removed(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertNotIn("function initThemeSelector(editor)", source)
        self.assertNotIn("opview_nb_theme", source)
        self.assertNotIn("notebook-theme-select", source)

    def test_vim_loader_has_dual_cdn_and_explicit_failure_path(self):
        source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("/vendor/monaco-vim.umd.js", source)
        self.assertIn("https://cdn.jsdelivr.net/npm/monaco-vim/dist/monaco-vim.js", source)
        self.assertIn("https://unpkg.com/monaco-vim/dist/monaco-vim.js", source)
        self.assertIn("flushVimWaiters(false);", source)
        self.assertIn("setNote('Vim unavailable', '#b42318');", source)

    def test_cell_monaco_keeps_alternating_line_decorations(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        style_source = LIVE_SYNC.parents[1].joinpath("assets", "style.css").read_text(encoding="utf-8")
        self.assertIn("var altLineDecorations = [];", monaco_source)
        self.assertIn("function updateAlternatingLines()", monaco_source)
        self.assertIn("className: (line % 2 === 1) ? 'nb-alt-line-a' : 'nb-alt-line-b'", monaco_source)
        self.assertIn("altLineDecorations = editor.deltaDecorations(altLineDecorations, decorations);", monaco_source)
        self.assertIn("[id^=\"nb-cell-editor-\"].theme-nb-light .monaco-editor .view-overlays .nb-alt-line-a", style_source)
        self.assertIn("[id^=\"nb-cell-editor-\"].theme-nb-light .monaco-editor .view-overlays .nb-alt-line-b", style_source)

    def test_cell_editor_recreate_checks_current_container_not_body(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("if (domNode && container.contains(domNode)) {", monaco_source)
        self.assertNotIn("if (domNode && document.body.contains(domNode)) {", monaco_source)

    def test_existing_cell_editor_syncs_external_value_changes(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("var currentValue = window._cellEditors[cellId].getValue();", monaco_source)
        self.assertIn("if (currentValue !== initValue) {", monaco_source)
        self.assertIn("window._monacoSyncing = true;", monaco_source)
        self.assertIn("window._cellEditors[cellId].setValue(initValue);", monaco_source)
        self.assertIn("window._monacoSyncing = false;", monaco_source)

    def test_client_debug_uses_multiline_buffer_and_error_hooks(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("function setClientDebug(message) {", monaco_source)
        self.assertIn("return;", monaco_source)
        self.assertIn("function dumpClientState(reason)", monaco_source)
        self.assertIn("window.addEventListener('error', function (event) {", monaco_source)
        self.assertIn("window.addEventListener('unhandledrejection', function (event) {", monaco_source)

    def test_client_debug_tracks_editor_dimensions_and_focus(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("'mount container for ' + cellId +", monaco_source)
        self.assertIn("'editor layout for ' + cellId +", monaco_source)
        self.assertIn("'updateCellHeight ' + cellId +", monaco_source)
        self.assertIn("'post-create ' + cellId +", monaco_source)
        self.assertIn("editor.onDidFocusEditorWidget(function () {", monaco_source)
        self.assertIn("editor.onDidBlurEditorWidget(function () {", monaco_source)
        self.assertIn("editor.onDidChangeCursorSelection(function (event) {", monaco_source)
        self.assertIn("container.addEventListener('mousedown', function () {", monaco_source)
        self.assertIn("'editor change ' + cellId +", monaco_source)

    def test_cell_editor_creation_waits_for_nonzero_container_width(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("function scheduleCellEditorRetry(cellId, reason) {", monaco_source)
        self.assertIn("if (container.offsetWidth === 0) {", monaco_source)
        self.assertIn("scheduleCellEditorRetry(cellId, 'container width is 0');", monaco_source)
        self.assertIn("window.setTimeout(function () {", monaco_source)
        self.assertIn("createCellEditors();", monaco_source)
        self.assertIn("delete window._cellEditorRetryCounts[cellId];", monaco_source)

    def test_mutation_observer_refreshes_on_cell_attribute_changes(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("function createCellEditors(forceSyncExisting) {", monaco_source)
        self.assertIn("var selector = forceSyncExisting ? '[id^=\"nb-cell-editor-\"]' : '[data-cell-init=\"true\"]';", monaco_source)
        self.assertIn("if (m.type === 'attributes') {", monaco_source)
        self.assertIn("m.attributeName === 'data-cell-init' || m.attributeName === 'data-cell-value'", monaco_source)
        self.assertIn("if (m.attributeName === 'data-cell-value') forceSyncExisting = true;", monaco_source)
        self.assertIn("setClientDebug('mutation attribute ' + target.id + ' | ' + m.attributeName);", monaco_source)
        self.assertIn("setClientDebug('mutation refresh -> createCellEditors' + (forceSyncExisting ? ' (forceSyncExisting)' : ''));", monaco_source)
        self.assertIn("createCellEditors(forceSyncExisting);", monaco_source)
        self.assertIn("attributes: true,", monaco_source)
        self.assertIn("attributeFilter: ['data-cell-init', 'data-cell-value'],", monaco_source)

    def test_cell_height_uses_four_line_minimum_without_internal_scroll(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("var MIN_CELL_LINES = 4;", monaco_source)
        self.assertIn("var visibleLines = Math.max(MIN_CELL_LINES, model ? model.getLineCount() : 1);", monaco_source)
        self.assertIn("padding:              { top: 0, bottom: 0 },", monaco_source)
        self.assertIn("var minHeight = visibleLines * 34;", monaco_source)
        self.assertIn("var h = Math.max(minHeight, editor.getContentHeight());", monaco_source)

    def test_code_cells_render_single_inline_results_column(self):
        ui_source = pathlib.Path(__file__).resolve().parents[1].joinpath("ui", "calculation_notebook.py").read_text(encoding="utf-8")
        manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn("def build_notebook_execution_view(", ui_source)
        self.assertIn('build_notebook_results(outputs)', ui_source)
        self.assertIn('build_notebook_results(cell_match.get("outputs", []))', manager_source)
        self.assertNotIn('build_notebook_execution_view(cell_match.get("execution_blocks", []))', manager_source)

    def test_markdown_cells_do_not_auto_preview_while_editing(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertNotIn("if (cellType === 'markdown' && window._renderMarkdownCell) {", monaco_source)
        self.assertNotIn("if (cellType === 'markdown' && window._renderMarkdownCell && initialValue) {", monaco_source)

    def test_markdown_preview_starts_hidden_even_for_markdown_cells(self):
        ui_source = pathlib.Path(__file__).resolve().parents[1].joinpath("ui", "calculation_notebook.py").read_text(encoding="utf-8")
        self.assertIn('"display": "none",', ui_source)
        self.assertNotIn('"display": "none" if cell_type == "code" else "block"', ui_source)

    def test_markdown_debug_is_targeted_and_preview_logs_are_exposed(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        live_sync_source = LIVE_SYNC.read_text(encoding="utf-8")
        self.assertIn("function debugMarkdown(message, cellType) {", monaco_source)
        self.assertIn("if (cellType !== 'markdown') return;", monaco_source)
        self.assertIn("debugMarkdown('editor focus ' + cellId", monaco_source)
        self.assertIn("debugMarkdown('cursor ' + cellId", monaco_source)
        self.assertIn("function showMarkdownEditor(cellId) {", live_sync_source)
        self.assertIn("window._showMarkdownEditor = showMarkdownEditor;", live_sync_source)

    def test_markdown_preview_ignores_zero_click_remount_events(self):
        manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn("var trig = ctx.triggered[0];", manager_source)
        self.assertIn("if (trig.value === 0 || trig.value === null) return window.dash_clientside.no_update;", manager_source)

    def test_markdown_preview_button_toggles_back_to_editor(self):
        manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn("if (trigger.indexOf('\"type\":\"nb-cell-edit\"') !== -1) {", manager_source)
        self.assertIn("if (!window._showMarkdownEditor) return window.dash_clientside.no_update;", manager_source)
        self.assertIn("window._showMarkdownEditor(cellId);", manager_source)

    def test_markdown_preview_callback_accepts_explicit_edit_trigger(self):
        manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('Input({"type": "nb-cell-preview", "index": ALL}, "n_clicks")', manager_source)
        self.assertIn('Input({"type": "nb-cell-edit", "index": ALL}, "n_clicks")', manager_source)
        self.assertNotIn('nb-cell-preview-toggle', manager_source)
        self.assertIn('Output("notebook-markdown-preview-dummy", "data")', manager_source)

    def test_markdown_help_panel_has_clientside_toggle(self):
        manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        ui_source = pathlib.Path(__file__).resolve().parents[1].joinpath("ui", "calculation_notebook.py").read_text(encoding="utf-8")
        self.assertIn('document.getElementById(\'notebook-md-panel\')', manager_source)
        self.assertIn('Input("notebook-md-help-btn", "n_clicks")', manager_source)
        self.assertIn('Input("notebook-md-close-btn", "n_clicks")', manager_source)
        self.assertIn('Output("notebook-md-panel-dummy", "data")', manager_source)
        self.assertIn('dcc.Store(id="notebook-markdown-preview-dummy")', ui_source)
        self.assertIn('dcc.Store(id="notebook-md-panel-dummy")', ui_source)

    def test_markdown_focus_enters_edit_and_blur_returns_preview(self):
        monaco_source = MONACO_NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("if (cellType === 'markdown' && window._showMarkdownEditor) {", monaco_source)
        self.assertIn("window._showMarkdownEditor(cellId);", monaco_source)
        self.assertIn("window.setTimeout(function () {", monaco_source)
        self.assertIn("if (cellType !== 'markdown') return;", monaco_source)
        self.assertIn("if (window._markdownJustOpened && window._markdownJustOpened[cellId]) return;", monaco_source)
        self.assertIn("if (editor.hasTextFocus()) return;", monaco_source)
        self.assertIn("if (window._renderMarkdownCell) {", monaco_source)
        self.assertIn("window._renderMarkdownCell(cellId, editor.getValue());", monaco_source)

    def test_markdown_preview_click_handler_handles_text_nodes(self):
        live_sync_source = LIVE_SYNC.read_text(encoding="utf-8")
        self.assertIn("window._markdownJustOpened = window._markdownJustOpened || {};", live_sync_source)
        self.assertIn("var target = event.target && event.target.nodeType === 3", live_sync_source)
        self.assertIn("? event.target.parentElement", live_sync_source)
        self.assertIn("var preview = target && target.closest", live_sync_source)
        self.assertIn("window._markdownJustOpened[cellId] = true;", live_sync_source)
        self.assertIn("window.setTimeout(function () {", live_sync_source)
        self.assertIn("delete window._markdownJustOpened[cellId];", live_sync_source)
        self.assertIn("showMarkdownEditor(cellId);", live_sync_source)

    def test_opview_serves_vendor_assets(self):
        source = OPVIEW_APP.read_text(encoding="utf-8")
        self.assertIn("@app.server.route('/vendor/<path:filename>')", source)
        self.assertIn('send_from_directory(BASE_DIR / "vendor", filename)', source)

    def test_plot_panel_uses_card_store_and_pattern_callbacks(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('Output("notebook-plots-panel", "children")', source)
        self.assertIn('Input("nb-plot-new-btn", "n_clicks")', source)
        self.assertIn('{"type": "nb-plot-card-x", "index": ALL}', source)
        self.assertIn('{"type": "nb-plot-card-remove-btn", "index": ALL}', source)
        self.assertNotIn('Input("nb-plot-add-btn", "n_clicks")', source)
        self.assertNotIn('Input("nb-plot-clear-btn", "n_clicks")', source)
        self.assertNotIn('Output("nb-plot-selector-cards", "children")', source)

    def test_insert_example_reads_live_text_not_textarea(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('Output("nb-op-sync", "data")', source)
        self.assertIn('Object.keys(window._cellEditors).forEach(function(id) {', source)
        self.assertIn('cell["source"] = sources[cid]', source)

    def test_clear_path_resets_hidden_live_and_run_text(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('Output("notebook-live-text", "value", allow_duplicate=True)', source)
        self.assertIn('Output("notebook-run-text", "value", allow_duplicate=True)', source)
        self.assertIn('def clear_notebook(_submit_n_clicks):', source)
        self.assertIn('return "", "", "", ""', source)
        self.assertNotIn('Output("notebook-run-text", "value", allow_duplicate=True),\n            Output("notebook-results", "children")', source)

    def test_insert_example_prefers_first_empty_cell_before_appending(self):
        source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        self.assertIn('if selected_snippet and selected_snippet in NOTEBOOK_SNIPPETS:', source)
        self.assertIn('snippet = NOTEBOOK_SNIPPETS[selected_snippet]', source)
        self.assertIn('empty_cell = NotebookCallbackManager._find_example_target_cell(cells)', source)
        self.assertIn('empty_cell["source"] = snippet', source)
        self.assertIn('cells.append(default_cell(source=snippet))', source)

    def test_cell_callbacks_emit_visible_server_debug(self):
        manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
        ui_source = pathlib.Path(__file__).resolve().parents[1].joinpath("ui", "calculation_notebook.py").read_text(encoding="utf-8")
        self.assertIn('def auto_run_cell(', manager_source)
        self.assertIn('def run_cell_callback(', manager_source)
        self.assertNotIn('id="notebook-debug"', ui_source)


if __name__ == "__main__":
    unittest.main()
