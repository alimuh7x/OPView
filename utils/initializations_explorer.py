"""
Helpers for the Initializations Explorer tab.
"""

from __future__ import annotations

import math
from random import Random
from time import time


def _effective_origin(offset: tuple[int, int], spacing: tuple[int, int], nx: int, ny: int) -> tuple[int, int]:
    distx = offset[0] if offset[0] < nx and spacing[0] < nx else 0
    disty = offset[1] if offset[1] < ny and spacing[1] < ny else 0
    return distx, disty


def _randint_deviation(rng: Random, deviation: int) -> int:
    if deviation <= 0:
        return 0
    return rng.randrange(2 * deviation) - deviation


def simulate_quasi_random_nuclei_2d(
    *,
    nx: int,
    ny: int,
    offset: tuple[int, int],
    spacing: tuple[int, int],
    deviation: tuple[int, int],
    threshold: float,
    seed: int,
) -> dict:
    """
    Simulate the 2D analogue of OpenPhase QuasiRandomNuclei.

    Returns a structure that is easy to consume from both unit tests and Dash UI code.
    """
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    spacing_x = max(1, int(spacing[0]))
    spacing_y = max(1, int(spacing[1]))
    deviation_x = max(0, int(deviation[0]))
    deviation_y = max(0, int(deviation[1]))
    threshold = max(0.0, min(1.0, float(threshold)))

    if seed == -1:
        seed = int(time())

    rng = Random(seed)
    origin = _effective_origin((int(offset[0]), int(offset[1])), (spacing_x, spacing_y), nx, ny)

    candidates = []
    final_points = []
    accepted_count = 0
    rejected_out_of_bounds_count = 0

    for i in range(origin[0], nx, spacing_x):
        for j in range(origin[1], ny, spacing_y):
            candidates.append({"x": i, "y": j})
            chance = rng.random()
            if chance > threshold:
                di = 0 if spacing_x >= nx or deviation_x == 0 else _randint_deviation(rng, deviation_x)
                dj = 0 if spacing_y >= ny or deviation_y == 0 else _randint_deviation(rng, deviation_y)
                accepted_count += 1

                if 0 <= i + di < nx and 0 <= j + dj < ny:
                    final_points.append(
                        {
                            "x": i + di,
                            "y": j + dj,
                            "base_x": i,
                            "base_y": j,
                            "dx": di,
                            "dy": dj,
                        }
                    )
                else:
                    rejected_out_of_bounds_count += 1

    return {
        "nx": nx,
        "ny": ny,
        "origin": origin,
        "spacing": (spacing_x, spacing_y),
        "deviation": (deviation_x, deviation_y),
        "threshold": threshold,
        "seed": seed,
        "candidate_points": candidates,
        "candidate_count": len(candidates),
        "accepted_count": accepted_count,
        "rejected_out_of_bounds_count": rejected_out_of_bounds_count,
        "final_points": final_points,
        "final_count": len(final_points),
    }


def build_quasi_random_summary(data: dict) -> str:
    """Return a short plain-language explanation of the current settings."""
    spacing_x, spacing_y = data["spacing"]
    deviation_x, deviation_y = data["deviation"]
    origin_x, origin_y = data["origin"]
    threshold_pct = int(round(data["threshold"] * 100))
    return (
        f"The candidate lattice starts at ({origin_x}, {origin_y}) and steps by "
        f"({spacing_x}, {spacing_y}). A higher threshold keeps fewer nuclei, and the current "
        f"threshold filters out roughly the lower {threshold_pct}% of random chances. "
        f"Deviation allows each accepted nucleus to shift by up to ±{deviation_x} in x and "
        f"±{deviation_y} in y before boundary checks remove out-of-domain points."
    )


def _normalized_vector_2d(orientation: tuple[float, float]) -> tuple[float, float]:
    ox = float(orientation[0])
    oy = float(orientation[1])
    length = math.hypot(ox, oy)
    if length == 0:
        return 0.0, 1.0
    return ox / length, oy / length


def _empty_grid(nx: int, ny: int, value: float = 0.0) -> list[list[float]]:
    return [[float(value) for _ in range(nx)] for _ in range(ny)]


