"""
Configuration module for OPView.

Contains application configuration, tab configs, paths, and constants.
"""

from .tabs import TabConfig, ConfigManager, TAB_CONFIGS, tensor_scalars
from .paths import (
    BASE_DIR, COMPARISON_FOLDER_NAME, DEFAULT_VTK_FOLDER_NAME,
    TEXTDATA_FOLDER_NAME, ALLOWED_VTK_EXTENSIONS, ALLOWED_TEXTDATA_EXTENSIONS,
    get_base_dir, vtk_data_dir, comparison_data_dir, textdata_dir
)
from .constants import (
    APP_TITLE, APP_VERSION, TENSOR_COMPONENTS, TAB_ORDER,
    SKIP_FOLDERS, TEXTDATA_FOLDER_VARIANTS
)

__all__ = [
    # Tab configuration
    'TabConfig',
    'ConfigManager',
    'TAB_CONFIGS',
    'tensor_scalars',

    # Paths
    'BASE_DIR',
    'COMPARISON_FOLDER_NAME',
    'DEFAULT_VTK_FOLDER_NAME',
    'TEXTDATA_FOLDER_NAME',
    'ALLOWED_VTK_EXTENSIONS',
    'ALLOWED_TEXTDATA_EXTENSIONS',
    'get_base_dir',
    'vtk_data_dir',
    'comparison_data_dir',
    'textdata_dir',

    # Constants
    'APP_TITLE',
    'APP_VERSION',
    'TENSOR_COMPONENTS',
    'TAB_ORDER',
    'SKIP_FOLDERS',
    'TEXTDATA_FOLDER_VARIANTS',
]
