"""
Path resolution utilities for OPView.

Provides functions for resolving VTK paths and cross-platform folder dialogs.
"""

import subprocess
import sys
from pathlib import Path


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
    if sys.platform == "darwin":
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
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, Exception):
            pass
        return None

    # Windows/Linux: Try easygui first, then plyer
    try:
        import easygui
        path = easygui.diropenbox(title=title)
        if path:
            return path
    except Exception:
        pass

    try:
        from plyer import filechooser
        selection = filechooser.choose_dir(title=title)
        if selection and len(selection) > 0:
            return selection[0]
    except Exception:
        pass

    return None


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
