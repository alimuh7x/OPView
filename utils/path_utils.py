"""
Path resolution utilities for OPView.

Provides functions for resolving VTK paths and cross-platform folder dialogs.
"""

import subprocess
import sys
import re
import os
from pathlib import Path


def _running_in_wsl() -> bool:
    """Return True when running inside WSL."""
    if not sys.platform.startswith("linux"):
        return False
    if os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return False


def _choose_folder_via_windows_powershell(title: str) -> str | None:
    """Open Windows folder picker from WSL and return Windows path."""
    safe_title = title.replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dlg = New-Object System.Windows.Forms.FolderBrowserDialog; "
        f"$dlg.Description = '{safe_title}'; "
        "if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
        "Write-Output $dlg.SelectedPath }"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        return None
    return None


def _choose_folder_via_tk_windows(title: str) -> str | None:
    """Open a topmost Tk folder chooser on Windows."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        path = filedialog.askdirectory(title=title, parent=root, mustexist=True)
        root.destroy()
        return path or None
    except Exception:
        return None


def choose_folder(title: str = "Select Folder") -> str | None:
    """
    Open a native folder selection dialog.

    On macOS, uses osascript (AppleScript) to avoid threading issues with
    Tkinter/pyobjus when called from Dash callbacks (which run in background threads).

    Args:
        title: Dialog title

    Returns:
        Selected folder path as string, or None if cancelled/failed
    """
    print(f"[choose_folder] platform={sys.platform} title={title!r}", flush=True)

    if sys.platform == "darwin":
        print("[choose_folder] trying osascript chooser", flush=True)
        # macOS: Use osascript to avoid NSWindow threading issues
        script = f'''
        set folderPath to POSIX path of (choose folder with prompt "{title}")
        return folderPath
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0 and result.stdout.strip():
                print("[choose_folder] selected via osascript", flush=True)
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, Exception):
            print("[choose_folder] osascript failed", flush=True)
            pass
        print("[choose_folder] no folder selected via osascript", flush=True)
        return None

    if sys.platform.startswith("win"):
        print("[choose_folder] trying topmost Tk folder picker (Windows)", flush=True)
        path = _choose_folder_via_tk_windows(title)
        if path:
            print("[choose_folder] selected via Tk folder picker", flush=True)
            return path
        print("[choose_folder] Tk folder picker unavailable/failed or cancelled", flush=True)
        return None

    # Linux/WSL: under WSL prefer Windows dialog first, then zenity.
    if sys.platform.startswith("linux"):
        if _running_in_wsl():
            print("[choose_folder] trying Windows PowerShell folder picker (WSL)", flush=True)
            path = _choose_folder_via_windows_powershell(title)
            if path:
                print("[choose_folder] selected via Windows PowerShell", flush=True)
                return path
            print("[choose_folder] Windows PowerShell picker unavailable/failed", flush=True)
        try:
            print("[choose_folder] trying zenity --file-selection --directory", flush=True)
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", f"--title={title}"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and result.stdout.strip():
                print("[choose_folder] selected via zenity", flush=True)
                return result.stdout.strip()
            print("[choose_folder] zenity returned no selection", flush=True)
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            print("[choose_folder] zenity unavailable/failed", flush=True)

    # Windows/Linux: Try easygui first, then plyer
    try:
        print("[choose_folder] trying easygui.diropenbox", flush=True)
        import easygui
        path = easygui.diropenbox(title=title)
        if path:
            print("[choose_folder] selected via easygui", flush=True)
            return path
        print("[choose_folder] easygui returned no selection", flush=True)
        # On native Windows, treat dialog cancel as final user intent.
        if sys.platform.startswith("win"):
            return None
    except Exception:
        print("[choose_folder] easygui unavailable/failed", flush=True)
        pass

    try:
        print("[choose_folder] trying plyer.filechooser.choose_dir", flush=True)
        from plyer import filechooser
        selection = filechooser.choose_dir(title=title)
        if selection and len(selection) > 0:
            print("[choose_folder] selected via plyer", flush=True)
            return selection[0]
        print("[choose_folder] plyer returned no selection", flush=True)
    except Exception:
        print("[choose_folder] plyer unavailable/failed", flush=True)
        pass

    print("[choose_folder] no folder selected (all methods failed or cancelled)", flush=True)
    return None


def normalize_folder_path_for_runtime(path_str: str | None) -> str | None:
    """
    Normalize pasted folder paths across Windows/WSL runtimes.

    - On Linux/WSL, convert `X:\\foo\\bar` -> `/mnt/x/foo/bar`
    - On Windows, convert `/mnt/x/foo/bar` -> `X:\\foo\\bar`
    """
    if not path_str:
        return path_str

    raw = path_str.strip()
    if not raw:
        return raw

    if sys.platform.startswith("linux"):
        # Windows drive path (e.g. E:\RUB\OpenPhase\...)
        m = re.match(r"^([A-Za-z]):[\\/](.*)$", raw)
        if m:
            drive = m.group(1).lower()
            rest = m.group(2).replace("\\", "/")
            return f"/mnt/{drive}/{rest}"
        return raw

    if sys.platform.startswith("win"):
        # WSL mount path (e.g. /mnt/e/RUB/OpenPhase/...)
        m = re.match(r"^/mnt/([A-Za-z])/(.*)$", raw)
        if m:
            drive = m.group(1).upper()
            rest = m.group(2).replace("/", "\\")
            return f"{drive}:\\{rest}"
        return raw

    return raw


def resolve_vtk_path(pattern: str, current_project_vtk_path: Path = None) -> Path:
    """
    Resolve a file or glob pattern into the VTK data directory.

    Args:
        pattern: File pattern or path to resolve
        current_project_vtk_path: Path to selected project's VTK folder

    Returns:
        Resolved absolute Path

    Examples:
        >>> resolve_vtk_path("file.vtk")
        Path("/path/to/VTK/file.vtk")

        >>> resolve_vtk_path("VTK/file.vtk")
        Path("/path/to/VTK/file.vtk")

        >>> resolve_vtk_path("/absolute/path/file.vtk")
        Path("/absolute/path/file.vtk")
    """
    p = Path(pattern)

    # If already absolute, return as-is
    if p.is_absolute():
        return p

    # Strip leading "VTK" if present
    parts = p.parts
    if parts and parts[0].lower() == "vtk":
        p = Path(*parts[1:])

    # Resolve relative to VTK data directory
    from config import vtk_data_dir
    return vtk_data_dir(current_project_vtk_path) / p
