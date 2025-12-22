"""
Callback management module for OPView.

Provides organized callback registration through specialized managers.
"""

from .base import BaseCallbackManager
from .tab_manager import TabCallbackManager
from .project_manager import ProjectCallbackManager
from .data_manager import DataCallbackManager
from .manager import CallbackManager

__all__ = [
    'BaseCallbackManager',
    'TabCallbackManager',
    'ProjectCallbackManager',
    'DataCallbackManager',
    'CallbackManager',
]