def simulate_layer_2d(
    *,
    nx: int,
    ny: int,
    position: tuple[float, float],
    orientation: tuple[float, float],
    thickness: float,
) -> dict:
    """Simulate the 2D analogue of Layer as a sharp band around a line."""
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    thickness = max(0.0, float(thickness))
    normal = _normalized_vector_2d(orientation)
    field = _empty_grid(nx, ny)

    for j in range(ny):
        for i in range(nx):
            distance = abs((float(i) - position[0]) * normal[0] + (float(j) - position[1]) * normal[1])
            field[j][i] = 1.0 if distance <= 0.5 * thickness else 0.0

    return {
        "nx": nx,
        "ny": ny,
        "field": field,
        "position": (float(position[0]), float(position[1])),
        "orientation": normal,
        "thickness": thickness,
    }


def simulate_fractional_2d(*, nx: int, ny: int, minority_layer_thickness: float) -> dict:
    """Simulate the 2D analogue of Fractional using y as the layering direction."""
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    offset = float(minority_layer_thickness)
    majority = _empty_grid(nx, ny)
    minority = _empty_grid(nx, ny)
    phase_map = [[0 for _ in range(nx)] for _ in range(ny)]

    for j in range(ny):
        for i in range(nx):
            y = float(j)
            if y > offset:
                major, minor, label = 1.0, 0.0, 1
            else:
                major, minor, label = 0.0, 1.0, 0
            majority[j][i] = major
            minority[j][i] = minor
            phase_map[j][i] = label

    return {
        "nx": nx,
        "ny": ny,
        "offset": offset,
        "majority": majority,
        "minority": minority,
        "phase_map": phase_map,
    }


def simulate_three_fractionals_2d(
    *,
    nx: int,
    ny: int,
    majority_phase_layer_thickness: float,
    minority_phase_layer_thickness1: float,
) -> dict:
    """Simulate the 2D analogue of ThreeFractionals using y as the layering direction."""
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    offset1 = float(majority_phase_layer_thickness)
    offset2 = float(minority_phase_layer_thickness1)
    interface2 = offset1 + offset2
    phase1 = _empty_grid(nx, ny)
    phase2 = _empty_grid(nx, ny)
    phase3 = _empty_grid(nx, ny)
    phase_map = [[0 for _ in range(nx)] for _ in range(ny)]

    for j in range(ny):
        for i in range(nx):
            y = float(j)
            if y < offset1:
                p1, p2, p3, label = 1.0, 0.0, 0.0, 0
            elif y < interface2:
                p1, p2, p3, label = 0.0, 1.0, 0.0, 1
            else:
                p1, p2, p3, label = 0.0, 0.0, 1.0, 2
            phase1[j][i] = p1
            phase2[j][i] = p2
            phase3[j][i] = p3
            phase_map[j][i] = label

    return {
        "nx": nx,
        "ny": ny,
        "offset1": offset1,
        "offset2": offset2,
        "phase1": phase1,
        "phase2": phase2,
        "phase3": phase3,
        "phase_map": phase_map,
    }


def build_layer_summary(data: dict) -> str:
    px, py = data["position"]
    ox, oy = data["orientation"]
    return (
        f"The layer is centered around point ({px:.1f}, {py:.1f}) with normalized orientation "
        f"({ox:.2f}, {oy:.2f}). Thickness controls the full band width, and this explorer "
        f"shows a sharp single-phase band with no diffuse interface."
    )


def build_fractional_summary(data: dict) -> str:
    return (
        f"The minority phase occupies the lower part of the domain up to y ≈ {data['offset']:.1f}, "
        f"and the majority phase fills the region above it. The explorer shows a sharp two-phase split "
        f"so the layer thickness is easier to understand."
    )


def build_three_fractionals_summary(data: dict) -> str:
    interface2 = data["offset1"] + data["offset2"]
    return (
        f"The first interface sits near y ≈ {data['offset1']:.1f}, and the second near y ≈ {interface2:.1f}. "
        f"The three colored regions represent three different phases with sharp boundaries between them."
    )


def _phase_grid(nx: int, ny: int, phase_id: int = 0) -> list[list[int]]:
    return [[int(phase_id) for _ in range(nx)] for _ in range(ny)]


