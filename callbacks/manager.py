"""
Main callback manager orchestrator for OPView.

Coordinates all callback managers and registers callbacks.
"""

from .tab_manager import TabCallbackManager
from .project_manager import ProjectCallbackManager
from .data_manager import DataCallbackManager
from .graphs_manager import GraphsCallbackManager
from .formula_manager import FormulaCallbackManager
from .notebook_manager import NotebookCallbackManager
from .initializations_explorer_manager import InitializationsExplorerCallbackManager


class CallbackManager:
    """
    Orchestrates all callback managers.

    Coordinates registration of callbacks across different feature areas:
    - Tab navigation and rendering
    - Project folder selection
    - Data visualization
    - Comparison (registered separately via ComparisonManager)
    """

    def __init__(self, app, context, data_manager, ui_manager=None, comparison_manager=None):
        """
        Initialize callback manager.

        Args:
            app: Dash application instance
            context: AppContext instance
            data_manager: DataManager instance
            ui_manager: UIManager instance (optional, for future use)
            comparison_manager: ComparisonManager instance (optional)
        """
        self.app = app
        self.context = context
        self.data_manager = data_manager
        self.ui_manager = ui_manager
        self.comparison_manager = comparison_manager

        # Initialize sub-managers
        self.tab_manager = TabCallbackManager(app, context, ui_manager)
        self.project_manager = ProjectCallbackManager(app, context)
        self.data_manager_callbacks = DataCallbackManager(app, context, data_manager)
        self.graphs_manager = GraphsCallbackManager(app, context)
        self.formula_manager = FormulaCallbackManager(app, context)
        self.notebook_manager = NotebookCallbackManager(app, context)
        self.initializations_explorer_manager = InitializationsExplorerCallbackManager(app, context)

    def register_all(self):
        """
        Register all callbacks.

        Coordinates callback registration across all managers.
        Comparison callbacks are registered automatically when
        ComparisonManager is initialized.
        """
        print("[CallbackManager] Registering callbacks...")

        # Register tab callbacks
        self.tab_manager.register()
        print(f"  ✓ Tab callbacks: {self.tab_manager.count()}")

        # Register project callbacks
        self.project_manager.register()
        print(f"  ✓ Project callbacks: {self.project_manager.count()}")

        # Register data visualization callbacks
        self.data_manager_callbacks.register()
        print(f"  ✓ Data callbacks: {self.data_manager_callbacks.count()}")

        self.graphs_manager.register()
        print(f"  ✓ Graph callbacks: {self.graphs_manager.count()}")

        self.formula_manager.register()
        print(f"  ✓ Formula callbacks: {self.formula_manager.count()}")

        self.notebook_manager.register()
        print(f"  ✓ Notebook callbacks: {self.notebook_manager.count()}")

        self.initializations_explorer_manager.register()
        print(f"  ✓ Initializations Explorer callbacks: {self.initializations_explorer_manager.count()}")

        # Note: Comparison callbacks are already registered by ComparisonManager
        if self.comparison_manager:
            print(f"  ✓ Comparison callbacks: registered via ComparisonManager")

        total = (
            self.tab_manager.count() +
            self.project_manager.count() +
            self.data_manager_callbacks.count() +
            self.graphs_manager.count() +
            self.formula_manager.count() +
            self.notebook_manager.count() +
            self.initializations_explorer_manager.count()
        )
        print(f"[CallbackManager] Total callbacks registered: {total}")

    def get_callback_summary(self):
        """
        Get summary of registered callbacks.

        Returns:
            Dictionary with callback counts per manager
        """
        return {
            'tab': self.tab_manager.count(),
            'project': self.project_manager.count(),
            'data': self.data_manager_callbacks.count(),
            'graphs': self.graphs_manager.count(),
            'formula': self.formula_manager.count(),
            'notebook': self.notebook_manager.count(),
            'initializations_explorer': self.initializations_explorer_manager.count(),
            'total': (
                self.tab_manager.count() +
                self.project_manager.count() +
                self.data_manager_callbacks.count() +
                self.graphs_manager.count() +
                self.formula_manager.count() +
                self.notebook_manager.count() +
                self.initializations_explorer_manager.count()
            )
        }
