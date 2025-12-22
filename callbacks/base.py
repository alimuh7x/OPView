"""
Base callback manager for OPView.
"""

from abc import ABC, abstractmethod
from typing import List, Any


class BaseCallbackManager(ABC):
    """
    Abstract base class for all callback managers.

    Provides common functionality for tracking and managing callbacks.
    """

    def __init__(self, app, context):
        """
        Initialize base callback manager.

        Args:
            app: Dash application instance
            context: AppContext instance for state management
        """
        self.app = app
        self.context = context
        self._callbacks: List[Any] = []

    @abstractmethod
    def register(self) -> None:
        """
        Register all callbacks managed by this manager.

        Subclasses must implement this method to register their specific callbacks.
        """
        pass

    def _track_callback(self, callback_func):
        """
        Track a registered callback function.

        Args:
            callback_func: The callback function to track

        Returns:
            The callback function (for decorator chaining)
        """
        self._callbacks.append(callback_func)
        return callback_func

    def count(self) -> int:
        """
        Get the number of registered callbacks.

        Returns:
            Count of registered callbacks
        """
        return len(self._callbacks)

    def callback_names(self) -> List[str]:
        """
        Get names of all registered callbacks.

        Returns:
            List of callback function names
        """
        return [cb.__name__ for cb in self._callbacks if hasattr(cb, '__name__')]
