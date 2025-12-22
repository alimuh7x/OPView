"""
Main application orchestrator for OPView.
"""

from pathlib import Path
from dash import Dash
import dash_mantine_components as dmc

from .context import AppContext


class OPViewApp:
    """
    Main application orchestrator.

    Coordinates all managers and initializes the application.
    """

    def __init__(self, data_dir: Path = Path('TextData')):
        """
        Initialize OPView application.

        Args:
            data_dir: Directory containing TextData files
        """
        self.context = AppContext(data_dir)
        self.app = self._create_dash_app()

        # Managers (initialized in initialize() method)
        self.config_manager = None
        self.data_manager = None
        self.ui_manager = None
        self.callback_manager = None
        self.comparison_manager = None

    def _create_dash_app(self) -> Dash:
        """
        Create and configure Dash app.

        Returns:
            Configured Dash application instance
        """
        app = Dash(
            __name__,
            suppress_callback_exceptions=True,
            external_stylesheets=[dmc.styles.ALL]
        )
        app.title = "OPView - Phase Field Visualization"
        return app

    def initialize(self):
        """
        Initialize all managers and load data.

        This method should be called after instantiation to set up
        the application before running the server.
        """
        # Phase 2: Load configuration ✅
        from config import ConfigManager
        self.config_manager = ConfigManager()
        print(f"[AppInit] Configuration loaded: {len(self.config_manager.tabs)} tabs")

        # Phase 3: Initialize data sources ✅
        from data import DataManager
        self.data_manager = DataManager(self.context)
        self.data_manager.load_all()
        print(f"[AppInit] Data sources loaded: {len(self.context.data_sources)} OOP sources")

        # Scan for projects (using utils module)
        from utils import scan_project_folders, get_reader, resolve_vtk_path
        self.context.discovered_project_folders = scan_project_folders()

        # Phase 7: Inject context and data_manager into OPView.py (backwards compatibility)
        import OPView
        OPView.app_context = self.context
        OPView.data_manager = self.data_manager
        # Also update legacy globals from context for backwards compatibility
        OPView.discovered_project_folders = self.context.discovered_project_folders
        print(f"[AppInit] Injected context into OPView.py for backwards compatibility")

        # Phase 7: Initialize UI manager
        # self.ui_manager = UIManager(self.context, self.config_manager)

        # Phase 4: Initialize comparison manager ✅
        from comparisonmgr import ComparisonManager
        self.comparison_manager = ComparisonManager(
            self.app, self.context, self.config_manager,
            get_reader, resolve_vtk_path
        )
        print(f"[AppInit] Comparison manager initialized")

        # Build layout (temporary - using existing layout)
        from OPView import app as existing_app
        self.app.layout = existing_app.layout

        # Phase 5: Register all callbacks ✅
        from callbacks import CallbackManager
        self.callback_manager = CallbackManager(
            self.app, self.context, self.data_manager,
            self.ui_manager, self.comparison_manager
        )
        self.callback_manager.register_all()

        print("[AppInit] Application initialized (Phases 1-5 complete)")

    def run(self, host='127.0.0.1', port=8050, debug=True):
        """
        Start the Dash server.

        Args:
            host: Server host address
            port: Server port number
            debug: Enable debug mode
        """
        self.app.run_server(host=host, port=port, debug=debug)
