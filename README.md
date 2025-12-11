# VTK 2D Slice Viewer


## Start the app (Linux / macOS / WSL)

```bash
cd /path/to/OPView
chmod +x setup.sh     # run once
./setup.sh
source myenv/bin/activate
python app.py
```

Open http://127.0.0.1:8050 in your browser.  
Stop the server with `Ctrl+C`, and exit the virtual environment with `deactivate`.

## Restarting later

```bash
cd /path/to/OPView
source myenv/bin/activate
python app.py
```

Open http://127.0.0.1:8050, stop with `Ctrl+C`, and run `deactivate` once you're done.

## Libraries installed

`setup.sh` runs `pip install -r requirements.txt`, which installs:

- `dash`
- `dash-mantine-components`
- `plotly`
- `numpy`
- `scipy`
- `pyvista`
- `vtk`
- `markdown`
- `kaleido`

## Python version

- Installed Python **3.12** or **3.13** (Python 3.14 is not compatible with VTK).