def _payload(
    *,
    nx: int,
    ny: int,
    phase_map: list[list[int]],
    phase_labels: dict[int, str],
    phase_colors: dict[int, str],
    summary: str,
    stats: list[tuple[str, str]],
    markers: list[dict] | None = None,
    boundary_points: list[tuple[int, int]] | None = None,
) -> dict:
    return {
        "nx": nx,
        "ny": ny,
        "phase_map": phase_map,
        "phase_labels": phase_labels,
        "phase_colors": phase_colors,
        "summary": summary,
        "stats": stats,
        "markers": markers or [],
        "boundary_points": boundary_points or [],
    }


def simulate_single_2d(*, nx: int, ny: int) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=_phase_grid(nx, ny, 0),
        phase_labels={0: "phase"},
        phase_colors={0: "#2563eb"},
        summary="Single fills the whole domain with one phase.",
        stats=[("Phase count", "1")],
    )


def simulate_sectional_plane_2d(
    *,
    nx: int,
    ny: int,
    point: tuple[float, float],
    orientation: tuple[float, float],
) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    normal = _normalized_vector_2d(orientation)
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            distance = (float(i) - point[0]) * normal[0] + (float(j) - point[1]) * normal[1]
            if distance < 0.0:
                phase_map[j][i] = 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "sectioned phase"},
        phase_colors={0: "#f8fafc", 1: "#2563eb"},
        summary=(
            f"SectionalPlane places the phase on the negative side of a plane through ({point[0]:.1f}, {point[1]:.1f}) "
            f"with normal ({normal[0]:.2f}, {normal[1]:.2f})."
        ),
        stats=[("Phase count", "1"), ("Point", f"{point[0]:.1f}, {point[1]:.1f}")],
    )


def simulate_two_walls_2d(*, nx: int, ny: int, walls_thickness: float) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    thickness = max(0.0, float(walls_thickness))
    phase_map = _phase_grid(nx, ny, 1)
    for j in range(ny):
        if j <= thickness or j >= ny - 1 - thickness:
            for i in range(nx):
                phase_map[j][i] = 0
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "walls", 1: "channel"},
        phase_colors={0: "#475569", 1: "#fde68a"},
        summary="TwoWalls creates the same wall phase at the bottom and top, with a different channel phase in the middle.",
        stats=[("Phase count", "2"), ("Wall thickness", f"{thickness:.1f}")],
    )


def simulate_two_different_walls_2d(*, nx: int, ny: int, walls_thickness: float) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    thickness = max(0.0, float(walls_thickness))
    phase_map = _phase_grid(nx, ny, 1)
    for j in range(ny):
        if j <= thickness:
            for i in range(nx):
                phase_map[j][i] = 0
        elif j >= ny - 1 - thickness:
            for i in range(nx):
                phase_map[j][i] = 2
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "wall 1", 1: "channel", 2: "wall 2"},
        phase_colors={0: "#60a5fa", 1: "#fde68a", 2: "#10b981"},
        summary="TwoDifferentWalls creates two wall layers with different phases on the two sides of the channel.",
        stats=[("Phase count", "3"), ("Wall thickness", f"{thickness:.1f}")],
    )


def simulate_sphere_2d(*, nx: int, ny: int, center: tuple[float, float], radius: float) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    radius = max(0.0, float(radius))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            if math.hypot(float(i) - center[0], float(j) - center[1]) <= radius:
                phase_map[j][i] = 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "sphere phase"},
        phase_colors={0: "#f8fafc", 1: "#2563eb"},
        summary=f"Sphere places one circular phase with radius {radius:.1f} around ({center[0]:.1f}, {center[1]:.1f}).",
        stats=[("Phase count", "1"), ("Radius", f"{radius:.1f}")],
    )


def simulate_sphere_in_grain_2d(*, nx: int, ny: int, center: tuple[float, float], radius: float) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    radius = max(0.0, float(radius))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            if math.hypot(float(i) - center[0], float(j) - center[1]) <= radius:
                phase_map[j][i] = 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "parent phase", 1: "inner sphere phase"},
        phase_colors={0: "#fde68a", 1: "#2563eb"},
        summary="SphereInGrain replaces a circular part of the parent phase by a different inner phase.",
        stats=[("Phase count", "2"), ("Radius", f"{radius:.1f}")],
    )


