"""
UI for the Initializations Explorer tab.
"""

from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from utils.initializations_explorer import (
    build_fractional_summary,
    build_layer_summary,
    build_quasi_random_summary,
    build_three_fractionals_summary,
    simulate_blobby_auto_2d,
    simulate_cylinder_2d,
    simulate_ellipsoid_2d,
    simulate_fractional_2d,
    simulate_layer_2d,
    simulate_paraboloid_2d,
    simulate_quasi_random_nuclei_2d,
    simulate_quasi_random_spheres_2d,
    simulate_random_nuclei_2d,
    simulate_rectangular_2d,
    simulate_sectional_plane_2d,
    simulate_single_2d,
    simulate_sphere_2d,
    simulate_sphere_in_grain_2d,
    simulate_thermal_grooving_2d,
    simulate_three_fractionals_2d,
    simulate_triple_junction_2d,
    simulate_two_different_walls_2d,
    simulate_two_walls_2d,
    simulate_voronoi_tessellation_2d,
    simulate_young3_2d,
    simulate_young4_2d,
    simulate_young4_periodic_2d,
)


PANEL_STYLE = {
    "background": "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
    "border": "1px solid #dbe3ef",
    "borderRadius": "16px",
    "boxShadow": "0 10px 28px rgba(15, 23, 42, 0.06)",
    "padding": "16px 18px",
}

SECTION_TITLE_STYLE = {
    "fontSize": "14px",
    "fontWeight": "700",
    "letterSpacing": "0.04em",
    "textTransform": "uppercase",
    "color": "#355070",
    "marginBottom": "10px",
}

METHOD_OPTIONS = sorted([
    {"label": "QuasiRandomNuclei", "value": "quasi-random-nuclei"},
    {"label": "QuasiRandomSpheres", "value": "quasi-random-spheres"},
    {"label": "RandomNuclei", "value": "random-nuclei"},
    {"label": "Single", "value": "single"},
    {"label": "SectionalPlane", "value": "sectional-plane"},
    {"label": "Layer", "value": "layer"},
    {"label": "Fractional", "value": "fractional"},
    {"label": "ThreeFractionals", "value": "three-fractionals"},
    {"label": "TwoWalls", "value": "two-walls"},
    {"label": "TwoDifferentWalls", "value": "two-different-walls"},
    {"label": "Sphere", "value": "sphere"},
    {"label": "SphereInGrain", "value": "sphere-in-grain"},
    {"label": "Ellipsoid", "value": "ellipsoid"},
    {"label": "Rectangular", "value": "rectangular"},
    {"label": "Cylinder", "value": "cylinder"},
    {"label": "Paraboloid", "value": "paraboloid"},
    {"label": "ThermalGrooving", "value": "thermal-grooving"},
    {"label": "TripleJunction", "value": "triple-junction"},
    {"label": "Young3", "value": "young3"},
    {"label": "Young4", "value": "young4"},
    {"label": "Young4Periodic", "value": "young4-periodic"},
    {"label": "VoronoiTessellation", "value": "voronoi-tessellation"},
    {"label": "BlobbyAuto", "value": "blobby-auto"},
], key=lambda item: item["label"].lower())


def _axis_tick_step(size: int) -> int:
    if size <= 12:
        return 1
    if size <= 24:
        return 2
    if size <= 40:
        return 5
    if size <= 80:
        return 10
    return 20


def default_quasi_random_settings() -> dict:
    return {
        "method": "quasi-random-nuclei",
        "nx": 50,
        "ny": 50,
        "offset_x": 0,
        "offset_y": 0,
        "spacing_x": 5,
        "spacing_y": 5,
        "deviation_x": 0,
        "deviation_y": 0,
        "threshold": 0.0,
        "seed": 1,
    }


def default_quasi_random_spheres_settings() -> dict:
    return {"method": "quasi-random-spheres", "nx": 50, "ny": 50, "dist": 8, "radius1": 3.0, "radius2": 2.0, "probability1": 0.5, "offset": 2, "seed": 1}


def default_random_nuclei_settings() -> dict:
    return {"method": "random-nuclei", "nx": 50, "ny": 50, "n_particles": 20, "on_plane": "none", "seed": 1}


def default_single_settings() -> dict:
    return {"method": "single", "nx": 50, "ny": 50}


def default_sectional_plane_settings() -> dict:
    return {"method": "sectional-plane", "nx": 50, "ny": 50, "point_x": 25.0, "point_y": 25.0, "orientation_x": 0.0, "orientation_y": 1.0}


