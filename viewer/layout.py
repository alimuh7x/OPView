"""Dash layout helpers for viewer tabs."""
from dash import dcc, html
import dash_mantine_components as dmc


def format_range_value(value: float):
    """Format range values to 6 decimals, switch to scientific notation beyond ±9999."""
    if value is None:
        return value
    abs_val = abs(value)
    if abs_val == 0 or 1e-6 <= abs_val < 1e4:
        return round(value, 6)
    return float(f"{value:.6e}")


def build_controls(
    viewer_id: str,
    scalar_options,
    state,
    slider_disabled,
    slider_max,
    axis_label,
    palette_options,
    time_options=None,
    time_value=None,
    include_range_section: bool = True,
    include_hidden_line_toggle: bool = False,
):
    """Return control panel stacked above the graph."""

    # Row 1: Optional Time Step, Scalar Field
    first_row_children = []

    if time_options:
        first_row_children.extend([
            html.Label([
                html.Span("t", className="label-icon"),
                "Time Step:",
            ], className='field-label grid-label'),
            html.Div([
                dcc.Dropdown(
                    id=component_id(viewer_id, 'time'),
                    options=time_options,
                    value=time_value,
                    clearable=False,
                    searchable=False,
                )
            ], className='dropdown-wrapper'),
        ])

    first_row_children.extend([
        html.Label([
            html.Span("S", className="label-icon"),
            "Field:",
        ], className='field-label grid-label'),
        html.Div([
            dcc.Dropdown(
                id=component_id(viewer_id, 'scalar'),
                options=scalar_options,
                value=state.scalar_key,
                clearable=False,
                searchable=False,
            )
        ], className='dropdown-wrapper'),
    ])

    rows = [
        html.Div(first_row_children, className='controls-grid-row'),
    ]

    if include_range_section:
        rows.extend([
            html.Div([
                html.Label([
                    html.Img(src='/assets/bar-chart.png', className="label-img"),
                    "Range:",
                ], className='field-label grid-label'),
                dcc.Input(
                    id=component_id(viewer_id, 'rangeMin'),
                    type='number',
                    value=format_range_value(state.range_min),
                    step='any',
                    placeholder='Min'
                ),
                dcc.Input(
                    id=component_id(viewer_id, 'rangeMax'),
                    type='number',
                    value=format_range_value(state.range_max),
                    step='any',
                    placeholder='Max'
                ),
                html.Button(
                    html.Img(src='/assets/Reset.png', alt='Reset', className='btn-icon'),
                    id=component_id(viewer_id, 'reset'),
                    className='btn btn-danger reset-btn'
                ),
                html.Div([
                    dmc.Switch(
                        id=component_id(viewer_id, 'clickModeRange'),
                        label="Range Selection on Map",
                        checked=state.click_mode == 'range',
                        labelPosition="right",
                        size="xs",
                        radius="xs",
                        color="#c50623",
                        disabled=False,
                        withThumbIndicator=True,
                    )
                ], className='scan-option scan-option--inline'),
            ], className='controls-grid-row range-row-extended range-row-with-toggle'),

            html.Div([
                # Row 3: Color Map icon + dropdown, Range slider, Full Scale toggle
                html.Label([
                    html.Img(src='/assets/color-scale.png', className="label-img"),
                ], className='field-label grid-label'),
                html.Div([
                    dcc.Dropdown(
                        id=component_id(viewer_id, 'palette'),
                        options=palette_options,
                        value=state.palette,
                        clearable=False,
                        searchable=False,
                    )
                ], className='dropdown-wrapper'),
                html.Div([
                    dcc.RangeSlider(
                        id=component_id(viewer_id, 'rangeSlider'),
                        min=format_range_value(state.range_min),
                        max=format_range_value(state.range_max),
                        value=[format_range_value(state.range_min), format_range_value(state.range_max)],
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className='range-slider-dual',
                        allowCross=False
                    ),
                    html.Div([
                        html.Span(id=component_id(viewer_id, 'rangeMinDisplay'), style={'display': 'none'}),
                        html.Span(id=component_id(viewer_id, 'rangeMaxDisplay'), style={'display': 'none'}),
                    ], style={'display': 'none'})
                ], className='range-slider-track'),
                html.Div([
                    dmc.Switch(
                        id=component_id(viewer_id, 'colorscaleMode'),
                        label="Full Scale",
                        checked=state.colorscale_mode == 'dynamic',
                        labelPosition="right",
                        size="xs",
                        radius="xs",
                        color="#c50623",
                        disabled=False,
                        withThumbIndicator=True,
                    )
                ], className='scan-option scan-option--inline'),
            ], className='range-slider-row range-slider-with-mode')
        ])

    rows.append(html.Div([
        html.Label(axis_label, className='field-label grid-label'),
        dcc.Slider(
            id=component_id(viewer_id, 'slice'),
            min=0,
            max=slider_max,
            value=state.slice_index,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": True},
            disabled=slider_disabled,
            className='slice-slider'
        ),
        dcc.Input(
            id=component_id(viewer_id, 'sliceInput'),
            type='number',
            value=state.slice_index,
            min=0,
            max=slider_max,
            step=1,
            placeholder='Slice',
            disabled=slider_disabled,
            className='slice-input'
        )
    ], className='controls-grid-row slice-row-extended', style={'display': 'none' if slider_disabled else 'grid'}, id=component_id(viewer_id, 'sliceContainer')))

    # Note: Hidden line toggle RadioItems removed - now using DMC Switch components in line scan card

    return html.Div(rows, className='control-panel panel-card')

