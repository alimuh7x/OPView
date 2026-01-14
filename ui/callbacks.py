"""
Callback factory functions for OPView.

Provides reusable callback patterns that work with OOP data sources.
"""

from typing import Callable, List, Optional
from dash import Input, Output


def create_histogram_callback(app, data_source, id_prefix: str) -> Callable:
    """
    Factory function to create histogram callbacks.

    Creates a callback that updates a histogram figure and summary text
    based on component selection, bin count, and fit options.

    Args:
        app: Dash app instance
        data_source: HistogramDataSource instance
        id_prefix: ID prefix for components (e.g., 'stress-hist')

    Returns:
        The created callback function

    Example:
        >>> stress_data = StressData(data_dir)
        >>> create_histogram_callback(app, stress_data, 'stress-hist')
    """
    @app.callback(
        Output(f'{id_prefix}-fig', 'figure'),
        Output(f'{id_prefix}-summary', 'children'),
        Input(f'{id_prefix}-component', 'value'),
        Input(f'{id_prefix}-bins', 'value'),
        Input(f'{id_prefix}-fit', 'value'),
        prevent_initial_call=True
    )
    def update_histogram(component, bins, fit_value):
        """Update histogram based on component, bins, and fit selection"""
        fit_enabled = bool(fit_value and 'fit' in fit_value)

        # Use default component if none selected
        if not component:
            component = data_source.get_default_components()[0]

        # Use default bins if not specified
        if bins is None:
            bins = data_source.default_bins

        # Data source handles histogram computation
        return data_source.get_histogram_data(component, bins, fit=fit_enabled)

    return update_histogram


