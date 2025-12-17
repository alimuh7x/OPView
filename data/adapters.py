"""
Data adapters that bridge existing OPView data to the callback factory system.

These adapters wrap the existing global data dictionaries and helper functions
to provide the interface expected by callback factories, without requiring
a complete refactor of the data loading logic.
"""

import plotly.graph_objects as go
import numpy as np
from typing import List, Dict, Optional, Tuple


class CallbackDataAdapter:
    """Base adapter class with common properties"""

    def __init__(self, data_dict, is_available=True):
        """
        Initialize adapter.

        Args:
            data_dict: The global data dictionary (e.g., STRESS_STRAIN_DATA)
            is_available: Whether the data is available
        """
        self._data = data_dict
        self.is_available = is_available and bool(data_dict)
        self.default_bins = 30

    def get_default_components(self) -> List[str]:
        """Get default components to display"""
        return []


class StressHistogramAdapter(CallbackDataAdapter):
    """Adapter for stress histogram data"""

    def __init__(self, data_dict, stress_values_func, histogram_func):
        super().__init__(data_dict)
        self._stress_values_func = stress_values_func
        self._histogram_func = histogram_func

    def get_default_components(self) -> List[str]:
        return ['Sigma_xx']

    def get_histogram_data(self, component: str, bins: int = None,
                          fit: bool = False) -> Tuple[go.Figure, str]:
        """
        Get histogram figure and summary.

        Args:
            component: Component name
            bins: Number of bins
            fit: Whether to fit distribution

        Returns:
            Tuple of (figure, summary_text)
        """
        values = self._stress_values_func(component)
        if bins is None:
            bins = self.default_bins
        return self._histogram_func(values, "Stress (MPa)", bins, fit=fit)


class StrainHistogramAdapter(CallbackDataAdapter):
    """Adapter for strain histogram data"""

    def __init__(self, data_dict, strain_values_func, histogram_func):
        super().__init__(data_dict)
        self._strain_values_func = strain_values_func
        self._histogram_func = histogram_func

    def get_default_components(self) -> List[str]:
        return ['Epsilon_xx']

    def get_histogram_data(self, component: str, bins: int = None,
                          fit: bool = False) -> Tuple[go.Figure, str]:
        """Get histogram figure and summary"""
        values = self._strain_values_func(component)
        if bins is None:
            bins = self.default_bins
        return self._histogram_func(values, "Strain (%)", bins, fit=fit)


class GrainHistogramAdapter(CallbackDataAdapter):
    """Adapter for grain size histogram data"""

    def __init__(self, data_dict, grain_histogram_func):
        super().__init__(data_dict)
        self._grain_histogram_func = grain_histogram_func

    def get_histogram_data(self, time_value: float = None, bins: int = None,
                          fit: bool = False) -> Tuple[go.Figure, str]:
        """Get grain histogram figure and summary"""
        if bins is None:
            bins = self.default_bins
        return self._grain_histogram_func(time_value, bins, fit=fit)


class StressStrainComponentAdapter(CallbackDataAdapter):
    """Adapter for stress-strain component selection"""

    def __init__(self, data_dict, build_figure_func):
        super().__init__(data_dict)
        self._build_figure_func = build_figure_func

    def get_default_components(self) -> List[str]:
        return ['Sigma_xx', 'Mises']

    def build_figure(self, components: List[str]) -> go.Figure:
        """Build stress-strain figure for selected components"""
        # The existing function handles component selection internally
        # We can't easily refactor this without changing the function signature
        # For now, just call it and let it handle everything
        return self._build_figure_func(components)


class CRSSComponentAdapter(CallbackDataAdapter):
    """Adapter for CRSS component selection"""

    def __init__(self, data_dict, build_figure_func):
        super().__init__(data_dict)
        self._build_figure_func = build_figure_func

    def get_default_components(self) -> List[str]:
        return ['Average']

    def build_figure(self, components: List[str]) -> go.Figure:
        """Build CRSS figure for selected components"""
        return self._build_figure_func(components)


class SizeDetailsMultiAdapter(CallbackDataAdapter):
    """Adapter for size details with multiple outputs"""

    def __init__(self, data_dict, update_func):
        super().__init__(data_dict)
        self._update_func = update_func

    def build_detail_figures(self, time_value: float,
                           mode: str) -> Tuple[go.Figure, go.Figure]:
        """Build both size detail figures"""
        return self._update_func(time_value, mode)