#  HEAD: --------------------- Heatmap plot section -------------------------------------------------------

def build_graph_section(viewer_id: str):
    """Graph container - main heatmap block."""
    return html.Div([

        # -------------------------
        # Top bar (title + buttons)
        # -------------------------
        html.Div([
            html.Div(id=component_id(viewer_id, 'mapTitle'), className='map-title'),
            html.Div([
                html.Div([
                    dmc.Switch(
                        id=component_id(viewer_id, 'interfacesOverlay'),
                        label="Interfaces Overlay",
                        checked=False,
                        labelPosition="left",
                        size="xs",
                        radius="xs",
                        color="#c50623",
                        disabled=False,
                        withThumbIndicator=True,
                    ),
                ], className='scan-option scan-option--inline interfaces-overlay-toggle'),
                html.Button([
                    html.Img(src='/assets/download.png', alt='Download', className='btn-icon'),
                    html.Span("PNG")
                ],
                    id=component_id(viewer_id, 'downloadHeatmapBtn'),
                    n_clicks=0,
                    className='graph-toolbar-btn graph-toolbar-btn--icon',
                    title='Download heatmap as PNG'
                ),
            ], className="graph-topbar-actions"),
        ], className="graph-topbar"),

        # -------------------------
        # Centered Heatmap Section
        # -------------------------
        html.Div([       # <-- ✔ this must be heatmap-wrapper
            html.Div([   # <-- ✔ this must be heatmap-row (cards with gap)

                # --- Left: Logo card ---
                html.Div(
                    html.Img(
                        src='/assets/OP_Logo.png',
                        className='heatmap-logo',
                        alt='OP logo'
                    ),
                    className='heatmap-logo-card'
                ),

                # --- Middle: Heatmap card ---
                html.Div(
                    dcc.Graph(
                        id=component_id(viewer_id, 'graph'),
                        className='heatmap-main-graph',
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'responsive': False,
                            'toImageButtonOptions': {'scale': 4}
                        }
                    ),
                    id=component_id(viewer_id, 'heatmapCard'),
                    className='heatmap-main-card',
                    style={'width': '600px', 'height': '380px'}
                ),

                # --- Right: Colorbar card ---
                html.Div(
                    dcc.Graph(
                        id=component_id(viewer_id, 'colorbar'),
                        className='heatmap-colorbar-graph',
                        config={
                            'displayModeBar': False,
                            'displaylogo': False,
                            'responsive': False
                        }
                    ),
                    className='heatmap-colorbar-card',
                    style={'width': '90px', 'height': '380px'}
                ),

            ], className='heatmap-row'),   # <-- correct
        ], className='heatmap-wrapper'),   # <-- correct

        html.Div(id=component_id(viewer_id, 'clickInfo'), className='toast-anchor')

    ], className='graph-card')



