"""
Card classes for building UI components in an object-oriented way.

Each card type (TimeSeriesCard, HistogramCard, etc.) encapsulates:
- The data source
- UI layout building
- Default configurations
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from dash import html, dcc
from data.base import DataSource, TimeSeriesDataSource, HistogramDataSource
from .components import (
    build_simple_card, time_dropdown, component_checklist,
    bins_slider, chart_style_radio, graph
)


class BaseCard(ABC):
    """
    Abstract base class for all cards.

    Encapsulates the data source and provides methods to build the UI.
    """

    def __init__(self, data_source: DataSource, card_id: str):
        """
        Initialize card with data source.

        Args:
            data_source: The data source object
            card_id: Unique identifier for this card (for component IDs)
        """
        self.data = data_source
        self.card_id = card_id

    @abstractmethod
    def build(self) -> Optional[html.Div]:
        """
        Build the card UI.

        Returns:
            Card component or None if data not available
        """
        pass

    def _component_id(self, suffix: str) -> str:
        """
        Generate component ID.

        Args:
            suffix: Component suffix (e.g., 'time', 'graph')

        Returns:
            Full component ID (e.g., 'stress-strain-time')
        """
        return f"{self.card_id}-{suffix}"


class TimeSeriesCard(BaseCard):
    """
    Card for displaying time-series data with line plots.

    Features:
    - Component selection (checklist)
    - Time-based plot
    """

    def __init__(self, data_source: TimeSeriesDataSource, card_id: str):
        super().__init__(data_source, card_id)
        if not isinstance(data_source, TimeSeriesDataSource):
            raise TypeError("TimeSeriesCard requires a TimeSeriesDataSource")

    def build(self) -> Optional[html.Div]:
        """Build time-series card"""
        if not self.data.is_available:
            return None

        return build_simple_card(
            title=self.data.display_name,
            controls=[
                component_checklist(
                    component_id=self._component_id('components'),
                    options=self.data.get_component_options(),
                    default_values=self.data.get_default_components()
                )
            ],
            graphs=[
                graph(self._component_id('graph'))
            ]
        )


class HistogramCard(BaseCard):
    """
    Card for displaying histogram data.

    Features:
    - Time selection
    - Bins slider
    - Optional distribution fitting
    """

    def __init__(self, data_source: HistogramDataSource, card_id: str,
                 show_time: bool = True, show_fit: bool = True):
        """
        Initialize histogram card.

        Args:
            data_source: Histogram data source
            card_id: Card identifier
            show_time: Whether to show time selection dropdown
            show_fit: Whether to show distribution fit toggle
        """
        super().__init__(data_source, card_id)
        if not isinstance(data_source, HistogramDataSource):
            raise TypeError("HistogramCard requires a HistogramDataSource")

        self.show_time = show_time
        self.show_fit = show_fit

    def build(self) -> Optional[html.Div]:
        """Build histogram card"""
        if not self.data.is_available:
            return None

        controls = []

        # Time selection if applicable and requested
        if self.show_time and isinstance(self.data, TimeSeriesDataSource):
            controls.append(
                time_dropdown(
                    self._component_id('time'),
                    self.data.get_time_steps()
                )
            )

        # Component selection
        controls.append(
            component_checklist(
                component_id=self._component_id('component'),
                options=self.data.get_component_options(),
                default_values=self.data.get_default_components(),
                label='Component'
            )
        )

        # Bins slider
        controls.append(
            bins_slider(
                self._component_id('bins'),
                min_bins=self.data.min_bins,
                max_bins=self.data.max_bins,
                step=self.data.bin_step,
                default=self.data.default_bins
            )
        )

        # Distribution fit toggle if requested
        if self.show_fit:
            controls.append(
                chart_style_radio(
                    self._component_id('fit'),
                    options=[
                        {'label': 'No Fit', 'value': 'none'},
                        {'label': 'With Fit', 'value': 'fit'}
                    ]
                )
            )

        return build_simple_card(
            title=self.data.display_name,
            controls=controls,
            graphs=[graph(self._component_id('graph'))]
        )


class TimeSeriesDetailsCard(BaseCard):
    """
    Card for time-series data with detailed views.

    Features:
    - Time selection
    - Chart style selection (bar/line)
    - Multiple graphs (main + detail)
    """

    def __init__(self, data_source: TimeSeriesDataSource, card_id: str):
        super().__init__(data_source, card_id)
        if not isinstance(data_source, TimeSeriesDataSource):
            raise TypeError("Requires TimeSeriesDataSource")

    def build(self) -> Optional[html.Div]:
        """Build time-series details card"""
        if not self.data.is_available:
            return None

        return build_simple_card(
            title=self.data.display_name,
            controls=[
                time_dropdown(
                    self._component_id('time'),
                    self.data.get_time_steps()
                ),
                chart_style_radio(self._component_id('mode'))
            ],
            graphs=[
                graph(self._component_id('main')),
                graph(self._component_id('detail'))
            ]
        )


class CardFactory:
    """
    Factory for creating cards from data sources.

    Simplifies card creation by automatically choosing the right card type.
    """

    @staticmethod
    def create_time_series_card(data_source: TimeSeriesDataSource,
                               card_id: str) -> TimeSeriesCard:
        """Create a time-series card"""
        return TimeSeriesCard(data_source, card_id)

    @staticmethod
    def create_histogram_card(data_source: HistogramDataSource,
                            card_id: str,
                            show_time: bool = True,
                            show_fit: bool = True) -> HistogramCard:
        """Create a histogram card"""
        return HistogramCard(data_source, card_id, show_time, show_fit)

    @staticmethod
    def create_details_card(data_source: TimeSeriesDataSource,
                          card_id: str) -> TimeSeriesDetailsCard:
        """Create a time-series details card"""
        return TimeSeriesDetailsCard(data_source, card_id)

    @staticmethod
    def auto_create(data_source: DataSource, card_id: str,
                   card_type: str = 'auto') -> Optional[BaseCard]:
        """
        Automatically create appropriate card based on data source type.

        Args:
            data_source: The data source
            card_id: Card identifier
            card_type: Type of card ('auto', 'timeseries', 'histogram', 'details')

        Returns:
            Appropriate card instance or None
        """
        if card_type == 'auto':
            # Choose based on data source capabilities
            if isinstance(data_source, HistogramDataSource):
                return HistogramCard(data_source, card_id)
            elif isinstance(data_source, TimeSeriesDataSource):
                return TimeSeriesCard(data_source, card_id)
            else:
                raise ValueError(f"Cannot auto-create card for {type(data_source)}")

        elif card_type == 'timeseries':
            return TimeSeriesCard(data_source, card_id)
        elif card_type == 'histogram':
            return HistogramCard(data_source, card_id)
        elif card_type == 'details':
            return TimeSeriesDetailsCard(data_source, card_id)
        else:
            raise ValueError(f"Unknown card type: {card_type}")


# =============================================================================
# Convenience functions for backward compatibility
# =============================================================================

def build_stress_strain_card(data_dir):
    """
    Build stress-strain card (convenience function).

    Example:
        >>> from data.sources import StressStrainData
        >>> data = StressStrainData(data_dir)
        >>> card = build_stress_strain_card(data_dir)
    """
    from data.sources import StressStrainData
    data = StressStrainData(data_dir)
    card = TimeSeriesCard(data, 'stress-strain')
    return card.build()


def build_grain_distribution_card(data_dir):
    """Build grain distribution card"""
    from data.sources import GrainSizeData
    data = GrainSizeData(data_dir)
    card = HistogramCard(data, 'grain-dist')
    return card.build()


def build_crss_card(data_dir):
    """Build CRSS evolution card"""
    from data.sources import CRSSData
    data = CRSSData(data_dir)
    card = TimeSeriesCard(data, 'crss')
    return card.build()