def default_layer_settings() -> dict:
    return {"method": "layer", "nx": 50, "ny": 50, "point_x": 25.0, "point_y": 25.0, "orientation_x": 0.0, "orientation_y": 1.0, "thickness": 12.0}


def default_fractional_settings() -> dict:
    return {"method": "fractional", "nx": 50, "ny": 50, "minority_thickness": 15.0}


def default_three_fractionals_settings() -> dict:
    return {"method": "three-fractionals", "nx": 50, "ny": 50, "majority_thickness": 14.0, "minority1_thickness": 14.0}


def default_two_walls_settings() -> dict:
    return {"method": "two-walls", "nx": 50, "ny": 50, "walls_thickness": 6.0}


def default_two_different_walls_settings() -> dict:
    return {"method": "two-different-walls", "nx": 50, "ny": 50, "walls_thickness": 6.0}


def default_sphere_settings() -> dict:
    return {"method": "sphere", "nx": 50, "ny": 50, "center_x": 25.0, "center_y": 25.0, "radius": 10.0}


def default_sphere_in_grain_settings() -> dict:
    return {"method": "sphere-in-grain", "nx": 50, "ny": 50, "center_x": 25.0, "center_y": 25.0, "radius": 10.0}


def default_ellipsoid_settings() -> dict:
    return {"method": "ellipsoid", "nx": 50, "ny": 50, "center_x": 25.0, "center_y": 25.0, "radius_x": 12.0, "radius_y": 8.0}


def default_rectangular_settings() -> dict:
    return {"method": "rectangular", "nx": 50, "ny": 50, "center_x": 25.0, "center_y": 25.0, "size_x": 18.0, "size_y": 12.0, "angle_deg": 0.0}


def default_cylinder_settings() -> dict:
    return {"method": "cylinder", "nx": 50, "ny": 50, "center_x": 25.0, "center_y": 25.0, "radius": 6.0, "length": 24.0, "axis": 2}


def default_paraboloid_settings() -> dict:
    return {"method": "paraboloid", "nx": 50, "ny": 50, "center_x": 25.0, "center_y": 12.0, "radius": 10.0}


def default_thermal_grooving_settings() -> dict:
    return {"method": "thermal-grooving", "nx": 50, "ny": 50, "groove_width": 12.0, "groove_depth": 8.0}


def default_voronoi_settings() -> dict:
    return {"method": "voronoi-tessellation", "nx": 50, "ny": 50, "ngrains": 12, "seed": 1}


def default_blobby_auto_settings() -> dict:
    return {"method": "blobby-auto", "nx": 50, "ny": 50, "center_x": 25.0, "center_y": 25.0, "base_radius": 12.0, "max_amplitude": 4.0, "num_bumps": 5, "seed": 1}


DEFAULTS_BY_METHOD = {
    "quasi-random-nuclei": default_quasi_random_settings,
    "quasi-random-spheres": default_quasi_random_spheres_settings,
    "random-nuclei": default_random_nuclei_settings,
    "single": default_single_settings,
    "sectional-plane": default_sectional_plane_settings,
    "layer": default_layer_settings,
    "fractional": default_fractional_settings,
    "three-fractionals": default_three_fractionals_settings,
    "two-walls": default_two_walls_settings,
    "two-different-walls": default_two_different_walls_settings,
    "sphere": default_sphere_settings,
    "sphere-in-grain": default_sphere_in_grain_settings,
    "ellipsoid": default_ellipsoid_settings,
    "rectangular": default_rectangular_settings,
    "cylinder": default_cylinder_settings,
    "paraboloid": default_paraboloid_settings,
    "thermal-grooving": default_thermal_grooving_settings,
    "triple-junction": default_single_settings,
    "young3": default_single_settings,
    "young4": default_single_settings,
    "young4-periodic": default_single_settings,
    "voronoi-tessellation": default_voronoi_settings,
    "blobby-auto": default_blobby_auto_settings,
}


def _slider_block(component_id: str, label: str, min_value: float, max_value: float, value: float, step: float = 1) -> html.Div:
    return html.Div(
        [
            html.Div(label, style={"fontSize": "13px", "fontWeight": "700", "color": "#4a5568", "marginBottom": "6px"}),
            dcc.Slider(id=component_id, min=min_value, max=max_value, step=step, value=value, tooltip={"placement": "bottom", "always_visible": True}),
        ],
        style={"marginBottom": "18px"},
    )


