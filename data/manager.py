"""
Data manager for coordinating all data sources.
"""

from pathlib import Path
from typing import Dict, Optional, Any

from .loaders import LegacyDataLoader
from .sources import (
    GrainSizeData,
    StressStrainData,
    StressData,
    StrainData,
    CRSSData
)


class DataManager:
    """
    Manages all data sources (both OOP and legacy).

    Coordinates loading and provides unified access to all application data.
    """

    def __init__(self, context):
        """
        Initialize data manager.

        Args:
            context: AppContext instance for state management
        """
        self.context = context
        self.data_dir = context.data_dir

        # Legacy data loader
        self.legacy_loader = LegacyDataLoader(self.data_dir)

        # OOP data sources
        self.grain_data = GrainSizeData(self.data_dir)
        self.stress_strain_data = StressStrainData(self.data_dir)
        self.stress_data = StressData(self.data_dir)
        self.strain_data = StrainData(self.data_dir)
        self.crss_data = CRSSData(self.data_dir)

        # Register OOP data sources in context
        self.context.data_sources = {
            'grain': self.grain_data,
            'stress_strain': self.stress_strain_data,
            'stress': self.stress_data,
            'strain': self.strain_data,
            'crss': self.crss_data,
        }

        # Legacy data cache
        self.legacy_data = {
            'size_details': None,
            'size_averages': None,
            'stress_strain': None,
            'crss': None,
            'plastic_strain': None,
        }

    def load_all_oop(self) -> None:
        """Load all OOP data sources."""
        for source in self.context.data_sources.values():
            source.load()

    def load_all_legacy(self) -> None:
        """Load all legacy data sources."""
        self.legacy_data = self.legacy_loader.load_all()

    def load_all(self) -> None:
        """Load all data sources (both OOP and legacy)."""
        self.load_all_oop()
        self.load_all_legacy()

    def get_legacy_data(self, data_type: str) -> Optional[Dict[str, Any]]:
        """
        Get legacy data by type.

        Args:
            data_type: One of 'size_details', 'size_averages', 'stress_strain',
                      'crss', 'plastic_strain'

        Returns:
            Loaded data dict or None if not available
        """
        if data_type not in self.legacy_data:
            return None

        # Lazy load if not already loaded
        if self.legacy_data[data_type] is None:
            loader_method = getattr(self.legacy_loader, f'load_{data_type}', None)
            if loader_method:
                self.legacy_data[data_type] = loader_method()

        return self.legacy_data[data_type]

    def is_legacy_available(self, data_type: str) -> bool:
        """
        Check if legacy data type is available.

        Args:
            data_type: Legacy data type name

        Returns:
            True if data is available
        """
        data = self.get_legacy_data(data_type)
        return data is not None

    def get_oop_source(self, source_name: str):
        """
        Get OOP data source by name.

        Args:
            source_name: One of 'grain', 'stress_strain', 'stress', 'strain', 'crss'

        Returns:
            Data source instance or None
        """
        return self.context.data_sources.get(source_name)

    def get_available_sources(self) -> Dict[str, bool]:
        """
        Get availability status of all data sources.

        Returns:
            Dictionary mapping source names to availability status
        """
        return {
            # OOP sources
            'grain_oop': self.grain_data.is_available,
            'stress_strain_oop': self.stress_strain_data.is_available,
            'stress_oop': self.stress_data.is_available,
            'strain_oop': self.strain_data.is_available,
            'crss_oop': self.crss_data.is_available,

            # Legacy sources
            'size_details_legacy': self.is_legacy_available('size_details'),
            'size_averages_legacy': self.is_legacy_available('size_averages'),
            'stress_strain_legacy': self.is_legacy_available('stress_strain'),
            'crss_legacy': self.is_legacy_available('crss'),
            'plastic_strain_legacy': self.is_legacy_available('plastic_strain'),
        }
