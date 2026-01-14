"""
Data callback manager for OPView.

Manages callbacks related to data visualization using OOP data sources.
"""

from .base import BaseCallbackManager


class DataCallbackManager(BaseCallbackManager):
    """
    Manages data visualization callbacks using factories.

    Registers callbacks for histograms, component selections,
    and time series visualizations.
    """

    def __init__(self, app, context, data_manager):
        """
        Initialize data callback manager.

        Args:
            app: Dash application instance
            context: AppContext instance
            data_manager: DataManager instance with OOP data sources
        """
        super().__init__(app, context)
        self.data_manager = data_manager

    def register(self) -> None:
        """Register all data visualization callbacks."""
        self._register_histograms()
        self._register_component_selections()
        self._register_time_series()
        self._register_grain_histogram()

    def _register_histograms(self):
        """Register histogram callbacks using factories."""
        from data.base import HistogramDataSource
        from ui.callbacks import create_histogram_callback

        sources = {
            'stress': self.data_manager.stress_data,
            'strain': self.data_manager.strain_data,
        }

        for name, source in sources.items():
            if isinstance(source, HistogramDataSource) and source.is_available:
                cb = create_histogram_callback(
                    self.app, source,
                    f'{name}-hist-fig', f'{name}-hist-summary',
                    f'{name}-hist-bins', f'{name}-hist-fit', f'{name}-hist-component'
                )
                self._track_callback(cb)

    def _register_component_selections(self):
        """Register component selection callbacks."""
        from ui.callbacks import create_component_selection_callback

        sources = {
            'stress-strain': self.data_manager.stress_strain_data,
            'crss': self.data_manager.crss_data,
        }

        for name, source in sources.items():
            if source.is_available:
                cb = create_component_selection_callback(
                    self.app, source,
                    f'{name}-fig', f'{name}-components'
                )
                self._track_callback(cb)

    def _register_time_series(self):
        """Register time series callbacks."""
        from ui.callbacks import create_time_series_callback

        # Grain size time series
        if self.data_manager.grain_data.is_available:
            cb = create_time_series_callback(
                self.app, self.data_manager.grain_data,
                'size-ave-fig', 'size-ave-summary'
            )
            self._track_callback(cb)

    def _register_grain_histogram(self):
        """Register grain distribution histogram callback."""
        grain_data = self.data_manager.grain_data

        if not grain_data.is_available:
            return

        from dash import Output, Input
        from OPView import ui_manager

        @self.app.callback(
            Output('grain-dist-fig', 'figure'),
            Output('grain-dist-summary', 'children'),
            Input('grain-dist-time', 'value'),
            Input('grain-dist-bins', 'value'),
            Input('grain-dist-fit', 'value'),
            prevent_initial_call=True
        )
        def update_grain_histogram(time_value, bins, fit_value):
            """Update grain distribution histogram."""
            fit_enabled = bool(fit_value and 'fit' in fit_value)
            if time_value is None:
                times = grain_data.get_time_steps()
                time_value = times[0] if times else 0
            return ui_manager.build_grain_histogram(float(time_value), bins or 15, fit=fit_enabled)

        self._track_callback(update_grain_histogram)
