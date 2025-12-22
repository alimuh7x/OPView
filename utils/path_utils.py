"""
Path resolution utilities for OPView.

Provides functions for resolving VTK paths.
"""

from pathlib import Path


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
