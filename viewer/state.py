"""State container for each VTK viewer tab."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class ViewerState:
    """Serialisable state for a single dataset panel."""

    scalar_key: str
    scalar_label: str
    axis: str
    slice_index: int
    colorA: str
    colorB: str
    palette: str
    threshold: float
    range_min: float
    range_max: float
    file_path: str
    scale: float = 1.0
    units: Optional[str] = None
    click_count: int = 0
    first_click: Optional[float] = None
    clicked_message: Optional[str] = None
    colorscale_mode: str = "normal"  # "normal" or "dynamic"
    line_scan_y: Optional[float] = None  # Y position for horizontal line scan
    line_scan_x: Optional[float] = None  # X position for vertical line scan
    line_scan_direction: str = "horizontal"  # "horizontal" or "vertical"
    click_mode: str = "range"  # "range" or "linescan" - what clicking does
    line_overlay_visible: bool = True  # Toggle for showing scan indicator
    interfaces_overlay_visible: bool = False  # Show Interfaces (band) overlay

    def to_dict(self) -> Dict[str, Any]:
        """Return JSON-serialisable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]], fallback: "ViewerState") -> "ViewerState":
        """Restore state from dict or return fallback."""
        if not data:
            return fallback
        return cls(**{**fallback.to_dict(), **data})


def initial_state(
    scalar_key: str,
    scalar_label: str,
    axis: str,
    slice_index: int,
    stats: Dict[str, float],
    colorA: str,
    colorB: str,
    file_path: str,
    scale: float = 1.0,
    units: Optional[str] = None,
    palette: str = "aqua-fire",
) -> ViewerState:
    """Create a ViewerState with defaults derived from dataset statistics."""
    threshold = (stats["min"] + stats["max"]) / 2
    return ViewerState(
        scalar_key=scalar_key,
        scalar_label=scalar_label,
        axis=axis,
        slice_index=slice_index,
        colorA=colorA,
        colorB=colorB,
        palette=palette,
        threshold=threshold,
        range_min=stats["min"],
        range_max=stats["max"],
        file_path=file_path,
        scale=scale,
        units=units,
    )
