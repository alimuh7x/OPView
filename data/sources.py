"""
Concrete data source implementations for different data types.

Provides fully functional data sources that load from TextData files
and support histogram, time-series, and component selection callbacks.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from .base import TensorDataSource, TimeSeriesDataSource, HistogramDataSource


class StressStrainData(TensorDataSource, TimeSeriesDataSource):
    """Manages stress-strain curve data"""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.file_path = data_dir / "StressStrainFile.txt"

    @property
    def file_pattern(self) -> str:
        return "StressStrainFile*.txt"

    @property
    def display_name(self) -> str:
        return "Stress–Strain Curves"

    @property
    def component_symbol(self) -> str:
        return "σ"

    @property
    def component_prefix(self) -> str:
        return "Sigma"

    def load(self) -> bool:
        """Load stress-strain data from text file"""
        if not self.file_path.exists():
            self._loaded = True
            return False

        try:
            with self.file_path.open() as fh:
                lines = [line.strip() for line in fh if line.strip()]
        except OSError:
            self._loaded = True
            return False

        if not lines:
            self._loaded = True
            return False

        header = [token.strip() for token in lines[0].replace(',', ' ').split()]
        rows = []
        for line in lines[1:]:
            parts = [token.strip() for token in line.replace(',', ' ').split()]
            if len(parts) != len(header):
                continue
            try:
                rows.append([float(p) for p in parts])
            except ValueError:
                continue

        if not rows:
            self._loaded = True
            return False

        columns = {name: [row[idx] for row in rows] for idx, name in enumerate(header)}
        columns_ci = {name.lower(): name for name in columns}

        def find_column_name(*names):
            for name in names:
                if name in columns:
                    return name
                resolved = columns_ci.get(name.lower())
                if resolved is not None:
                    return resolved
            return None

        def col(*names):
            name = find_column_name(*names)
            return columns.get(name) if name is not None else None

        x_col = find_column_name('E_xx', 'Epsilon_xx', 'Strain', 'strain', 'epsilon_xx')

        # Build data structure
        self._data = {
            'columns': columns,
            'x_column': x_col,
            # Support both legacy headers (E_xx) and common OP headers (Epsilon_xx).
            'strain': col('E_xx', 'Epsilon_xx', 'Strain', 'strain', 'epsilon_xx') or [],
            'components': {
                'Sigma_xx': col('S_xx', 'Sigma_xx', 'sigma_xx'),
                'Sigma_yy': col('S_yy', 'Sigma_yy', 'sigma_yy'),
                'Sigma_zz': col('S_zz', 'Sigma_zz', 'sigma_zz'),
                'Sigma_xy': col('S_xy', 'Sigma_xy', 'sigma_xy'),
                'Sigma_yz': col('S_yz', 'Sigma_yz', 'sigma_yz'),
                'Sigma_zx': col('S_zx', 'Sigma_zx', 'sigma_zx'),
                'Mises': col('Mises', 'vonMises', 'von_mises'),
            },
            'strain_components': {
                'Epsilon_xx': col('E_xx', 'Epsilon_xx', 'Strain', 'strain', 'epsilon_xx'),
                'Epsilon_yy': col('E_yy', 'Epsilon_yy', 'epsilon_yy'),
                'Epsilon_zz': col('E_zz', 'Epsilon_zz', 'epsilon_zz'),
            }
        }

        # Remove None values
        self._data['components'] = {k: v for k, v in self._data['components'].items() if v is not None}
        self._data['strain_components'] = {k: v for k, v in self._data['strain_components'].items() if v is not None}

        self._loaded = True
        # Consider this data available if we have an x-axis and at least one other column.
        has_x = bool(self._data.get('strain'))
        has_y = len(columns.keys()) > (1 if x_col in columns else 0)
        return has_x and has_y

    def get_component_options(self) -> List[Dict[str, str]]:
        """Expose all file columns as selectable series (except the x-axis)."""
        if not self.is_available:
            return []

        columns: Dict[str, Any] = self._data.get('columns', {}) or {}
        x_col = self._data.get('x_column')

        options = []
        for name in columns.keys():
            if name == x_col:
                continue
            options.append({'label': name, 'value': name})
        return options

    def get_default_components(self) -> List[str]:
        """Default to showing σ_xx and von Mises"""
        if not self.is_available:
            return ['Sigma_xx', 'Mises']

        columns = list((self._data.get('columns', {}) or {}).keys())
        x_col = self._data.get('x_column')
        candidates = [c for c in columns if c != x_col]

        preferred = [c for c in ('Sigma_xx', 'Mises') if c in candidates]
        if preferred:
            return preferred
        return candidates[:2]

    def _get_component_values(self, component: str) -> Optional[np.ndarray]:
        """Get strain or stress values for a component"""
        if not self.is_available:
            return None
        columns = self._data.get('columns', {}) or {}
        if component in columns:
            return np.array(columns[component])

        # Backward compatibility for callers that use canonical tensor component keys.
        comps = self._data.get('components', {}) or {}
        if component in comps and comps[component] is not None:
            return np.array(comps[component])

        return None

    def _scale_series(self, name: str, values: np.ndarray) -> Tuple[np.ndarray, str]:
        lname = (name or "").lower()
        if any(token in lname for token in ("sigma", "mises", "pressure")):
            return values / 1e6, "Stress (MPa)"
        if any(token in lname for token in ("epsilon", "strain")) or lname.startswith("e_"):
            return values * 100.0, "Strain (%)"
        return values, "Value"

    def build_figure(self, components: List[str]) -> go.Figure:
        """Build stress-strain figure for selected components"""
        if not self.is_available:
            return go.Figure()

        x_col = self._data.get('x_column') or "Strain"
        strain = np.array(self._data['strain']) * 100.0  # Convert to percent
        labels = {
            "Sigma_xx": "σ_xx",
            "Sigma_yy": "σ_yy",
            "Sigma_zz": "σ_zz",
            "Mises": "von Mises",
        }

        selected = components or self.get_default_components()
        traces = []
        y_axis_titles = set()
        for comp in selected:
            values = self._get_component_values(comp)
            if values is None or len(values) == 0:
                continue
            y_scaled, y_title = self._scale_series(comp, np.asarray(values, dtype=float))
            y_axis_titles.add(y_title)
            traces.append(go.Scatter(
                x=strain,
                y=y_scaled,
                mode='lines+markers',
                line=dict(width=1.5),
                marker=dict(size=6, line=dict(width=0)),
                name=labels.get(comp, comp)
            ))

        fig = go.Figure(data=traces)
        fig.update_layout(
            margin=dict(l=50, r=30, t=90, b=60),
            height=320,
            template='plotly_white',
            legend=dict(
                orientation='h',
                x=0,
                xanchor='left',
                y=1.18,
                yanchor='bottom',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(24,53,104,0.15)',
                borderwidth=1
            )
        )
        fig.update_xaxes(
            title="ε_xx (%)",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title="Stress (MPa)",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        return fig


class StressData(TensorDataSource, HistogramDataSource):
    """Manages stress histogram data"""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self._parent_data = None  # Reference to StressStrainData

    @property
    def file_pattern(self) -> str:
        return "StressStrainFile*.txt"

    @property
    def display_name(self) -> str:
        return "Stress Distribution"

    @property
    def component_symbol(self) -> str:
        return "σ"

    @property
    def component_prefix(self) -> str:
        return "Sigma"

    def load(self) -> bool:
        """Load stress data from parent StressStrainData"""
        # StressData shares the same file as StressStrainData
        stress_strain = StressStrainData(self.data_dir)
        if stress_strain.load():
            self._data = stress_strain._data
            self._parent_data = stress_strain
            self._loaded = True
            return True
        self._loaded = True
        return False

    def get_default_components(self) -> List[str]:
        return ['Sigma_xx']

    def _get_component_values(self, component: str) -> Optional[np.ndarray]:
        if not self.is_available:
            return None

        comps = self._data.get('components', {})

        # Handle Average component
        if component == 'Average':
            all_values = []
            for values in comps.values():
                if values:
                    all_values.append(np.array(values))
            if all_values:
                return np.mean(all_values, axis=0) / 1e6  # Convert to MPa
            return None

        values = comps.get(component)
        return np.array(values) / 1e6 if values is not None else None  # Convert to MPa

    def get_histogram_data(self, component: str, bins: int = None,
                          fit: bool = False) -> Tuple[go.Figure, str]:
        """Get histogram figure and summary for stress distribution"""
        values = self._get_component_values(component)
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

        fig = go.Figure(data=[hist])

        # Add fitted distribution if requested
        if fit and arr.size > 10:
            mu, sigma = arr.mean(), arr.std()
            x_fit = np.linspace(arr.min(), arr.max(), 100)
            y_fit = stats.norm.pdf(x_fit, mu, sigma)
            # Scale to match histogram
            y_fit = y_fit * (arr.size * (arr.max() - arr.min()) / nbins)

            fig.add_trace(go.Scatter(
                x=x_fit,
                y=y_fit,
                mode='lines',
                name='Normal Fit',
                line=dict(color='#c50623', width=2)
            ))

        fig.update_layout(
            xaxis_title="Stress (MPa)",
            yaxis_title="Frequency",
            template='plotly_white',
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
        )

        # Generate summary statistics
        summary = f"**Mean:** {arr.mean():.2f} MPa  \n"
        summary += f"**Std Dev:** {arr.std():.2f} MPa  \n"
        summary += f"**Min:** {arr.min():.2f} MPa  \n"
        summary += f"**Max:** {arr.max():.2f} MPa"

        return fig, summary


class StrainData(TensorDataSource, HistogramDataSource):
    """Manages strain histogram data"""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self._parent_data = None

    @property
    def file_pattern(self) -> str:
        return "StressStrainFile*.txt"

    @property
    def display_name(self) -> str:
        return "Strain Distribution"

    @property
    def component_symbol(self) -> str:
        return "ε"

    @property
    def component_prefix(self) -> str:
        return "Epsilon"

    def load(self) -> bool:
        """Load strain data from parent StressStrainData"""
        stress_strain = StressStrainData(self.data_dir)
        if stress_strain.load():
            self._data = stress_strain._data
            self._parent_data = stress_strain
            self._loaded = True
            return True
        self._loaded = True
        return False

    def get_default_components(self) -> List[str]:
        return ['Epsilon_xx']

    def _get_component_values(self, component: str) -> Optional[np.ndarray]:
        if not self.is_available:
            return None

        comps = self._data.get('strain_components', {})

        # Handle Average component
        if component == 'Average':
            all_values = []
            for values in comps.values():
                if values:
                    all_values.append(np.array(values))
            if all_values:
                return np.mean(all_values, axis=0) * 100.0  # Convert to percent
            return None

        values = comps.get(component)
        return np.array(values) * 100.0 if values is not None else None  # Convert to percent

    def get_histogram_data(self, component: str, bins: int = None,
                          fit: bool = False) -> Tuple[go.Figure, str]:
        """Get histogram figure and summary for strain distribution"""
        values = self._get_component_values(component)
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

        fig = go.Figure(data=[hist])

        # Add fitted distribution if requested
        if fit and arr.size > 10:
            mu, sigma = arr.mean(), arr.std()
            x_fit = np.linspace(arr.min(), arr.max(), 100)
            y_fit = stats.norm.pdf(x_fit, mu, sigma)
            y_fit = y_fit * (arr.size * (arr.max() - arr.min()) / nbins)

            fig.add_trace(go.Scatter(
                x=x_fit,
                y=y_fit,
                mode='lines',
                name='Normal Fit',
                line=dict(color='#c50623', width=2)
            ))

        fig.update_layout(
            xaxis_title="Strain (%)",
            yaxis_title="Frequency",
            template='plotly_white',
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
        )

        summary = f"**Mean:** {arr.mean():.2f} %  \n"
        summary += f"**Std Dev:** {arr.std():.2f} %  \n"
        summary += f"**Min:** {arr.min():.2f} %  \n"
        summary += f"**Max:** {arr.max():.2f} %"

        return fig, summary


class CRSSData(TimeSeriesDataSource):
    """Manages CRSS (Critical Resolved Shear Stress) evolution data"""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.file_path = data_dir / "CRSSFile.txt"

    @property
    def file_pattern(self) -> str:
        return "CRSS*.txt"

    @property
    def display_name(self) -> str:
        return "CRSS Evolution"

    def load(self) -> bool:
        """Load CRSS data"""
        if not self.file_path.exists():
            self._loaded = True
            return False

        try:
            with self.file_path.open() as fh:
                lines = [line.strip() for line in fh if line.strip()]
        except OSError:
            self._loaded = True
            return False

        if not lines:
            self._loaded = True
            return False

        header = [h.strip() for h in lines[0].split(',')]
        if 'Time' not in header:
            self._loaded = True
            return False

        times = []
        time_idx = header.index('Time')
        slip_columns = [
            (idx, name)
            for idx, name in enumerate(header)
            if name.lower().startswith('ss_')
        ]
        series = {name: [] for _, name in slip_columns}

        for line in lines[1:]:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) <= time_idx:
                continue
            try:
                time_val = float(parts[time_idx])
            except ValueError:
                continue

            times.append(time_val)
            for idx, name in slip_columns:
                if idx < len(parts):
                    try:
                        series[name].append(float(parts[idx]))
                    except ValueError:
                        series[name].append(0.0)

        self._data = {
            'times': times,
            'series': series
        }

        self._loaded = True
        return bool(times) and bool(series)

    def get_component_options(self) -> List[Dict[str, str]]:
        """Get CRSS component options (slip systems)"""
        if not self.is_available:
            return []

        series = self._data.get('series', {})

        def sort_key(name):
            digits = ''.join(ch for ch in name if ch.isdigit())
            return int(digits) if digits else name

        options = [{'label': 'Average', 'value': 'Average'}]
        for name in sorted(series.keys(), key=sort_key):
            label = name.replace('ss_', 'SS ').upper()
            options.append({'label': label, 'value': name})

        return options

    def get_default_components(self) -> List[str]:
        """Default to showing average"""
        return ['Average']

    def _get_component_values(self, component: str) -> Optional[np.ndarray]:
        """Get CRSS values for a component"""
        if not self.is_available:
            return None

        if component == 'Average':
            series = self._data.get('series', {})
            if not series:
                return None
            all_values = [np.array(values) for values in series.values()]
            return np.mean(all_values, axis=0) if all_values else None

        series = self._data.get('series', {})
        return np.array(series.get(component, [])) if component in series else None

    def build_figure(self, components: List[str]) -> go.Figure:
        """Build CRSS evolution figure"""
        if not self.is_available:
            return go.Figure()

        times = self._data['times']
        selected = components or self.get_default_components()

        traces = []
        for comp in selected:
            values = self._get_component_values(comp)
            if values is not None and len(values) > 0:
                label = comp.replace('ss_', 'SS ').upper() if comp != 'Average' else 'Average'
                traces.append(go.Scatter(
                    x=times,
                    y=values,
                    mode='lines+markers',
                    name=label
                ))

        fig = go.Figure(data=traces)
        fig.update_layout(
            xaxis_title="Time Step",
            yaxis_title="CRSS",
            template='plotly_white',
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
        )
        return fig


class GrainSizeData(TimeSeriesDataSource, HistogramDataSource):
    """Manages grain size details and distribution data"""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.file_path = data_dir / "SizeDetails.dat"
        self.average_file = data_dir / "SizeAveInfo.dat"

    @property
    def file_pattern(self) -> str:
        return "SizeDetailsFile*.txt"

    @property
    def display_name(self) -> str:
        return "Grain Size"

    def load(self) -> bool:
        """Load grain size data"""
        if not self.file_path.exists():
            self._loaded = True
            return False

        rows = []
        try:
            with self.file_path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    try:
                        rows.append([float(p) for p in parts])
                    except ValueError:
                        continue
        except OSError:
            self._loaded = True
            return False

        if not rows:
            self._loaded = True
            return False

        # Determine columns: first is time, second often count, rest are values
        has_count = len(rows[0]) > 2
        values_offset = 2 if has_count else 1
        labels = [str(idx + 1) for idx in range(len(rows[0]) - values_offset)]
        data_matrix = [row[values_offset:] for row in rows]
        times = [row[0] for row in rows]
        counts = [row[1] for row in rows] if has_count else None

        self._data = {
            "times": times,
            "counts": counts,
            "labels": labels,
            "values": data_matrix,
        }

        # Try to load average data
        if self.average_file.exists():
            try:
                with self.average_file.open() as fh:
                    avg_lines = [line.strip() for line in fh if line.strip()]
                avg_rows = []
                for line in avg_lines:
                    parts = line.split()
                    try:
                        avg_rows.append([float(p) for p in parts])
                    except ValueError:
                        continue
                if avg_rows:
                    self._data['avg_times'] = [row[0] for row in avg_rows]
                    self._data['averages'] = [row[1] for row in avg_rows]
            except OSError:
                pass

        self._loaded = True
        return True

    def get_component_options(self) -> List[Dict[str, str]]:
        """Get grain size metric options"""
        if not self.is_available:
            return []
        labels = self._data.get('labels', [])
        return [{'label': f"Grain {label}", 'value': label} for label in labels]

    def get_default_components(self) -> List[str]:
        """Default to first available metric"""
        options = self.get_component_options()
        return [options[0]['value']] if options else []

    def _get_component_values(self, component: str) -> Optional[np.ndarray]:
        """Get grain size values for a metric"""
        if not self.is_available:
            return None
        # For grain size, component would be grain number
        # This is time-series data per grain
        return None

    def get_histogram_data(self, time_value: float = None, bins: int = None,
                          fit: bool = False) -> Tuple[go.Figure, str]:
        """Get grain size distribution histogram at a specific time"""
        if not self.is_available:
            return go.Figure(), "_No data available._"

        times = self._data['times']
        values = self._data['values']

        if not times or not values:
            return go.Figure(), "_No data available._"

        try:
            time_value = float(time_value)
        except (TypeError, ValueError):
            time_value = times[0]

        # Find closest time index
        row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
        row_values = values[row_index]

        if not row_values:
            return go.Figure(), "_No data available._"

        arr = np.array(row_values)
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

        fig = go.Figure(data=[hist])

        if fit and arr.size > 10:
            mu, sigma = arr.mean(), arr.std()
            x_fit = np.linspace(arr.min(), arr.max(), 100)
            y_fit = stats.norm.pdf(x_fit, mu, sigma)
            y_fit = y_fit * (arr.size * (arr.max() - arr.min()) / nbins)

            fig.add_trace(go.Scatter(
                x=x_fit,
                y=y_fit,
                mode='lines',
                name='Normal Fit',
                line=dict(color='#c50623', width=2)
            ))

        fig.update_layout(
            xaxis_title="Grain Size",
            yaxis_title="Frequency",
            template='plotly_white',
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
        )

        summary = f"**Time:** {times[row_index]:.2f}  \n"
        summary += f"**Mean:** {arr.mean():.2f}  \n"
        summary += f"**Std Dev:** {arr.std():.2f}  \n"
        summary += f"**Count:** {len(arr)}"

        return fig, summary


class PlasticStrainData(TimeSeriesDataSource):
    """Manages plastic strain evolution data"""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.file_path = data_dir / "PlasticStrain.txt"

    @property
    def file_pattern(self) -> str:
        return "PlasticStrain*.txt"

    @property
    def display_name(self) -> str:
        return "Plastic Strain"

    def load(self) -> bool:
        """Load plastic strain data"""
        if not self.file_path.exists():
            self._loaded = True
            return False

        # TODO: Implement actual loading based on file format
        self._data = None
        self._loaded = True
        return self._data is not None

    def get_component_options(self) -> List[Dict[str, str]]:
        """Get plastic strain component options"""
        if not self.is_available:
            return []
        components = self._data.get('components', [])
        return [{'label': comp, 'value': comp} for comp in components]

    def get_default_components(self) -> List[str]:
        """Default components"""
        options = self.get_component_options()
        return [opt['value'] for opt in options[:2]] if len(options) >= 2 else []

    def _get_component_values(self, component: str) -> Optional[np.ndarray]:
        """Get plastic strain values"""
        if not self.is_available:
            return None
        data = self._data.get('data', {})
        return np.array(data.get(component, [])) if component in data else None


class GenericTextDataSource:
    """Generic data source for any CSV/space-delimited text file.

    Auto-detects file format and provides dynamic column selection for plotting.
    Supports both comma-delimited and space-delimited formats with automatic
    time column detection.

    This is a standalone class that does not inherit from the abstract DataSource
    base classes, as it's designed to work with arbitrary text files with
    unknown structure.
    """

    def __init__(self, file_path: Path, file_name: str = None):
        """
        Initialize generic text data source.

        Args:
            file_path: Path to text file
            file_name: Display name (optional, uses filename if not provided)
        """
        self.file_path = file_path
        self.file_name = file_name or file_path.name
        self._columns = []
        self._data = None
        self._loaded = False

    def load(self) -> bool:
        """Load CSV/space-delimited file and auto-detect format.

        Tries comma separator first. If no commas found in header,
        falls back to whitespace separator (for files like StressStrainFile.txt).

        Returns:
            True if data loaded successfully, False otherwise
        """
        if not self.file_path.exists():
            self._loaded = True
            return False

        try:
            # Read first line to check format
            with open(self.file_path, 'r') as f:
                first_line = f.readline().strip()

            # If comma found in header, use comma separator
            if ',' in first_line:
                self._data = pd.read_csv(self.file_path, sep=',')
            else:
                # No commas - use whitespace separator (for stress-strain files, etc.)
                self._data = pd.read_csv(self.file_path, sep=r'\s+')

        except Exception as e:
            print(f"[GenericTextDataSource] Failed to load {self.file_path}: {e}")
            self._loaded = True
            return False

        # Clean column names (strip whitespace)
        self._data.columns = self._data.columns.str.strip()

        # Store available columns (excluding time column)
        time_cols = ['Time', 'TimeStep', 'time', 'timestep']
        self._columns = [col for col in self._data.columns if col not in time_cols]

        self._loaded = True
        return True

    @property
    def is_available(self) -> bool:
        """Check if data is available."""
        return self.file_path.exists() and self._data is not None

    def get_available_columns(self) -> List[str]:
        """Get list of plottable columns.

        Returns:
            List of column names (excluding time column)
        """
        return self._columns

    def get_time_column(self) -> str:
        """Detect and return time column name.

        Returns:
            Name of time column, or first column if no time column found
        """
        time_cols = ['Time', 'TimeStep', 'time', 'timestep']
        for col in time_cols:
            if col in self._data.columns:
                return col
        # Default to first column if no time column found
        return self._data.columns[0]

    def build_figure(self, selected_columns: List[str], **kwargs):
        """Build time-series plot for selected columns.

        Args:
            selected_columns: List of column names to plot
            **kwargs: Additional keyword arguments (unused, for interface compatibility)

        Returns:
            Plotly figure object
        """
        if not self.is_available or not selected_columns:
            return go.Figure()

        time_col = self.get_time_column()
        time_data = self._data[time_col]

        fig = go.Figure()

        # Color palette for multiple series
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

        for idx, col in enumerate(selected_columns):
            if col in self._data.columns:
                color = colors[idx % len(colors)]
                fig.add_trace(go.Scatter(
                    x=time_data,
                    y=self._data[col],
                    mode='lines+markers',
                    name=col,
                    line=dict(width=2, color=color),
                    marker=dict(size=4, color=color)
                ))

        fig.update_layout(
            title=f"{self.file_name} - Time Series",
            xaxis_title=time_col,
            yaxis_title="Value",
            hovermode='x unified',
            template='plotly_white',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)'
            ),
            margin=dict(l=60, r=30, t=50, b=50)
        )

        return fig