def _dropdown_block(component_id: str, label: str, options: list[dict], value) -> html.Div:
    return html.Div(
        [
            html.Div(label, style={"fontSize": "13px", "fontWeight": "700", "color": "#4a5568", "marginBottom": "6px"}),
            dcc.Dropdown(id=component_id, options=options, value=value, clearable=False),
        ],
        style={"marginBottom": "18px"},
    )


def _build_stats(items: list[tuple[str, str]]) -> html.Div:
    card_style = {
        "background": "#ffffff",
        "border": "1px solid #dde6f2",
        "borderRadius": "12px",
        "padding": "12px 14px",
        "minWidth": "120px",
    }
    return html.Div(
        [
            html.Div(
                [
                    html.Div(label, style={"fontSize": "12px", "color": "#667085", "marginBottom": "4px"}),
                    html.Div(value, style={"fontSize": "24px", "fontWeight": "800", "color": "#0f2942"}),
                ],
                style=card_style,
            )
            for label, value in items
        ],
        style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
    )


def _base_figure(nx: int, ny: int) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
        height=620,
        plot_bgcolor="#fbfcfe",
        paper_bgcolor="#ffffff",
        showlegend=False,
    )
    figure.update_xaxes(range=[-0.5, nx - 0.5], dtick=_axis_tick_step(nx), gridcolor="rgba(53, 80, 112, 0.10)", zeroline=False, title={"text": "x", "font": {"size": 18}}, tickfont={"size": 16}, constrain="domain")
    figure.update_yaxes(range=[-0.5, ny - 0.5], dtick=_axis_tick_step(ny), gridcolor="rgba(53, 80, 112, 0.10)", zeroline=False, scaleanchor="x", scaleratio=1, title={"text": "y", "font": {"size": 18}}, tickfont={"size": 16})
    figure.add_shape(type="rect", x0=-0.5, y0=-0.5, x1=nx - 0.5, y1=ny - 0.5, line={"color": "#355070", "width": 2})
    return figure


def _discrete_colorscale(colors: list[str]) -> list[list[float | str]]:
    if len(colors) == 1:
        return [[0.0, colors[0]], [1.0, colors[0]]]
    scale: list[list[float | str]] = []
    denom = len(colors) - 1
    for index, color in enumerate(colors):
        start = 0.0 if index == 0 else (index - 0.5) / denom
        end = 1.0 if index == len(colors) - 1 else (index + 0.5) / denom
        scale.append([max(0.0, start), color])
        scale.append([min(1.0, end), color])
    return scale


def _render_payload(data: dict) -> tuple[go.Figure, html.Div, html.Div]:
    figure = _base_figure(data["nx"], data["ny"])
    phase_map = data.get("phase_map")
    if phase_map is not None:
        phase_ids = sorted({value for row in phase_map for value in row})
        local_id = {phase_id: index for index, phase_id in enumerate(phase_ids)}
        z = [[local_id[value] for value in row] for row in phase_map]
        colors = [data["phase_colors"][phase_id] for phase_id in phase_ids]
        ticktext = [data["phase_labels"][phase_id] for phase_id in phase_ids]
        figure.add_trace(
            go.Heatmap(
                z=z,
                zmin=0,
                zmax=max(0, len(phase_ids) - 1),
                colorscale=_discrete_colorscale(colors),
                colorbar={"title": "Phase", "tickvals": list(range(len(phase_ids))), "ticktext": ticktext},
                hovertemplate="x=%{x}, y=%{y}<br>phase=%{z}<extra></extra>",
            )
        )
    if data.get("boundary_points"):
        figure.add_trace(
            go.Scatter(
                x=[x for x, _ in data["boundary_points"]],
                y=[y for _, y in data["boundary_points"]],
                mode="markers",
                marker={"size": 3, "color": "#111827"},
                hoverinfo="skip",
            )
        )
    if data.get("markers"):
        for marker in data["markers"]:
            figure.add_trace(
                go.Scatter(
                    x=[marker["x"]],
                    y=[marker["y"]],
                    mode="markers",
                    marker={"size": marker.get("size", 8), "color": marker.get("color", "#111827"), "line": {"width": 1, "color": "#0f172a"}},
                    hovertemplate=f"{marker.get('label', 'marker')}<br>x=%{{x}}, y=%{{y}}<extra></extra>",
                )
            )
    stats = _build_stats(data["stats"])
    explanation = html.Div(
        [
            html.Div("How to read this", style=SECTION_TITLE_STYLE),
            html.P(data["summary"], style={"margin": 0, "fontSize": "14px", "lineHeight": "1.6", "color": "#4b5563"}),
        ],
        style={**PANEL_STYLE, "marginTop": "14px"},
    )
    return figure, stats, explanation


