# Callbacks Guide - OPView

## Overview

Dash callbacks connect UI components to data processing logic. This guide shows:
- ✅ **Current callback patterns** in the codebase
- ✅ **Using OOP data sources** with callbacks
- ✅ **Reusable callback helpers** to reduce duplication
- ✅ **Best practices** for callback organization

---

## Current Callback Patterns

### Pattern Analysis (17 callbacks total)

```
📊 Main Tab Callbacks (6):
   - size-card-main/line: Time + Chart Mode → 2 Figures
   - grain-dist-fig: Time + Bins + Fit → Figure + Summary
   - stress-strain-fig: Components → Figure
   - stress-hist: Component + Bins + Fit → Figure + Summary
   - strain-hist: Component + Bins + Fit → Figure + Summary
   - crss-avg-fig: Components → Figure

🔄 Comparison Tab Callbacks (7):
   - File picker and management
   - Heatmap field/range/palette controls
   - Dynamic heatmap rows generation
   - Controls state synchronization

🗂️ Tab Management (4):
   - Tab switching logic
   - Content visibility toggling
   - Folder/project selection
```

---

## Callback Patterns

### Pattern 1: Histogram Callbacks

**Current Implementation (Repetitive):**
```python
@app.callback(
    Output('stress-hist-fig', 'figure'),
    Output('stress-hist-summary', 'children'),
    Input('stress-hist-component', 'value'),
    Input('stress-hist-bins', 'value'),
    Input('stress-hist-fit', 'value')
)
def update_stress_hist(selected_component, bins, fit_value):
    values = stress_series_values(selected_component)
    fit_enabled = bool(fit_value and 'fit' in fit_value)
    fig, summary = build_histogram_figure(values, "Stress (MPa)", bins, fit=fit_enabled)
    return fig, summary

@app.callback(
    Output('strain-hist-fig', 'figure'),
    Output('strain-hist-summary', 'children'),
    Input('strain-hist-component', 'value'),
    Input('strain-hist-bins', 'value'),
    Input('strain-hist-fit', 'value')
)
def update_strain_hist(selected_component, bins, fit_value):
    values = strain_series_values(selected_component)
    fit_enabled = bool(fit_value and 'fit' in fit_value)
    fig, summary = build_histogram_figure(values, "Strain (%)", bins, fit=fit_enabled)
    return fig, summary
```

**With OOP Data Sources (Clean):**
```python
from data import StressData, StrainData

stress_data = StressData(data_dir)
strain_data = StrainData(data_dir)

@app.callback(
    Output('stress-hist-fig', 'figure'),
    Output('stress-hist-summary', 'children'),
    Input('stress-hist-component', 'value'),
    Input('stress-hist-bins', 'value'),
    Input('stress-hist-fit', 'value')
)
def update_stress_hist(component, bins, fit_value):
    fit_enabled = bool(fit_value and 'fit' in fit_value)
    # Data source knows how to get its own histogram!
    return stress_data.get_histogram_data(component, bins, fit=fit_enabled)

@app.callback(
    Output('strain-hist-fig', 'figure'),
    Output('strain-hist-summary', 'children'),
    Input('strain-hist-component', 'value'),
    Input('strain-hist-bins', 'value'),
    Input('strain-hist-fit', 'value')
)
def update_strain_hist(component, bins, fit_value):
    fit_enabled = bool(fit_value and 'fit' in fit_value)
    return strain_data.get_histogram_data(component, bins, fit=fit_enabled)
```

**Benefits:**
- No manual value extraction
- Data source handles histogram computation
- Consistent behavior across all histograms

---

### Pattern 2: Time-Series Callbacks

