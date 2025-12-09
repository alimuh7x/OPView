# Quick Start Guide - VTK 2D Slice Viewer

## Installation & Running (3 Steps)

### Step 1: Create Virtual Environment
```bash
python -m venv venv
```

### Step 2: Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### Step 3: Install & Run
```bash
pip install -r requirements.txt
python sample_data/generate_sample_vti.py
python app.py
```

**Open browser:** http://127.0.0.1:8050

---

## Important Notes

### Python Version
- **Recommended:** Python 3.12
- **Issue with 3.14:** VTK may have compatibility issues

If you encounter VTK import errors, use Python 3.12:
```bash
python3.12 -m venv venv
```

### First Time Setup
The app will automatically generate sample VTI files if they don't exist. You'll see:
```
Sample data not found. Generating sample VTI files...
```

---

## Using the Application

### Interface Overview
```
┌─────────────────────────────────────────────────────────┐
│              VTK 2D Slice Viewer                        │
├──────────────┬──────────────────────────────────────────┤
│              │                                           │
│  Controls    │         Interactive Heatmap              │
│              │                                           │
│  - Color A   │                                           │
│  - Color B   │         [Click to set threshold]         │
│  - Threshold │                                           │
│  - Slice     │                                           │
│  - Reset     │                                           │
│              │                                           │
│  Statistics  │         Clicked Info                     │
│              │                                           │
└──────────────┴──────────────────────────────────────────┘
```

### Quick Actions

1. **Change colors:** Type color names in Color A/B fields (e.g., "blue", "red", "green")
2. **Set threshold:** Click anywhere on the heatmap OR type value in Threshold field
3. **Change slice:** Move the slider (only for 3D datasets)
4. **Reset:** Click "Reset to Initial" button

### Color Options
- Names: `blue`, `red`, `green`, `orange`, `purple`, `yellow`
- Hex: `#0000FF`, `#FF0000`, `#00FF00`
- RGB: `rgb(0,0,255)`, `rgb(255,0,0)`

---

## Troubleshooting

### Problem: VTK Import Error
**Solution:** Use Python 3.12 instead of 3.14

### Problem: Port 8050 in use
**Solution:** Edit `app.py` line ~300, change port:
```python
app.run_server(debug=True, host='127.0.0.1', port=8051)
```

### Problem: No sample files
**Solution:** Run:
```bash
python sample_data/generate_sample_vti.py
```

---

## Load Your Own VTK File

Edit `app.py` around line 53:
```python
default_file = 'sample_data/sample_3d.vti'  # Change this path
```

Then restart the application.

---

## What You Get

### Files Created
```
sample_data/sample_3d.vti      # 3D test data (50×40×30)
sample_data/sample_2d.vti      # 2D test data (100×80)
sample_data/phase_field.vti    # Phase field (60×50×40)
```

### Application Features
- Two-color threshold visualization
- Interactive threshold selection (click on map)
- Slice navigation for 3D data
- Real-time statistics
- Custom color selection
- Reset functionality

---

## Need Help?

See the full **README.md** for detailed documentation.
