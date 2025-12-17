"""
Base classes for data management in OPView.

This module provides object-oriented abstractions for managing different
data types (stress, strain, CRSS, grain size) with their specific properties.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


class DataSource(ABC):
    """
    Abstract base class for all data sources.

    Each data type (stress, strain, CRSS, etc.) should inherit from this
    and implement the required methods.
    """

    def __init__(self, data_dir: Path):
        """
        Initialize data source.

        Args:
            data_dir: Directory containing the data files
        """
        self.data_dir = data_dir
        self._data = None
        self._loaded = False

    @property
    @abstractmethod
    def file_pattern(self) -> str:
        """Return the file pattern to search for (e.g., 'StressStrain*.txt')"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return human-readable name (e.g., 'Stress-Strain Data')"""
        pass

    @abstractmethod
    def load(self) -> bool:
        """
        Load data from files.

        Returns:
            True if data was loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_component_options(self) -> List[Dict[str, str]]:
        """
        Get component options for dropdowns/checklists.

        Returns:
            List of {'label': ..., 'value': ...} dicts
        """
        pass

    @abstractmethod
    def get_default_components(self) -> List[str]:
        """
        Get default selected components.

        Returns:
            List of component values to select by default
        """
        pass

    @property
    def data(self):
        """Get the loaded data (lazy load if not already loaded)"""
        if not self._loaded:
            self.load()
        return self._data

    @property
    def is_available(self) -> bool:
        """Check if data is available"""
        if not self._loaded:
            self.load()
        return self._data is not None

    def get_min_max(self, component: str) -> Tuple[float, float]:
        """
        Get min/max values for a component.

        Args:
            component: Component name

        Returns:
            Tuple of (min, max) values
        """
        if not self.is_available:
            return (0.0, 1.0)

        values = self._get_component_values(component)
        if values is None or len(values) == 0:
            return (0.0, 1.0)

        return (float(np.min(values)), float(np.max(values)))

    @abstractmethod
    def _get_component_values(self, component: str) -> Optional[np.ndarray]:
        """
        Internal method to get raw values for a component.

        Args:
            component: Component name

        Returns:
            Array of values or None
        """
        pass


class TensorDataSource(DataSource):
    """
    Base class for tensor data (stress, strain).

    Provides common functionality for 3x3 tensor components.
    """

    @property
    def standard_components(self) -> List[str]:
        """Standard tensor component names"""
        return ['xx', 'yy', 'zz', 'xy', 'yz', 'xz']

    def get_component_options(self) -> List[Dict[str, str]]:
        """Get tensor component options with proper symbols"""
        symbol = self.component_symbol
        components = []

        for comp in self.standard_components:
            components.append({
                'label': f'{symbol}_{comp}',
                'value': f'{self.component_prefix}_{comp}'
            })

        # Add von Mises if applicable
        if self.has_von_mises:
            components.append({
                'label': 'von Mises',
                'value': 'Mises'
            })

        return components

    @property
    @abstractmethod
    def component_symbol(self) -> str:
        """Symbol for display (σ for stress, ε for strain)"""
        pass

    @property
    @abstractmethod
    def component_prefix(self) -> str:
        """Prefix for data keys (Sigma, Epsilon)"""
        pass

    @property
    def has_von_mises(self) -> bool:
        """Whether this data includes von Mises values"""
        return True


class TimeSeriesDataSource(DataSource):
    """
    Base class for time-series data.

    Handles data that varies over time steps.
    """

    def get_time_steps(self) -> List[float]:
        """
        Get available time steps.

        Returns:
            List of time values
        """
        if not self.is_available:
            return []

        return self._data.get('times', [])

    def get_time_options(self) -> List[Dict[str, str]]:
        """
        Get formatted time options for dropdowns.

        Returns:
            List of {'label': ..., 'value': ...} dicts
        """
        times = self.get_time_steps()
        options = []

        for t in times:
            if t.is_integer():
                label = str(int(t))
            else:
                label = f"{t:.3f}".rstrip('0').rstrip('.')
            options.append({'label': label, 'value': str(t)})

        return options

    def get_default_time(self) -> Optional[str]:
        """Get default time step (first available)"""
        options = self.get_time_options()
        return options[0]['value'] if options else None


class HistogramDataSource(DataSource):
    """
    Base class for histogram data.

    Handles data that should be displayed as histograms.
    """

    @property
    def default_bins(self) -> int:
        """Default number of bins for histogram"""
        return 15

    @property
    def min_bins(self) -> int:
        """Minimum number of bins"""
        return 5

    @property
    def max_bins(self) -> int:
        """Maximum number of bins"""
        return 50

    @property
    def bin_step(self) -> int:
        """Step size for bin slider"""
        return 5

    def get_histogram_data(self, time_value: float, bins: int = None) -> Tuple[Any, str]:
        """
        Get histogram data for a specific time.

        Args:
            time_value: Time step value
            bins: Number of bins (uses default if None)

        Returns:
            Tuple of (figure, summary_text)
        """
        if bins is None:
            bins = self.default_bins

        return self._compute_histogram(time_value, bins)

    @abstractmethod
    def _compute_histogram(self, time_value: float, bins: int) -> Tuple[Any, str]:
        """
        Internal method to compute histogram.

        Args:
            time_value: Time step
            bins: Number of bins

        Returns:
            Tuple of (figure, summary)
        """
        pass
