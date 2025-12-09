# VTK 2D Slice Viewer - Development Notes

## Project Overview

A production-ready interactive Dash application for visualizing VTK files with advanced two-color threshold visualization. Built with Python, Dash, Plotly, and PyVista.

**Current Status**: ✅ Fully functional and running at http://127.0.0.1:8050

---

## Quick Start

### Running the Application

```bash
# Activate virtual environment (if using one)
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Run the application
python3 app.py
```

**Access at**: http://127.0.0.1:8050

### Current Configuration

- **VTK File**: `PhaseField_Initial.vts`
- **Dimensions**: 128×128×128 (3D)
- **Scalar Fields**: 6 available
  - Interfaces
  - Flags
  - PhaseFields
  - PhaseFraction_0
  - PhaseFraction_1
  - Junctions
- **Slice Range**: 0-127 (Y-axis)
- **Rendering**: 500×500 interpolation with smoothing
- **Aspect Ratio**: 1:1 (square)

---

## File Structure

```
Dash/
├── app.py                          # Main application (~490 lines)
├── PhaseField_Initial.vts          # Current VTK file (128×128×128)
├── requirements.txt                # Python dependencies
├── README.md                       # User documentation
├── QUICK_START.md                  # Quick start guide
├── Claude.md                       # This file (development notes)
│
├── utils/
│   ├── __init__.py
│   └── vtk_reader.py              # VTK file loading and slicing (~192 lines)
│
├── sample_data/
│   ├── generate_sample_vti.py     # Sample data generator
│   ├── sample_3d.vti              # 3D test data (50×40×30)
│   ├── sample_2d.vti              # 2D test data (100×80)
│   └── phase_field.vti            # Phase field data (60×50×40)
│
└── assets/
    └── style.css                   # Custom CSS styling
```

---

## Key Features

### Current Implementation

1. **Two-Color Gradient Visualization**
   - Gradient colorscale: Min Color → White (midpoint) → Max Color
   - Smooth transitions with white at threshold value
   - Customizable colors (names, hex, RGB)

2. **Interactive Range Selection**
   - **Two-click system**:
     - 1st click sets MIN value
     - 2nd click sets MAX value
   - Visual feedback with color-coded indicators:
     - Gray: Ready for first click
     - Yellow: Waiting for second click
     - Green: Range set successfully
   - Manual min/max input fields

3. **Scalar Field Selector**
   - Dropdown to switch between 6 available fields
   - Automatic range reset when changing fields
   - Threshold auto-calculated as midpoint

4. **3D Slicing**
   - Slider for Y-axis slicing (0-127)
   - Real-time slice updates
   - Works with all scalar fields

