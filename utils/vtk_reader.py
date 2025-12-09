"""
VTK File Reader Utility
Loads VTK files and extracts 2D slices for visualization
"""
import pyvista as pv
import numpy as np


class VTKReader:
    def __init__(self, file_path):
        """
        Initialize VTK reader with file path

        Args:
            file_path (str): Path to VTK file (.vtk, .vti, .vtp, .vtr, .vts)
        """
        self.file_path = file_path
        self.mesh = None
        self.scalar_name = None
        self.dimensions = None
        self.is_3d = False
        self._interpolation_cache = {}
        self.load_file()

    def load_file(self):
        """Load VTK file using PyVista"""
        self.mesh = pv.read(self.file_path)

        # Detect scalar field (first available scalar array)
        if self.mesh.n_arrays > 0:
            self.scalar_name = self.mesh.array_names[0]
        else:
            raise ValueError("No scalar arrays found in VTK file")

        # Detect dimensions
        if hasattr(self.mesh, 'dimensions'):
            self.dimensions = self.mesh.dimensions
        else:
            # For unstructured grids, estimate from bounds
            bounds = self.mesh.bounds
            self.dimensions = (
                int(bounds[1] - bounds[0] + 1),
                int(bounds[3] - bounds[2] + 1),
                int(bounds[5] - bounds[4] + 1)
            )

        # Check if 3D (more than 1 cell in any direction)
        self.is_3d = (
            self.dimensions[0] > 1 and
            self.dimensions[1] > 1 and
            self.dimensions[2] > 1
        )

    def get_slice(self, axis='y', index=None, scalar_name=None, component=None):
        """
        Extract 2D slice from mesh

        Args:
            axis (str): Axis to slice along ('x', 'y', or 'z')
            index (int): Slice index. If None, uses middle slice
            scalar_name (str): Name of scalar field to extract. If None, uses default

        Returns:
            tuple: (x_coords, y_coords, scalar_values, stats)
        """
        # Use specified scalar or default
        if scalar_name is None:
            scalar_name = self.scalar_name
        if not self.is_3d:
            return self._extract_2d_data(scalar_name, component)

        # Determine slice index
        axis_map = {'x': 0, 'y': 1, 'z': 2}
        axis_idx = axis_map[axis.lower()]

        if index is None:
            index = self.dimensions[axis_idx] // 2

        # Clip index to valid range
        index = max(0, min(index, self.dimensions[axis_idx] - 1))

        # Extract slice using PyVista
        bounds = self.mesh.bounds
        x_mid = (bounds[0] + bounds[1]) * 0.5
        y_mid = (bounds[2] + bounds[3]) * 0.5
        z_mid = (bounds[4] + bounds[5]) * 0.5

        if axis.lower() == 'x':
            x_val = bounds[0] + (bounds[1] - bounds[0]) * index / max(1, self.dimensions[0] - 1)
            slice_mesh = self.mesh.slice(normal='x', origin=(x_val, y_mid, z_mid))
        elif axis.lower() == 'y':
            y_val = bounds[2] + (bounds[3] - bounds[2]) * index / max(1, self.dimensions[1] - 1)
            slice_mesh = self.mesh.slice(normal='y', origin=(x_mid, y_val, z_mid))
        else:  # z
            z_val = bounds[4] + (bounds[5] - bounds[4]) * index / max(1, self.dimensions[2] - 1)
            slice_mesh = self.mesh.slice(normal='z', origin=(x_mid, y_mid, z_val))

        return self._process_slice(slice_mesh, axis, scalar_name, component)

    def _extract_2d_data(self, scalar_name=None, component=None):
        """Extract data from 2D mesh"""
        if scalar_name is None:
            scalar_name = self.scalar_name
        points = self.mesh.points
        scalars = self.mesh[scalar_name]
        scalars = self._select_component(scalars, component)

        # Determine which two axes have variation
        std_devs = np.std(points, axis=0)
        active_axes = np.where(std_devs > 1e-10)[0]

        if len(active_axes) < 2:
            active_axes = [0, 1]  # Default to XY

        x_coords = points[:, active_axes[0]]
        y_coords = points[:, active_axes[1]]

        # Compute statistics
        stats = {
            'min': float(np.min(scalars)),
            'max': float(np.max(scalars)),
            'mean': float(np.mean(scalars)),
            'std': float(np.std(scalars))
        }

        return x_coords, y_coords, scalars, stats

    def _process_slice(self, slice_mesh, axis, scalar_name=None, component=None):
        """Process sliced mesh to extract coordinates and scalars"""
        if scalar_name is None:
            scalar_name = self.scalar_name
        points = slice_mesh.points
        scalars = slice_mesh[scalar_name]
        scalars = self._select_component(scalars, component)

        # Determine coordinate axes based on slice axis
        if axis.lower() == 'x':
            x_coords = points[:, 1]  # Y
            y_coords = points[:, 2]  # Z
        elif axis.lower() == 'y':
            x_coords = points[:, 0]  # X
            y_coords = points[:, 2]  # Z
        else:  # z
            x_coords = points[:, 0]  # X
            y_coords = points[:, 1]  # Y

        # Compute statistics
        stats = {
            'min': float(np.min(scalars)),
            'max': float(np.max(scalars)),
            'mean': float(np.mean(scalars)),
            'std': float(np.std(scalars))
        }

        return x_coords, y_coords, scalars, stats

    def get_max_slice_index(self, axis='y'):
        """Get maximum valid slice index for given axis"""
        axis_map = {'x': 0, 'y': 1, 'z': 2}
        axis_idx = axis_map[axis.lower()]
        return self.dimensions[axis_idx] - 1

    def interpolate_to_grid(self, x_coords, y_coords, scalars, resolution=100):
        """
        Interpolate scattered data to regular grid for heatmap
        """
        from scipy.interpolate import griddata

        x_min, x_max = np.min(x_coords), np.max(x_coords)
        y_min, y_max = np.min(y_coords), np.max(y_coords)

        xi = np.linspace(x_min, x_max, resolution)
        yi = np.linspace(y_min, y_max, resolution)
        X_grid, Y_grid = np.meshgrid(xi, yi)

        Z_grid = griddata(
            (x_coords, y_coords),
            scalars,
            (X_grid, Y_grid),
            method='linear',
            fill_value=np.nan
        )

        return X_grid, Y_grid, Z_grid

    def get_interpolated_slice(self, axis='y', index=None, scalar_name=None, component=None, resolution=100):
        """
        Retrieve (and cache) interpolated grid + stats for a slice.
        """
        if scalar_name is None:
            scalar_name = self.scalar_name

        cache_key = (scalar_name, component, axis.lower(), index if index is not None else -1, resolution)

        if cache_key in self._interpolation_cache:
            return self._interpolation_cache[cache_key]

        x_coords, y_coords, scalars, stats = self.get_slice(axis=axis, index=index, scalar_name=scalar_name, component=component)
        X_grid, Y_grid, Z_grid = self.interpolate_to_grid(x_coords, y_coords, scalars, resolution=resolution)
        result = (X_grid, Y_grid, Z_grid, stats)
        self._interpolation_cache[cache_key] = result
        return result

    @property
    def scalar_fields(self):
        """List available scalar arrays."""
        return list(self.mesh.array_names)

    def _select_component(self, scalars, component):
        """Return either a selected component or the scalar array as-is."""
        if scalars.ndim == 1:
            return scalars
        if scalars.ndim == 2:
            if component is not None and 0 <= component < scalars.shape[1]:
                return scalars[:, component]
            return np.linalg.norm(scalars, axis=1)
        return scalars
