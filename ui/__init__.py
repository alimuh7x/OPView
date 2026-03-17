"""
UI components module for OPView.

Provides both functional and object-oriented APIs for building UI:
- Functional API: Simple functions for quick layouts (backward compatible)
- OOP API: Flexible component classes with full control over styling
- Callback API: Factory functions for creating reusable callbacks
"""

# Functional API (backward compatible)
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

# Object-Oriented API (new component system)
from .flex_components import (
    # Base classes
    Component,
    Flex,

    # Layout variants
    Row,
    Column,
    MainTabFlex,
    ComparisonTabFlex,

    # Components
    Dropdown,
    Slider,
    RangeSlider,
    TextInput,
    Button,
    Graph,
    Label,
    RadioItems,
    Checklist,
    Card,

    # Helpers
    LabeledComponent,
    labeled,
)

# CSS constants
from .styles import CSS

# Card builders
from .cards import (
    TimeSeriesCard,
    HistogramCard,
    TimeSeriesDetailsCard,
    CardFactory,
    build_stress_strain_card,
    build_grain_distribution_card,
    build_crss_card,
)

# UI Manager
from .ui_manager import UIManager

# Layout builder
from .layout import build_app_layout

# Graphs tab
from .graphs import (
    build_graphs_tab_layout,
    build_graph_card,
    get_textdata_files,
    build_multifile_panel,
    build_multifile_figure,
)
from .formula_graphs import (
    build_formula_panel,
    build_formula_figure,
)

# Callback factories
from .callbacks import (
    create_histogram_callback,
    create_time_series_callback,
    create_component_selection_callback,
    create_multi_output_callback,
    CallbackRegistry,
    register_all_callbacks,
)

__all__ = [
    # Functional API
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

    # OOP API - Base
    'Component',
    'Flex',

    # OOP API - Layouts
    'Row',
    'Column',
    'MainTabFlex',
    'ComparisonTabFlex',

    # OOP API - Components
    'Dropdown',
    'Slider',
    'RangeSlider',
    'TextInput',
    'Button',
    'Graph',
    'Label',
    'RadioItems',
    'Checklist',
    'Card',

    # OOP API - Helpers
    'LabeledComponent',
    'labeled',

    # CSS
    'CSS',

    # Card Builders
    'TimeSeriesCard',
    'HistogramCard',
    'TimeSeriesDetailsCard',
    'CardFactory',
    'build_stress_strain_card',
    'build_grain_distribution_card',
    'build_crss_card',

    # UI Manager
    'UIManager',

    # Layout
    'build_app_layout',

    # Graphs tab
    'build_graphs_tab_layout',
    'build_graph_card',
    'get_textdata_files',
    'build_multifile_panel',
    'build_multifile_figure',
    'build_formula_panel',
    'build_formula_figure',

    # Callback API
    'create_histogram_callback',
    'create_time_series_callback',
    'create_component_selection_callback',
    'create_multi_output_callback',
    'CallbackRegistry',
    'register_all_callbacks',
]
