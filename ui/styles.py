"""
CSS class name constants for OPView.

Wraps existing CSS classes to avoid hardcoding strings throughout the codebase.
"""


class CSS:
    """CSS class name constants - wraps existing stylesheet classes"""

    # Card structure
    CARD = 'dataset-block textdata-card'
    CARD_HEADER = 'dataset-header'
    CARD_ACCENT = 'dataset-accent'
    CARD_TITLE = 'dataset-title'

    # Controls
    CONTROL = 'textdata-control'
    CONTROLS = 'textdata-controls'
    INPUT = 'textdata-input'
    LABEL = 'textdata-label'
    SLIDER = 'textdata-slider'
    RADIO = 'textdata-radio'
    CHECKLIST = 'textdata-checklist'

    # CRSS-specific
    CRSS_CONTROL = 'textdata-control crss-control'
    CRSS_CHECKLIST = 'crss-checklist'

    # Graphs
    PLOT = 'textdata-plot'
    GRAPHS = 'textdata-graphs'

    # Buttons (if you have them)
    BUTTON = 'textdata-button'

    @classmethod
    def combine(cls, *class_names: str) -> str:
        """
        Combine multiple CSS classes.

        Args:
            *class_names: CSS class names to combine

        Returns:
            Space-separated class names

        Example:
            >>> CSS.combine(CSS.CONTROL, 'custom-class')
            'textdata-control custom-class'
        """
        return ' '.join(class_names)