def create_time_series_callback(
    app,
    data_source,
    graph_id: str,
    time_id: str,
    component_id: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Factory for time-series visualization callbacks.

    Creates a callback that updates a graph based on time step selection
    and optionally component selection.

    Args:
        app: Dash app instance
        data_source: TimeSeriesDataSource instance
        graph_id: ID of the graph component
        time_id: ID of the time dropdown
        component_id: Optional ID of component selector (checklist/dropdown)
        **kwargs: Additional callback options

    Returns:
        The created callback function

    Example:
        >>> crss_data = CRSSData(data_dir)
        >>> create_time_series_callback(
        ...     app, crss_data,
        ...     graph_id='crss-fig',
        ...     time_id='crss-time',
        ...     component_id='crss-components'
        ... )
    """
    inputs = [Input(time_id, 'value')]
    if component_id:
        inputs.append(Input(component_id, 'value'))

    @app.callback(
        Output(graph_id, 'figure'),
        inputs,
        prevent_initial_call=True,
        **kwargs
    )
    def update_time_series(*args):
        """Update time-series figure based on time and component selection"""
        time_value = args[0]
        components = args[1] if len(args) > 1 else None

        # Use default time if none selected
        if time_value is None:
            time_value = data_source.get_default_time()

        # Use default components if none selected
        if components is None or (isinstance(components, list) and len(components) == 0):
            components = data_source.get_default_components()

        # Data source builds the figure
        return data_source.build_time_series_figure(time_value, components)

    return update_time_series


def create_component_selection_callback(
    app,
    data_source,
    graph_id: str,
    component_id: str,
    **kwargs
) -> Callable:
    """
    Factory for component selection callbacks.

    Creates a callback that updates a graph based on component checklist selection.

    Args:
        app: Dash app instance
        data_source: DataSource instance with build_figure method
        graph_id: ID of the graph
        component_id: ID of the component checklist/dropdown
        **kwargs: Additional callback options

    Returns:
        The created callback function

    Example:
        >>> stress_strain_data = StressStrainData(data_dir)
        >>> create_component_selection_callback(
        ...     app, stress_strain_data,
        ...     graph_id='stress-strain-fig',
        ...     component_id='stress-components'
        ... )
    """
    @app.callback(
        Output(graph_id, 'figure'),
        Input(component_id, 'value'),
        prevent_initial_call=True,
        **kwargs
    )
    def update_components(selected_components):
        """Update figure based on component selection"""
        # Use default components if none selected
        components = selected_components or data_source.get_default_components()

        # Data source builds the figure
        return data_source.build_figure(components)

    return update_components


def create_multi_output_callback(
    app,
    outputs: List[tuple],
    inputs: List[tuple],
    callback_func: Callable,
    **kwargs
) -> Callable:
    """
    Generic factory for multi-output callbacks.

    Creates a callback with multiple outputs and inputs using a provided function.

    Args:
        app: Dash app instance
        outputs: List of (component_id, property) tuples
        inputs: List of (component_id, property) tuples
        callback_func: Function to handle the callback logic
        **kwargs: Additional callback options

    Returns:
        The created callback function

    Example:
        >>> def update_size_details(time, mode):
        ...     return grain_data.build_detail_figures(time, mode)
        >>>
        >>> create_multi_output_callback(
        ...     app,
        ...     outputs=[('size-main', 'figure'), ('size-line', 'figure')],
        ...     inputs=[('size-time', 'value'), ('size-mode', 'value')],
        ...     callback_func=update_size_details
        ... )
    """
    output_list = [Output(comp_id, prop) for comp_id, prop in outputs]
    input_list = [Input(comp_id, prop) for comp_id, prop in inputs]

    @app.callback(
        output_list,
        input_list,
        prevent_initial_call=True,
        **kwargs
    )
    def wrapper(*args):
        """Wrapper that calls the provided callback function"""
        return callback_func(*args)

    return wrapper


class CallbackRegistry:
    """
    Central registry for automatic callback registration.

    Manages callback creation and registration for data sources,
    ensuring callbacks are only created for available data.

    Example:
        >>> registry = CallbackRegistry(app)
        >>> registry.register_histogram(stress_data, 'stress-hist')
        >>> registry.register_component_selection(
        ...     stress_strain_data, 'stress-strain-fig', 'stress-components'
        ... )
    """

    def __init__(self, app):
        """
        Initialize callback registry.

        Args:
            app: Dash app instance
        """
        self.app = app
        self.callbacks = []

    def register_histogram(self, data_source, id_prefix: str) -> Optional[Callable]:
        """
        Register a histogram callback.

        Args:
            data_source: HistogramDataSource instance
            id_prefix: ID prefix for components

        Returns:
            The created callback function, or None if data not available
        """
        if not data_source.is_available:
            return None

        cb = create_histogram_callback(self.app, data_source, id_prefix)
        self.callbacks.append(cb)
        return cb

    def register_time_series(
        self,
        data_source,
        graph_id: str,
        time_id: str,
        component_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Callable]:
        """
        Register a time-series callback.

        Args:
            data_source: TimeSeriesDataSource instance
            graph_id: ID of the graph component
            time_id: ID of the time dropdown
            component_id: Optional ID of component selector
            **kwargs: Additional callback options

        Returns:
            The created callback function, or None if data not available
        """
        if not data_source.is_available:
            return None

        cb = create_time_series_callback(
            self.app, data_source, graph_id, time_id, component_id, **kwargs
        )
        self.callbacks.append(cb)
        return cb

    def register_component_selection(
        self,
        data_source,
        graph_id: str,
        component_id: str,
        **kwargs
    ) -> Optional[Callable]:
        """
        Register a component selection callback.

        Args:
            data_source: DataSource instance
            graph_id: ID of the graph
            component_id: ID of the component checklist
            **kwargs: Additional callback options

        Returns:
            The created callback function, or None if data not available
        """
        if not data_source.is_available:
            return None

        cb = create_component_selection_callback(
            self.app, data_source, graph_id, component_id, **kwargs
        )
        self.callbacks.append(cb)
        return cb

    def register_custom(
        self,
        outputs: List[tuple],
        inputs: List[tuple],
        callback_func: Callable,
        **kwargs
    ) -> Callable:
        """
        Register a custom callback with multiple outputs/inputs.

        Args:
            outputs: List of (component_id, property) tuples
            inputs: List of (component_id, property) tuples
            callback_func: Function to handle the callback logic
            **kwargs: Additional callback options

        Returns:
            The created callback function
        """
        cb = create_multi_output_callback(
            self.app, outputs, inputs, callback_func, **kwargs
        )
        self.callbacks.append(cb)
        return cb

    def get_callback_count(self) -> int:
        """Get the number of registered callbacks"""
        return len(self.callbacks)


# Convenience function for bulk registration
def register_all_callbacks(app, data_sources: dict, callback_configs: list):
    """
    Bulk register callbacks from configuration.

    Args:
        app: Dash app instance
        data_sources: Dictionary of data source instances
        callback_configs: List of callback configuration dicts

    Example:
        >>> data_sources = {
        ...     'stress': StressData(data_dir),
        ...     'strain': StrainData(data_dir),
        ...     'crss': CRSSData(data_dir)
        ... }
        >>>
        >>> callback_configs = [
        ...     {'type': 'histogram', 'source': 'stress', 'id': 'stress-hist'},
        ...     {'type': 'histogram', 'source': 'strain', 'id': 'strain-hist'},
        ...     {'type': 'component', 'source': 'crss', 'graph': 'crss-fig', 'component': 'crss-comp'}
        ... ]
        >>>
        >>> register_all_callbacks(app, data_sources, callback_configs)
    """
    registry = CallbackRegistry(app)

    for config in callback_configs:
        source_key = config.get('source')
        data_source = data_sources.get(source_key)

        if data_source is None:
            continue

        callback_type = config.get('type')

        if callback_type == 'histogram':
            registry.register_histogram(data_source, config['id'])

        elif callback_type == 'time_series':
            registry.register_time_series(
                data_source,
                config['graph'],
                config['time'],
                config.get('component')
            )

        elif callback_type == 'component':
            registry.register_component_selection(
                data_source,
                config['graph'],
                config['component']
            )

    return registry