**Current Implementation:**
```python
@app.callback(
    Output('grain-dist-fig', 'figure'),
    Output('grain-dist-summary', 'children'),
    Input('grain-dist-time', 'value'),
    Input('grain-dist-bins', 'value'),
    Input('grain-dist-fit', 'value')
)
def update_grain_distribution(selected_time, bins, fit_value):
    fit_enabled = bool(fit_value and 'fit' in fit_value)
    # Manually parse time, find index, get values...
    fig, summary = build_grain_histogram(selected_time, bins, fit=fit_enabled)
    return fig, summary
```

**With OOP Data Sources:**
```python
from data import GrainSizeData

grain_data = GrainSizeData(data_dir)

@app.callback(
    Output('grain-dist-fig', 'figure'),
    Output('grain-dist-summary', 'children'),
    Input('grain-dist-time', 'value'),
    Input('grain-dist-bins', 'value'),
    Input('grain-dist-fit', 'value')
)
def update_grain_distribution(time_value, bins, fit_value):
    fit_enabled = bool(fit_value and 'fit' in fit_value)
    # Data source handles time parsing and indexing
    return grain_data.get_histogram_data(time_value, bins, fit=fit_enabled)
```

---

### Pattern 3: Component Selection Callbacks

**Current Implementation:**
```python
@app.callback(
    Output('stress-strain-fig', 'figure'),
    Input('stress-components', 'value')
)
def update_stress_strain(components):
    data = STRESS_STRAIN_DATA
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
    # ... layout configuration ...
    return fig
```

**With OOP Data Sources:**
```python
from data import StressStrainData

stress_strain_data = StressStrainData(data_dir)

@app.callback(
    Output('stress-strain-fig', 'figure'),
    Input('stress-components', 'value')
)
def update_stress_strain(components):
    # Data source knows its default components and labels
    selected = components or stress_strain_data.get_default_components()
    return stress_strain_data.build_figure(selected)
```

---

## Reusable Callback Helpers

### Helper 1: Generic Histogram Callback Factory

Create histogram callbacks automatically:

```python
# In ui/callbacks.py
def create_histogram_callback(app, data_source, id_prefix):
    """
    Factory function to create histogram callbacks.

    Args:
        app: Dash app instance
        data_source: HistogramDataSource instance
        id_prefix: ID prefix for components (e.g., 'stress-hist')

    Returns:
        The created callback function
    """
    @app.callback(
        Output(f'{id_prefix}-fig', 'figure'),
        Output(f'{id_prefix}-summary', 'children'),
        Input(f'{id_prefix}-component', 'value'),
        Input(f'{id_prefix}-bins', 'value'),
        Input(f'{id_prefix}-fit', 'value')
    )
    def update_histogram(component, bins, fit_value):
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        return data_source.get_histogram_data(component, bins, fit=fit_enabled)

    return update_histogram


# Usage
from data import StressData, StrainData
from ui.callbacks import create_histogram_callback

stress_data = StressData(data_dir)
strain_data = StrainData(data_dir)

# Create callbacks in 1 line each!
create_histogram_callback(app, stress_data, 'stress-hist')
create_histogram_callback(app, strain_data, 'strain-hist')
```

### Helper 2: Time-Series Callback Factory

```python
# In ui/callbacks.py
def create_time_series_callback(app, data_source, graph_id, time_id, component_id=None):
    """
    Factory for time-series visualization callbacks.

    Args:
        app: Dash app instance
        data_source: TimeSeriesDataSource instance
        graph_id: ID of the graph component
        time_id: ID of the time dropdown
        component_id: Optional ID of component selector
    """
    inputs = [Input(time_id, 'value')]
    if component_id:
        inputs.append(Input(component_id, 'value'))

    @app.callback(
        Output(graph_id, 'figure'),
        inputs
    )
    def update_time_series(*args):
        time_value = args[0]
        components = args[1] if len(args) > 1 else None

        if components:
            return data_source.build_time_series_figure(time_value, components)
        else:
            return data_source.build_time_series_figure(time_value)

    return update_time_series


# Usage
from data import CRSSData
from ui.callbacks import create_time_series_callback

crss_data = CRSSData(data_dir)

create_time_series_callback(
    app,
    crss_data,
    graph_id='crss-avg-fig',
    time_id='crss-time',
    component_id='crss-component-select'
)
```

