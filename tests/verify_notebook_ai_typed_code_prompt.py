from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE_SYNC = ROOT / "assets" / "notebook_live_sync.js"


def expect_contains(label: str, source: str, needle: str) -> None:
    print(f"[debug][notebook-ai-typed-code] checking {label}")
    print(f"[debug][notebook-ai-typed-code] expected snippet: {needle}")
    if needle not in source:
        print(f"[debug][notebook-ai-typed-code] missing {label}")
        raise AssertionError(f"Missing expected snippet for {label}: {needle}")
    print(f"[debug][notebook-ai-typed-code] found {label}")


def main() -> None:
    source = LIVE_SYNC.read_text(encoding="utf-8")

    print(f"[debug][notebook-ai-typed-code] source path: {LIVE_SYNC}")
    expect_contains(
        "typed language rule",
        source,
        "If the user gives typed code from C, C++, Java, or similar languages, convert it into notebook syntax",
    )
    expect_contains(
        "type removal rule",
        source,
        "remove type keywords like double, float, int, or const",
    )
    expect_contains(
        "runnable snippet rule",
        source,
        "return a runnable notebook snippet, not just a single rewritten line",
    )
    expect_contains(
        "placeholder rule",
        source,
        "add placeholder/default assignments for any referenced variables that are missing from the current notebook context",
    )
    print("[debug][notebook-ai-typed-code] verification complete")


if __name__ == "__main__":
    main()
