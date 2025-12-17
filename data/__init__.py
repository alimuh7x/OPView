"""
Data management module for OPView.

Provides object-oriented data sources for different data types.
"""

from .base import (
    DataSource,
    TensorDataSource,
    TimeSeriesDataSource,
    HistogramDataSource,
)

from .sources import (
    StressStrainData,
    StressData,
    StrainData,
    CRSSData,
    GrainSizeData,
    PlasticStrainData,
)

__all__ = [
    # Base classes
    'DataSource',
    'TensorDataSource',
    'TimeSeriesDataSource',
    'HistogramDataSource',

    # Concrete sources
    'StressStrainData',
    'StressData',
    'StrainData',
    'CRSSData',
    'GrainSizeData',
    'PlasticStrainData',
]