### Helper 3: Component Selection Callback Factory

```python
# In ui/callbacks.py
def create_component_selection_callback(app, data_source, graph_id, component_id):
    """
    Factory for component selection callbacks.

    Args:
        app: Dash app instance
        data_source: DataSource instance
        graph_id: ID of the graph
        component_id: ID of the component checklist
    """
    @app.callback(
        Output(graph_id, 'figure'),
        Input(component_id, 'value')
    )
    def update_components(selected_components):
        components = selected_components or data_source.get_default_components()
        return data_source.build_figure(components)

    return update_components


# Usage
from data import StressStrainData

stress_strain_data = StressStrainData(data_dir)

create_component_selection_callback(
    app,
    stress_strain_data,
    graph_id='stress-strain-fig',
    component_id='stress-components'
)
```

---

## Complete Example: Automatic Callback Registration

### Before (17+ lines per callback)

```python
# Manually write each callback
@app.callback(...)
def update_stress_hist(...):
    # 15 lines of logic
    pass

@app.callback(...)
def update_strain_hist(...):
    # 15 lines of logic (duplicate!)
    pass

@app.callback(...)
def update_crss(...):
    # 15 lines of logic
    pass
```

### After (1-2 lines per callback)

```python
# In OPView.py
from data import StressData, StrainData, CRSSData, GrainSizeData
from ui.callbacks import (
    create_histogram_callback,
    create_time_series_callback,
    create_component_selection_callback
)

# Initialize data sources
data_dir = Path('TextData')
stress_data = StressData(data_dir)
strain_data = StrainData(data_dir)
crss_data = CRSSData(data_dir)
grain_data = GrainSizeData(data_dir)

# Register all callbacks
if stress_data.is_available:
    create_histogram_callback(app, stress_data, 'stress-hist')

if strain_data.is_available:
    create_histogram_callback(app, strain_data, 'strain-hist')

if crss_data.is_available:
    create_component_selection_callback(
        app, crss_data, 'crss-avg-fig', 'crss-component-select'
    )

if grain_data.is_available:
    create_histogram_callback(app, grain_data, 'grain-dist')
```

---

## Advanced Pattern: Callback Registry

For even more automation:

```python
# In ui/callbacks.py
class CallbackRegistry:
    """Central registry for automatic callback registration"""

    def __init__(self, app):
        self.app = app
        self.callbacks = []

    def register_histogram(self, data_source, id_prefix):
        """Register a histogram callback"""
        if data_source.is_available:
            cb = create_histogram_callback(self.app, data_source, id_prefix)
            self.callbacks.append(cb)
            return cb
        return None

    def register_time_series(self, data_source, graph_id, time_id, component_id=None):
        """Register a time-series callback"""
        if data_source.is_available:
            cb = create_time_series_callback(
                self.app, data_source, graph_id, time_id, component_id
            )
            self.callbacks.append(cb)
            return cb
        return None

    def register_component_selection(self, data_source, graph_id, component_id):
        """Register a component selection callback"""
        if data_source.is_available:
            cb = create_component_selection_callback(
                self.app, data_source, graph_id, component_id
            )
            self.callbacks.append(cb)
            return cb
        return None


# Usage in OPView.py
from ui.callbacks import CallbackRegistry

registry = CallbackRegistry(app)

# Register all callbacks in a structured way
registry.register_histogram(stress_data, 'stress-hist')
registry.register_histogram(strain_data, 'strain-hist')
registry.register_histogram(grain_data, 'grain-dist')
registry.register_component_selection(stress_strain_data, 'stress-strain-fig', 'stress-components')
registry.register_time_series(crss_data, 'crss-avg-fig', 'crss-time', 'crss-component-select')
```

---

## Callback Organization Best Practices

