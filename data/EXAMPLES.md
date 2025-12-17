# Data Source Examples

## Quick Reference: Adding New Data Types

With `ScalarDataSource` and `VectorDataSource`, adding new physical fields is **trivial**.

---

## Scalar Fields (Temperature, Diffusion, etc.)

### Temperature Data (10 lines!)

```python
from data.base import ScalarDataSource

class TemperatureData(ScalarDataSource):
    file_pattern = "Temperature*.txt"
    display_name = "Temperature Distribution"
    scalar_name = "Temperature"
    scalar_unit = "K"
    scalar_symbol = "T"

    def load(self) -> bool:
        # Load from Temperature*.txt file
        # Store in self._data = {'data': {'temperature': values}, 'times': [...]}
        return True
```

**That's it!** You get automatically:
- `get_component_options()` → `[{'label': 'T (K)', 'value': 'temperature'}]`
- `get_default_components()` → `['temperature']`
- `get_min_max('temperature')` → Auto-calculated from data
- `get_time_options()` → Formatted time steps
- Histogram support

---

### Diffusion Coefficient

```python
class DiffusionData(ScalarDataSource):
    file_pattern = "Diffusion*.txt"
    display_name = "Diffusion Coefficient"
    scalar_name = "Diffusion"
    scalar_unit = "m²/s"
    scalar_symbol = "D"

    def load(self) -> bool:
        # Your loading logic
        return True
```

---

### Electric Potential

```python
class ElectricPotentialData(ScalarDataSource):
    file_pattern = "Potential*.txt"
    display_name = "Electric Potential"
    scalar_name = "Potential"
    scalar_unit = "V"
    scalar_symbol = "φ"  # Greek phi

    def load(self) -> bool:
        # Your loading logic
        return True
```

---

### Concentration

```python
class ConcentrationData(ScalarDataSource):
    file_pattern = "Concentration*.txt"
    display_name = "Species Concentration"
    scalar_name = "Concentration"
    scalar_unit = "mol/m³"
    scalar_symbol = "C"

    def load(self) -> bool:
        # Your loading logic
        return True
```

---

## Vector Fields (Velocity, E-field, etc.)

### Velocity Field (10 lines!)

```python
from data.base import VectorDataSource

class VelocityData(VectorDataSource):
    file_pattern = "Velocity*.txt"
    display_name = "Velocity Field"
    vector_symbol = "v"
    vector_unit = "m/s"

    def load(self) -> bool:
        # Load from Velocity*.txt file
        # Store in self._data = {
        #     'data': {'v_x': [...], 'v_y': [...], 'v_z': [...]},
        #     'times': [...]
        # }
        return True
```

**That's it!** You get automatically:
- `get_component_options()` → `[v_x, v_y, v_z, |v|]` with units
- `get_default_components()` → `['v_mag']` (magnitude)
- `get_min_max('v_mag')` → Auto-calculated from √(v_x² + v_y² + v_z²)
- `get_time_options()` → Formatted time steps

---

### Electric Field

```python
class ElectricFieldData(VectorDataSource):
    file_pattern = "ElectricField*.txt"
    display_name = "Electric Field"
    vector_symbol = "E"
    vector_unit = "V/m"

    def load(self) -> bool:
        # Your loading logic
        return True
```

**Auto-generated options:**
- `E_x (V/m)`
- `E_y (V/m)`
- `E_z (V/m)`
- `|E| (V/m)` ← Magnitude (default)

---

### Magnetic Field

```python
class MagneticFieldData(VectorDataSource):
    file_pattern = "MagneticField*.txt"
    display_name = "Magnetic Field"
    vector_symbol = "B"
    vector_unit = "T"

    def load(self) -> bool:
        # Your loading logic
        return True
```

---

### Force Field

```python
class ForceData(VectorDataSource):
    file_pattern = "Force*.txt"
    display_name = "Force Distribution"
    vector_symbol = "F"
    vector_unit = "N"

    def load(self) -> bool:
        # Your loading logic
        return True
```

---

### Displacement Field

```python
class DisplacementData(VectorDataSource):
    file_pattern = "Displacement*.txt"
    display_name = "Displacement Field"
    vector_symbol = "u"
    vector_unit = "m"

    def load(self) -> bool:
        # Your loading logic
        return True
```