# Helper function to create all adapters from OPView globals
def create_adapters(opview_globals):
    """
    Create all data adapters from OPView global variables and functions.

    Args:
        opview_globals: The globals() dict from OPView.py

    Returns:
        Dictionary of adapter instances

    Usage:
        In OPView.py:
        >>> adapters = create_adapters(globals())
        >>> stress_adapter = adapters['stress_hist']
    """
    adapters = {}

    # Check if data is available
    has_stress_strain = bool(opview_globals.get('STRESS_STRAIN_DATA'))
    has_crss = bool(opview_globals.get('CRSS_DATA'))
    has_size = bool(opview_globals.get('SIZE_DETAILS_DATA'))

    # Create adapters if data is available
    if has_stress_strain:
        adapters['stress_hist'] = StressHistogramAdapter(
            opview_globals['STRESS_STRAIN_DATA'],
            opview_globals['stress_series_values'],
            opview_globals['build_histogram_figure']
        )

        adapters['strain_hist'] = StrainHistogramAdapter(
            opview_globals['STRESS_STRAIN_DATA'],
            opview_globals['strain_series_values'],
            opview_globals['build_histogram_figure']
        )

        # For stress-strain component selection, we need a wrapper
        # because the existing function does everything internally
        def build_stress_strain_figure(components):
            """Wrapper for stress-strain figure building"""
            data = opview_globals['STRESS_STRAIN_DATA']
            strain = np.array(data['strain']) * 100.0
            comp_map = data['components']
            labels = {
                "Sigma_xx": "σ_xx",
                "Sigma_yy": "σ_yy",
                "Sigma_zz": "σ_zz",
                "Mises": "von Mises",
            }
            default_components = ['Sigma_xx', 'Mises']
            selected = components or default_components
            traces = []
            for comp in selected:
                values = comp_map.get(comp)
                if values is None:
                    continue
                traces.append(go.Scatter(
                    x=strain,
                    y=np.array(values) / 1e6,
                    mode='lines',
                    name=labels.get(comp, comp)
                ))
            fig = go.Figure(data=traces)
            fig.update_layout(
                xaxis_title='Strain (%)',
                yaxis_title='Stress (MPa)',
                template='plotly_white',
                margin=dict(l=50, r=30, t=40, b=60),
                height=400,
            )
            axis_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f')
            tick_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
            fig.update_xaxes(title_font=axis_font, tickfont=tick_font)
            fig.update_yaxes(title_font=axis_font, tickfont=tick_font)
            return fig

        adapters['stress_strain'] = StressStrainComponentAdapter(
            opview_globals['STRESS_STRAIN_DATA'],
            build_stress_strain_figure
        )

    if has_crss:
        adapters['crss'] = CRSSComponentAdapter(
            opview_globals['CRSS_DATA'],
            opview_globals['build_crss_figure']
        )

    if has_size:
        adapters['grain_hist'] = GrainHistogramAdapter(
            opview_globals['SIZE_DETAILS_DATA'],
            opview_globals['build_grain_histogram']
        )

        # For size details, we need a wrapper for the existing function
        def build_size_figures(selected_time, chart_mode):
            """Wrapper for size detail figures"""
            data = opview_globals['SIZE_DETAILS_DATA']
            times = data['times']
            labels = data['labels']
            values = data['values']
            if not times or not labels:
                return go.Figure(), go.Figure()
            try:
                time_value = float(selected_time)
            except (TypeError, ValueError):
                time_value = times[0]
            row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
            row_values = values[row_index]

            if chart_mode not in {'line', 'bar'}:
                chart_mode = 'bar'

            main_fig = go.Figure()
            if chart_mode == 'bar':
                main_fig.add_bar(x=labels, y=row_values, marker_color='#183568')
            else:
                main_fig.add_scatter(x=labels, y=row_values, mode='lines+markers',
                                   line=dict(color='#183568'))
            main_fig.update_layout(
                margin=dict(l=50, r=30, t=40, b=60),
                height=320,
                template='plotly_white'
            )
            axis_title_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f')
            tick_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
            main_fig.update_xaxes(title="Grain Number", title_font=axis_title_font, tickfont=tick_font)
            main_fig.update_yaxes(title="Grain Size", title_font=axis_title_font, tickfont=tick_font)

            size_average_data = opview_globals.get('SIZE_AVERAGE_DATA')
            if size_average_data:
                avg_times = size_average_data['times']
                avg_values = size_average_data['averages']
            else:
                avg_times = times
                avg_values = [sum(row) / len(row) if row else 0 for row in values]

            line_fig = go.Figure(
                data=[go.Scatter(x=avg_times, y=avg_values, mode='lines+markers',
                               line=dict(color='#c50623'))]
            )
            line_fig.update_layout(
                margin=dict(l=50, r=30, t=40, b=60),
                height=320,
                template='plotly_white'
            )
            line_fig.update_xaxes(title="Time Step", title_font=axis_title_font, tickfont=tick_font)
            line_fig.update_yaxes(title="Average Grain Size", title_font=axis_title_font, tickfont=tick_font)

            return main_fig, line_fig

        adapters['size_details'] = SizeDetailsMultiAdapter(
            opview_globals['SIZE_DETAILS_DATA'],
            build_size_figures
        )

    return adapters
