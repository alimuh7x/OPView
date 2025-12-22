"""
Application constants for OPView.

Defines global constants used throughout the application.
"""

# Application metadata
APP_TITLE = "OPView"
APP_VERSION = "2.0.0"

# Tensor components
TENSOR_COMPONENTS = ['xx', 'yy', 'zz', 'xy', 'yz', 'zx']

# Tab order for main navigation
TAB_ORDER = ['phase-field', 'composition', 'mechanics', 'plasticity']

# Folders to skip when scanning for projects
SKIP_FOLDERS = {
    '.git', '.vscode', '.claude', '.gemini', '__pycache__',
    'venv', 'venv312', 'venv_py312', 'assets', 'utils',
    'viewer', 'sample_data', 'node_modules', 'app', 'config',
    'callbacks', 'comparison', 'data', 'ui'
}

# TextData folder name variants (case-insensitive search)
TEXTDATA_FOLDER_VARIANTS = ["TextData", "Textdata", "textdata", "TEXTDATA"]
