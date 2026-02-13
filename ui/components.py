"""
Reusable UI components for OPView cards and controls.

This module provides small, composable functions to eliminate code duplication
and make card building simple and consistent.
"""

from dash import html, dcc
from typing import List, Dict, Any, Optional


# ============================================================================
# Card Structure Components
# ============================================================================

def card_header(title: str) -> html.Div:
    """
    Create a standardized card header with accent bar and title.

    Args:
        title: The title text to display

    Returns:
        html.Div containing the header structure

    Example:
        >>> card_header("Grain Details")
    """
    return html.Div([
        html.Span(className='dataset-accent'),
        html.H3(title, className='dataset-title')
    ], className='dataset-header')


def card_container(title: str, content: List) -> html.Div:
    """
    Create a complete card with header and content.

    Args:
        title: Card title
        content: List of Dash components to put in the card body

    Returns:
        Complete card component

    Example:
        >>> card_container("My Card", [
        ...     controls_section([...]),
        ...     graphs_section([...])
        ... ])
    """
    return html.Div([
        card_header(title),
        html.Div(content, className='textdata-graphs')
    ], className='dataset-block textdata-card')


def controls_section(controls: List) -> html.Div:
    """
    Wrap multiple controls in a controls container.

    Args:
        controls: List of control components

    Returns:
        Controls container
    """
    return html.Div(controls, className='textdata-controls')


def graphs_section(graphs: List) -> html.Div:
    """
    Wrap multiple graphs in a graphs container.

    Args:
        graphs: List of graph components

    Returns:
        Graphs container
    """
    return html.Div(graphs, className='textdata-graphs')


# ============================================================================
# Control Components
# ============================================================================

def labeled_control(label: str, control_component,
                   control_class: str = 'textdata-control') -> html.Div:
    """
    Create a labeled control group.

    Args:
        label: Label text
        control_component: The Dash component (dropdown, slider, etc.)
        control_class: CSS class for the control wrapper

    Returns:
        Labeled control div

    Example:
        >>> labeled_control("Time Step", dcc.Dropdown(...))
    """
    return html.Div([
        html.Label(label, className='textdata-label'),
        control_component
    ], className=control_class)


def time_dropdown(component_id: str, times: List[float],
                 default_index: int = 0) -> html.Div:
    """
    Create a standardized time step dropdown control.

    Args:
        component_id: The Dash component ID
        times: List of time values
        default_index: Index of default time selection

    Returns:
        Labeled time dropdown control

    Example:
        >>> time_dropdown('grain-dist-time', [0, 0.5, 1.0, 1.5])
    """
    time_options = format_time_options(times)
    default_value = time_options[default_index]['value'] if time_options else None

    dropdown = dcc.Dropdown(
        id=component_id,
        options=time_options,
        value=default_value,
        clearable=False,
        searchable=False,
        className='textdata-input'
    )

    return labeled_control('Time Step', dropdown)


def component_checklist(component_id: str, options: List[Dict[str, str]],
                       default_values: List[str],
                       label: str = 'Components',
                       class_name: str = 'textdata-radio') -> html.Div:
    """
    Create a component selection checklist.

    Args:
        component_id: The Dash component ID
        options: List of {label, value} dicts
        default_values: List of default selected values
        label: Label text
        class_name: CSS class for checklist

    Returns:
        Labeled checklist control

    Example:
        >>> component_checklist(
        ...     'stress-components',
        ...     [{'label': 'σ_xx', 'value': 'Sigma_xx'}],
        ...     ['Sigma_xx']
        ... )
    """
    checklist = dcc.Checklist(
        id=component_id,
        options=options,
        value=default_values,
        className=class_name,
        labelStyle={'display': 'inline-flex', 'alignItems': 'center',
                   'marginRight': '12px'},
        inputStyle={'marginRight': '4px'}
    )

    return labeled_control(label, checklist)


