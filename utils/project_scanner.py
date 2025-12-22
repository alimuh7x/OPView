"""
Project folder scanning utilities for OPView.

Provides functions to discover and scan project folders containing
VTK and TextData subdirectories.
"""

from pathlib import Path
from typing import Dict, List, Any


def scan_project_folders(base_path: Path = None) -> Dict[str, Dict[str, Any]]:
    """
    Scan the current directory for folders containing VTK or TextData subdirectories.

    Args:
        base_path: Directory to scan (defaults to current working directory)

    Returns:
        Dictionary mapping folder names to their contents:
        {
            'Project1': {
                'path': Path object,
                'has_vtk': True/False,
                'has_textdata': True/False,
                'vtk_path': Path to VTK folder or None,
                'textdata_path': Path to TextData folder or None,
                'vtk_file_count': number of VTK files,
                'textdata_file_count': number of text data files
            },
            ...
        }
    """
    from config import ALLOWED_VTK_EXTENSIONS, SKIP_FOLDERS

    if base_path is None:
        base_path = Path.cwd()

    project_folders = {}

    # Scan only immediate subdirectories of the base path
    for item in base_path.iterdir():
        if not item.is_dir():
            continue

        # Skip special folders
        if item.name in SKIP_FOLDERS or item.name.startswith('.'):
            continue

        # Check for VTK and TextData subdirectories
        vtk_path = item / "VTK"
        textdata_variants = ["TextData", "Textdata", "textdata", "TEXTDATA"]
        textdata_path = None

        for variant in textdata_variants:
            potential_path = item / variant
            if potential_path.exists() and potential_path.is_dir():
                textdata_path = potential_path
                break

        has_vtk = vtk_path.exists() and vtk_path.is_dir()
        has_textdata = textdata_path is not None

        # Only include folders that have at least VTK or TextData
        if has_vtk or has_textdata:
            # Count files
            vtk_count = 0
            if has_vtk:
                vtk_count = sum(
                    1 for f in vtk_path.iterdir()
                    if f.is_file() and f.suffix.lower() in ALLOWED_VTK_EXTENSIONS
                )

            textdata_count = 0
            if has_textdata:
                textdata_count = sum(
                    1 for f in textdata_path.iterdir()
                    if f.is_file() and f.suffix.lower() in ('.txt', '.dat')
                )

            project_folders[item.name] = {
                'path': item,
                'has_vtk': has_vtk,
                'has_textdata': has_textdata,
                'vtk_path': vtk_path if has_vtk else None,
                'textdata_path': textdata_path,
                'vtk_file_count': vtk_count,
                'textdata_file_count': textdata_count
            }

    return project_folders


def get_project_folder_options(discovered_folders: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convert discovered project folders to dropdown options.

    Args:
        discovered_folders: Dictionary from scan_project_folders()

    Returns:
        List of dropdown option dictionaries with 'label' and 'value' keys
    """
    options = []
    for folder_name, folder_info in sorted(discovered_folders.items()):
        vtk_count = folder_info.get('vtk_file_count', 0)
        textdata_count = folder_info.get('textdata_file_count', 0)
        label = f"{folder_name} ({vtk_count} VTK, {textdata_count} TextData)"
        options.append({'label': label, 'value': folder_name})
    return options


def _scan_vtk_dir(directory: Path) -> List[str]:
    """
    Scan a VTK directory for supported files.

    Args:
        directory: Path to VTK directory

    Returns:
        Sorted list of absolute file paths
    """
    from config import ALLOWED_VTK_EXTENSIONS

    paths = []
    if not directory or not directory.exists():
        return paths

    try:
        for child in directory.rglob("*"):
            if child.is_file() and child.suffix.lower() in ALLOWED_VTK_EXTENSIONS:
                paths.append(str(child.resolve()))
    except OSError:
        return []

    return sorted(paths)
