from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
NOTEBOOK_UI = ROOT / "ui" / "calculation_notebook.py"
NOTEBOOK_MANAGER = ROOT / "callbacks" / "notebook_manager.py"
PLOT_PANEL_JS = ROOT / "assets" / "notebook_plot_panel.js"


def expect_contains(label: str, source: str, needle: str) -> None:
    print(f"[debug][notebook-plot-panel] checking {label}")
    print(f"[debug][notebook-plot-panel] expected snippet: {needle}")
    if needle not in source:
        print(f"[debug][notebook-plot-panel] missing {label}")
        raise AssertionError(f"Missing expected snippet for {label}: {needle}")
    print(f"[debug][notebook-plot-panel] found {label}")


def main() -> None:
    ui_source = NOTEBOOK_UI.read_text(encoding="utf-8")
    manager_source = NOTEBOOK_MANAGER.read_text(encoding="utf-8")
    js_source = PLOT_PANEL_JS.read_text(encoding="utf-8")

    print(f"[debug][notebook-plot-panel] ui path: {NOTEBOOK_UI}")
    print(f"[debug][notebook-plot-panel] manager path: {NOTEBOOK_MANAGER}")
    print(f"[debug][notebook-plot-panel] js path: {PLOT_PANEL_JS}")

    expect_contains("width store", ui_source, 'dcc.Store(id="nb-plots-panel-width", data=460)')
    expect_contains("order store", ui_source, 'dcc.Store(id="nb-plots-order", data=[])')
    expect_contains("resize handle", ui_source, 'id="nb-plots-resize-handle"')
    expect_contains("plots shell", ui_source, 'id="notebook-plots-shell"')
    expect_contains("width sync callback", manager_source, 'Output("nb-plots-panel-width", "data")')
    expect_contains("order sync callback", manager_source, 'Output("nb-plots-order", "data")')
    expect_contains("drag card class", manager_source, 'className="nb-plot-draggable-card"')
    expect_contains("drag handle class", manager_source, 'className="nb-plot-drag-handle"')
    expect_contains("resize wire", js_source, 'function wireResizeHandle()')
    expect_contains("drag wire", js_source, 'function wireDraggableCards()')
    expect_contains("width input sync", js_source, 'setHiddenValue("nb-plots-width-input"')
    expect_contains("order input sync", js_source, 'setHiddenValue("nb-plots-order-input"')
    print("[debug][notebook-plot-panel] verification complete")


if __name__ == "__main__":
    main()