### 1. Group by Feature

```python
# Main tab callbacks
if stress_data.is_available:
    registry.register_histogram(stress_data, 'stress-hist')
    registry.register_component_selection(stress_strain_data, 'stress-strain-fig', 'stress-components')

if strain_data.is_available:
    registry.register_histogram(strain_data, 'strain-hist')

# Comparison tab callbacks
registry.register_comparison_callbacks(comparison_data)

# Tab management callbacks
registry.register_tab_callbacks()
```

### 2. Conditional Registration

```python
# Only register if data is available
for data_source, config in data_configs:
    if data_source.is_available:
        registry.register_histogram(data_source, config['id_prefix'])
```

### 3. Separate Callback Files

```
callbacks/
├── __init__.py
├── factories.py      # Callback factory functions
├── main_tab.py       # Main tab specific callbacks
├── comparison.py     # Comparison tab callbacks
└── utils.py          # Shared callback utilities
```

---

## Integration with Data Sources

### Data Source Methods for Callbacks

Data sources can provide callback-friendly methods:

```python
# In data/base.py
class HistogramDataSource(DataSource):
    """Base class with histogram callback support"""

    def get_histogram_data(self, component: str, bins: int = None,
                          fit: bool = False) -> Tuple[go.Figure, str]:
        """
        Get histogram figure and summary for callback.

        Args:
            component: Component name
            bins: Number of bins
            fit: Whether to fit distribution

        Returns:
            Tuple of (figure, summary_text)
        """
        values = self._get_component_values(component)
        if values is None:
            return go.Figure(), "No data available"

        fig = self._build_histogram_figure(values, bins, fit)
        summary = self._compute_summary_stats(values)
        return fig, summary


class TimeSeriesDataSource(DataSource):
    """Base class with time-series callback support"""

    def build_time_series_figure(self, time_value: float,
                                 components: List[str] = None) -> go.Figure:
        """
        Build time-series figure for callback.

        Args:
            time_value: Selected time step
            components: Selected components (uses defaults if None)

        Returns:
            Plotly figure
        """
        components = components or self.get_default_components()

        # Find time index
        times = self.get_time_steps()
        time_idx = self._find_nearest_time_index(time_value, times)

        # Build traces
        traces = []
        for comp in components:
            values = self._get_component_values(comp)
            if values is not None:
                traces.append(self._create_trace(comp, values[time_idx]))

        return go.Figure(data=traces, layout=self._get_default_layout())
```

---

## Summary

### Callback Patterns in OPView

| Pattern | Count | Factory Helper Available |
|---------|-------|-------------------------|
| Histogram (Time + Bins + Fit) | 3 | ✅ `create_histogram_callback` |
| Component Selection | 2 | ✅ `create_component_selection_callback` |
| Time Series | 2 | ✅ `create_time_series_callback` |
| Comparison Tab (Pattern Matching) | 7 | 🔄 Can be abstracted |
| Tab Management | 3 | 🔄 Can be abstracted |

### Benefits of Callback Factories

- ✅ **Eliminate duplication**: Write callback logic once
- ✅ **Consistent behavior**: All callbacks follow same patterns
- ✅ **Easy to extend**: Add new data types in 1 line
- ✅ **Type safe**: Data sources know their own structure
- ✅ **Maintainable**: Change callback logic in one place
- ✅ **Testable**: Factory functions are easy to unit test

### Code Reduction

- **Before**: ~17 lines per callback × 6 callbacks = ~102 lines
- **After**: ~1 line per callback registration = ~6 lines
- **Reduction**: ~94% less callback code!

---

## Next Steps

1. **Create `ui/callbacks.py`** with factory functions
2. **Add callback methods** to data source classes
3. **Create CallbackRegistry** for centralized management
4. **Migrate existing callbacks** one at a time
5. **Extract comparison callbacks** into reusable patterns

**The callback factory pattern works seamlessly with OOP data sources!** 🚀
