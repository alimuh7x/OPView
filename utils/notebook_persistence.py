"""Helpers for notebook JSON save/load payloads."""

from __future__ import annotations


NOTEBOOK_JSON_VERSION = 3


def serialize_notebook_cells(cells: list[dict] | None) -> dict:
    """Build the canonical JSON payload for notebook save/export."""
    normalized = []
    for cell in cells or []:
        normalized.append(
            {
                "id": cell.get("id") or "",
                "type": cell.get("type", "code"),
                "source": cell.get("source", ""),
            }
        )
    return {
        "version": NOTEBOOK_JSON_VERSION,
        "cells": normalized,
    }


def deserialize_notebook_cells(payload: dict | None) -> list[dict]:
    """Normalize saved JSON into rerunnable notebook cells."""
    cells = []
    for cell in (payload or {}).get("cells", []) or []:
        cells.append(
            {
                "id": cell.get("id") or "",
                "type": cell.get("type", "code"),
                "source": cell.get("source", ""),
                "outputs": [],
                "dirty": False,
            }
        )
    return cells
