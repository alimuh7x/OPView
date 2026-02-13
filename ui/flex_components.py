"""
Object-oriented component system for building flexible UI layouts.

This module provides a component-based architecture where:
- Each UI element is a class with style properties (width, height, margin, etc.)
- Flex containers manage layout and can be nested
- Components have sensible defaults that can be overridden
- Everything composes together like Lego blocks
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dash import html, dcc
import dash_mantine_components as dmc
from .styles import CSS


# =============================================================================
# Base Component Class
# =============================================================================

class Component(ABC):
    """
    Abstract base class for all UI components.

    Provides common style properties and methods for all components.
    """

    # Default style values (can be overridden in subclasses)
    DEFAULT_WIDTH = None
    DEFAULT_HEIGHT = None
    DEFAULT_MARGIN = None
    DEFAULT_PADDING = None

    def __init__(self):
        """Initialize component with default styles"""
        # Style properties (can be set per instance)
        self.width = self.DEFAULT_WIDTH
        self.height = self.DEFAULT_HEIGHT
        self.margin = self.DEFAULT_MARGIN
        self.padding = self.DEFAULT_PADDING

        # Additional style properties
        self.min_width = None
        self.max_width = None
        self.flex_grow = None
        self.flex_shrink = None

        # CSS class
        self.className = None
        self.additional_classes = []

    def _build_style(self) -> Dict[str, Any]:
        """
        Build inline style dictionary from properties.

        Returns:
            Style dict for Dash components
        """
        style = {}

        if self.width:
            style['width'] = self.width
        if self.height:
            style['height'] = self.height
        if self.margin:
            style['margin'] = self.margin
        if self.padding:
            style['padding'] = self.padding
        if self.min_width:
            style['minWidth'] = self.min_width
        if self.max_width:
            style['maxWidth'] = self.max_width
        if self.flex_grow is not None:
            style['flexGrow'] = self.flex_grow
        if self.flex_shrink is not None:
            style['flexShrink'] = self.flex_shrink

        return style

    def _build_class_name(self) -> Optional[str]:
        """
        Build complete className string.

        Returns:
            Combined CSS class names
        """
        classes = []
        if self.className:
            classes.append(self.className)
        classes.extend(self.additional_classes)
        return ' '.join(classes) if classes else None

    @abstractmethod
    def build(self):
        """
        Build and return the Dash component.

        Must be implemented by subclasses.
        """
        pass


# =============================================================================
# Flex Container
# =============================================================================

class Flex(Component):
    """
    Flexible box layout container.

    Can contain any components and other Flex containers (nesting).
    """

    # Default flex layout values
    DEFAULT_DIRECTION = 'row'
    DEFAULT_ALIGN = 'flex-start'
    DEFAULT_JUSTIFY = 'flex-start'
    DEFAULT_GAP = '10px'
    DEFAULT_WIDTH = '100%'
    DEFAULT_WRAP = 'nowrap'

    def __init__(self):
        """Initialize flex container"""
        super().__init__()

        # Flex-specific properties
        self.direction = self.DEFAULT_DIRECTION
        self.align = self.DEFAULT_ALIGN  # align-items
        self.justify = self.DEFAULT_JUSTIFY  # justify-content
        self.gap = self.DEFAULT_GAP
        self.wrap = self.DEFAULT_WRAP

        # Children components
        self.children = []

        # Default className
        self.className = CSS.CONTROLS

    def add(self, component: Component) -> 'Flex':
        """
        Add a component to this flex container.

        Args:
            component: Component instance to add

        Returns:
            Self (for chaining)
        """
        self.children.append(component)
        return self

    def dropdown(self, component_id: str, options: List[Dict],
                value=None, **kwargs) -> 'Dropdown':
        """
        Create and add a dropdown to this flex container.

        Args:
            component_id: Component ID
            options: Dropdown options
            value: Default value
            **kwargs: Additional dropdown arguments

        Returns:
            The created Dropdown instance
        """
        drop = Dropdown(component_id, options, value=value, **kwargs)
        self.add(drop)
        return drop

    def slider(self, component_id: str, min_val: float, max_val: float,
              value=None, **kwargs) -> 'Slider':
        """Create and add a slider"""
        slide = Slider(component_id, min_val, max_val, value=value, **kwargs)
        self.add(slide)
        return slide

    def range_slider(self, component_id: str, min_val: float, max_val: float,
                    value: List[float] = None, **kwargs) -> 'RangeSlider':
        """Create and add a range slider"""
        rslide = RangeSlider(component_id, min_val, max_val, value=value, **kwargs)
        self.add(rslide)
        return rslide

    def text_input(self, component_id: str, value: str = '',
                  placeholder: str = '', **kwargs) -> 'TextInput':
        """Create and add a text input"""
        tinput = TextInput(component_id, value=value, placeholder=placeholder, **kwargs)
        self.add(tinput)
        return tinput

    def button(self, component_id: str, label: str, **kwargs) -> 'Button':
        """Create and add a button"""
        btn = Button(component_id, label, **kwargs)
        self.add(btn)
        return btn

    def graph(self, component_id: str, figure=None, **kwargs) -> 'Graph':
        """Create and add a graph"""
        g = Graph(component_id, figure=figure, **kwargs)
        self.add(g)
        return g

    def label(self, text: str, **kwargs) -> 'Label':
        """Create and add a label"""
        lbl = Label(text, **kwargs)
        self.add(lbl)
        return lbl

    def build(self) -> html.Div:
        """Build the flex container as html.Div"""
        style = self._build_style()

        # Add flex-specific styles
        style.update({
            'display': 'flex',
            'flexDirection': self.direction,
            'alignItems': self.align,
            'justifyContent': self.justify,
            'gap': self.gap,
            'flexWrap': self.wrap
        })

        return html.Div(
            children=[child.build() for child in self.children],
            style=style,
            className=self._build_class_name()
        )


# =============================================================================
# Flex Variants for Different Contexts
# =============================================================================

class Row(Flex):
    """Horizontal flex container (row direction)"""
    DEFAULT_DIRECTION = 'row'
    DEFAULT_ALIGN = 'center'


class Column(Flex):
    """Vertical flex container (column direction)"""
    DEFAULT_DIRECTION = 'column'
    DEFAULT_ALIGN = 'stretch'
    DEFAULT_WIDTH = None


class MainTabFlex(Flex):
    """Flex container optimized for main tab layouts"""
    DEFAULT_GAP = '15px'
    DEFAULT_ALIGN = 'center'
    DEFAULT_JUSTIFY = 'flex-start'


class ComparisonTabFlex(Flex):
    """Flex container optimized for comparison tab layouts"""
    DEFAULT_GAP = '20px'
    DEFAULT_ALIGN = 'center'
    DEFAULT_JUSTIFY = 'space-between'


# =============================================================================
# Concrete Components
# =============================================================================

class Dropdown(Component):
    """Dropdown selection component"""

    DEFAULT_WIDTH = '150px'
    DEFAULT_MARGIN = '0 5px'

    def __init__(self, component_id: str, options: List[Dict],
                 value=None, clearable: bool = False,
                 searchable: bool = False, **kwargs):
        """
        Initialize dropdown.

        Args:
            component_id: Unique component ID
            options: List of {'label': ..., 'value': ...} dicts
            value: Default selected value
            clearable: Allow clearing selection
            searchable: Enable search functionality
            **kwargs: Additional dcc.Dropdown arguments
        """
        super().__init__()
        self.id = component_id
        self.options = options
        self.value = value
        self.clearable = clearable
        self.searchable = searchable
        self.kwargs = kwargs
        self.className = CSS.INPUT

    def build(self) -> dcc.Dropdown:
        """Build dropdown component"""
        return dcc.Dropdown(
            id=self.id,
            options=self.options,
            value=self.value,
            clearable=self.clearable,
            searchable=self.searchable,
            style=self._build_style(),
            className=self._build_class_name(),
            **self.kwargs
        )


class Slider(Component):
    """Slider component for numeric input"""

    DEFAULT_WIDTH = '200px'
    DEFAULT_MARGIN = '10px 5px'

    def __init__(self, component_id: str, min_val: float, max_val: float,
                 value=None, step: float = 1, marks: Dict = None, **kwargs):
        """
        Initialize slider.

        Args:
            component_id: Unique component ID
            min_val: Minimum value
            max_val: Maximum value
            value: Default value
            step: Step size
            marks: Slider marks
            **kwargs: Additional dcc.Slider arguments
        """
        super().__init__()
        self.id = component_id
        self.min = min_val
        self.max = max_val
        self.value = value if value is not None else min_val
        self.step = step
        self.marks = marks
        self.kwargs = kwargs
        self.className = CSS.SLIDER

    def build(self) -> dcc.Slider:
        """Build slider component"""
        return dcc.Slider(
            id=self.id,
            min=self.min,
            max=self.max,
            value=self.value,
            step=self.step,
            marks=self.marks,
            className=self._build_class_name(),
            **self.kwargs
        )


class Button(Component):
    """Button component"""

    DEFAULT_MARGIN = '5px'

    def __init__(self, component_id: str, label: str, **kwargs):
        """
        Initialize button.

        Args:
            component_id: Unique component ID
            label: Button text
            **kwargs: Additional html.Button arguments
        """
        super().__init__()
        self.id = component_id
        self.label = label
        self.kwargs = kwargs
        self.className = CSS.BUTTON

    def build(self) -> html.Button:
        """Build button component"""
        return html.Button(
            self.label,
            id=self.id,
            style=self._build_style(),
            className=self._build_class_name(),
            **self.kwargs
        )


class Graph(Component):
    """Graph/plot component"""

    DEFAULT_WIDTH = '100%'
    DEFAULT_HEIGHT = '400px'

    def __init__(self, component_id: str, figure=None, **kwargs):
        """
        Initialize graph.

        Args:
            component_id: Unique component ID
            figure: Plotly figure object
            **kwargs: Additional dcc.Graph arguments
        """
        super().__init__()
        self.id = component_id
        self.figure = figure
        self.kwargs = kwargs
        self.className = CSS.PLOT

    def build(self) -> dcc.Graph:
        """Build graph component"""
        return dcc.Graph(
            id=self.id,
            figure=self.figure,
            style=self._build_style(),
            className=self._build_class_name(),
            **self.kwargs
        )


class Label(Component):
    """Text label component"""

    DEFAULT_MARGIN = '5px 10px'

    def __init__(self, text: str, **kwargs):
        """
        Initialize label.

        Args:
            text: Label text
            **kwargs: Additional html.Label arguments
        """
        super().__init__()
        self.text = text
        self.kwargs = kwargs
        self.className = CSS.LABEL

    def build(self) -> html.Label:
        """Build label component"""
        return html.Label(
            self.text,
            style=self._build_style(),
            className=self._build_class_name(),
            **self.kwargs
        )


class TextInput(Component):
    """Text input component"""

    DEFAULT_WIDTH = '200px'
    DEFAULT_MARGIN = '5px'

    def __init__(self, component_id: str, value: str = '',
                 placeholder: str = '', input_type: str = 'text', **kwargs):
        """
        Initialize text input.

        Args:
            component_id: Unique component ID
            value: Default value
            placeholder: Placeholder text
            input_type: Input type (text, number, password, email, etc.)
            **kwargs: Additional dcc.Input arguments
        """
        super().__init__()
        self.id = component_id
        self.value = value
        self.placeholder = placeholder
        self.input_type = input_type
        self.kwargs = kwargs
        self.className = CSS.INPUT

    def build(self) -> dcc.Input:
        """Build text input component"""
        return dcc.Input(
            id=self.id,
            type=self.input_type,
            value=self.value,
            placeholder=self.placeholder,
            style=self._build_style(),
            className=self._build_class_name(),
            **self.kwargs
        )


class RangeSlider(Component):
    """Range slider component for selecting min/max values"""

    DEFAULT_WIDTH = '250px'
    DEFAULT_MARGIN = '10px 5px'

    def __init__(self, component_id: str, min_val: float, max_val: float,
                 value: List[float] = None, step: float = 1,
                 marks: Dict = None, **kwargs):
        """
        Initialize range slider.

        Args:
            component_id: Unique component ID
            min_val: Minimum value
            max_val: Maximum value
            value: Default range [min, max]
            step: Step size
            marks: Slider marks
            **kwargs: Additional dcc.RangeSlider arguments
        """
        super().__init__()
        self.id = component_id
        self.min = min_val
        self.max = max_val
        self.value = value if value is not None else [min_val, max_val]
        self.step = step
        self.marks = marks
        self.kwargs = kwargs
        self.className = CSS.SLIDER

    def build(self) -> dcc.RangeSlider:
        """Build range slider component"""
        return dcc.RangeSlider(
            id=self.id,
            min=self.min,
            max=self.max,
            value=self.value,
            step=self.step,
            marks=self.marks,
            className=self._build_class_name(),
            **self.kwargs
        )


class RadioItems(Component):
    """Radio button group component"""

    DEFAULT_MARGIN = '5px'

    def __init__(self, component_id: str, options: List[Dict],
                 value=None, inline: bool = True, **kwargs):
        """
        Initialize radio items.

        Args:
            component_id: Unique component ID
            options: List of {'label': ..., 'value': ...} dicts
            value: Default selected value
            inline: Display items inline
            **kwargs: Additional dcc.RadioItems arguments
        """
        super().__init__()
        self.id = component_id
        self.options = options
        self.value = value if value is not None else (options[0]['value'] if options else None)
        self.inline = inline
        self.kwargs = kwargs
        self.className = CSS.RADIO

    def build(self) -> dcc.RadioItems:
        """Build radio items component"""
        return dcc.RadioItems(
            id=self.id,
            options=self.options,
            value=self.value,
            inline=self.inline,
            className=self._build_class_name(),
            labelStyle={'display': 'inline-flex', 'alignItems': 'center',
                       'marginRight': '12px'},
            inputStyle={'marginRight': '4px'},
            **self.kwargs
        )


class Checklist(Component):
    """Checkbox list component"""

    DEFAULT_MARGIN = '5px'

    def __init__(self, component_id: str, options: List[Dict],
                 value: List = None, **kwargs):
        """
        Initialize checklist.

        Args:
            component_id: Unique component ID
            options: List of {'label': ..., 'value': ...} dicts
            value: Default selected values (list)
            **kwargs: Additional dcc.Checklist arguments
        """
        super().__init__()
        self.id = component_id
        self.options = options
        self.value = value or []
        self.kwargs = kwargs
        self.className = CSS.RADIO

    def build(self) -> dcc.Checklist:
        """Build checklist component"""
        return dcc.Checklist(
            id=self.id,
            options=self.options,
            value=self.value,
            className=self._build_class_name(),
            labelStyle={'display': 'inline-flex', 'alignItems': 'center',
                       'marginRight': '12px'},
            inputStyle={'marginRight': '4px'},
            **self.kwargs
        )


# =============================================================================
# Card Components
# =============================================================================

class Card(Component):
    """Card container with header and content"""

    DEFAULT_WIDTH = '100%'

    def __init__(self, title: str):
        """
        Initialize card.

        Args:
            title: Card title
        """
        super().__init__()
        self.title = title
        self.content = []
        self.className = CSS.CARD

    def add(self, component: Component) -> 'Card':
        """Add content to card"""
        self.content.append(component)
        return self

    def add_header(self) -> html.Div:
        """Build card header"""
        return html.Div([
            html.Span(className=CSS.CARD_ACCENT),
            html.H3(self.title, className=CSS.CARD_TITLE)
        ], className=CSS.CARD_HEADER)

    def build(self) -> html.Div:
        """Build complete card"""
        return html.Div([
            self.add_header(),
            html.Div(
                [comp.build() for comp in self.content],
                className=CSS.GRAPHS
            )
        ], className=self._build_class_name(), style=self._build_style())


# =============================================================================
# Labeled Components (Component + Label)
# =============================================================================

class LabeledComponent(Component):
    """Wrapper that adds a label to any component"""

    DEFAULT_MARGIN = '5px'

    def __init__(self, label: str, component: Component):
        """
        Initialize labeled component.

        Args:
            label: Label text
            component: Component to label
        """
        super().__init__()
        self.label_text = label
        self.component = component
        self.className = CSS.CONTROL

    def build(self) -> html.Div:
        """Build labeled component"""
        return html.Div([
            html.Label(self.label_text, className=CSS.LABEL),
            self.component.build()
        ], className=self._build_class_name(), style=self._build_style())


# =============================================================================
# Helper Functions
# =============================================================================

def labeled(label: str, component: Component) -> LabeledComponent:
    """
    Add a label to a component.

    Args:
        label: Label text
        component: Component to label

    Returns:
        LabeledComponent instance

    Example:
        >>> drop = Dropdown('time', options)
        >>> labeled("Time Step", drop)
    """
    return LabeledComponent(label, component)
