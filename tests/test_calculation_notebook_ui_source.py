"""
Source-level regression tests for calculation notebook execution controls.
"""
from __future__ import annotations

import pathlib
import unittest
import importlib.util


NOTEBOOK_UI = pathlib.Path(__file__).resolve().parents[1] / "ui" / "calculation_notebook.py"
STYLE_CSS = pathlib.Path(__file__).resolve().parents[1] / "assets" / "style.css"


def _load_notebook_ui_module():
    spec = importlib.util.spec_from_file_location("calculation_notebook_test_module", NOTEBOOK_UI)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load notebook UI module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CalculationNotebookUiSourceTests(unittest.TestCase):
    def test_notebook_has_manual_run_control_ids(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('"notebook-auto-update"', source)
        self.assertIn('"notebook-run-btn"', source)
        self.assertIn('"notebook-run-text"', source)

    def test_auto_update_defaults_to_enabled(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('id="notebook-auto-update"', source)
        self.assertIn('value=["auto"]', source)
        self.assertIn('id="notebook-auto-update-state"', source)

    def test_notebook_has_var_refresh_dummy_store(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('dcc.Store(id="notebook-var-refresh-dummy")', source)

    def test_vars_button_removed_from_toolbar(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertNotIn('nb-vars-toggle-btn', source)

    def test_vim_mode_controls_removed_from_toolbar(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertNotIn('id="notebook-vim-toggle"', source)
        self.assertNotIn('id="notebook-vim-note"', source)
        self.assertNotIn('notebook-vim-btn', source)

    def test_theme_selector_removed_from_toolbar(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertNotIn('id="notebook-theme-select"', source)

    def test_plot_panel_uses_card_based_quick_plots(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('id="nb-plot-new-btn"', source)
        self.assertNotIn('id="nb-plot-add-btn"', source)
        self.assertNotIn('id="nb-plot-clear-btn"', source)
        self.assertNotIn('Quick plots update automatically when you pick X and Y', source)
        self.assertNotIn('"maxHeight": "calc(100vh - 80px)"', source)

    def test_quick_start_includes_pythonic_syntax_examples(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        quick_start = source.split('"Quick Start": """\\', 1)[1].split('"Newton\'s Law of Cooling": """\\', 1)[0]

        self.assertIn("theta = 45 * deg", quick_start)
        self.assertNotIn("angle = 45 * deg", quick_start)
        self.assertIn("# ── Multiline expressions ───────────────────────────", quick_start)
        self.assertIn("# ── Dictionaries ───────────────────────────────────", quick_start)
        self.assertIn("# ── List comprehensions ────────────────────────────", quick_start)
        self.assertIn("# ── Split matrix literals ──────────────────────────", quick_start)

    def test_markdown_cells_have_explicit_preview_and_edit_controls(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('"type": "nb-cell-preview"', source)
        self.assertIn('"type": "nb-cell-edit"', source)
        self.assertNotIn('"type": "nb-cell-preview-toggle"', source)
        self.assertIn('"Preview"', source)
        self.assertIn('"Edit"', source)

    def test_notebook_toolbar_exposes_markdown_help_panel(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('"Markdown Help"', source)
        self.assertIn('"notebook-md-help-btn"', source)
        self.assertIn('id="notebook-md-panel"', source)

    def test_notebook_uses_white_canvas_and_separates_toolbar(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('"background": "#ffffff"', source)
        self.assertIn('"borderBottom": "1px solid rgba(226,232,240,0.95)"', source)
        self.assertIn('"boxShadow": "0 1px 0 rgba(15,23,42,0.04)"', source)

    def test_inserter_strip_is_subtle_and_gap_is_tight(self):
        ui_source = NOTEBOOK_UI.read_text(encoding="utf-8")
        css_source = STYLE_CSS.read_text(encoding="utf-8")

        self.assertIn('"padding": "1px 2px"', ui_source)
        self.assertIn('"gap": "4px"', ui_source)
        self.assertIn(".nb-cell-inserter { opacity: 0.02;", css_source)
        self.assertIn(".nb-cell-inserter:hover { opacity: 0.92;", css_source)
        self.assertIn("color: #001f41;", css_source)

    def test_markdown_toolbar_is_hover_only(self):
        source = STYLE_CSS.read_text(encoding="utf-8")

        self.assertIn(".nb-markdown-toolbar {", source)
        self.assertIn("pointer-events: none;", source)
        self.assertIn(".nb-markdown-cell:hover .nb-markdown-toolbar {", source)
        self.assertIn("pointer-events: auto;", source)

    def test_markdown_preview_styles_cover_tables_links_and_blockquotes(self):
        source = STYLE_CSS.read_text(encoding="utf-8")

        self.assertIn(".nb-markdown-preview table", source)
        self.assertIn(".nb-markdown-preview a", source)
        self.assertIn(".nb-markdown-preview blockquote", source)
        self.assertIn(".nb-markdown-preview pre code", source)
        self.assertIn(".nb-markdown-preview hr", source)

    def test_build_cell_returns_component_for_code_and_markdown_cells(self):
        module = _load_notebook_ui_module()

        code_cell = module.default_cell(source="x = 1")
        markdown_cell = module.default_cell(cell_type="markdown", source="# Title")

        code_component = module.build_cell(code_cell, 0, 2)
        markdown_component = module.build_cell(markdown_cell, 1, 2)

        self.assertIsNotNone(code_component)
        self.assertIsNotNone(markdown_component)

    def test_default_notebook_state_starts_with_code_cell(self):
        module = _load_notebook_ui_module()

        state = module.default_notebook_state()

        self.assertEqual(state["cells"][0]["type"], "code")

    def test_markdown_cells_render_as_document_blocks_while_code_cells_stay_framed(self):
        module = _load_notebook_ui_module()

        code_component = module.build_cell(module.default_cell(source="x = 1"), 0, 2)
        markdown_component = module.build_cell(module.default_cell(cell_type="markdown", source="# Title"), 1, 2)

        code_style = code_component.to_plotly_json()["props"]["style"]
        markdown_style = markdown_component.to_plotly_json()["props"]["style"]

        self.assertIn("border", code_style)
        self.assertEqual(code_style.get("borderLeft"), "none")
        self.assertEqual(markdown_style.get("border"), "none")
        self.assertEqual(markdown_style.get("boxShadow"), "none")

    def test_markdown_preview_uses_tighter_vertical_padding(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('"padding": "12px 16px 4px 16px"', source)
        self.assertNotIn('"padding": "12px 16px"', source)

    def test_markdown_preview_and_edit_join_right_side_action_group(self):
        module = _load_notebook_ui_module()

        markdown_component = module.build_cell(module.default_cell(cell_type="markdown", source="# Title"), 1, 2)
        controls = markdown_component.children[0].children[0].children[3]
        labels = []
        for child in controls.children:
            labels.append(getattr(child, "children", None))

        self.assertEqual(labels[0], "Preview")
        self.assertEqual(labels[1], "Edit")
        self.assertEqual(labels[2], "✕")
        self.assertNotIn("↑", labels)
        self.assertNotIn("↓", labels)

    def test_code_cells_do_not_duplicate_markdown_delete_button_ids(self):
        module = _load_notebook_ui_module()

        code_cell = module.default_cell(source="x = 1")
        code_component = module.build_cell(code_cell, 0, 1)
        ids = []

        def walk(node):
            if node is None:
                return
            if isinstance(node, (list, tuple)):
                for item in node:
                    walk(item)
                return
            node_id = getattr(node, "id", None)
            if node_id is not None:
                ids.append(node_id)
            walk(getattr(node, "children", None))

        walk(code_component)
        delete_ids = [node_id for node_id in ids if node_id == {"type": "nb-cell-delete", "index": code_cell["id"]}]
        self.assertEqual(len(delete_ids), 1)

    def test_markdown_edit_action_uses_red_visual_treatment(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('"color": "#991b1b"', source)
        self.assertIn('"border": "1px solid rgba(185,28,28,0.18)"', source)

    def test_result_gutter_uses_single_dark_blue_for_results(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")
        self.assertIn('"color": "#b42318" if is_error else "#001f41" if value else "#b0bec5"', source)

    def test_notebook_reuses_single_documentation_blue_across_actions(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertNotIn('#1d4ed8', source)
        self.assertNotIn('#4338ca', source)
        self.assertNotIn('#1e3a8a', source)
        self.assertIn('"color": "#001f41"', source)

    def test_result_gutter_supports_table_like_columns(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")
        self.assertIn('def build_notebook_results(', source)
        self.assertIn('result_lines: list[dict] | list[str] | None = None,', source)
        self.assertIn('name_col_width = max(72, min(220, max(label_lengths or [0]) * 9 + 16))', source)
        self.assertIn('"gridTemplateColumns": f"{name_col_width}px minmax(0, 1fr) 56px"', source)
        self.assertIn('"Data"', source)
        self.assertIn('"Value"', source)
        self.assertIn('"Count"', source)

    def test_result_gutter_renders_inline_matrix_tables(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('kind = str(line.get("kind", "") or "")', source)
        self.assertIn('row_span = int(line.get("row_span", 1) or 1)', source)
        self.assertIn('matrix_rows = line.get("matrix", [])', source)
        self.assertIn('"display": "grid"', source)
        self.assertIn('"gridTemplateColumns": "repeat("', source)

    def test_code_cells_render_single_inline_results_column(self):
        module = _load_notebook_ui_module()

        code_cell = module.default_cell(source="A = eye(3)")
        code_cell["outputs"] = [
            {
                "name": "A",
                "kind": "matrix",
                "value": "3x3 matrix",
                "count": "3x3",
                "row_span": 3,
                "matrix": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
            }
        ]

        code_component = module.build_cell(code_cell, 0, 1)
        row_component = code_component.children[0]
        results_component = row_component.children[1].children[0]
        rendered = results_component.to_plotly_json()

        self.assertEqual(rendered["props"]["id"]["type"], "nb-cell-results")
        self.assertIn("gridTemplateColumns", rendered["props"]["children"][0].to_plotly_json()["props"]["style"])

    def test_code_cells_do_not_render_a_results_header_row(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertNotIn('id=f"nb-cell-results-header-{cell_id}"', source)
        self.assertNotIn('html.Div("Expression"', source)
        self.assertNotIn('html.Div("Size"', source)
        self.assertIn('build_notebook_results(outputs)', source)
        self.assertIn('"width": "440px"', source)

    def test_empty_result_gutter_defaults_to_four_rows(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('NOTEBOOK_ROWS = 4', source)
        self.assertIn('min_rows: int = NOTEBOOK_ROWS,', source)

    def test_results_column_uses_zero_top_padding(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('"padding": "0 10px 8px 0"', source)

    def test_cells_container_renders_top_inserter_before_first_cell(self):
        source = NOTEBOOK_UI.read_text(encoding="utf-8")

        self.assertIn('items = [_build_cell_inserter("__start__")]', source)


if __name__ == "__main__":
    unittest.main()
