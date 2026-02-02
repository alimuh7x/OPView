"""
Tab configuration for OPView application.

Defines all tab structures, datasets, and scalar field configurations.

IMPORTANT: file_glob patterns are relative to the project's VTK folder
(which may be named "VTK", "Results", "Output", or anything else).
The pattern should only specify the filename pattern, NOT include the folder.
Example: "PhaseField_*.vts" NOT "VTK/PhaseField_*.vts"
"""

from typing import List, Dict, Optional, Any
from pathlib import Path


def tensor_scalars(array_name: str, prefix: str) -> List[Dict[str, Any]]:
    """
    Generate tensor component scalar configurations.

    Args:
        array_name: Name of the tensor array in VTK files
        prefix: Display prefix (e.g., 'σ' for stress, 'ε' for strain)

    Returns:
        List of scalar configurations for all tensor components
    """
    TENSOR_COMPONENTS = ['xx', 'yy', 'zz', 'xy', 'yz', 'zx']
    return [
        {'label': f"{prefix}_{comp}", 'array': array_name, 'component': idx}
        for idx, comp in enumerate(TENSOR_COMPONENTS)
    ]


# Main tab configurations
TAB_CONFIGS = [
    {
        "id": "mechanics",
        "label": "Mechanics",
        "icon": "⚙",
        "datasets": [
            {
                "id": "stresses",
                "label": "Stress Tensor",
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "Stresses_*.vts",
                "scalars": [
                    {'label': 'Pressure', 'array': 'Pressure'},
                    {'label': 'von Mises', 'array': 'von Mises'},
                    *tensor_scalars('Stresses', 'σ')
                ],
            },
            {
                "id": "elastic",
                "label": "Elastic Strains",
                "file_glob": "ElasticStrains_*.vts",
                "units": "%",
                "scale": 100.0,
                "scalars": tensor_scalars('ElasticStrains', 'ε'),
            },
        ],
    },
    {
        "id": "plasticity",
        "label": "Plasticity",
        "icon": "🧪",
        "datasets": [
            {
                "id": "crss",
                "label": "CRSS",
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "CRSS_*.vts",
                "scalars": [
                    {'label': f"CRSS {i}", 'array': f"CRSS_0_{i}"}
                    for i in range(12)
                ],
            },
            {
                "id": "plastic-strain",
                "label": "Plastic Strain",
                "file_glob": "PlasticStrain_*.vts",
                "units": "%",
                "scale": 100.0,
                "scalars": tensor_scalars('PlasticStrain', 'εᵖ'),
            },
        ],
    },
]


class TabConfig:
    """Configuration for a single tab."""

    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize tab configuration from dictionary.

        Args:
            config_dict: Dictionary containing tab configuration
        """
        self.id = config_dict.get('id', '')
        self.label = config_dict.get('label', '')
        self.datasets = config_dict.get('datasets', [])

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get dataset configuration by ID.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dataset configuration dict or None if not found
        """
        for dataset in self.datasets:
            if dataset.get('id') == dataset_id:
                return dataset
        return None


class ConfigManager:
    """
    Manages all application configuration.

    Provides centralized access to tab configurations, paths, and constants.
    """

    def __init__(self):
        """Initialize configuration manager."""
        self.tabs = self._load_tab_configs()
        self._tab_order = [tab.id for tab in self.tabs]

    def _load_tab_configs(self) -> List[TabConfig]:
        """
        Load tab configurations.

        Returns:
            List of TabConfig objects
        """
        return [TabConfig(config) for config in TAB_CONFIGS]

    def get_tab(self, tab_id: str) -> Optional[TabConfig]:
        """
        Get tab configuration by ID.

        Args:
            tab_id: Tab identifier

        Returns:
            TabConfig object or None if not found
        """
        for tab in self.tabs:
            if tab.id == tab_id:
                return tab
        return None

    def get_tab_labels(self) -> List[str]:
        """
        Get all tab labels in order.

        Returns:
            List of tab labels
        """
        return [tab.label for tab in self.tabs]

    def get_tab_ids(self) -> List[str]:
        """
        Get all tab IDs in order.

        Returns:
            List of tab IDs
        """
        return [tab.id for tab in self.tabs]

    def get_raw_configs(self) -> List[Dict[str, Any]]:
        """
        Get raw tab configuration dictionaries.

        Returns:
            List of tab configuration dicts (for backward compatibility)
        """
        return TAB_CONFIGS
