"""
Generate Sample VTI Files for Testing
Creates synthetic 2D and 3D VTK ImageData files
"""
import numpy as np
import pyvista as pv


def generate_3d_vti(filename='sample_3d.vti', nx=50, ny=40, nz=30):
    """
    Generate 3D VTI file with synthetic scalar field

    Args:
        filename (str): Output filename
        nx, ny, nz (int): Grid dimensions
    """
    # Create coordinate arrays
    x = np.linspace(0, 10, nx)
    y = np.linspace(0, 8, ny)
    z = np.linspace(0, 6, nz)

    # Create meshgrid
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    # Create synthetic scalar field (combination of sinusoids and exponentials)
    scalar_field = (
        np.sin(X * 0.5) * np.cos(Y * 0.7) * np.exp(-0.1 * Z) +
        0.3 * np.sin(2 * X) * np.sin(2 * Y) +
        0.2 * np.exp(-((X - 5)**2 + (Y - 4)**2 + (Z - 3)**2) / 10)
    )

    # Add some noise
    scalar_field += 0.05 * np.random.randn(*scalar_field.shape)

    # Create PyVista ImageData
    grid = pv.ImageData()
    grid.dimensions = (nx, ny, nz)
    grid.origin = (0, 0, 0)
    grid.spacing = (
        10.0 / (nx - 1) if nx > 1 else 1.0,
        8.0 / (ny - 1) if ny > 1 else 1.0,
        6.0 / (nz - 1) if nz > 1 else 1.0
    )

    # Add scalar field
    grid.point_data['temperature'] = scalar_field.flatten(order='F')

    # Save to file
    grid.save(filename)
    print(f"Generated 3D VTI file: {filename}")
    print(f"  Dimensions: {nx} x {ny} x {nz}")
    print(f"  Scalar range: [{scalar_field.min():.3f}, {scalar_field.max():.3f}]")


def generate_2d_vti(filename='sample_2d.vti', nx=100, ny=80):
    """
    Generate 2D VTI file with synthetic scalar field

    Args:
        filename (str): Output filename
        nx, ny (int): Grid dimensions
    """
    # Create coordinate arrays
    x = np.linspace(0, 10, nx)
    y = np.linspace(0, 8, ny)

    # Create meshgrid
    X, Y = np.meshgrid(x, y, indexing='ij')

    # Create synthetic scalar field (wave patterns and gradients)
    scalar_field = (
        np.sin(X * 0.8) * np.cos(Y * 0.6) +
        0.5 * np.sin(2 * X + Y) +
        0.3 * np.exp(-((X - 5)**2 + (Y - 4)**2) / 5)
    )

    # Add gradient
    scalar_field += 0.2 * X + 0.1 * Y

    # Add noise
    scalar_field += 0.03 * np.random.randn(*scalar_field.shape)

    # Create PyVista ImageData (set Z dimension to 1)
    grid = pv.ImageData()
    grid.dimensions = (nx, ny, 1)
    grid.origin = (0, 0, 0)
    grid.spacing = (
        10.0 / (nx - 1) if nx > 1 else 1.0,
        8.0 / (ny - 1) if ny > 1 else 1.0,
        1.0
    )

    # Add scalar field
    grid.point_data['pressure'] = scalar_field.flatten(order='F')

    # Save to file
    grid.save(filename)
    print(f"Generated 2D VTI file: {filename}")
    print(f"  Dimensions: {nx} x {ny}")
    print(f"  Scalar range: [{scalar_field.min():.3f}, {scalar_field.max():.3f}]")


def generate_phase_field_vti(filename='phase_field.vti', nx=60, ny=50, nz=40):
    """
    Generate phase field simulation data (relevant for materials science)

    Args:
        filename (str): Output filename
        nx, ny, nz (int): Grid dimensions
    """
    # Create coordinate arrays
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    z = np.linspace(0, 1, nz)

    # Create meshgrid
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    # Simulate phase field with multiple grains
    phase = np.zeros_like(X)

    # Add multiple circular/spherical grains
    centers = [
        (0.25, 0.25, 0.25),
        (0.75, 0.25, 0.75),
        (0.25, 0.75, 0.75),
        (0.75, 0.75, 0.25),
        (0.5, 0.5, 0.5)
    ]

    for i, (cx, cy, cz) in enumerate(centers):
        dist = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        phase += (i + 1) * np.exp(-50 * dist**2)

    # Normalize
    phase = phase / phase.max()

    # Add interface sharpening
    phase = np.tanh(10 * (phase - 0.3))

    # Create PyVista ImageData
    grid = pv.ImageData()
    grid.dimensions = (nx, ny, nz)
    grid.origin = (0, 0, 0)
    grid.spacing = (1.0 / (nx - 1), 1.0 / (ny - 1), 1.0 / (nz - 1))

    # Add phase field
    grid.point_data['phase'] = phase.flatten(order='F')

    # Save to file
    grid.save(filename)
    print(f"Generated phase field VTI file: {filename}")
    print(f"  Dimensions: {nx} x {ny} x {nz}")
    print(f"  Phase range: [{phase.min():.3f}, {phase.max():.3f}]")


if __name__ == '__main__':
    import os

    # Ensure sample_data directory exists
    os.makedirs('sample_data', exist_ok=True)

    # Generate test files
    generate_3d_vti('sample_data/sample_3d.vti', nx=50, ny=40, nz=30)
    generate_2d_vti('sample_data/sample_2d.vti', nx=100, ny=80)
    generate_phase_field_vti('sample_data/phase_field.vti', nx=60, ny=50, nz=40)

    print("\nAll sample VTI files generated successfully!")
    print("Files created in 'sample_data/' directory")
