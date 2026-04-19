"""
Verification script: OPView (viewer app) only exposes Single/Multi/Custom Graph tabs.

This is source-level on purpose (no Dash server needed).
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    layout_py = root / "ui" / "layout.py"
    opview_py = root / "OPView.py"

    print(f"[verify][opview-viewer] root={root}", flush=True)
    print(f"[verify][opview-viewer] reading layout={layout_py}", flush=True)
    src = layout_py.read_text(encoding="utf-8")
    print(f"[verify][opview-viewer] bytes={len(src.encode('utf-8'))}", flush=True)

    must_have = ["Single View", "Multi View", "Custom Graph"]
    must_not_have = [
        "Formula Plot",
        "Calculation Notebook",
        "Initializations Explorer",
        "Mechanical Loads Explorer",
        "Design Showcase",
    ]

    for label in must_have:
        print(f"[verify][opview-viewer] check_have {label!r}", flush=True)
        assert label in src, f"Missing expected tab label: {label}"
        print(f"[verify][opview-viewer] ok_have {label!r}", flush=True)

    for label in must_not_have:
        print(f"[verify][opview-viewer] check_not_have {label!r}", flush=True)
        assert label not in src, f"Unexpected tab label still present: {label}"
        print(f"[verify][opview-viewer] ok_not_have {label!r}", flush=True)

    print(f"[verify][opview-viewer] reading opview={opview_py}", flush=True)
    op_src = opview_py.read_text(encoding="utf-8")
    print(f"[verify][opview-viewer] opview_bytes={len(op_src.encode('utf-8'))}", flush=True)

    forbidden_regs = [
        "FormulaCallbackManager",
        "NotebookCallbackManager",
        "InitializationsExplorerCallbackManager",
        "MechanicalLoadsCallbackManager",
    ]
    for token in forbidden_regs:
        print(f"[verify][opview-viewer] check_not_register {token!r}", flush=True)
        assert token not in op_src, f"OPView.py still references {token}"
        print(f"[verify][opview-viewer] ok_not_register {token!r}", flush=True)

    print("[verify][opview-viewer] PASS", flush=True)


if __name__ == "__main__":
    main()

