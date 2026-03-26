"""
Callback management module for OPView.

Provides organized callback registration through specialized managers.
"""

from .base import BaseCallbackManager
from .tab_manager import TabCallbackManager
from .project_manager import ProjectCallbackManager
from .data_manager import DataCallbackManager
from .graphs_manager import GraphsCallbackManager
from .formula_manager import FormulaCallbackManager
from .notebook_manager import NotebookCallbackManager
from .initializations_explorer_manager import InitializationsExplorerCallbackManager
from .manager import CallbackManager

__all__ = [
    'BaseCallbackManager',
    'TabCallbackManager',
    'ProjectCallbackManager',
    'DataCallbackManager',
    'GraphsCallbackManager',
    'FormulaCallbackManager',
    'NotebookCallbackManager',
    'InitializationsExplorerCallbackManager',
    'CallbackManager',
]