def simulate_ellipsoid_2d(*, nx: int, ny: int, center: tuple[float, float], radius_x: float, radius_y: float) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    radius_x = max(0.1, float(radius_x))
    radius_y = max(0.1, float(radius_y))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            dx = (float(i) - center[0]) / radius_x
            dy = (float(j) - center[1]) / radius_y
            if dx * dx + dy * dy <= 1.0:
                phase_map[j][i] = 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "ellipsoid phase"},
        phase_colors={0: "#f8fafc", 1: "#2563eb"},
        summary="Ellipsoid creates one elliptical phase region with independent x and y radii.",
        stats=[("Phase count", "1"), ("Radii", f"{radius_x:.1f}, {radius_y:.1f}")],
    )


def simulate_rectangular_2d(
    *,
    nx: int,
    ny: int,
    center: tuple[float, float],
    size_x: float,
    size_y: float,
    angle_deg: float,
) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    size_x = max(0.0, float(size_x))
    size_y = max(0.0, float(size_y))
    angle = math.radians(float(angle_deg))
    ca = math.cos(angle)
    sa = math.sin(angle)
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            dx = float(i) - center[0]
            dy = float(j) - center[1]
            xr = ca * dx + sa * dy
            yr = -sa * dx + ca * dy
            if abs(xr) <= size_x / 2.0 and abs(yr) <= size_y / 2.0:
                phase_map[j][i] = 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "rectangular phase"},
        phase_colors={0: "#f8fafc", 1: "#2563eb"},
        summary="Rectangular creates a rectangular grain; the angle slider lets you understand the rotated overload visually.",
        stats=[("Phase count", "1"), ("Angle", f"{angle_deg:.1f}°")],
    )


def simulate_cylinder_2d(
    *,
    nx: int,
    ny: int,
    center: tuple[float, float],
    radius: float,
    length: float,
    axis: int,
) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    radius = max(0.0, float(radius))
    length = max(0.0, float(length))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            dx = float(i) - center[0]
            dy = float(j) - center[1]
            inside = False
            if axis == 2:
                inside = math.hypot(dx, dy) <= radius
            elif axis == 0:
                inside = abs(dx) <= length / 2.0 and abs(dy) <= radius
            else:
                inside = abs(dy) <= length / 2.0 and abs(dx) <= radius
            if inside:
                phase_map[j][i] = 1
    axis_name = {0: "x", 1: "y", 2: "z"}[axis]
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "cylinder phase"},
        phase_colors={0: "#f8fafc", 1: "#2563eb"},
        summary=f"Cylinder is shown in 2D as a stripe when its axis lies in-plane, and as a circle when the axis is out-of-plane ({axis_name}).",
        stats=[("Phase count", "1"), ("Axis", axis_name.upper())],
    )


def simulate_paraboloid_2d(*, nx: int, ny: int, center: tuple[float, float], radius: float) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    radius = max(1.0, float(radius))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            x = float(i) - center[0]
            y = float(j) - center[1]
            profile = (x * x) / max(radius, 1.0) - radius / 2.0
            if y >= profile:
                phase_map[j][i] = 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "paraboloid phase"},
        phase_colors={0: "#f8fafc", 1: "#2563eb"},
        summary="Paraboloid is shown in 2D as a parabolic front so you can see how the curved initialization grows with radius.",
        stats=[("Phase count", "1"), ("Radius", f"{radius:.1f}")],
    )


def simulate_quasi_random_spheres_2d(
    *,
    nx: int,
    ny: int,
    dist: int,
    radius1: float,
    radius2: float,
    probability_phase1: float,
    offset: int,
    seed: int,
) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    dist = max(1, int(dist))
    radius1 = max(0.0, float(radius1))
    radius2 = max(0.0, float(radius2))
    probability_phase1 = max(0.0, min(1.0, float(probability_phase1)))
    offset = max(0, int(offset))
    rng = Random(int(time()) if seed == -1 else seed)
    phase_map = _phase_grid(nx, ny, 0)
    markers = []
    threshold = 0.05
    for base_x in range(dist if dist < nx else 0, nx, 2 * dist):
        for base_y in range(dist if dist < ny else 0, ny, 2 * dist):
            if rng.random() <= threshold:
                continue
            dx = 0 if offset == 0 else rng.randrange(2 * offset) - offset
            dy = 0 if offset == 0 else rng.randrange(2 * offset) - offset
            cx = base_x + dx
            cy = base_y + dy
            if cx < 0 or cx >= nx or cy < 0 or cy >= ny:
                continue
            phase_id = 1 if rng.random() < probability_phase1 else 2
            radius = radius1 if phase_id == 1 else radius2
            for j in range(ny):
                for i in range(nx):
                    if math.hypot(float(i) - cx, float(j) - cy) <= radius:
                        phase_map[j][i] = phase_id
            markers.append({"x": cx, "y": cy, "color": "#0f172a", "size": 6, "label": f"seed {phase_id}"})
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "phase 1 spheres", 2: "phase 2 spheres"},
        phase_colors={0: "#f8fafc", 1: "#2563eb", 2: "#f59e0b"},
        summary="QuasiRandomSpheres places circles on a coarse lattice, jitters them by offset, then chooses between two phases using the phase-1 probability.",
        stats=[("Phase count", "2"), ("Placed spheres", str(len(markers)))],
        markers=markers,
    )


