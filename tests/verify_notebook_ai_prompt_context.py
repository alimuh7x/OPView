from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE_SYNC = ROOT / "assets" / "notebook_live_sync.js"


def expect_contains(label: str, source: str, needle: str) -> None:
    print(f"[debug][notebook-ai-prompt] checking {label}")
    print(f"[debug][notebook-ai-prompt] expected snippet: {needle}")
    if needle not in source:
        print(f"[debug][notebook-ai-prompt] missing {label}")
        raise AssertionError(f"Missing expected snippet for {label}: {needle}")
    print(f"[debug][notebook-ai-prompt] found {label}")


def main() -> None:
    source = LIVE_SYNC.read_text(encoding="utf-8")

    print(f"[debug][notebook-ai-prompt] source path: {LIVE_SYNC}")
    expect_contains(
        "collision rule",
        source,
        "Do not overwrite existing notebook variables unless the user explicitly asks.",
    )
    expect_contains(
        "unique variable rule",
        source,
        "If you need a new variable, choose a unique descriptive name that does not collide with existing notebook variables.",
    )
    expect_contains(
        "missing input rule",
        source,
        "If required inputs are missing, say which variables are missing instead of inventing unsafe code.",
    )
    expect_contains("array vars context var", source, "var arrayVarsCtx = '';")
    expect_contains("array vars state", source, "nbState.array_variables")
    expect_contains("existing names section", source, "Existing notebook variable names (do not reuse unless explicitly asked):")
    expect_contains("scalar vars section", source, "Current scalar variables:")
    expect_contains("array vars section", source, "Current array variables:")
    print("[debug][notebook-ai-prompt] verification complete")


if __name__ == "__main__":
    main()
