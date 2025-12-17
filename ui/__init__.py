"""
UI components module for OPView.

Provides reusable components for building consistent UI cards and controls.
"""

from .components import (
    # Card structure
    card_header,
    card_container,
    controls_section,
    graphs_section,

    # Controls
    labeled_control,
    time_dropdown,
    component_checklist,
    bins_slider,
    chart_style_radio,
    graph,

    # Utilities
    format_time_options,
    create_tensor_component_options,

    # High-level helpers
    build_simple_card,
)

__all__ = [
    'card_header',
    'card_container',
    'controls_section',
    'graphs_section',
    'labeled_control',
    'time_dropdown',
    'component_checklist',
    'bins_slider',
    'chart_style_radio',
    'graph',
    'format_time_options',
    'create_tensor_component_options',
    'build_simple_card',
]
