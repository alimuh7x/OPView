from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
STYLE_CSS = ROOT / "assets" / "style.css"
NOTEBOOK_UI = ROOT / "ui" / "calculation_notebook.py"


def expect_contains(label: str, source: str, needle: str) -> None:
    print(f"[debug][notebook-markdown-typography] checking {label}")
    print(f"[debug][notebook-markdown-typography] expected snippet: {needle}")
    if needle not in source:
        print(f"[debug][notebook-markdown-typography] missing {label}")
        raise AssertionError(f"Missing expected snippet for {label}: {needle}")
    print(f"[debug][notebook-markdown-typography] found {label}")


def main() -> None:
    css_source = STYLE_CSS.read_text(encoding="utf-8")
    ui_source = NOTEBOOK_UI.read_text(encoding="utf-8")

    print(f"[debug][notebook-markdown-typography] css path: {STYLE_CSS}")
    print(f"[debug][notebook-markdown-typography] ui path: {NOTEBOOK_UI}")

    expect_contains("preview base font", css_source, "font-size: 15px;")
    expect_contains("h1 size", css_source, ".nb-markdown-preview h1 { font-size: 1.55rem; }")
    expect_contains("h2 size", css_source, ".nb-markdown-preview h2 { font-size: 1.32rem; }")
    expect_contains("h3 size", css_source, ".nb-markdown-preview h3 { font-size: 1.14rem; }")
    expect_contains("h4 size", css_source, ".nb-markdown-preview h4 { font-size: 1.02rem; }")
    expect_contains("ui preview font", ui_source, '"fontSize": "15px"')

    print("[debug][notebook-markdown-typography] verification complete")


if __name__ == "__main__":
    main()
