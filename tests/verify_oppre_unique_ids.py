"""
Verification script: OPPre layout has no duplicate Dash component IDs.

This helps catch Dash DuplicateIdError without opening the browser.
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
            print(f"[verify][oppre-ids] id={nid}", flush=True)
            ids.append(nid)
        kids = _get_children(item)
        if kids is not None:
            _walk(kids, ids)


def main() -> None:
    print("[verify][oppre-ids] start", flush=True)
    from OPPre import build_oppre_layout

    layout = build_oppre_layout()
    print(f"[verify][oppre-ids] layout_type={type(layout)}", flush=True)

    ids: list[str] = []
    _walk(layout, ids)
    print(f"[verify][oppre-ids] ids_collected={len(ids)}", flush=True)

    counts = Counter(ids)
    dupes = [(k, v) for (k, v) in counts.items() if v > 1]
    print(f"[verify][oppre-ids] unique_ids={len(counts)} dupes={len(dupes)}", flush=True)

    if dupes:
        for k, v in sorted(dupes, key=lambda kv: (-kv[1], kv[0]))[:25]:
            print(f"[verify][oppre-ids] DUP id={k} count={v}", flush=True)
        raise SystemExit("[verify][oppre-ids] FAIL: duplicate IDs found")

    print("[verify][oppre-ids] PASS", flush=True)


if __name__ == "__main__":
    main()