def simulate_random_nuclei_2d(*, nx: int, ny: int, n_particles: int, on_plane: str, seed: int) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    n_particles = max(0, int(n_particles))
    rng = Random(int(time()) if seed == -1 else seed)
    markers = []
    used = set()
    for _ in range(n_particles):
        for _try in range(500):
            if on_plane == "Xbottom":
                x, y = 0, rng.randrange(ny)
            elif on_plane == "Xtop":
                x, y = nx - 1, rng.randrange(ny)
            elif on_plane == "Ybottom":
                x, y = rng.randrange(nx), 0
            elif on_plane == "Ytop":
                x, y = rng.randrange(nx), ny - 1
            else:
                x, y = rng.randrange(nx), rng.randrange(ny)
            if (x, y) not in used:
                used.add((x, y))
                markers.append({"x": x, "y": y, "color": "#2563eb", "size": 10, "label": "nucleus"})
                break
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=_phase_grid(nx, ny, 0),
        phase_labels={0: "background"},
        phase_colors={0: "#f8fafc"},
        summary=f"RandomNuclei plants isolated nuclei at random positions{'' if on_plane == 'none' else f' constrained to {on_plane}'}.",
        stats=[("Phase count", "1"), ("Nuclei", str(len(markers)))],
        markers=markers,
    )


def simulate_triple_junction_2d(*, nx: int, ny: int) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    phase_map = _phase_grid(nx, ny, 0)
    cx = nx / 2.0
    cy = ny / 2.0
    for j in range(ny):
        for i in range(nx):
            angle = math.atan2(float(j) - cy, float(i) - cx)
            if angle < -math.pi / 3:
                phase_map[j][i] = 0
            elif angle < math.pi / 3:
                phase_map[j][i] = 1
            else:
                phase_map[j][i] = 2
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "phase 1", 1: "phase 2", 2: "phase 3"},
        phase_colors={0: "#60a5fa", 1: "#f59e0b", 2: "#10b981"},
        summary="TripleJunction shows three phase wedges meeting at one point.",
        stats=[("Phase count", "3")],
    )


def simulate_young3_2d(*, nx: int, ny: int) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            if i < nx / 3:
                phase_map[j][i] = 1
            elif i < 2 * nx / 3:
                phase_map[j][i] = 2
            else:
                phase_map[j][i] = 3
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={1: "alpha", 2: "beta", 3: "gamma"},
        phase_colors={1: "#60a5fa", 2: "#f59e0b", 3: "#10b981"},
        summary="Young3 is shown as three neighboring regions meeting along vertical interfaces, which is the 2D teaching analogue of the 3D setup.",
        stats=[("Phase count", "3")],
    )


def simulate_young4_2d(*, nx: int, ny: int) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            if i < nx / 2 and j < ny / 2:
                phase_map[j][i] = 1
            elif i >= nx / 2 and j < ny / 2:
                phase_map[j][i] = 2
            elif i < nx / 2:
                phase_map[j][i] = 3
            else:
                phase_map[j][i] = 4
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={1: "alpha", 2: "beta", 3: "gamma", 4: "delta"},
        phase_colors={1: "#60a5fa", 2: "#f59e0b", 3: "#10b981", 4: "#a855f7"},
        summary="Young4 is shown as four meeting regions so the four-phase topology is easy to inspect.",
        stats=[("Phase count", "4")],
    )


