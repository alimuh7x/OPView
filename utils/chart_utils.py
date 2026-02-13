"""
Chart and data visualization utilities for OPView.

Provides helper functions for creating histograms, fitting distributions,
and extracting series values from data.
"""

import warnings
import numpy as np
import plotly.graph_objects as go
from scipy import stats


def compute_average_series(series_dict):
    """Return element-wise average across provided series."""
    arrays = []
    lengths = []
    for values in series_dict.values():
        if values is None:
            continue
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            continue
        arrays.append(arr)
        lengths.append(arr.size)
    if not arrays:
        return None
    min_len = min(lengths)
    stacked = np.vstack([arr[:min_len] for arr in arrays])
    return np.mean(stacked, axis=0)


def fit_best_distribution(data):
    """Fit candidate distributions and select best via BIC."""
    if data is None:
        return None
    arr = np.asarray(data, dtype=float)
    if arr.size < 3 or np.allclose(arr.std(), 0):
        return None
    candidates = {
        "Normal": stats.norm,
        "Lognormal": stats.lognorm,
        "Weibull": stats.weibull_min,
        "Gamma": stats.gamma
    }
    best = None
    n = arr.size
    for name, dist in candidates.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                params = dist.fit(arr)
        except Exception:
            continue
        try:
            loglik = np.sum(dist.logpdf(arr, *params))
        except Exception:
            continue
        k = len(params)
        aic = 2 * k - 2 * loglik
        bic = np.log(n) * k - 2 * loglik
        if not best or bic < best['bic']:
            best = {
                "name": name,
                "dist": dist,
                "params": params,
                "aic": aic,
                "bic": bic
            }
    return best


def format_fit_summary(best_fit):
    """Format distribution fit results as markdown with LaTeX."""
    if not best_fit:
        return "_No valid fit available._"
    label_map = {
        "Normal": ["\\mu", "\\sigma"],
        "Lognormal": ["s", "\\mu", "\\sigma"],
        "Weibull": ["k", "\\lambda", "\\theta"],
        "Gamma": ["k", "\\theta", "\\lambda"]
    }
    labels = label_map.get(best_fit["name"]) or [f"\\theta_{i+1}" for i in range(len(best_fit["params"]))]
    param_lines = []
    for label, value in zip(labels, best_fit["params"]):
        param_lines.append(f"{label} &= {value:.3g}")
    params_block = " \\\\ ".join(param_lines)
    return (
        f"**Best Fit:** $\\text{{{best_fit['name']}}}$\n\n"
        f"$$\\begin{{aligned}}{params_block}\\end{{aligned}}$$\n\n"
        f"$$\\mathrm{{AIC}} = {best_fit['aic']:.2f}\\quad "
        f"\\mathrm{{BIC}} = {best_fit['bic']:.2f}$$"
    )


def build_histogram_figure(values, x_label, bins=None, fit=False):
    """
    Build a Plotly histogram figure with optional best-fit distribution overlay.

    Args:
        values: Data array to histogram
        x_label: Label for x-axis
        bins: Number of bins (auto-computed if None)
        fit: Whether to fit and overlay best distribution

    Returns:
        Tuple of (figure, summary_markdown)
    """
    if values is None:
        return go.Figure(), "No data available"
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return go.Figure(), "No data available"
    if bins is None:
        nbins = max(10, min(60, int(np.sqrt(arr.size) * 3)))
    else:
        nbins = max(5, min(100, int(bins)))
    hist = go.Histogram(
        x=arr,
        nbinsx=nbins,
        marker_color='#183568',
        name='Histogram'
    )

    x_min, x_max = arr.min(), arr.max()
    if np.isclose(x_min, x_max):
        x_min -= 1
        x_max += 1
    x_vals = np.linspace(x_min, x_max, 400)
    summary = "_Enable **Best-fit PDF** to evaluate distributions._"
    traces = [hist]

    if fit:
        best_fit = fit_best_distribution(arr)
        if best_fit:
            pdf_vals = best_fit['dist'].pdf(x_vals, *best_fit['params'])
            counts, edges = np.histogram(arr, bins=nbins)
            bin_width = edges[1] - edges[0]
            pdf_scaled = pdf_vals * arr.size * bin_width
            pdf_line = go.Scatter(
                x=x_vals,
                y=pdf_scaled,
                mode='lines',
                line=dict(color='#0d2244', width=2),
                name=f"{best_fit['name']} PDF"
            )
            traces.append(pdf_line)
            summary = format_fit_summary(best_fit)
        else:
            summary = "_No valid fit available._"

    fig = go.Figure(data=traces)
    fig.update_layout(
        margin=dict(l=50, r=20, t=30, b=50),
        height=320,
        template='plotly_white',
        bargap=0.05
    )
    fig.update_xaxes(
        title=x_label,
        title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
        tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
    )
    fig.update_yaxes(
        title="Frequency",
        title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
        tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
    )
    fig.update_traces(showlegend=False, selector=lambda t: isinstance(t, go.Histogram))
    return fig, summary


def crss_series_values(component, data_accessor):
    """
    Extract CRSS series values for a given component.

    Args:
        component: Component name or 'Average'
        data_accessor: Function to get legacy data (e.g., get_legacy_data)

    Returns:
        Numpy array of values in MPa, or None
    """
    data = data_accessor('crss')
    if not data:
        return None
    if component == 'Average':
        return np.asarray(data['averages']) / 1e6
    values = (data.get('series') or {}).get(component)
    return np.asarray(values) / 1e6 if values is not None else None


def stress_series_values(component, data_accessor):
    """
    Extract stress series values for a given component.

    Args:
        component: Component name or 'Average'
        data_accessor: Function to get legacy data (e.g., get_legacy_data)

    Returns:
        Numpy array of values in MPa, or None
    """
    data = data_accessor('stress_strain')
    if not data:
        return None
    comps = data.get('components') or {}
    if component == 'Average':
        avg = compute_average_series(comps)
        return avg / 1e6 if avg is not None else None
    values = comps.get(component)
    return np.asarray(values) / 1e6 if values is not None else None


def strain_series_values(component, data_accessor):
    """
    Extract strain series values for a given component.

    Args:
        component: Component name or 'Average'
        data_accessor: Function to get legacy data (e.g., get_legacy_data)

    Returns:
        Numpy array of values in percent, or None
    """
    data = data_accessor('stress_strain')
    if not data:
        return None
    comps = data.get('strain_components') or {}
    if component == 'Average':
        avg = compute_average_series(comps)
        return avg * 100.0 if avg is not None else None
    values = comps.get(component)
    return np.asarray(values) * 100.0 if values is not None else None