---

## Using the Data Sources

### With UI Components

```python
from data import TemperatureData, VelocityData
from ui import TimeSeriesCard, Row, Dropdown, RangeSlider

# Temperature card
temp_data = TemperatureData(data_dir)

row = Row()
drop = row.dropdown(
    'temp-component',
    temp_data.get_component_options(),  # T (K)
    value=temp_data.get_default_components()[0]
)

min_val, max_val = temp_data.get_min_max('temperature')
range_slider = row.range_slider('temp-range', min_val, max_val)

# Or use TimeSeriesCard
card = TimeSeriesCard(temp_data, 'temperature-card')
return card.build()  # Auto-generates everything!


# Velocity card
velocity_data = VelocityData(data_dir)

row2 = Row()
drop = row2.dropdown(
    'velocity-component',
    velocity_data.get_component_options(),  # v_x, v_y, v_z, |v|
    value='v_mag'  # Default to magnitude
)

card = TimeSeriesCard(velocity_data, 'velocity-card')
return card.build()
```

---

## Complete Example: Adding Temperature to Your App

### Step 1: Create the Data Source (10 lines)

```python
# In data/sources.py
from .base import ScalarDataSource

class TemperatureData(ScalarDataSource):
    file_pattern = "Temperature*.txt"
    display_name = "Temperature Distribution"
    scalar_name = "Temperature"
    scalar_unit = "K"
    scalar_symbol = "T"

    def load(self) -> bool:
        # Your existing temperature loading logic here
        file_path = self.data_dir / "TemperatureFile.txt"
        # ... load data ...
        self._data = {
            'data': {'temperature': temperature_values},
            'times': time_steps
        }
        self._loaded = True
        return True
```

### Step 2: Export It

```python
# In data/__init__.py
from .sources import (..., TemperatureData)

__all__ = [..., 'TemperatureData']
```

### Step 3: Use It

```python
# In your card building code
from data import TemperatureData
from ui import TimeSeriesCard

def build_temperature_card(data_dir):
    temp_data = TemperatureData(data_dir)
    card = TimeSeriesCard(temp_data, 'temperature')
    return card.build()
```

**Done!** Full temperature visualization in ~15 lines total.

---

## Comparison: Before vs After

### ❌ Before (Manual - ~80 lines)

```python
def build_temperature_card():
    data = TEMPERATURE_DATA
    if not data:
        return None

    # Manually create options
    options = [{'label': 'Temperature (K)', 'value': 'temp'}]

    # Manually calculate min/max
    min_temp = min(data['values'])
    max_temp = max(data['values'])

    # Manually format time options
    time_options = []
    for t in data['times']:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        time_options.append({'label': label, 'value': str(t)})

    # Manually build UI
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Temperature', className='dataset-title')
        ], className='dataset-header'),
        # ... 60 more lines of HTML ...
    ])
```

### ✅ After (OOP - ~13 lines)

```python
from data import TemperatureData
from ui import TimeSeriesCard

class TemperatureData(ScalarDataSource):  # 10 lines
    file_pattern = "Temperature*.txt"
    display_name = "Temperature Distribution"
    scalar_name = "Temperature"
    scalar_unit = "K"
    scalar_symbol = "T"
    def load(self): ...

def build_temperature_card(data_dir):  # 3 lines
    temp_data = TemperatureData(data_dir)
    return TimeSeriesCard(temp_data, 'temperature').build()
```

**~84% code reduction!**

---

## Summary

### To Add New Scalar Field:
1. Create class inheriting from `ScalarDataSource`
2. Set 5 properties (name, unit, symbol, file_pattern, display_name)
3. Implement `load()` method
4. **Done!** (~10 lines)

### To Add New Vector Field:
1. Create class inheriting from `VectorDataSource`
2. Set 4 properties (symbol, unit, file_pattern, display_name)
3. Implement `load()` method
4. **Done!** (~10 lines)

### You Get Automatically:
- ✅ Component options with proper formatting
- ✅ Default component selection
- ✅ Min/max calculation
- ✅ Time step formatting
- ✅ Histogram support (for scalars)
- ✅ Magnitude calculation (for vectors)
- ✅ Works with all UI components
- ✅ Works with card builders

**Adding new physical fields is now trivial!** 🚀
