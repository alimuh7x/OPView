"""
UI Manager for OPView - Centralized UI card building.

This module contains the UIManager class which builds all UI cards
for the main application tabs. Extracted from OPView.py Phase 9.
"""

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from pathlib import Path


class UIManager:
    """
    Centralized UI card builder for OPView.

    Manages all UI card construction using injected data sources.
    """

    def __init__(self, grain_data, stress_strain_data, stress_data,
                 strain_data, crss_data, get_legacy_data_fn,
                 build_histogram_figure_fn):
        """
        Initialize UIManager with data sources.

        Args:
            grain_data: GrainSizeData instance
            stress_strain_data: StressStrainData instance
            stress_data: StressData instance
            strain_data: StrainData instance
            crss_data: CRSSData instance
            get_legacy_data_fn: Function to get legacy data
            build_histogram_figure_fn: Function from utils.chart_utils
        """
        self.grain_data = grain_data
        self.stress_strain_data = stress_strain_data
        self.stress_data = stress_data
        self.strain_data = strain_data
        self.crss_data = crss_data
        self.get_legacy_data = get_legacy_data_fn
        self.build_histogram_figure = build_histogram_figure_fn

    def build_size_details_card(self):
        """Build size details card using OOP structure"""
        if not self.grain_data.is_available:
            return None

        # Get time steps from OOP data source
        times = self.grain_data.get_time_steps()
        if not times:
            return None

        time_options = []
        for t in times:
            if t.is_integer():
                label = str(int(t))
            else:
                label = f"{t:.3f}".rstrip('0').rstrip('.')
            time_options.append({'label': label, 'value': str(t)})

        # Get grain labels from OOP data source
        value_labels = self.grain_data._data.get('labels', [])
        if not value_labels:
            return None
        default_time = time_options[0]['value'] if time_options else None

        return html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3('Grain Details', className='dataset-title')
            ], className='dataset-header'),
            html.Div([
                html.Div([
                    html.Div([
                        html.Label('Time Step', className='textdata-label'),
                        dcc.Dropdown(
                            id='size-card-time',
                            options=time_options,
                            value=default_time,
                            clearable=False,
                            searchable=False,
                            className='textdata-input'
                        )
                    ], className='textdata-control'),
                    html.Div([
                        html.Label('Chart Style', className='textdata-label'),
                        dcc.RadioItems(
                            id='size-card-mode',
                            options=[
                                {'label': 'Bar', 'value': 'bar'},
                                {'label': 'Line', 'value': 'line'}
                            ],
                            value='bar',
                            inline=True,
                            className='textdata-radio',
                            labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                            inputStyle={'marginRight': '4px'}
                        )
                    ], className='textdata-control'),
                ], className='textdata-controls'),
                dcc.Graph(id='size-card-main', className='textdata-plot'),
                dcc.Graph(id='size-card-line', className='textdata-plot')
            ], className='textdata-graphs')
        ], className='dataset-block textdata-card')

    def build_grain_distribution_card(self):
        """Build grain distribution card using OOP structure"""
        if not self.grain_data.is_available:
            return None

        # Get time steps from OOP data source
        times = self.grain_data.get_time_steps()
        if not times:
            return None

        time_options = []
        for t in times:
            if t.is_integer():
                label = str(int(t))
            else:
                label = f"{t:.3f}".rstrip('0').rstrip('.')
            time_options.append({'label': label, 'value': str(t)})

        default_time = time_options[0]['value']
        default_time_val = float(default_time)
        default_bins = 15

        # Use legacy function for histogram (grain uses time-based, not component-based)
        default_fig, default_summary = self.build_grain_histogram(
            time_value=default_time_val,
            bins=default_bins,
            fit=False
        )
        return html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3('Grain Distribution', className='dataset-title')
            ], className='dataset-header'),
            html.Div([
                html.Div([
                    html.Div([
                        html.Label('Time Step', className='textdata-label'),
                        dcc.Dropdown(
                            id='grain-dist-time',
                            options=time_options,
                            value=default_time,
                            clearable=False,
                            searchable=False,
                            className='textdata-input'
                        )
                    ], className='textdata-control'),
                    html.Div([
                        html.Label('Number of Bins', className='textdata-label'),
                        dcc.Slider(
                            id='grain-dist-bins',
                            min=5,
                            max=50,
                            step=5,
                            value=default_bins,
                            marks={i: str(i) for i in [5, 15, 25, 35, 45]},
                            className='textdata-slider'
                        )
                    ], className='textdata-control'),
                    html.Div([
                        html.Label('Best-fit PDF', className='textdata-label'),
                        dcc.Checklist(
                            id='grain-dist-fit',
                            options=[{'label': 'Enable', 'value': 'fit'}],
                            value=[],
                            className='textdata-checkbox'
                        )
                    ], className='textdata-control'),
                ], className='textdata-controls'),
                dcc.Graph(id='grain-dist-fig', figure=default_fig, className='textdata-plot'),
                dcc.Markdown(id='grain-dist-summary', children=default_summary, className='fit-summary', mathjax=True)
            ], className='textdata-graphs')
        ], className='dataset-block textdata-card')

    def build_stress_strain_card(self):
        """Build stress-strain card using OOP structure"""
        if not self.stress_strain_data.is_available:
            return None

        # Use OOP data source to get options and default figure
        options = self.stress_strain_data.get_component_options()
        default_components = self.stress_strain_data.get_default_components()
        fig = self.stress_strain_data.build_figure(default_components)

        return html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3('Stress-Strain Curve', className='dataset-title')
            ], className='dataset-header'),
            html.Div([
            html.Div([
                html.Div([
                    html.Label('Components', className='textdata-label'),
                    dcc.Checklist(
                        id='stress-strain-select',
                        options=options,
                        value=default_components,
                        className='crss-checklist'
                    )
                ], className='textdata-control')
            ], className='textdata-controls'),
                dcc.Graph(id='stress-strain-fig', className='textdata-plot')
            ], className='textdata-graphs')
        ], className='dataset-block textdata-card')

    def build_stress_hist_card(self):
        """Legacy PDF-based stress histogram card – hidden from UI."""
        return None

    def build_strain_hist_card(self):
        """Legacy PDF-based strain histogram card – hidden from UI."""
        return None

    def build_crss_card(self):
        """Build CRSS card using OOP structure"""
        if not self.crss_data.is_available:
            return None

        # Use OOP data source to get options
        options = self.crss_data.get_component_options()
        default_components = self.crss_data.get_default_components()
        fig = self.crss_data.build_figure(default_components)

        return html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3('CRSS Evolution', className='dataset-title')
            ], className='dataset-header'),
            html.Div([
            html.Div([
                html.Div([
                    html.Label('Components', className='textdata-label'),
                    dcc.Checklist(
                        id='crss-component-select',
                        options=options,
                        value=default_components,
                        className='crss-checklist'
                    )
                ], className='textdata-control crss-control')
            ], className='textdata-controls'),
                dcc.Graph(id='crss-avg-fig', figure=fig, className='textdata-plot')
            ], className='textdata-graphs')
        ], className='dataset-block textdata-card')

    def build_crss_hist_card(self):
        """LEGACY - Incomplete function, not used. Use build_crss_card() instead."""
        data = self.get_legacy_data('crss')
        if not data:
            return None
        series = data.get('series') or {}
        # NOTE: This function was never completed
        return None

    def build_plastic_strain_card(self):
        """Build plastic strain card"""
        data = self.get_legacy_data('plastic_strain')
        if not data:
            return None
        eps_fig, rate_fig = self.build_plastic_strain_figures()

        return html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3('Plastic Strain', className='dataset-title')
            ], className='dataset-header'),
            html.Div([
                dcc.Graph(id='plastic-strain-eps', figure=eps_fig, className='textdata-plot'),
                dcc.Graph(id='plastic-strain-rate', figure=rate_fig, className='textdata-plot')
            ], className='textdata-graphs')
        ], className='dataset-block textdata-card')

    # Helper methods

    def build_grain_histogram(self, time_value, bins, fit=False):
        """LEGACY - Replaced by grain_data.get_histogram_data()

        Uses get_legacy_data() to access SIZE_DETAILS_DATA.
        Use grain_data.get_histogram_data(time_value, bins, fit) instead.
        """
        data = self.get_legacy_data('size_details')
        if not data:
            return go.Figure(), "_No data available._"
        times = data['times']
        values = data['values']
        if not times or not values:
            return go.Figure(), "_No data available._"
        try:
            time_value = float(time_value)
        except (TypeError, ValueError):
            time_value = times[0]
        row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
        row_values = values[row_index]
        if not row_values:
            return go.Figure(), "_No data available._"
        fig, summary = self.build_histogram_figure(row_values, "Grain Size", bins, fit=fit)
        summary = f"**Time:** {times[row_index]:.3f}\n\n" + summary
        return fig, summary

    def build_plastic_strain_figures(self):
        """LEGACY - Helper for build_plastic_strain_card()"""
        data = self.get_legacy_data('plastic_strain')
        times = data['times']
        eps = data['epsilons']
        rates = data['rates']
        strain_traces = []
        rate_traces = []

        # Compute max strain
        max_strain = 0.0
        for key, values in eps.items():
            if values and len(values) > 0:
                val_array = np.asarray(values, dtype=float)
                max_val = val_array.max() if val_array.size > 0 else 0.0
                if max_val > max_strain:
                    max_strain = max_val

        for key in sorted(eps.keys()):
            strain_vals = eps.get(key, [])
            if not strain_vals:
                continue
            strain_traces.append(go.Scatter(
                x=times,
                y=strain_vals,
                mode='lines',
                line=dict(width=2),
                name=key.replace('eps_', '').upper()
            ))
        for key in sorted(rates.keys()):
            rate_vals = rates.get(key, [])
            if not rate_vals:
                continue
            rate_traces.append(go.Scatter(
                x=times,
                y=rate_vals,
                mode='lines',
                line=dict(width=2),
                name=key.replace('rate_', '').upper()
            ))

        eps_fig = go.Figure(data=strain_traces)
        eps_fig.update_layout(
            margin=dict(l=50, r=30, t=70, b=60),
            height=320,
            template='plotly_white',
            legend=dict(
                orientation='h',
                x=0,
                xanchor='left',
                y=1.18,
                yanchor='bottom',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#E1E8ED',
                borderwidth=1
            )
        )
        eps_fig.update_xaxes(
            title="Time",
            title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
            tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
        )
        eps_fig.update_yaxes(
            title="Plastic Strain",
            title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
            tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b'),
            range=[0, max_strain * 1.05]
        )

        rate_fig = go.Figure(data=rate_traces)
        rate_fig.update_layout(
            margin=dict(l=50, r=30, t=70, b=60),
            height=320,
            template='plotly_white',
            legend=dict(
                orientation='h',
                x=0,
                xanchor='left',
                y=1.18,
                yanchor='bottom',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#E1E8ED',
                borderwidth=1
            )
        )
        rate_fig.update_xaxes(
            title="Time",
            title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
            tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
        )
        rate_fig.update_yaxes(
            title="Plastic Strain Rate",
            title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
            tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
        )

        return eps_fig, rate_fig