def build_quasi_random_figure(settings: dict, reroll_count: int = 0) -> tuple[go.Figure, html.Div, html.Div]:
    effective_seed = int(settings["seed"]) + int(reroll_count) * 9973
    data = simulate_quasi_random_nuclei_2d(nx=settings["nx"], ny=settings["ny"], offset=(settings["offset_x"], settings["offset_y"]), spacing=(settings["spacing_x"], settings["spacing_y"]), deviation=(settings["deviation_x"], settings["deviation_y"]), threshold=settings["threshold"], seed=effective_seed)
    figure = _base_figure(settings["nx"], settings["ny"])
    if data["final_points"]:
        figure.add_trace(go.Scatter(x=[point["x"] for point in data["final_points"]], y=[point["y"] for point in data["final_points"]], mode="markers", marker={"size": 11, "color": "#f59e0b", "line": {"width": 1.5, "color": "#9a6700"}}, customdata=[[point["base_x"], point["base_y"], point["dx"], point["dy"]] for point in data["final_points"]], hovertemplate=("Final nucleus<br>x=%{x}, y=%{y}<br>base=(%{customdata[0]}, %{customdata[1]})<br>shift=(%{customdata[2]}, %{customdata[3]})<extra></extra>")))
    stats = _build_stats([("Final nuclei", str(data["final_count"])), ("Effective origin", f"{data['origin'][0]}, {data['origin'][1]}")])
    explanation = html.Div([html.Div("How to read this", style=SECTION_TITLE_STYLE), html.P(build_quasi_random_summary(data), style={"margin": 0, "fontSize": "14px", "lineHeight": "1.6", "color": "#4b5563"})], style={**PANEL_STYLE, "marginTop": "14px"})
    return figure, stats, explanation


def build_layer_figure(settings: dict) -> tuple[go.Figure, html.Div, html.Div]:
    data = simulate_layer_2d(nx=settings["nx"], ny=settings["ny"], position=(settings["point_x"], settings["point_y"]), orientation=(settings["orientation_x"], settings["orientation_y"]), thickness=settings["thickness"])
    payload = {
        "nx": data["nx"],
        "ny": data["ny"],
        "phase_map": [[int(value) for value in row] for row in data["field"]],
        "phase_labels": {0: "background", 1: "layer"},
        "phase_colors": {0: "#f8fafc", 1: "#2563eb"},
        "summary": build_layer_summary(data),
        "stats": [("Thickness", f"{settings['thickness']:.1f}"), ("Phase count", "1")],
    }
    return _render_payload(payload)


def build_fractional_figure(settings: dict) -> tuple[go.Figure, html.Div, html.Div]:
    data = simulate_fractional_2d(nx=settings["nx"], ny=settings["ny"], minority_layer_thickness=settings["minority_thickness"])
    payload = {
        "nx": data["nx"],
        "ny": data["ny"],
        "phase_map": data["phase_map"],
        "phase_labels": {0: "minority", 1: "majority"},
        "phase_colors": {0: "#92400e", 1: "#fde68a"},
        "summary": build_fractional_summary(data),
        "stats": [("Layer thickness", f"{settings['minority_thickness']:.1f}"), ("Phase count", "2")],
    }
    return _render_payload(payload)


def build_three_fractionals_figure(settings: dict) -> tuple[go.Figure, html.Div, html.Div]:
    data = simulate_three_fractionals_2d(nx=settings["nx"], ny=settings["ny"], majority_phase_layer_thickness=settings["majority_thickness"], minority_phase_layer_thickness1=settings["minority1_thickness"])
    payload = {
        "nx": data["nx"],
        "ny": data["ny"],
        "phase_map": data["phase_map"],
        "phase_labels": {0: "phase 1", 1: "phase 2", 2: "phase 3"},
        "phase_colors": {0: "#60a5fa", 1: "#f59e0b", 2: "#10b981"},
        "summary": build_three_fractionals_summary(data),
        "stats": [("Majority thickness", f"{settings['majority_thickness']:.1f}"), ("Minority 1 thickness", f"{settings['minority1_thickness']:.1f}"), ("Phase count", "3")],
    }
    return _render_payload(payload)


