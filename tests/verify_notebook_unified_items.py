from __future__ import annotations

import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
NOTEBOOK_UI = ROOT / "ui" / "calculation_notebook.py"
NOTEBOOK_MANAGER = ROOT / "callbacks" / "notebook_manager.py"
NOTEBOOK_PERSISTENCE = ROOT / "utils" / "notebook_persistence.py"
NOTEBOOK_DRAG_JS = ROOT / "assets" / "notebook_plot_panel.js"
STYLE_CSS = ROOT / "assets" / "style.css"


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    print("[verify][unified-notebook] loading modules")
    ui = _load_module("verify_notebook_ui", NOTEBOOK_UI)
    persistence = _load_module("verify_notebook_persistence", NOTEBOOK_PERSISTENCE)

    print("[verify][unified-notebook] creating default plot cell")
    plot_cell = ui.default_cell(cell_type="plot")
    print(f"[verify][unified-notebook] plot cell id={plot_cell['id']}")
    print(f"[verify][unified-notebook] plot cell type={plot_cell['type']}")
    print(f"[verify][unified-notebook] plot spec keys={sorted(plot_cell['plot_spec'].keys())}")

    print("[verify][unified-notebook] building inline plot component")
    plot_component = ui.build_cell(plot_cell, 1, 3)
    plot_json = plot_component.to_plotly_json()
    print(f"[verify][unified-notebook] plot wrapper class={plot_json['props'].get('className')}")
    print(f"[verify][unified-notebook] plot wrapper draggable={plot_json['props'].get('draggable')}")
    print(f"[verify][unified-notebook] plot wrapper overflow={plot_json['props']['style'].get('overflow')}")
    print(f"[verify][unified-notebook] plot wrapper width={plot_json['props']['style'].get('width')}")
    print(f"[verify][unified-notebook] plot wrapper maxWidth={plot_json['props']['style'].get('maxWidth')}")
    print(f"[verify][unified-notebook] plot wrapper boxSizing={plot_json['props']['style'].get('boxSizing')}")

    print("[verify][unified-notebook] building code and markdown components for resize checks")
    code_component = ui.build_cell(ui.default_cell(source="x = 1"), 0, 3)
    markdown_component = ui.build_cell(ui.default_cell(cell_type="markdown", source="# Notes"), 1, 3)
    code_style = code_component.to_plotly_json()["props"]["style"]
    markdown_style = markdown_component.to_plotly_json()["props"]["style"]
    print(f"[verify][unified-notebook] code overflow={code_style.get('overflow')}")
    print(f"[verify][unified-notebook] markdown overflow={markdown_style.get('overflow')}")
    print(f"[verify][unified-notebook] code width={code_style.get('width')}")
    print(f"[verify][unified-notebook] markdown width={markdown_style.get('width')}")
    print(f"[verify][unified-notebook] code maxWidth={code_style.get('maxWidth')} boxSizing={code_style.get('boxSizing')}")
    print(f"[verify][unified-notebook] markdown maxWidth={markdown_style.get('maxWidth')} boxSizing={markdown_style.get('boxSizing')}")
    print(f"[verify][unified-notebook] default code column={ui.default_cell(source='x = 1').get('column')}")
    print(f"[verify][unified-notebook] default code panel_width={ui.default_cell(source='x = 1').get('panel_width')}")
    print(f"[verify][unified-notebook] default left_column_width_pct={ui.default_notebook_state().get('layout', {}).get('left_column_width_pct')}")

    print("[verify][unified-notebook] serializing mixed notebook items")
    cells = [
        ui.default_cell(source="x = linspace(0, 1, 5)"),
        ui.default_cell(cell_type="markdown", source="# Notes"),
        plot_cell,
    ]
    plot_cell["plot_spec"] = {
        "x_var": "x",
        "y_vars": ["x"],
        "plot_type": "lines",
        "title": "x profile",
        "x_title": "x",
        "y_title": "value",
    }
    payload = persistence.serialize_notebook_cells(cells)
    print(f"[verify][unified-notebook] payload version={payload['version']}")
    print(f"[verify][unified-notebook] payload layout={payload.get('layout')}")
    print(f"[verify][unified-notebook] payload item types={[cell['type'] for cell in payload['cells']]}")
    print(f"[verify][unified-notebook] payload plot spec={payload['cells'][2].get('plot_spec')}")

    print("[verify][unified-notebook] restoring serialized payload")
    restored = persistence.deserialize_notebook_cells(payload)
    print(f"[verify][unified-notebook] restored item types={[cell['type'] for cell in restored]}")
    print(f"[verify][unified-notebook] restored plot spec={restored[2].get('plot_spec')}")

    print("[verify][unified-notebook] checking manager and drag script markers")
    manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
    drag_source = NOTEBOOK_DRAG_JS.read_text(encoding="utf-8")
    style_source = STYLE_CSS.read_text(encoding="utf-8")
    checks = [
        ('Input({"type": "nb-add-plot",        "index": ALL}, "n_clicks")', manager_source),
        ('Input({"type": "nb-cell-move-left",', manager_source),
        ('Input({"type": "nb-cell-move-right",', manager_source),
        ('Input("nb-item-order-input", "value")', manager_source),
        ('Input("nb-item-width-input", "value")', manager_source),
        ('Input("nb-column-split-input", "value")', manager_source),
        ('Output({"type": "nb-plot-item-graph", "index": ALL}, "figure")', manager_source),
        ('id="notebook-cells-column-left"', NOTEBOOK_UI.read_text(encoding="utf-8")),
        ('id="notebook-cells-column-right"', NOTEBOOK_UI.read_text(encoding="utf-8")),
        ('id="notebook-columns-splitter"', NOTEBOOK_UI.read_text(encoding="utf-8")),
        ('function wireNotebookItems()', drag_source),
        ('setHiddenValue("nb-item-order-input"', drag_source),
        ('setHiddenValue("nb-item-width-input"', drag_source),
        ('setHiddenValue("nb-column-split-input"', drag_source),
        ('.nb-item-drag-handle', drag_source),
        ('.nb-item-resize-handle', drag_source),
        ('card.dataset.dragReady', drag_source),
        ('event.target && event.target.closest(".nb-item-drag-handle")', drag_source),
        ('opacity: 1;', style_source),
        ('pointer-events: auto;', style_source),
    ]
    for marker, blob in checks:
        print(f"[verify][unified-notebook] marker present={marker in blob} :: {marker}")
        if marker not in blob:
            raise AssertionError(f"Missing marker: {marker}")

    print("[verify][unified-notebook] all checks passed")


if __name__ == "__main__":
    main()
