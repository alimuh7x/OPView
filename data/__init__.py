"""
Data management module for OPView.

Provides object-oriented data sources for different data types.
"""

from .base import (
    DataSource,
    TensorDataSource,
    TimeSeriesDataSource,
    HistogramDataSource,
    ScalarDataSource,
    VectorDataSource,
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
    'ScalarDataSource',
    'VectorDataSource',

    # Concrete sources
    'StressStrainData',
    'StressData',
    'StrainData',
    'CRSSData',
    'GrainSizeData',
    'PlasticStrainData',
]
