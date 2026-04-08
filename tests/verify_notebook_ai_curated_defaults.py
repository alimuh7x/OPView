from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE_SYNC = ROOT / "assets" / "notebook_live_sync.js"


def expect_contains(label: str, source: str, needle: str) -> None:
    print(f"[debug][notebook-ai-defaults] checking {label}")
    print(f"[debug][notebook-ai-defaults] expected snippet: {needle}")
    if needle not in source:
        print(f"[debug][notebook-ai-defaults] missing {label}")
        raise AssertionError(f"Missing expected snippet for {label}: {needle}")
    print(f"[debug][notebook-ai-defaults] found {label}")


def main() -> None:
    source = LIVE_SYNC.read_text(encoding="utf-8")

    print(f"[debug][notebook-ai-defaults] source path: {LIVE_SYNC}")
    expect_contains("defaults header", source, "Important defaults:")
    expect_contains("linspace default", source, "linspace(start, stop, num=50)")
    expect_contains("arange default", source, "arange(start, stop, step=1)")
    expect_contains("cfl default", source, "cfl_dt(dx, u, cfl=1)")
    expect_contains("diffusion default", source, "diffusion_dt(dx, D, f=0.5)")
    expect_contains("plot default", source, 'plot(x, y, type=\\"line\\")')
    print("[debug][notebook-ai-defaults] verification complete")


if __name__ == "__main__":
    main()
