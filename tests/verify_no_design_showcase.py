"""
Verification script: Design Showcase removed.

Runs without starting Dash. Confirms that:
- the Design Showcase UI tab is not present in the layout source
- tab routing no longer references design-showcase outputs/branches
- the ui/design_showcase.py module is gone
"""

from __future__ import annotations

from pathlib import Path


def _read_text(path: Path) -> str:
    print(f"[verify][no-design-showcase] read: {path}", flush=True)
    text = path.read_text(encoding="utf-8")
    print(f"[verify][no-design-showcase] read_ok: bytes={len(text.encode('utf-8'))}", flush=True)
    return text


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    print(f"[verify][no-design-showcase] repo_root={repo_root}", flush=True)

    layout_py = repo_root / "ui" / "layout.py"
    tab_manager_py = repo_root / "callbacks" / "tab_manager.py"
    showcase_py = repo_root / "ui" / "design_showcase.py"

    print(f"[verify][no-design-showcase] check_exists layout_py={layout_py.exists()}", flush=True)
    print(f"[verify][no-design-showcase] check_exists tab_manager_py={tab_manager_py.exists()}", flush=True)
    print(f"[verify][no-design-showcase] check_exists showcase_py={showcase_py.exists()}", flush=True)

    if showcase_py.exists():
        raise SystemExit("[verify][no-design-showcase] FAIL: ui/design_showcase.py still exists")
    print("[verify][no-design-showcase] OK: ui/design_showcase.py removed", flush=True)

    layout_src = _read_text(layout_py)
    print("[verify][no-design-showcase] scan layout for tokens", flush=True)
    assert "Design Showcase" not in layout_src, "layout.py still contains label 'Design Showcase'"
    print("[verify][no-design-showcase] OK: layout.py has no 'Design Showcase' label", flush=True)
    assert "design-showcase" not in layout_src, "layout.py still contains 'design-showcase' token"
    print("[verify][no-design-showcase] OK: layout.py has no 'design-showcase' token", flush=True)
    assert "design-showcase-content" not in layout_src, "layout.py still contains 'design-showcase-content' id"
    print("[verify][no-design-showcase] OK: layout.py has no 'design-showcase-content' id", flush=True)

    tab_manager_src = _read_text(tab_manager_py)
    print("[verify][no-design-showcase] scan tab_manager for tokens", flush=True)
    assert "design-showcase-content" not in tab_manager_src, "tab_manager.py still references 'design-showcase-content'"
    print("[verify][no-design-showcase] OK: tab_manager.py has no 'design-showcase-content'", flush=True)
    assert "active_folder == 'design-showcase'" not in tab_manager_src, "tab_manager.py still has a design-showcase branch"
    print("[verify][no-design-showcase] OK: tab_manager.py has no design-showcase branch", flush=True)

    print("[verify][no-design-showcase] PASS", flush=True)


if __name__ == "__main__":
    print("[verify][no-design-showcase] start", flush=True)
    main()
    print("[verify][no-design-showcase] done", flush=True)