def _section_style(is_visible: bool) -> dict:
    return {"display": "block" if is_visible else "none"}


def build_initializations_controls(method: str) -> html.Div:
    quasi = default_quasi_random_settings()
    quasi_spheres = default_quasi_random_spheres_settings()
    random_nuclei = default_random_nuclei_settings()
    section = default_sectional_plane_settings()
    layer = default_layer_settings()
    fractional = default_fractional_settings()
    three = default_three_fractionals_settings()
    walls = default_two_walls_settings()
    sphere = default_sphere_settings()
    ellipsoid = default_ellipsoid_settings()
    rectangular = default_rectangular_settings()
    cylinder = default_cylinder_settings()
    paraboloid = default_paraboloid_settings()
    thermal = default_thermal_grooving_settings()
    voronoi = default_voronoi_settings()
    blobby = default_blobby_auto_settings()

    return html.Div(
        [
            html.Div("Method", style=SECTION_TITLE_STYLE),
            dcc.Dropdown(
                id="initializations-method-selector",
                options=METHOD_OPTIONS,
                value=method,
                clearable=False,
                maxHeight=320,
                optionHeight=38,
                style={"marginBottom": "18px"},
            ),
            html.Div("Domain", style=SECTION_TITLE_STYLE),
            _slider_block("initializations-nx", "Nx", 8, 120, quasi["nx"]),
            _slider_block("initializations-ny", "Ny", 8, 120, quasi["ny"]),
            html.Div(
                [
                    html.Div("Origin / Spacing", style=SECTION_TITLE_STYLE),
                    _slider_block("initializations-offset-x", "offsetX", 0, 60, quasi["offset_x"]),
                    _slider_block("initializations-offset-y", "offsetY", 0, 60, quasi["offset_y"]),
                    _slider_block("initializations-spacing-x", "spacingX", 1, 120, quasi["spacing_x"]),
                    _slider_block("initializations-spacing-y", "spacingY", 1, 120, quasi["spacing_y"]),
                    html.Div("Deviation / Filter", style=SECTION_TITLE_STYLE),
                    _slider_block("initializations-deviation-x", "deviationX", 0, 20, quasi["deviation_x"]),
                    _slider_block("initializations-deviation-y", "deviationY", 0, 20, quasi["deviation_y"]),
                    _slider_block("initializations-threshold", "threshold", 0, 1, quasi["threshold"], step=0.01),
                    _slider_block("initializations-seed", "seed", 1, 200, quasi["seed"]),
                    html.Div([html.Button("Reroll Same Settings", id="initializations-reroll-btn", className="graphs-add-panel-btn", n_clicks=0), html.Button("Regular", id="initializations-preset-regular-btn", className="graphs-add-panel-btn", n_clicks=0, style={"background": "#f8fbff", "color": "#355070"}), html.Button("More Random", id="initializations-preset-random-btn", className="graphs-add-panel-btn", n_clicks=0, style={"background": "#f8fbff", "color": "#355070"})], style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginTop": "8px"}),
                ],
                style=_section_style(method == "quasi-random-nuclei"),
            ),
            html.Div(
                [
                    html.Div("Sphere Lattice", style=SECTION_TITLE_STYLE),
                    _slider_block("initializations-dist-spheres", "dist", 1, 30, quasi_spheres["dist"]),
                    _slider_block("initializations-radius1-spheres", "radius1", 1, 15, quasi_spheres["radius1"], step=0.5),
                    _slider_block("initializations-radius2-spheres", "radius2", 1, 15, quasi_spheres["radius2"], step=0.5),
                    _slider_block("initializations-probability1-spheres", "probabilityPhase1", 0, 1, quasi_spheres["probability1"], step=0.01),
                    _slider_block("initializations-offset-spheres", "offset", 0, 15, quasi_spheres["offset"]),
                    _slider_block("initializations-seed-spheres", "seed", 1, 200, quasi_spheres["seed"]),
                ],
                style=_section_style(method == "quasi-random-spheres"),
            ),
            html.Div(
                [
                    html.Div("RandomNuclei Settings", style=SECTION_TITLE_STYLE),
                    _slider_block("initializations-n-particles-random", "Nparticles", 1, 200, random_nuclei["n_particles"]),
                    _dropdown_block("initializations-on-plane-random", "onPlane", [{"label": "None", "value": "none"}, {"label": "Xbottom", "value": "Xbottom"}, {"label": "Xtop", "value": "Xtop"}, {"label": "Ybottom", "value": "Ybottom"}, {"label": "Ytop", "value": "Ytop"}], random_nuclei["on_plane"]),
                    _slider_block("initializations-seed-random", "seed", 1, 200, random_nuclei["seed"]),
                ],
                style=_section_style(method == "random-nuclei"),
            ),
            html.Div([html.Div("Point / Orientation", style=SECTION_TITLE_STYLE), _slider_block("initializations-point-x-section", "pointX", 0, 120, section["point_x"]), _slider_block("initializations-point-y-section", "pointY", 0, 120, section["point_y"]), _slider_block("initializations-orientation-x-section", "orientationX", -1, 1, section["orientation_x"], step=0.05), _slider_block("initializations-orientation-y-section", "orientationY", -1, 1, section["orientation_y"], step=0.05)], style=_section_style(method == "sectional-plane")),
            html.Div([html.Div("Point / Orientation", style=SECTION_TITLE_STYLE), _slider_block("initializations-point-x", "pointX", 0, 120, layer["point_x"]), _slider_block("initializations-point-y", "pointY", 0, 120, layer["point_y"]), _slider_block("initializations-orientation-x", "orientationX", -1, 1, layer["orientation_x"], step=0.05), _slider_block("initializations-orientation-y", "orientationY", -1, 1, layer["orientation_y"], step=0.05), _slider_block("initializations-thickness", "thickness", 1, 40, layer["thickness"], step=0.5)], style=_section_style(method == "layer")),
            html.Div([html.Div("Fractional Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-minority-thickness", "minorityLayerThickness", 1, 60, fractional["minority_thickness"], step=0.5)], style=_section_style(method == "fractional")),
            html.Div([html.Div("ThreeFractionals Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-majority-thickness", "majorityPhaseLayerThickness", 1, 60, three["majority_thickness"], step=0.5), _slider_block("initializations-minority1-thickness", "minorityPhaseLayerThickness1", 1, 60, three["minority1_thickness"], step=0.5)], style=_section_style(method == "three-fractionals")),
            html.Div([html.Div("Wall Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-walls-thickness-two", "wallsThickness", 1, 20, walls["walls_thickness"], step=0.5)], style=_section_style(method == "two-walls")),
            html.Div([html.Div("Wall Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-walls-thickness-different", "wallsThickness", 1, 20, walls["walls_thickness"], step=0.5)], style=_section_style(method == "two-different-walls")),
            html.Div([html.Div("Circle Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-center-x-sphere", "centerX", 0, 120, sphere["center_x"], step=0.5), _slider_block("initializations-center-y-sphere", "centerY", 0, 120, sphere["center_y"], step=0.5), _slider_block("initializations-radius-sphere", "radius", 1, 40, sphere["radius"], step=0.5)], style=_section_style(method == "sphere")),
            html.Div([html.Div("Circle Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-center-x-sphere-in-grain", "centerX", 0, 120, sphere["center_x"], step=0.5), _slider_block("initializations-center-y-sphere-in-grain", "centerY", 0, 120, sphere["center_y"], step=0.5), _slider_block("initializations-radius-sphere-in-grain", "radius", 1, 40, sphere["radius"], step=0.5)], style=_section_style(method == "sphere-in-grain")),
            html.Div([html.Div("Ellipse Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-center-x-ellipsoid", "centerX", 0, 120, ellipsoid["center_x"], step=0.5), _slider_block("initializations-center-y-ellipsoid", "centerY", 0, 120, ellipsoid["center_y"], step=0.5), _slider_block("initializations-radius-x-ellipsoid", "radiusX", 1, 40, ellipsoid["radius_x"], step=0.5), _slider_block("initializations-radius-y-ellipsoid", "radiusY", 1, 40, ellipsoid["radius_y"], step=0.5)], style=_section_style(method == "ellipsoid")),
            html.Div([html.Div("Rectangle Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-center-x-rectangular", "centerX", 0, 120, rectangular["center_x"], step=0.5), _slider_block("initializations-center-y-rectangular", "centerY", 0, 120, rectangular["center_y"], step=0.5), _slider_block("initializations-size-x-rectangular", "sizeX", 1, 60, rectangular["size_x"], step=0.5), _slider_block("initializations-size-y-rectangular", "sizeY", 1, 60, rectangular["size_y"], step=0.5), _slider_block("initializations-angle-deg-rectangular", "angleDeg", -180, 180, rectangular["angle_deg"], step=1)], style=_section_style(method == "rectangular")),
            html.Div([html.Div("Cylinder Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-center-x-cylinder", "centerX", 0, 120, cylinder["center_x"], step=0.5), _slider_block("initializations-center-y-cylinder", "centerY", 0, 120, cylinder["center_y"], step=0.5), _slider_block("initializations-radius-cylinder", "radius", 1, 40, cylinder["radius"], step=0.5), _slider_block("initializations-length-cylinder", "length", 1, 80, cylinder["length"], step=0.5), _dropdown_block("initializations-axis-cylinder", "axis", [{"label": "X", "value": 0}, {"label": "Y", "value": 1}, {"label": "Z", "value": 2}], cylinder["axis"])], style=_section_style(method == "cylinder")),
            html.Div([html.Div("Paraboloid Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-center-x-paraboloid", "centerX", 0, 120, paraboloid["center_x"], step=0.5), _slider_block("initializations-center-y-paraboloid", "centerY", 0, 120, paraboloid["center_y"], step=0.5), _slider_block("initializations-radius-paraboloid", "radius", 1, 40, paraboloid["radius"], step=0.5)], style=_section_style(method == "paraboloid")),
            html.Div([html.Div("ThermalGrooving Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-groove-width-thermal", "grooveWidth", 1, 40, thermal["groove_width"], step=0.5), _slider_block("initializations-groove-depth-thermal", "grooveDepth", 1, 30, thermal["groove_depth"], step=0.5)], style=_section_style(method == "thermal-grooving")),
            html.Div([html.Div("Voronoi Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-ngrains-voronoi", "Ngrains", 1, 60, voronoi["ngrains"]), _slider_block("initializations-seed-voronoi", "seed", 1, 200, voronoi["seed"])], style=_section_style(method == "voronoi-tessellation")),
            html.Div([html.Div("Blobby Settings", style=SECTION_TITLE_STYLE), _slider_block("initializations-center-x-blobby", "centerX", 0, 120, blobby["center_x"], step=0.5), _slider_block("initializations-center-y-blobby", "centerY", 0, 120, blobby["center_y"], step=0.5), _slider_block("initializations-base-radius-blobby", "baseRadius", 1, 40, blobby["base_radius"], step=0.5), _slider_block("initializations-max-amplitude-blobby", "maxAmplitude", 0, 12, blobby["max_amplitude"], step=0.25), _slider_block("initializations-num-bumps-blobby", "numBumps", 1, 20, blobby["num_bumps"]), _slider_block("initializations-seed-blobby", "seed", 1, 200, blobby["seed"])], style=_section_style(method == "blobby-auto")),
        ],
        style={**PANEL_STYLE, "width": "390px", "minWidth": "390px"},
    )


def build_initializations_view(method: str, settings: dict | None = None, reroll_count: int = 0) -> tuple[go.Figure, html.Div, html.Div]:
    settings = settings or {}
    defaults = DEFAULTS_BY_METHOD.get(method, default_quasi_random_settings)()
    merged = {**defaults, **settings}

    if method == "quasi-random-nuclei":
        return build_quasi_random_figure(merged, reroll_count)
    if method == "layer":
        return build_layer_figure(merged)
    if method == "fractional":
        return build_fractional_figure(merged)
    if method == "three-fractionals":
        return build_three_fractionals_figure(merged)
    if method == "single":
        return _render_payload(simulate_single_2d(nx=merged["nx"], ny=merged["ny"]))
    if method == "sectional-plane":
        return _render_payload(simulate_sectional_plane_2d(nx=merged["nx"], ny=merged["ny"], point=(merged["point_x"], merged["point_y"]), orientation=(merged["orientation_x"], merged["orientation_y"])))
    if method == "two-walls":
        return _render_payload(simulate_two_walls_2d(nx=merged["nx"], ny=merged["ny"], walls_thickness=merged["walls_thickness"]))
    if method == "two-different-walls":
        return _render_payload(simulate_two_different_walls_2d(nx=merged["nx"], ny=merged["ny"], walls_thickness=merged["walls_thickness"]))
    if method == "sphere":
        return _render_payload(simulate_sphere_2d(nx=merged["nx"], ny=merged["ny"], center=(merged["center_x"], merged["center_y"]), radius=merged["radius"]))
    if method == "sphere-in-grain":
        return _render_payload(simulate_sphere_in_grain_2d(nx=merged["nx"], ny=merged["ny"], center=(merged["center_x"], merged["center_y"]), radius=merged["radius"]))
    if method == "ellipsoid":
        return _render_payload(simulate_ellipsoid_2d(nx=merged["nx"], ny=merged["ny"], center=(merged["center_x"], merged["center_y"]), radius_x=merged["radius_x"], radius_y=merged["radius_y"]))
    if method == "rectangular":
        return _render_payload(simulate_rectangular_2d(nx=merged["nx"], ny=merged["ny"], center=(merged["center_x"], merged["center_y"]), size_x=merged["size_x"], size_y=merged["size_y"], angle_deg=merged["angle_deg"]))
    if method == "cylinder":
        return _render_payload(simulate_cylinder_2d(nx=merged["nx"], ny=merged["ny"], center=(merged["center_x"], merged["center_y"]), radius=merged["radius"], length=merged["length"], axis=merged["axis"]))
    if method == "paraboloid":
        return _render_payload(simulate_paraboloid_2d(nx=merged["nx"], ny=merged["ny"], center=(merged["center_x"], merged["center_y"]), radius=merged["radius"]))
    if method == "quasi-random-spheres":
        return _render_payload(simulate_quasi_random_spheres_2d(nx=merged["nx"], ny=merged["ny"], dist=merged["dist"], radius1=merged["radius1"], radius2=merged["radius2"], probability_phase1=merged["probability1"], offset=merged["offset"], seed=merged["seed"]))
    if method == "random-nuclei":
        return _render_payload(simulate_random_nuclei_2d(nx=merged["nx"], ny=merged["ny"], n_particles=merged["n_particles"], on_plane=merged["on_plane"], seed=merged["seed"]))
    if method == "thermal-grooving":
        return _render_payload(simulate_thermal_grooving_2d(nx=merged["nx"], ny=merged["ny"], groove_width=merged["groove_width"], groove_depth=merged["groove_depth"]))
    if method == "triple-junction":
        return _render_payload(simulate_triple_junction_2d(nx=merged["nx"], ny=merged["ny"]))
    if method == "young3":
        return _render_payload(simulate_young3_2d(nx=merged["nx"], ny=merged["ny"]))
    if method == "young4":
        return _render_payload(simulate_young4_2d(nx=merged["nx"], ny=merged["ny"]))
    if method == "young4-periodic":
        return _render_payload(simulate_young4_periodic_2d(nx=merged["nx"], ny=merged["ny"]))
    if method == "voronoi-tessellation":
        return _render_payload(simulate_voronoi_tessellation_2d(nx=merged["nx"], ny=merged["ny"], ngrains=merged["ngrains"], seed=merged["seed"]))
    if method == "blobby-auto":
        return _render_payload(simulate_blobby_auto_2d(nx=merged["nx"], ny=merged["ny"], center=(merged["center_x"], merged["center_y"]), base_radius=merged["base_radius"], max_amplitude=merged["max_amplitude"], num_bumps=merged["num_bumps"], seed=merged["seed"]))

    return build_quasi_random_figure(default_quasi_random_settings(), 0)


def build_initializations_explorer() -> html.Div:
    method = "quasi-random-nuclei"
    controls = build_initializations_controls(method)
    figure, stats, explanation = build_initializations_view(method)
    plot_panel = html.Div(
        [
            dcc.Graph(id="initializations-figure", figure=figure, config={"displaylogo": False}, style={"height": "640px"}),
            html.Div(id="initializations-explanation", children=explanation),
        ],
        style={"flex": "1", "minWidth": "0"},
    )
    return html.Div(
        [
            html.Div(
                "Interactive explorer for OpenPhase initialization methods. Adjust each method’s parameters to understand what the initialization will create before using it in a simulation setup.",
                style={"fontSize": "14px", "color": "#667085", "marginBottom": "14px"},
            ),
            html.Div(
                [
                    html.Div(id="initializations-controls", children=controls),
                    html.Div(
                        [
                            html.Div(id="initializations-stats", children=stats, style={"marginBottom": "14px"}),
                            plot_panel,
                        ],
                        style={"flex": "1", "minWidth": "0"},
                    ),
                ],
                style={"display": "flex", "gap": "18px", "alignItems": "flex-start", "flexWrap": "wrap"},
            ),
        ],
        style={"padding": "6px 4px 18px 4px"},
    )