def build_line_scan_card(viewer_id: str, state):
    """Build combined line scan and histogram analysis card."""
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Line Scan & Histogram Analysis', className='dataset-title')
        ], className='dataset-header'),

        html.Div([
        # Line Scan Section - uniform toolbar
        html.Div([
            html.Div([
                html.Div([
                    dmc.Switch(
                        id=component_id(viewer_id, 'clickModeLine'),
                        label="Line Scan",
                        checked=getattr(state, 'click_mode', 'range') == 'linescan',
                        labelPosition="right",
                        size="xs",
                        radius="xs",
                        color="#c50623",
                        disabled=False,
                        withThumbIndicator=True,
                    )
                ], className='scan-option'),
                html.Div([
                    dmc.Switch(
                        id=component_id(viewer_id, 'lineOverlay'),
                        label="Show Line",
                        checked=True,
                        labelPosition="right",
                        size="xs",
                        radius="xs",
                        color="#c50623",
                        disabled=False,
                        withThumbIndicator=True,
                    )
                ], className='scan-option'),
                html.Div([
                    html.Span("Scan Direction", className='scan-option__label'),
                    dmc.SegmentedControl(
                        id=component_id(viewer_id, 'lineScanDir'),
                        value='horizontal' if getattr(state, 'line_scan_direction', 'horizontal') == 'horizontal' else 'vertical',
                        data=[
                            {'label': '↔', 'value': 'horizontal'},
                            {'label': '↕', 'value': 'vertical'},
                        ],
                        color="#c50623",
                        size="sm",
                    )
                ], className='scan-option scan-option--direction'),
            ], className='scan-toolbar'),
        ], className='modern-toggle-row'),
            dcc.Graph(id=component_id(viewer_id, 'lineScanPlot'), className='textdata-plot')
        ], className='textdata-graphs'),
        html.Div(id=component_id(viewer_id, 'lineScanInfo'), className='toast-anchor', style={'marginTop': '8px', 'marginBottom': '16px', 'fontSize': '12px', 'color': '#666'}),

        # Histogram Section (below line scan)
        html.Div([
            html.Div([
                html.Div([
                    html.Label('Histogram Field', className='textdata-label'),
                    dcc.Dropdown(
                        id=component_id(viewer_id, 'histogramField'),
                        options=[],  # Will be populated dynamically
                        value=None,
                        clearable=False,
                        className='textdata-input'
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Number of Bins', className='textdata-label'),
                    dcc.Slider(
                        id=component_id(viewer_id, 'histogramBins'),
                        min=10,
                        max=100,
                        step=5,
                        value=30,
                        marks={10: '10', 50: '50', 100: '100'},
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], className='textdata-control'),
            ], className='textdata-controls'),
            dcc.Graph(id=component_id(viewer_id, 'histogramPlot'), className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_histogram_card(viewer_id: str):
    """Deprecated - histogram is now combined with line scan card."""
    return None


def build_tab_layout(
    viewer_id: str,
    scalar_options,
    state,
    slider_disabled,
    slider_max,
    axis_label,
    palette_options,
    time_options=None,
    time_value=None,
    include_range_section=True,
    include_hidden_line_toggle=False
):
    """Return the full layout for a viewer tab."""
    return html.Div([
        html.Div([
            build_controls(
                viewer_id,
                scalar_options,
                state,
                slider_disabled,
                slider_max,
                axis_label,
                palette_options,
                time_options=time_options,
                time_value=time_value,
                include_range_section=include_range_section,
                include_hidden_line_toggle=include_hidden_line_toggle
            ),
            build_graph_section(viewer_id)
        ], className='stacked-card'),
        dcc.Store(id=component_id(viewer_id, 'state'), data=state.to_dict()),
    ], className='viewer-tab')


def component_id(viewer_id: str, suffix: str) -> str:
    """Generate component ids scoped to the viewer."""
    return f"{viewer_id}-{suffix}"