def bins_slider(component_id: str, min_bins: int = 5, max_bins: int = 50,
               step: int = 5, default: int = 15) -> html.Div:
    """
    Create a standardized bins slider for histograms.

    Args:
        component_id: The Dash component ID
        min_bins: Minimum number of bins
        max_bins: Maximum number of bins
        step: Step size
        default: Default value

    Returns:
        Labeled slider control
    """
    slider = dcc.Slider(
        id=component_id,
        min=min_bins,
        max=max_bins,
        step=step,
        value=default,
        marks={i: str(i) for i in range(min_bins, max_bins + 1, step * 2)},
        className='textdata-slider'
    )

    return labeled_control('Number of Bins', slider)


def chart_style_radio(component_id: str,
                     options: List[Dict[str, str]] = None) -> html.Div:
    """
    Create a chart style radio button control.

    Args:
        component_id: The Dash component ID
        options: List of style options (default: bar/line)

    Returns:
        Labeled radio control
    """
    if options is None:
        options = [
            {'label': 'Bar', 'value': 'bar'},
            {'label': 'Line', 'value': 'line'}
        ]

    radio = dcc.RadioItems(
        id=component_id,
        options=options,
        value=options[0]['value'],
        inline=True,
        className='textdata-radio',
        labelStyle={'display': 'inline-flex', 'alignItems': 'center',
                   'marginRight': '12px'},
        inputStyle={'marginRight': '4px'}
    )

    return labeled_control('Chart Style', radio)


def graph(component_id: str, figure=None, class_name: str = 'textdata-plot') -> dcc.Graph:
    """
    Create a standardized graph component.

    Args:
        component_id: The Dash component ID
        figure: Optional initial figure
        class_name: CSS class

    Returns:
        Graph component
    """
    return dcc.Graph(id=component_id, figure=figure, className=class_name)


# ============================================================================
# Data Formatting Utilities
# ============================================================================

def format_time_options(times: List[float]) -> List[Dict[str, str]]:
    """
    Format time values into Dash dropdown options.

    Handles integer times (displayed without decimals) and float times
    (displayed with minimal precision).

    Args:
        times: List of time values

    Returns:
        List of {label, value} dicts for dropdown options

    Example:
        >>> format_time_options([0.0, 1.0, 1.5, 2.0])
        [{'label': '0', 'value': '0.0'},
         {'label': '1', 'value': '1.0'},
         {'label': '1.5', 'value': '1.5'},
         {'label': '2', 'value': '2.0'}]
    """
    options = []
    for t in times:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        options.append({'label': label, 'value': str(t)})
    return options


def create_tensor_component_options(prefix: str = 'σ') -> List[Dict[str, str]]:
    """
    Create standard tensor component options.

    Args:
        prefix: Symbol prefix (σ for stress, ε for strain, etc.)

    Returns:
        List of component options

    Example:
        >>> create_tensor_component_options('σ')
        [{'label': 'σ_xx', 'value': 'Sigma_xx'}, ...]
    """
    return [
        {'label': f'{prefix}_xx', 'value': f'{prefix.capitalize()}_xx'},
        {'label': f'{prefix}_yy', 'value': f'{prefix.capitalize()}_yy'},
        {'label': f'{prefix}_zz', 'value': f'{prefix.capitalize()}_zz'},
        {'label': f'{prefix}_xy', 'value': f'{prefix.capitalize()}_xy'},
        {'label': f'{prefix}_yz', 'value': f'{prefix.capitalize()}_yz'},
        {'label': f'{prefix}_xz', 'value': f'{prefix.capitalize()}_xz'},
    ]


# ============================================================================
# High-Level Card Building Helpers
# ============================================================================

def build_simple_card(title: str, controls: List = None,
                     graphs: List = None) -> html.Div:
    """
    Build a complete card with controls and graphs.

    This is a simple helper that combines card_container, controls_section,
    and your components. Use this for straightforward cards.

    Args:
        title: Card title
        controls: List of control components (dropdowns, sliders, etc.)
        graphs: List of graph components

    Returns:
        Complete card component

    Example:
        >>> build_simple_card(
        ...     title="Grain Details",
        ...     controls=[
        ...         time_dropdown('time', times),
        ...         chart_style_radio('mode')
        ...     ],
        ...     graphs=[
        ...         graph('main-plot'),
        ...         graph('secondary-plot')
        ...     ]
        ... )
    """
    content = []

    if controls:
        content.append(controls_section(controls))

    if graphs:
        content.extend(graphs)

    return card_container(title, content)
