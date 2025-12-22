"""
VTK file and reader utilities for OPView.

Provides functions for VTK file management, reader caching,
and file listing.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from glob import glob


class ReaderCache:
    """
    Cache for VTKReader instances.

    Maintains a dictionary of VTKReader objects keyed by file path
    to avoid repeated file reads.
    """

    def __init__(self):
        """Initialize empty reader cache."""
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, default=None):
        """Get reader from cache."""
        return self._cache.get(key, default)

    def __getitem__(self, key: str):
        """Get reader from cache using subscript notation."""
        return self._cache[key]

    def __setitem__(self, key: str, value: Any):
        """Set reader in cache using subscript notation."""
        self._cache[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache

    def pop(self, key: str, default=None):
        """Remove and return reader from cache."""
        return self._cache.pop(key, default)

    def clear(self):
        """Clear all cached readers."""
        self._cache.clear()

    def size(self) -> int:
        """Get number of cached readers."""
        return len(self._cache)


# Global reader cache instance
reader_cache = ReaderCache()


def get_reader(file_path: str, vtk_path_resolver=None):
    """
    Return cached VTKReader for a given file path.

    Args:
        file_path: Path to VTK file (absolute or relative)
        vtk_path_resolver: Function to resolve relative paths

    Returns:
        VTKReader instance

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    from viewer import VTKReader

    debug = bool(os.environ.get("OPVIEW_DEBUG"))

    if not file_path:
        raise FileNotFoundError("VTK file not found: (empty path)")

    # Accept both absolute and relative/basename values
    resolved = Path(file_path)
    if not resolved.is_absolute():
        if vtk_path_resolver:
            resolved = vtk_path_resolver(str(resolved))
        else:
            from .path_utils import resolve_vtk_path
            resolved = resolve_vtk_path(str(resolved))

    resolved = resolved.resolve()

    if not resolved.exists():
        if debug:
            print(
                f"[OPVIEW_DEBUG] get_reader missing: input={file_path!r} "
                f"resolved={str(resolved)!r} cwd={str(Path.cwd())!r}",
                flush=True,
            )
        raise FileNotFoundError(f"VTK file not found: {file_path}")

    key = str(resolved)
    if key not in reader_cache:
        if debug:
            print(f"[OPVIEW_DEBUG] get_reader load: {key}", flush=True)
        reader_cache[key] = VTKReader(key)

    return reader_cache[key]


def list_vtk_files(directory=None) -> List[str]:
    """
    Return sorted absolute file paths from the VTK folder.

    Args:
        directory: Optional directory to scan. If None, checks if a
                  project folder is selected.

    Returns:
        Sorted list of absolute VTK file paths

    Note: Returns empty list at startup for speed. Scans when directory
          is provided or folder selected.
    """
    from .project_scanner import _scan_vtk_dir

    if directory is None:
        # FAST STARTUP: Don't scan at import time
        return []

    # Scan the specified directory
    return _scan_vtk_dir(directory)


def list_comparison_files(comparison_dir: Path) -> List[str]:
    """
    Return sorted filenames in the comparison folder.

    Args:
        comparison_dir: Path to comparison directory

    Returns:
        List of VTK file names (not full paths)
    """
    from config import ALLOWED_VTK_EXTENSIONS

    files = [
        child.name
        for child in sorted(comparison_dir.iterdir())
        if child.is_file() and child.suffix.lower() in ALLOWED_VTK_EXTENSIONS
    ]
    return files


def latest_file(pattern: str) -> str:
    """
    Return the most recent file matching the glob pattern.

    Args:
        pattern: Glob pattern to match files

    Returns:
        Path to most recent file, or None if no matches
    """
    matches = sorted(glob(pattern))
    return matches[-1] if matches else None
