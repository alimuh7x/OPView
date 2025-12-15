# OPView – VTK 2D Slice Viewer

## Quick start (Linux / macOS / WSL)

```bash
cd /path/to/OPView
chmod +x setup.sh          # one time
./setup.sh                 # creates myenv and installs requirements
source myenv/bin/activate
python OPView.py
```

Open http://127.0.0.1:8050 in your browser. Stop the server with `Ctrl+C`, and exit the virtual environment with `deactivate`.

## Restarting later

```bash
cd /path/to/OPView
source myenv/bin/activate
python OPView.py
```

## Data layout

At startup the viewer scans the immediate subfolders of the repository for simulation projects that contain `VTK/` (and optionally `TextData/`) directories, e.g. `Project1/VTK`. Put your VTK outputs there before launching the app.

## Requirements

- Python 3.12 or 3.13 (VTK is not compatible with 3.14)
- Dependencies from `requirements.txt` installed into `myenv` via `setup.sh`.
