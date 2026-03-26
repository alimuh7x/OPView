"""
Helpers for the Initializations Explorer tab.
"""

from __future__ import annotations

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
