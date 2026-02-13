"""
Dataset detection utilities for OPView.

Automatically detects which datasets have VTK files present in a project folder.
Extracted functionality to support panel-based auto-detection system.
"""

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DatasetInfo:
    """
    Information about a detected dataset.

    Attributes:
        dataset_id: Unique identifier (e.g., 'mechanics-stresses')
        label: Display label (e.g., 'Stress Tensor')
        module_id: Parent module ID (e.g., 'mechanics')
        module_label: Parent module label (e.g., 'Mechanics')
        module_icon: Module icon for UI grouping
        file_glob: Pattern used to match files (e.g., 'Stresses_*.vts')
        matched_files: List of actual file paths that matched
        dataset_config: Full dataset configuration from TAB_CONFIGS
    """
    dataset_id: str
    label: str
    module_id: str
    module_label: str
    module_icon: str
    file_glob: str
    matched_files: List[Path]
    dataset_config: Dict[str, Any]


def detect_available_datasets(
    vtk_folder: Path,
    tab_configs: List[Dict[str, Any]]
) -> List[DatasetInfo]:
    """
    Detect which datasets have files present in the VTK folder.

    Scans the VTK folder and matches files against patterns defined in TAB_CONFIGS.
    Only returns datasets that have at least one matching file.

    Args:
        vtk_folder: Path to VTK directory to scan
        tab_configs: List of tab configurations from config/tabs.py

    Returns:
        List of DatasetInfo objects for detected datasets

    Example:
        >>> from config.tabs import TAB_CONFIGS
        >>> detected = detect_available_datasets(Path('project/VTK'), TAB_CONFIGS)
        >>> print(f"Found {len(detected)} datasets")
        Found 3 datasets
        >>> print(detected[0].label)
        'Stress Tensor'
    """
    if not vtk_folder or not vtk_folder.exists():
        return []

    available = []

    # Iterate through all modules and their datasets
    for module_config in tab_configs:
        module_id = module_config.get('id', '')
        module_label = module_config.get('label', '')
        module_icon = module_config.get('icon', '•')
        datasets = module_config.get('datasets', [])

        for dataset_config in datasets:
            dataset_label = dataset_config.get('label', '')
            file_glob = dataset_config.get('file_glob', '')

            if not file_glob:
                # Skip datasets without file patterns
                continue

            # Check if any files match this pattern
            try:
                matched = list(vtk_folder.glob(file_glob))
            except (OSError, ValueError):
                # Handle invalid glob patterns gracefully
                matched = []

            if matched:
                # Files found - add to available datasets
                dataset_id = _generate_dataset_id(module_id, dataset_config.get('id', dataset_label))

                available.append(DatasetInfo(
                    dataset_id=dataset_id,
                    label=dataset_label,
                    module_id=module_id,
                    module_label=module_label,
                    module_icon=module_icon,
                    file_glob=file_glob,
                    matched_files=sorted(matched),
                    dataset_config=dataset_config
                ))

    return available


def _generate_dataset_id(module_id: str, dataset_id_or_label: str) -> str:
    """
    Generate a unique dataset ID.

    Args:
        module_id: Module identifier (e.g., 'mechanics')
        dataset_id_or_label: Dataset ID or label (e.g., 'stresses' or 'Stress Tensor')

    Returns:
        Unique dataset ID (e.g., 'mechanics-stresses')
    """
    # Normalize dataset component: lowercase, replace spaces with hyphens
    dataset_component = dataset_id_or_label.lower().replace(' ', '-')

    return f"{module_id}-{dataset_component}"


def verify_dataset_arrays(
    dataset_info: DatasetInfo,
    get_reader_func
) -> bool:
    """
    Verify that VTK files contain expected arrays (optional verification).

    This is an optional verification step that can be enabled per-dataset
    by adding a 'required_arrays' field to the dataset configuration.

    Args:
        dataset_info: Dataset information with matched files
        get_reader_func: Function to get VTK reader for a file

    Returns:
        True if arrays are present (or no verification required), False otherwise

    Example:
        In config/tabs.py, add to dataset config:
        {
            "label": "Stress Tensor",
            "file_glob": "Stresses_*.vts",
            "required_arrays": ["Stresses"],  # Optional verification
            ...
        }
    """
    required_arrays = dataset_info.dataset_config.get('required_arrays')

    if not required_arrays:
        # No verification required
        return True

    if not dataset_info.matched_files:
        return False

    # Check first matched file
    try:
        sample_file = dataset_info.matched_files[0]
        reader = get_reader_func(sample_file)
        available_arrays = reader.mesh.array_names if hasattr(reader, 'mesh') else []

        # Check if all required arrays are present
        return all(arr in available_arrays for arr in required_arrays)

    except Exception:
        # If verification fails, assume dataset is valid (conservative approach)
        return True


def detect_unconfigured_vtk_files(
    vtk_folder: Path,
    tab_configs: List[Dict[str, Any]]
) -> List[Path]:
    """
    Find VTK files NOT matched by any TAB_CONFIGS pattern.

    This enables automatic detection of any VTK file in the folder,
    even if it's not explicitly configured in TAB_CONFIGS. These files
    will be shown as generic panels with auto-discovered scalar fields.

    Args:
        vtk_folder: Path to VTK directory to scan
        tab_configs: List of tab configurations from config/tabs.py

    Returns:
        Sorted list of Path objects for unconfigured VTK files

    Example:
        >>> from config.tabs import TAB_CONFIGS
        >>> unconfigured = detect_unconfigured_vtk_files(Path('project/VTK'), TAB_CONFIGS)
        >>> print(f"Found {len(unconfigured)} unconfigured files")
        Found 2 unconfigured files
        >>> print([f.name for f in unconfigured])
        ['Temperature_001.vts', 'CustomData_001.vts']
    """
    import fnmatch

    # Import allowed extensions (supports .vtk, .vti, .vtp, .vtr, .vts)
    try:
        from config.paths import ALLOWED_VTK_EXTENSIONS
    except ImportError:
        # Fallback if import fails
        ALLOWED_VTK_EXTENSIONS = ('.vtk', '.vti', '.vtp', '.vtr', '.vts')

    if not vtk_folder or not vtk_folder.exists():
        return []

    # Get all VTK files in folder
    all_vtk_files = [
        f for f in vtk_folder.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_VTK_EXTENSIONS
    ]

    # Collect all configured patterns from TAB_CONFIGS
    configured_patterns = []
    for module in tab_configs:
        for dataset in module.get('datasets', []):
            if pattern := dataset.get('file_glob'):
                configured_patterns.append(pattern)

    # Find unconfigured files (not matching any pattern)
    unconfigured = []
    for vtk_file in all_vtk_files:
        is_configured = any(
            fnmatch.fnmatch(vtk_file.name, pattern)
            for pattern in configured_patterns
        )
        if not is_configured:
            unconfigured.append(vtk_file)

    return sorted(unconfigured)
