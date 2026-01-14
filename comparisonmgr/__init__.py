"""
Comparison manager module for OPView.

Wraps comparison functionality for OOP architecture.
"""

from .manager import ComparisonManager
from .helpers import (
    _comparison_panel_id,
    allowed_comparison_groups_for_tab,
    _comparison_entry_id,
    _comparison_group_name,
    _group_comparison_files,
    list_vtk_files,
    _comparison_entries,
    _comparison_entries_from_selected,
    _group_comparison_entries,
    _comparison_scalar_options,
    _comparison_palette_options,
    _parse_float,
    _clamp_range,
    _comparison_range_defaults,
    _comparison_settings,
    _comparison_dataset_config_from_entry,
    _manual_viewer_id,
    get_manual_panel,
    get_comparison_panels,
)
from .ui_builders import (
    _comparison_graph_id,
    _comparison_heatmap_data,
    build_comparison_heatmap_row,
    build_comparison_content,
)
from .callbacks import (
    register_comparison_callbacks,
    # Removed: _comparison_upload - Upload feature removed per user request
)

__all__ = [
    'ComparisonManager',
    # Helper functions
    '_comparison_panel_id',
    'allowed_comparison_groups_for_tab',
    '_comparison_entry_id',
    '_comparison_group_name',
    '_group_comparison_files',
    'list_vtk_files',
    '_comparison_entries',
    '_comparison_entries_from_selected',
    '_group_comparison_entries',
    '_comparison_scalar_options',
    '_comparison_palette_options',
    '_parse_float',
    '_clamp_range',
    '_comparison_range_defaults',
    '_comparison_settings',
    '_comparison_dataset_config_from_entry',
    '_manual_viewer_id',
    'get_manual_panel',
    'get_comparison_panels',
    # UI builders
    '_comparison_graph_id',
    '_comparison_heatmap_data',
    'build_comparison_heatmap_row',
    'build_comparison_content',
    # Callbacks
    'register_comparison_callbacks',
    # Removed: '_comparison_upload' - Upload feature removed per user request
]
