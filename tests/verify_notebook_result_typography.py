from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE_SYNC = ROOT / "assets" / "notebook_live_sync.js"


def expect_contains(label: str, source: str, needle: str) -> None:
    print(f"[debug][notebook-result-typography] checking {label}")
    print(f"[debug][notebook-result-typography] expected snippet: {needle}")
    if needle not in source:
        print(f"[debug][notebook-result-typography] missing {label}")
        raise AssertionError(f"Missing expected snippet for {label}: {needle}")
    print(f"[debug][notebook-result-typography] found {label}")


def main() -> None:
    source = LIVE_SYNC.read_text(encoding="utf-8")

    print(f"[debug][notebook-result-typography] source path: {LIVE_SYNC}")
    expect_contains("result row height", source, 'row.style.height = "30px";')
    expect_contains("result row line height", source, 'row.style.lineHeight = "30px";')
    expect_contains("result row font size", source, 'row.style.fontSize = "12px";')
    expect_contains(
        "result cell base",
        source,
        'const cellBase = "padding:0 6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;height:30px;line-height:30px;";',
    )
    print("[debug][notebook-result-typography] verification complete")


if __name__ == "__main__":
    main()
