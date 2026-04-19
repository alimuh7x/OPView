"""
Path configuration for OPView application.

Defines all path-related constants and helper functions.
"""

from pathlib import Path


# Base directory (repository root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Folder names
COMPARISON_FOLDER_NAME = "Comparison"
DEFAULT_VTK_FOLDER_NAME = "VTK"
TEXTDATA_FOLDER_NAME = "TextData"

# File extensions
ALLOWED_VTK_EXTENSIONS = ('.vtk', '.vti', '.vtp', '.vtr', '.vts')
ALLOWED_TEXTDATA_EXTENSIONS = ('.txt', '.dat', '.csv', '.opd')


def get_base_dir() -> Path:
    """
    Get the base directory (repository root).

    Returns:
        Path to repository root
    """
    return BASE_DIR


def vtk_data_dir(current_project_vtk_path: Path = None) -> Path:
    """
    Return the VTK data directory.

    Prefers the selected project folder, else CWD/VTK, else repo VTK.

    Args:
        current_project_vtk_path: Currently selected project VTK path

    Returns:
        Path to VTK data directory
    """
    # If a project folder is selected, use its VTK path
    if current_project_vtk_path and current_project_vtk_path.exists():
        return current_project_vtk_path

    # Otherwise, use default behavior
    cwd_vtk = Path.cwd() / DEFAULT_VTK_FOLDER_NAME
    if cwd_vtk.exists():
        return cwd_vtk

    fallback = BASE_DIR / DEFAULT_VTK_FOLDER_NAME
    return fallback if fallback.exists() else Path.cwd()


def comparison_data_dir() -> Path:
    """
    Return the comparison folder path.

    Prefers the user's working directory. Creates the directory
    inside the repository if no working-copy folder exists.

    Returns:
        Path to comparison data directory
    """
    cwd_dir = Path.cwd() / COMPARISON_FOLDER_NAME
    repo_dir = BASE_DIR / COMPARISON_FOLDER_NAME

    if cwd_dir.exists():
        return cwd_dir
    if repo_dir.exists():
        return repo_dir

    # Create in repository if doesn't exist
    repo_dir.mkdir(parents=True, exist_ok=True)
    return repo_dir


def textdata_dir() -> Path:
    """
    Return the TextData directory.

    Returns:
        Path to TextData directory
    """
    cwd_textdata = Path.cwd() / TEXTDATA_FOLDER_NAME
    if cwd_textdata.exists():
        return cwd_textdata

    repo_textdata = BASE_DIR / TEXTDATA_FOLDER_NAME
    return repo_textdata if repo_textdata.exists() else Path.cwd()