def simulate_young4_periodic_2d(*, nx: int, ny: int) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            phase_map[j][i] = (i // max(1, nx // 4) + j // max(1, ny // 2)) % 4 + 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={1: "phase 1", 2: "phase 2", 3: "phase 3", 4: "phase 4"},
        phase_colors={1: "#60a5fa", 2: "#f59e0b", 3: "#10b981", 4: "#a855f7"},
        summary="Young4Periodic is shown as a repeating four-phase arrangement to emphasize the periodic construction.",
        stats=[("Phase count", "4")],
    )


def simulate_thermal_grooving_2d(*, nx: int, ny: int, groove_width: float, groove_depth: float) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    groove_width = max(1.0, float(groove_width))
    groove_depth = max(1.0, float(groove_depth))
    phase_map = _phase_grid(nx, ny, 1)
    cx = nx / 2.0
    for j in range(ny):
        for i in range(nx):
            if j <= groove_depth and abs(float(i) - cx) <= groove_width / 2.0:
                phase_map[j][i] = 0
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "groove phase", 1: "matrix phase"},
        phase_colors={0: "#2563eb", 1: "#f59e0b"},
        summary="ThermalGrooving is shown as a groove-like pocket of one phase cut into another phase near the boundary.",
        stats=[("Phase count", "2"), ("Groove width", f"{groove_width:.1f}")],
    )


def simulate_voronoi_tessellation_2d(*, nx: int, ny: int, ngrains: int, seed: int) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    ngrains = max(1, int(ngrains))
    rng = Random(seed)
    seeds = []
    used = set()
    while len(seeds) < ngrains:
        point = (rng.randrange(nx), rng.randrange(ny))
        if point not in used:
            used.add(point)
            seeds.append(point)
    region_map = _phase_grid(nx, ny, 0)
    boundary_points = []
    for j in range(ny):
        for i in range(nx):
            region_map[j][i] = min(range(len(seeds)), key=lambda idx: (i - seeds[idx][0]) ** 2 + (j - seeds[idx][1]) ** 2)
    for j in range(ny):
        for i in range(nx):
            current = region_map[j][i]
            for di, dj in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                ii = i + di
                jj = j + dj
                if 0 <= ii < nx and 0 <= jj < ny and region_map[jj][ii] != current:
                    boundary_points.append((i, j))
                    break
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=_phase_grid(nx, ny, 0),
        phase_labels={0: "single phase"},
        phase_colors={0: "#dbeafe"},
        summary="VoronoiTessellation uses one thermodynamic phase but many grains; the fill stays one color and the black boundary overlay shows the grain network.",
        stats=[("Phase count", "1"), ("Grains", str(len(seeds)))],
        markers=[{"x": x, "y": y, "color": "#1f2937", "size": 7, "label": "seed"} for x, y in seeds],
        boundary_points=boundary_points,
    )


def simulate_blobby_auto_2d(
    *,
    nx: int,
    ny: int,
    center: tuple[float, float],
    base_radius: float,
    max_amplitude: float,
    num_bumps: int,
    seed: int,
) -> dict:
    nx = max(1, int(nx))
    ny = max(1, int(ny))
    base_radius = max(1.0, float(base_radius))
    max_amplitude = max(0.0, float(max_amplitude))
    num_bumps = max(1, int(num_bumps))
    rng = Random(seed)
    amplitudes = [rng.uniform(0.0, max_amplitude) / math.sqrt(k + 1) for k in range(num_bumps)]
    freqs = [rng.randint(2, 8) for _ in range(num_bumps)]
    phases = [rng.uniform(0.0, 2.0 * math.pi) for _ in range(num_bumps)]
    phase_map = _phase_grid(nx, ny, 0)
    for j in range(ny):
        for i in range(nx):
            dx = float(i) - center[0]
            dy = float(j) - center[1]
            angle = math.atan2(dy, dx)
            shape_radius = base_radius
            for amp, freq, phase in zip(amplitudes, freqs, phases):
                shape_radius += amp * math.sin(freq * angle + phase)
            if math.hypot(dx, dy) <= max(1.0, shape_radius):
                phase_map[j][i] = 1
    return _payload(
        nx=nx,
        ny=ny,
        phase_map=phase_map,
        phase_labels={0: "background", 1: "blobby phase"},
        phase_colors={0: "#f8fafc", 1: "#2563eb"},
        summary="BlobbyAuto perturbs a circular seed with sinusoidal bumps so you can explore how amplitude and bump count change the shape.",
        stats=[("Phase count", "1"), ("Bumps", str(num_bumps))],
    )
