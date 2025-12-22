"""
Application context for centralized state management.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any


class AppContext:
    """
    Centralized application state manager.

    Manages all global application state including project data,
    data sources, and caching layers.
    """

    def __init__(self, data_dir: Path):
        """
        Initialize application context.

        Args:
            data_dir: Base directory for TextData files
        """
        self.data_dir = data_dir

        # Project state
        self.current_project_vtk_path: Optional[str] = None
        self.loaded_project_names: List[str] = []
        self.discovered_project_folders: Dict[str, Any] = {}
        self.loaded_project_vtk_files: List[str] = []
        self.loaded_project_vtk_files_by_project: Dict[str, List[str]] = {}

        # Data sources
        self.data_sources: Dict[str, Any] = {}

        # Caches
        self.reader_cache: Dict[str, Any] = {}
        self.comparison_panels_cache: Dict[str, Any] = {}
        self.comparison_grid_cache: Dict[tuple, Any] = {}

        # Version tracking for cache invalidation
        self._version = 0

    def invalidate_cache(self) -> None:
        """Clear all caches and increment version."""
        self.reader_cache.clear()
        self.comparison_panels_cache.clear()
        self.comparison_grid_cache.clear()
        self._version += 1

    def update_project(
        self,
        vtk_path: Optional[str],
        project_names: List[str],
        folders: Dict[str, Any],
        files_by_project: Dict[str, List[str]]
    ) -> None:
        """
        Atomic project state update.

        Args:
            vtk_path: Current project VTK path
            project_names: List of loaded project names
            folders: Discovered project folders
            files_by_project: VTK files grouped by project
        """
        self.current_project_vtk_path = vtk_path
        self.loaded_project_names = project_names
        self.discovered_project_folders = folders
        self.loaded_project_vtk_files_by_project = files_by_project

        # Flatten all files from all projects
        all_files = []
        for files in files_by_project.values():
            all_files.extend(files)
        self.loaded_project_vtk_files = list(set(all_files))

        self._version += 1

    @property
    def version(self) -> int:
        """Get current state version for cache invalidation."""
        return self._version
