"""
Application core module for OPView.

Contains the main application orchestrator and context management.
"""

from .context import AppContext
from .opview_app import OPViewApp

__all__ = ['AppContext', 'OPViewApp']
