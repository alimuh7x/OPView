"""
Dataset registry for OPView.

Manages detected datasets and provides organized access for UI components.
Part of the panel-based auto-detection system.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
from utils.dataset_detector import DatasetInfo, detect_available_datasets


class DatasetRegistry:
    """
    Registry of available datasets for the current project.

    Replaces module-based selection with panel-based selection by detecting
    which datasets have files present and providing organized dropdown options.

    Example:
        >>> from config.tabs import TAB_CONFIGS
        >>> registry = DatasetRegistry(Path('project/VTK'), TAB_CONFIGS)
        >>> registry.detect()
        Detected 5 datasets in project/VTK
          - Phase Field (3 files)
          - Stress Tensor (10 files)
          - Elastic Strains (10 files)
          - CRSS (8 files)
          - Plastic Strain (8 files)
        >>> options = registry.get_dropdown_options()
        >>> stress_info = registry.get_by_id('mechanics-stress-tensor')
    """

    def __init__(self, vtk_folder: Path, tab_configs: List[Dict[str, Any]]):
        """
        Initialize dataset registry.

        Args:
            vtk_folder: Path to VTK directory
            tab_configs: Tab configurations from config/tabs.py
        """
        self.vtk_folder = vtk_folder
        self.tab_configs = tab_configs
        self._datasets: List[DatasetInfo] = []
        self._by_id: Dict[str, DatasetInfo] = {}
        self._by_module: Dict[str, List[DatasetInfo]] = {}

    def detect(self, verbose: bool = True) -> None:
        """
        Detect available datasets in VTK folder (configured + unconfigured).

        Scans the folder and populates the registry with:
        1. Configured datasets (from TAB_CONFIGS)
        2. Unconfigured VTK files (shown as generic panels)

        Args:
            verbose: If True, print detection results to console
        """
        from utils.dataset_detector import detect_unconfigured_vtk_files

        # Detect configured datasets (existing behavior)
        self._datasets = detect_available_datasets(self.vtk_folder, self.tab_configs)

        # NEW: Detect unconfigured files
        unconfigured_files = detect_unconfigured_vtk_files(self.vtk_folder, self.tab_configs)

        # Group unconfigured files by base name (optimize: avoid multiple glob calls)
        files_by_basename = {}
        for vtk_file in unconfigured_files:
            base_name = self._extract_base_name(vtk_file)
            if base_name not in files_by_basename:
                files_by_basename[base_name] = []
            files_by_basename[base_name].append(vtk_file)

        # Create DatasetInfo for each unique base name
        for base_name, matched_files in files_by_basename.items():
            dataset_id = f"auto-{base_name.lower()}"

            # Check if we already have this auto-detected dataset (avoid duplicates)
            if dataset_id not in {ds.dataset_id for ds in self._datasets}:
                # Use first file's suffix for pattern
                first_file = matched_files[0]
                pattern = f"{base_name}_*{first_file.suffix}"

                dataset_info = DatasetInfo(
                    dataset_id=dataset_id,
                    label=base_name,
                    module_id="unconfigured",
                    module_label="Other Files",
                    module_icon="📄",
                    file_glob=pattern,
                    matched_files=sorted(matched_files),
                    dataset_config={
                        "id": base_name.lower(),
                        "label": base_name,
                        # scalars: None - ViewerPanel will auto-discover!
                    }
                )
                self._datasets.append(dataset_info)

        # Build lookup dictionaries
        self._by_id = {ds.dataset_id: ds for ds in self._datasets}

        # Group by module for dropdown organization
        self._by_module = {}
        for ds in self._datasets:
            if ds.module_id not in self._by_module:
                self._by_module[ds.module_id] = []
            self._by_module[ds.module_id].append(ds)

        if verbose:
            configured_count = len([ds for ds in self._datasets if ds.module_id != "unconfigured"])
            unconfigured_count = len([ds for ds in self._datasets if ds.module_id == "unconfigured"])
            print(f"Detected {len(self._datasets)} datasets in {self.vtk_folder}")
            print(f"  Configured: {configured_count}, Unconfigured: {unconfigured_count}")
            for ds in self._datasets:
                print(f"  - {ds.label} ({len(ds.matched_files)} files)")

    def _extract_base_name(self, vtk_file: Path) -> str:
        """
        Extract base name from VTK file.

        Examples:
            Temperature_001.vts → "Temperature"
            CustomData_042.vti → "CustomData"
            SingleFile.vtk → "SingleFile"

        Args:
            vtk_file: Path to VTK file

        Returns:
            Base name without trailing numbers
        """
        import re

        name = vtk_file.stem  # Remove extension
        # Remove trailing numbers and underscores (e.g., "_001")
        match = re.match(r'^(.+?)_\d+$', name)
        return match.group(1) if match else name

    def get_by_id(self, dataset_id: str) -> Optional[DatasetInfo]:
        """
        Get dataset information by ID.

        Args:
            dataset_id: Dataset identifier (e.g., 'mechanics-stress-tensor')

        Returns:
            DatasetInfo object or None if not found
        """
        return self._by_id.get(dataset_id)

    def get_by_module(self, module_id: str) -> List[DatasetInfo]:
        """
        Get all datasets in a module.

        Args:
            module_id: Module identifier (e.g., 'mechanics')

        Returns:
            List of DatasetInfo objects in this module
        """
        return self._by_module.get(module_id, [])

    def get_dropdown_options(self, grouped: bool = True) -> List[Dict[str, Any]]:
        """
        Get dropdown options for panel selection.

        Args:
            grouped: If True, group options by module with category headers

        Returns:
            List of dropdown option dictionaries for Dash dropdown component

        Example (grouped=True):
            [
                {'label': '─── Phase Field ───', 'value': '__group_phase-field', 'disabled': True},
                {'label': '  Phase Field', 'value': 'phase-field-phase'},
                {'label': '─── Mechanics ───', 'value': '__group_mechanics', 'disabled': True},
                {'label': '  Stress Tensor', 'value': 'mechanics-stress-tensor'},
                {'label': '  Elastic Strains', 'value': 'mechanics-elastic-strains'},
            ]

        Example (grouped=False):
            [
                {'label': 'Phase Field', 'value': 'phase-field-phase'},
                {'label': 'Stress Tensor', 'value': 'mechanics-stress-tensor'},
                {'label': 'Elastic Strains', 'value': 'mechanics-elastic-strains'},
            ]
        """
        if not grouped:
            # Simple flat list
            return [
                {'label': ds.label, 'value': ds.dataset_id}
                for ds in self._datasets
            ]

        # Grouped by module with visual separators
        options = []

        # Preserve module order from TAB_CONFIGS
        for module_config in self.tab_configs:
            module_id = module_config.get('id', '')
            datasets_in_module = self._by_module.get(module_id, [])

            if not datasets_in_module:
                # Skip modules with no detected datasets
                continue

            # Add group header (disabled option for visual grouping)
            module_label = module_config.get('label', module_id)
            options.append({
                'label': f"─── {module_label} ───",
                'value': f"__group_{module_id}",
                'disabled': True
            })

            # Add dataset options (indented)
            for ds in datasets_in_module:
                options.append({
                    'label': f"  {ds.label}",
                    'value': ds.dataset_id
                })

        # NEW: Add unconfigured files section (auto-detected VTK files)
        unconfigured = self._by_module.get("unconfigured", [])
        if unconfigured:
            # Add "Other Files" section header
            options.append({
                'label': '─── Other Files ───',
                'value': '__group_unconfigured',
                'disabled': True
            })

            # Add auto-detected datasets (indented)
            for ds in unconfigured:
                options.append({
                    'label': f"  {ds.label}",
                    'value': ds.dataset_id
                })

        return options

    def get_status_message(self) -> str:
        """
        Get a human-readable status message about detected datasets.

        Returns:
            Status message string

        Examples:
            "5 data types found"
            "No data types found"
            "1 data type found"
        """
        count = len(self._datasets)
        if count == 0:
            return "No data types found"
        elif count == 1:
            return "1 data type found"
        else:
            return f"{count} data types found"

    @property
    def all_datasets(self) -> List[DatasetInfo]:
        """
        Get all detected datasets.

        Returns:
            List of all DatasetInfo objects
        """
        return self._datasets

    @property
    def module_ids(self) -> List[str]:
        """
        Get list of module IDs that have detected datasets.

        Returns:
            List of module IDs
        """
        return list(self._by_module.keys())

    @property
    def is_empty(self) -> bool:
        """
        Check if registry has no detected datasets.

        Returns:
            True if no datasets were detected
        """
        return len(self._datasets) == 0

    def __len__(self) -> int:
        """Return number of detected datasets."""
        return len(self._datasets)

    def __repr__(self) -> str:
        """String representation of registry."""
        return f"DatasetRegistry({len(self)} datasets, {len(self._by_module)} modules)"
