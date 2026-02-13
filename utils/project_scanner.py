"""
Project folder scanning utilities for OPView.

Provides functions to discover and scan project folders containing
VTK and TextData subdirectories.
"""

from pathlib import Path
from typing import Dict, List, Any


def scan_project_folders(base_path: Path = None, quick_scan: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Scan the current directory for folders containing VTK or TextData subdirectories.

    Args:
        base_path: Directory to scan (defaults to current working directory)
        quick_scan: If True, skip file counting for faster startup (default: True)

    Returns:
        Dictionary mapping folder names to their contents:
        {
            'Project1': {
                'path': Path object,
                'has_vtk': True/False,
                'has_textdata': True/False,
                'vtk_path': Path to VTK folder or None,
                'textdata_path': Path to TextData folder or None,
                'vtk_file_count': number of VTK files (or -1 if quick_scan),
                'textdata_file_count': number of text data files (or -1 if quick_scan)
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
            # Count files (skip if quick_scan for faster startup)
            if quick_scan:
                vtk_count = -1
                textdata_count = -1
            else:
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
                        if f.is_file() and f.suffix.lower() in ('.txt', '.dat', '.csv')
                    )

            # Add parent folder (loads both VTK and TextData if both exist)
            project_folders[item.name] = {
                'path': item,
                'has_vtk': has_vtk,
                'has_textdata': has_textdata,
                'vtk_path': vtk_path if has_vtk else None,
                'textdata_path': textdata_path,
                'vtk_file_count': vtk_count,
                'textdata_file_count': textdata_count,
                'is_subdirectory': False,
                'parent_folder': None
            }

            # Add VTK subdirectory as separate option (if exists)
            if has_vtk:
                project_folders[f"{item.name}/VTK"] = {
                    'path': vtk_path,
                    'has_vtk': True,
                    'has_textdata': False,
                    'vtk_path': vtk_path,
                    'textdata_path': None,
                    'vtk_file_count': vtk_count,
                    'textdata_file_count': 0,
                    'is_subdirectory': True,
                    'parent_folder': item.name
                }

            # Add TextData subdirectory as separate option (if exists)
            if has_textdata:
                project_folders[f"{item.name}/TextData"] = {
                    'path': textdata_path,
                    'has_vtk': False,
                    'has_textdata': True,
                    'vtk_path': None,
                    'textdata_path': textdata_path,
                    'vtk_file_count': 0,
                    'textdata_file_count': textdata_count,
                    'is_subdirectory': True,
                    'parent_folder': item.name
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
        # Add visual indicator for subdirectories
        if folder_info.get('is_subdirectory', False):
            label = f"  └─ {folder_name.split('/')[-1]}"  # Indented with tree character
        else:
            label = folder_name

        options.append({'label': label, 'value': folder_name})
    return options


def group_projects_by_parent(discovered_folders: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    """
    Group VTK/TextData folders by their parent project for hierarchical display.

    Creates a grouped structure where project names are headers and VTK folders
    are checkboxes underneath. Only subdirectories are included; parent folders
    with no subdirectories are excluded.

    Args:
        discovered_folders: Dict from scan_project_folders() containing all discovered folders

    Returns:
        Dict mapping project names to lists of VTK folder options

    Example:
        {
            'Project1': [
                {'label': 'VTKFolder1', 'value': 'Project1/VTKFolder1'},
                {'label': 'VTKFolder2', 'value': 'Project1/VTKFolder2'}
            ],
            'Project2': [
                {'label': 'Results', 'value': 'Project2/Results'}
            ]
        }
    """
    grouped = {}

    for folder_name, folder_info in sorted(discovered_folders.items()):
        # Only process subdirectories (VTK/TextData folders), skip parent folders
        if not folder_info.get('is_subdirectory', False):
            continue

        # Get parent project name
        parent = folder_info.get('parent_folder')
        if not parent:
            continue

        # Extract just the folder name (last part of path)
        folder_display_name = folder_name.split('/')[-1]

        # Initialize group if needed
        if parent not in grouped:
            grouped[parent] = []

        # Add folder to parent group
        grouped[parent].append({
            'label': folder_display_name,  # Display: "VTKFolder1"
            'value': folder_name            # Value: "Project1/VTKFolder1"
        })

    return grouped


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
