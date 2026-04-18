"""
Verification script: Calculation Notebook has no duplicate Dash component IDs.

This catches DuplicateIdError conditions before running the Dash server by:
- building the notebook layout with the default state
- traversing all component trees
- collecting every `id` (string or dict)
- failing if any ID repeats
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any


def _iter_children(node: Any):
    if node is None:
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            yield item
        return
    yield node


def _get_children(node: Any):
    try:
        return getattr(node, "children", None)
    except Exception:
        return None


def _normalise_id(raw_id: Any) -> str | None:
    if raw_id is None:
        return None
    if isinstance(raw_id, str):
        return raw_id
    if isinstance(raw_id, dict):
        try:
            return json.dumps(raw_id, sort_keys=True, separators=(",", ":"))
        except Exception:
            return str(raw_id)
    return str(raw_id)


def _walk(node: Any, ids: list[str]) -> None:
    for item in _iter_children(node):
        if item is None:
            continue
        raw_id = getattr(item, "id", None)
        nid = _normalise_id(raw_id)
        if nid:
            ids.append(nid)
        kids = _get_children(item)
        if kids is not None:
            _walk(kids, ids)


def main() -> None:
    print("[verify][notebook-ids] start", flush=True)
    from ui.calculation_notebook import build_calculation_notebook, default_notebook_state

    state = default_notebook_state()
    print(f"[verify][notebook-ids] default_state cells={len(state.get('cells') or [])}", flush=True)

    layout = build_calculation_notebook(state)
    print(f"[verify][notebook-ids] layout_type={type(layout)}", flush=True)

    ids: list[str] = []
    _walk(layout, ids)
    print(f"[verify][notebook-ids] ids_collected={len(ids)}", flush=True)

    counts = Counter(ids)
    dupes = [(k, v) for (k, v) in counts.items() if v > 1]
    print(f"[verify][notebook-ids] unique_ids={len(counts)} dupes={len(dupes)}", flush=True)

    if dupes:
        dupes_sorted = sorted(dupes, key=lambda kv: (-kv[1], kv[0]))[:25]
        print("[verify][notebook-ids] DUPLICATES (top 25):", flush=True)
        for k, v in dupes_sorted:
            print(f"[verify][notebook-ids] dup id={k} count={v}", flush=True)
        raise SystemExit("[verify][notebook-ids] FAIL: duplicate IDs found")

    print("[verify][notebook-ids] PASS", flush=True)


if __name__ == "__main__":
    main()

