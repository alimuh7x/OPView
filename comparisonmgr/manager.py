"""
Comparison manager - wraps existing comparison functionality.

This is a transitional implementation that wraps the existing
comparison functions from OPView.py while we complete the full extraction.
"""

from pathlib import Path


class ComparisonManager:
    """
    Manages comparison feature.

    Currently wraps existing OPView.py comparison functions.
    Will be fully extracted in future phases.
    """

    def __init__(self, app, context, config_manager, reader_factory, vtk_path_resolver):
        """
        Initialize comparison manager.

        Args:
            app: Dash application instance
            context: AppContext instance
            config_manager: ConfigManager instance
            reader_factory: Function to create VTK readers (get_reader)
            vtk_path_resolver: Function to resolve VTK paths
        """
        self.app = app
        self.context = context
        self.config_manager = config_manager
        self.reader_factory = reader_factory
        self.vtk_path_resolver = vtk_path_resolver

        # Comparison directory
        self.comparison_dir = self._get_comparison_dir()

        # Note: Callbacks are registered globally in OPView.py for now
        # Full extraction will happen in later phases

    def _get_comparison_dir(self) -> Path:
        """Get comparison data directory."""
        from config import comparison_data_dir
        return comparison_data_dir()

    def list_comparison_files(self):
        """
        List VTK files in comparison folder.

        Returns:
            List of file names
        """
        if not self.comparison_dir.exists():
            return []

        from config import ALLOWED_VTK_EXTENSIONS
        return [
            f.name for f in self.comparison_dir.glob('*.vt*')
            if f.suffix.lower() in ALLOWED_VTK_EXTENSIONS
        ]

    def get_available_vtk_files(self):
        """
        Get all available VTK files (projects + comparison).

        Returns:
            List of file paths
        """
        project_files = self.context.loaded_project_vtk_files or []
        comparison_files = self.list_comparison_files()

        # Comparison files need full paths
        comparison_paths = [
            str((self.comparison_dir / f).resolve())
            for f in comparison_files
        ]

        return sorted(set(project_files + comparison_paths))

    def build_comparison_content(self, tab_id, files, group_controls=None, group_selected=None):
        """
        Build comparison tab content.

        Args:
            tab_id: Active tab ID
            files: List of comparison file names
            group_controls: Stored control states per group
            group_selected: Selected file paths per group

        Returns:
            List of Dash components

        Note: Currently delegates to OPView.py build_comparison_content function
        """
        # Import the existing function from OPView.py
        from OPView import build_comparison_content

        # Determine allowed groups for this tab
        from OPView import allowed_comparison_groups_for_tab, TAB_CONFIGS
        allowed_groups = allowed_comparison_groups_for_tab(tab_id)

        return build_comparison_content(
            files,
            group_controls_by_group=group_controls,
            group_selected_paths_by_group=group_selected,
            allowed_groups=allowed_groups
        )