5. **Color Customization**
   - Min Color: Below threshold (default: blue)
   - Max Color: Above threshold (default: red)
   - Accepts: color names, hex codes (#FF0000), RGB values (rgb(255,0,0))

6. **Reset Functionality**
   - Resets threshold to initial value
   - Resets min/max range to full data range
   - Resets colors to blue/red
   - Clears click state

7. **High-Quality Rendering**
   - 500×500 interpolation resolution
   - `zsmooth='best'` for ParaView-quality smoothness
   - Square aspect ratio (1:1)
   - No axis labels/ticks for clean visualization

8. **Statistics Display**
   - Min, Max, Mean, Std Dev
   - Current threshold value
   - Updated in real-time

---

## Technical Architecture

### Core Technologies

- **Dash 2.14.0+**: Web framework
- **Plotly 5.18.0+**: Interactive plotting
- **PyVista 0.43.0+**: VTK file handling
- **NumPy 1.24.0+**: Numerical arrays
- **SciPy 1.11.0+**: Grid interpolation
- **VTK 9.2.0+**: VTK backend

### Key Code Sections

#### 1. Gradient Colorscale (app.py:372-376)

```python
colorscale = [
    [0.0, colorA],    # Min color at bottom
    [0.5, 'white'],   # White at midpoint
    [1.0, colorB]     # Max color at top
]
```

#### 2. High-Resolution Heatmap (app.py:379-396)

```python
fig = go.Figure(data=go.Heatmap(
    x=current_data['X_grid'][0, :],
    y=current_data['Y_grid'][:, 0],
    z=current_data['Z_grid'],
    colorscale=colorscale,
    zmid=threshold_manual,
    zmin=current_data.get('range_min', current_data['stats']['min']),
    zmax=current_data.get('range_max', current_data['stats']['max']),
    zsmooth='best',  # Enable smoothing
    colorbar=dict(
        title=dict(text="Scalar Value", side="right"),
        tickmode="linear"
    ),
    hovertemplate='Value: %{z:.4f}<extra></extra>'
))
```

#### 3. Square Aspect Ratio (app.py:398-419)

```python
fig.update_layout(
    xaxis=dict(
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        title=None,
        scaleanchor="y",  # Lock to y-axis
        scaleratio=1      # 1:1 ratio
    ),
    yaxis=dict(
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        title=None,
        constrain='domain'
    ),
    height=700,
    width=700  # Square
)
```

#### 4. Two-Click Range Selection (app.py:332-355)

```python
if triggered_id == 'heatmap' and click_data:
    clicked_z = click_data['points'][0]['z']

    if current_data['click_count'] == 0:
        # First click
        current_data['first_click'] = clicked_z
        current_data['click_count'] = 1
    else:
        # Second click - determine min/max
        val1 = current_data['first_click']
        val2 = clicked_z
        current_data['range_min'] = min(val1, val2)
        current_data['range_max'] = max(val1, val2)
        current_data['click_count'] = 0
        current_data['first_click'] = None
        # Auto-update threshold
        threshold_manual = (current_data['range_min'] + current_data['range_max']) / 2
```

#### 5. Reset Button Handler (app.py:277-291)

```python
if triggered_id == 'reset-button':
    current_data['threshold'] = current_data['initial_threshold']
    current_data['colorA'] = current_data['initial_colorA']
    current_data['colorB'] = current_data['initial_colorB']
    current_data['range_min'] = current_data['stats']['min']
    current_data['range_max'] = current_data['stats']['max']
    current_data['clicked_value'] = None
    current_data['click_count'] = 0
    current_data['first_click'] = None
```

#### 6. Scalar Field Reset (app.py:293-311)

```python
if triggered_id == 'scalar-field-dropdown' and scalar_field:
    if scalar_field != current_data.get('current_scalar'):
        # Reload data with new scalar field
        x_coords, y_coords, scalars, stats = vtk_reader.get_slice(
            axis=current_data['axis'],
            index=current_data['slice_index'],
            scalar_name=scalar_field
        )
        X_grid, Y_grid, Z_grid = vtk_reader.interpolate_to_grid(
            x_coords, y_coords, scalars, resolution=500
        )
        # Reset range to full data range
        current_data['range_min'] = stats['min']
        current_data['range_max'] = stats['max']
        threshold_manual = (stats['min'] + stats['max']) / 2
```

#### 7. VTK Reader - Slicing (utils/vtk_reader.py:53-96)

```python
def get_slice(self, axis='y', index=None, scalar_name=None):
    """Extract 2D slice from mesh"""
    if scalar_name is None:
        scalar_name = self.scalar_name

    if not self.is_3d:
        return self._extract_2d_data(scalar_name)

    # Determine slice index
    axis_map = {'x': 0, 'y': 1, 'z': 2}
    axis_idx = axis_map[axis.lower()]

    if index is None:
        index = self.dimensions[axis_idx] // 2

    # Extract slice using PyVista
    if axis.lower() == 'y':
        bounds = self.mesh.bounds
        y_val = bounds[2] + (bounds[3] - bounds[2]) * index / max(1, self.dimensions[1] - 1)
        slice_mesh = self.mesh.slice(normal='y', origin=(0, y_val, 0))

    return self._process_slice(slice_mesh, axis, scalar_name)
```

#### 8. Grid Interpolation (utils/vtk_reader.py:159-191)

```python
def interpolate_to_grid(self, x_coords, y_coords, scalars, resolution=100):
    """Interpolate scattered data to regular grid"""
    from scipy.interpolate import griddata

    # Create regular grid
    x_min, x_max = np.min(x_coords), np.max(x_coords)
    y_min, y_max = np.min(y_coords), np.max(y_coords)

    xi = np.linspace(x_min, x_max, resolution)
    yi = np.linspace(y_min, y_max, resolution)
    X_grid, Y_grid = np.meshgrid(xi, yi)

    # Interpolate
    Z_grid = griddata(
        (x_coords, y_coords),
        scalars,
        (X_grid, Y_grid),
        method='linear',
        fill_value=np.nan
    )

    return X_grid, Y_grid, Z_grid
```

---

## Layout Structure

### Left Column (25% width) - Controls

```
┌─────────────────────────┐
│ Controls                │
├─────────────────────────┤
│ Scalar Field Dropdown   │
│ Min Color Input         │
│ Max Color Input         │
│ Min Value Input         │
│ Max Value Input         │
│ Threshold Input         │
│ Slice Slider (0-127)    │
│ Reset Button            │
│ Statistics Display      │
└─────────────────────────┘
```

### Right Column (73% width) - Visualization

```
┌──────────────────────────────────┐
│                                  │
│      Interactive Heatmap         │
│                                  │
│    [700×700 square display]      │
│                                  │
│  Click to set min/max range      │
│                                  │
└──────────────────────────────────┘
│ Click Indicator                  │
│ (Gray/Yellow/Green feedback)     │
└──────────────────────────────────┘
```

---

## Development History

### Evolution Timeline

1. **Initial Build**
   - Basic VTK reader with PyVista
   - Simple two-color threshold (sharp transition)
   - Sample VTI data generation

2. **User Feedback Round 1**
   - Added scalar field selector (6 fields)
   - Changed to gradient with white midpoint
   - Removed axis labels and tick numbers

3. **User Feedback Round 2**
   - Increased resolution to 500×500
   - Added `zsmooth='best'` for ParaView-quality rendering

4. **User Feedback Round 3**
   - Changed click behavior: two-click min/max selection
   - Made visualization square (1:1 aspect ratio)
   - Fixed layout: controls left, figure right

5. **User Feedback Round 4**
   - Added manual min/max input fields
   - Fixed slice slider (was hardcoded to 39, now 0-127)

6. **User Feedback Round 5**
   - Auto-reset range when changing scalar fields
   - Added visual click indicators (gray/yellow/green)
   - Fixed layout wrapping issue

7. **User Feedback Round 6** (Current)
   - Reset button now resets min/max values
   - Renamed "Color A/B" to "Min/Max Color"
   - Added placeholder text showing color format examples

### Known Issues Resolved

1. ✅ **VTK Import Error** (Python 3.14 compatibility)
   - Solution: Use Python 3.12

2. ✅ **String Formatting Error** (clicked_value became string)
   - Solution: Changed f-string to str() conversion

3. ✅ **Colorbar titleside deprecated**
   - Solution: Changed to title dict with 'side' key

4. ✅ **Slice slider hardcoded to 39**
   - Solution: Dynamic sizing with (dimensions[1] - 1)

5. ✅ **Figure appearing below controls**
   - Solution: Changed flexWrap to 'nowrap'

---

## Usage Guide

### Basic Workflow

1. **Select Scalar Field**
   - Choose from dropdown (e.g., PhaseFraction_0)
   - Range auto-resets to data min/max

2. **Set Visualization Range**
   - **Option A: Click on heatmap**
     - 1st click: Sets MIN value (yellow indicator)
     - 2nd click: Sets MAX value (green indicator)
   - **Option B: Manual input**
     - Type values in Min/Max input fields
   - Threshold auto-updates to midpoint

3. **Customize Colors**
   - Min Color: Type color name, hex, or RGB
   - Max Color: Type color name, hex, or RGB
   - Examples: "blue", "#0000FF", "rgb(0,0,255)"

4. **Navigate 3D Slices**
   - Use slider to move through Y-axis (0-127)
   - Real-time updates

5. **Reset Everything**
   - Click "Reset to Initial" button
   - Restores: threshold, colors, min/max range, click state

### Advanced Features

#### Color Examples

```
Color Names:
- blue, red, green, yellow, orange, purple, cyan, magenta

Hex Codes:
- #0000FF (blue)
- #FF0000 (red)
- #00FF00 (green)

RGB Values:
- rgb(0,0,255) (blue)
- rgb(255,0,0) (red)
- rgb(0,255,0) (green)
```

#### Loading Custom VTK Files

Edit `app.py` line 67:

```python
default_file = 'path/to/your/file.vts'  # Change this
```

Supported formats:
- `.vtk` - Legacy VTK
- `.vti` - Image Data
- `.vtp` - Polygonal Data
- `.vtr` - Rectilinear Grid
- `.vts` - Structured Grid

---

## Data Flow

```
VTK File (.vts)
    ↓
PyVista Reader
    ↓
Extract Scalar Field (selected from dropdown)
    ↓
3D Slicing (if 3D data) → 2D slice at Y-index
    ↓
Scattered Points (x, y, scalar_value)
    ↓
SciPy Grid Interpolation (500×500 resolution)
    ↓
Regular Grid (X_grid, Y_grid, Z_grid)
    ↓
Plotly Heatmap with:
  - Gradient colorscale (min_color → white → max_color)
  - zmid = threshold
  - zmin/zmax = custom range
  - zsmooth = 'best'
    ↓
Interactive Visualization
```

---

## State Management

### Global State Variables

```python
current_data = {
    'X_grid': ndarray,              # Interpolated X coordinates
    'Y_grid': ndarray,              # Interpolated Y coordinates
    'Z_grid': ndarray,              # Interpolated scalar values
    'stats': {                      # Statistics
        'min': float,
        'max': float,
        'mean': float,
        'std': float
    },
    'threshold': float,             # Current threshold value
    'colorA': str,                  # Min color (below threshold)
    'colorB': str,                  # Max color (above threshold)
    'slice_index': int,             # Current Y-axis slice
    'axis': str,                    # Slicing axis ('y')
    'clicked_value': str/None,      # Click feedback message
    'initial_threshold': float,     # For reset
    'initial_colorA': str,          # For reset
    'initial_colorB': str,          # For reset
    'current_scalar': str,          # Currently selected scalar field
    'range_min': float,             # Display range minimum
    'range_max': float,             # Display range maximum
    'click_count': int,             # 0 or 1 (waiting for 2nd click)
    'first_click': float/None       # First clicked value
}
```

### Callback Triggers

The main callback responds to 9 inputs:

1. `scalar-field-dropdown` - Change scalar field
2. `color-a-input` - Change min color
3. `color-b-input` - Change max color
4. `threshold-input` - Manual threshold
5. `min-input` - Manual min value
6. `max-input` - Manual max value
7. `slice-slider` - Change slice
8. `reset-button` - Reset all
9. `heatmap.clickData` - Click on visualization

**Returns 9 outputs:**

1. Heatmap figure
2. Statistics display
3. Click info message
4. Threshold value
5. Color A value
6. Color B value
7. Slice index
8. Min value
9. Max value

---

## Performance Optimizations

1. **Grid Interpolation**: 500×500 resolution for smooth rendering
2. **zsmooth='best'**: Plotly's best smoothing algorithm
3. **Callback Optimization**: Single callback handles all interactions
4. **State Persistence**: Global `current_data` dict prevents re-computation
5. **Conditional Updates**: Only recalculate when necessary (slice change, field change)

---

## Future Enhancements

### Potential Features

1. **Axis Selection**
   - Add dropdown for X/Y/Z axis slicing
   - Currently hardcoded to Y-axis

2. **Export Functions**
   - PNG export of current view
   - MP4/GIF animation through slices
   - Data export (CSV, JSON)

3. **Multiple File Support**
   - File upload widget
   - File browser/selector
   - Compare two datasets side-by-side

4. **3D Visualization**
   - Toggle between 2D slice and 3D volume rendering
   - Isosurface extraction
   - 3D scatter plot mode

5. **Advanced Colormaps**
   - Custom colormap editor
   - Predefined scientific colormaps (viridis, plasma, etc.)
   - Three+ color gradients

6. **Analysis Tools**
   - Histogram of scalar values
   - Line profile extraction
   - Region selection and statistics

7. **Performance**
   - Caching of interpolated grids
   - WebGL rendering for large datasets
   - Progressive loading

---

## Troubleshooting

### Common Issues

1. **Port 8050 in use**
   ```python
   # Change port in app.py line 489
   app.run(debug=True, host='127.0.0.1', port=8051)
   ```

2. **VTK Import Error**
   - Use Python 3.12 (not 3.14)
   ```bash
   python3.12 -m venv venv
   ```

3. **File Not Found**
   - Check file path in app.py line 67
   - Ensure file exists in specified location

4. **Slow Performance**
   - Reduce interpolation resolution
   ```python
   # In app.py, change resolution parameter
   vtk_reader.interpolate_to_grid(..., resolution=300)  # Instead of 500
   ```

5. **Memory Issues (Large Files)**
   - Reduce interpolation resolution
   - Use smaller slice indices
   - Close other applications

---

## Dependencies

### requirements.txt

```
dash>=2.14.0
plotly>=5.18.0
pyvista>=0.43.0
numpy>=1.24.0
scipy>=1.11.0
vtk>=9.2.0
```

### Python Version

- **Recommended**: Python 3.12
- **Avoid**: Python 3.14 (VTK compatibility issues)

---

## Testing

### Manual Test Checklist

- [ ] Load application successfully
- [ ] All 6 scalar fields display correctly
- [ ] Slice slider moves through all 128 slices
- [ ] Click once → yellow indicator
- [ ] Click twice → green indicator with range set
- [ ] Manual min/max inputs work
- [ ] Threshold updates to midpoint
- [ ] Colors change (try: blue, #FF0000, rgb(0,255,0))
- [ ] Reset button restores all values
- [ ] Statistics update correctly
- [ ] Heatmap is square (1:1 aspect)
- [ ] Rendering is smooth (like ParaView)
- [ ] No axis labels/ticks visible

---

## Code Comments

### Important Code Locations

- **Line 67**: Default VTK file path
- **Line 36**: Interpolation resolution (currently 500)
- **Line 121-141**: Color input fields with placeholders
- **Line 183**: Slice slider max value (dynamic)
- **Line 277-291**: Reset button handler
- **Line 293-311**: Scalar field change handler
- **Line 332-355**: Two-click range selection
- **Line 372-376**: Gradient colorscale definition
- **Line 387**: zsmooth='best' for quality
- **Line 405-406**: Square aspect ratio settings
- **Line 489**: Server port configuration

---

## Git Status (Last Known)

```
Current branch: master

Modified:
- ../MachineLearning/Superalloys/Cube_Raft/CubeRaft_Report.md

Untracked:
- ../../eleventy-site/
- ../../hugo-site/
- ../../jekyll-site/

Recent commits:
- ca4e833 python code is added
- fd2e87e Exclude large data files from site
- d184506 publish
```

---

## Quick Reference

### Start Application
```bash
python3 app.py
# Open: http://127.0.0.1:8050
```

### Change VTK File
```python
# app.py line 67
default_file = 'your_file.vts'
```

### Change Resolution
```python
# app.py line 36, 294, 322
resolution=500  # Change to 300 for faster, 1000 for higher quality
```

### Change Port
```python
# app.py line 489
app.run(debug=True, host='127.0.0.1', port=8051)
```

### Change Default Colors
```python
# app.py lines 48-49, 54-55
'colorA': 'blue',      # Change to any color
'colorB': 'red',       # Change to any color
'initial_colorA': 'blue',
'initial_colorB': 'red',
```

---

## Contact & Support

For questions or issues:
1. Check README.md for user documentation
2. Check QUICK_START.md for setup guide
3. Review this file (Claude.md) for development details
4. Check code comments in app.py and utils/vtk_reader.py

---

## Version History

- **v1.0**: Initial build with basic two-color threshold
- **v1.1**: Added scalar field selector, gradient colorscale
- **v1.2**: High-resolution rendering (500×500)
- **v1.3**: Two-click range selection, square aspect ratio
- **v1.4**: Manual min/max inputs, fixed slice slider
- **v1.5**: Auto-reset on field change, visual indicators
- **v1.6** (Current): Reset includes min/max, renamed color labels

---

**Last Updated**: 2025-12-03
**Status**: Production Ready ✅
**Python Version**: 3.12
**Running at**: http://127.0.0.1:8050
