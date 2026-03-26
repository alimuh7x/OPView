"""
Callback manager for the Initializations Explorer tab.
"""

from __future__ import annotations

from dash import Input, Output, ctx
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager


class InitializationsExplorerCallbackManager(BaseCallbackManager):
    """Manage callbacks for the Initializations Explorer tab."""

    def register(self) -> None:
        self._register_apply_presets()
        self._register_update_method_controls()
        self._register_update_view()

    def _register_apply_presets(self) -> None:
        @self.app.callback(
            Output("initializations-offset-x", "value"),
            Output("initializations-offset-y", "value"),
            Output("initializations-spacing-x", "value"),
            Output("initializations-spacing-y", "value"),
            Output("initializations-deviation-x", "value"),
            Output("initializations-deviation-y", "value"),
            Output("initializations-threshold", "value"),
            Input("initializations-preset-regular-btn", "n_clicks"),
            Input("initializations-preset-random-btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def apply_presets(regular_clicks, random_clicks):
            if not ctx.triggered_id:
                raise PreventUpdate
            if ctx.triggered_id == "initializations-preset-regular-btn":
                return 0, 0, 10, 10, 0, 0, 0.0
            return 4, 3, 10, 8, 4, 3, 0.45

        self._track_callback(apply_presets)

    def _register_update_method_controls(self) -> None:
        @self.app.callback(
            Output("initializations-controls", "children"),
            Input("initializations-method-selector", "value"),
            prevent_initial_call=True,
        )
        def update_method_controls(method):
            from ui.initializations_explorer import build_initializations_controls

            return build_initializations_controls(method or "quasi-random-nuclei")

        self._track_callback(update_method_controls)

    def _register_update_view(self) -> None:
        @self.app.callback(
            Output("initializations-figure", "figure"),
            Output("initializations-stats", "children"),
            Output("initializations-explanation", "children"),
            Input("initializations-method-selector", "value"),
            Input("initializations-nx", "value"),
            Input("initializations-ny", "value"),
            Input("initializations-offset-x", "value"),
            Input("initializations-offset-y", "value"),
            Input("initializations-spacing-x", "value"),
            Input("initializations-spacing-y", "value"),
            Input("initializations-deviation-x", "value"),
            Input("initializations-deviation-y", "value"),
            Input("initializations-threshold", "value"),
            Input("initializations-seed", "value"),
            Input("initializations-reroll-btn", "n_clicks"),
            Input("initializations-dist-spheres", "value"),
            Input("initializations-radius1-spheres", "value"),
            Input("initializations-radius2-spheres", "value"),
            Input("initializations-probability1-spheres", "value"),
            Input("initializations-offset-spheres", "value"),
            Input("initializations-seed-spheres", "value"),
            Input("initializations-n-particles-random", "value"),
            Input("initializations-on-plane-random", "value"),
            Input("initializations-seed-random", "value"),
            Input("initializations-point-x-section", "value"),
            Input("initializations-point-y-section", "value"),
            Input("initializations-orientation-x-section", "value"),
            Input("initializations-orientation-y-section", "value"),
            Input("initializations-point-x", "value"),
            Input("initializations-point-y", "value"),
            Input("initializations-orientation-x", "value"),
            Input("initializations-orientation-y", "value"),
            Input("initializations-thickness", "value"),
            Input("initializations-minority-thickness", "value"),
            Input("initializations-majority-thickness", "value"),
            Input("initializations-minority1-thickness", "value"),
            Input("initializations-walls-thickness-two", "value"),
            Input("initializations-walls-thickness-different", "value"),
            Input("initializations-center-x-sphere", "value"),
            Input("initializations-center-y-sphere", "value"),
            Input("initializations-radius-sphere", "value"),
            Input("initializations-center-x-sphere-in-grain", "value"),
            Input("initializations-center-y-sphere-in-grain", "value"),
            Input("initializations-radius-sphere-in-grain", "value"),
            Input("initializations-center-x-ellipsoid", "value"),
            Input("initializations-center-y-ellipsoid", "value"),
            Input("initializations-radius-x-ellipsoid", "value"),
            Input("initializations-radius-y-ellipsoid", "value"),
            Input("initializations-center-x-rectangular", "value"),
            Input("initializations-center-y-rectangular", "value"),
            Input("initializations-size-x-rectangular", "value"),
            Input("initializations-size-y-rectangular", "value"),
            Input("initializations-angle-deg-rectangular", "value"),
            Input("initializations-center-x-cylinder", "value"),
            Input("initializations-center-y-cylinder", "value"),
            Input("initializations-radius-cylinder", "value"),
            Input("initializations-length-cylinder", "value"),
            Input("initializations-axis-cylinder", "value"),
            Input("initializations-center-x-paraboloid", "value"),
            Input("initializations-center-y-paraboloid", "value"),
            Input("initializations-radius-paraboloid", "value"),
            Input("initializations-groove-width-thermal", "value"),
            Input("initializations-groove-depth-thermal", "value"),
            Input("initializations-ngrains-voronoi", "value"),
            Input("initializations-seed-voronoi", "value"),
            Input("initializations-center-x-blobby", "value"),
            Input("initializations-center-y-blobby", "value"),
            Input("initializations-base-radius-blobby", "value"),
            Input("initializations-max-amplitude-blobby", "value"),
            Input("initializations-num-bumps-blobby", "value"),
            Input("initializations-seed-blobby", "value"),
            prevent_initial_call=False,
        )
        def update_view(
            method,
            nx,
            ny,
            offset_x,
            offset_y,
            spacing_x,
            spacing_y,
            deviation_x,
            deviation_y,
            threshold,
            seed,
            reroll_clicks,
            dist_spheres,
            radius1_spheres,
            radius2_spheres,
            probability1_spheres,
            offset_spheres,
            seed_spheres,
            n_particles_random,
            on_plane_random,
            seed_random,
            point_x_section,
            point_y_section,
            orientation_x_section,
            orientation_y_section,
            point_x,
            point_y,
            orientation_x,
            orientation_y,
            thickness,
            minority_thickness,
            majority_thickness,
            minority1_thickness,
            walls_thickness_two,
            walls_thickness_different,
            center_x_sphere,
            center_y_sphere,
            radius_sphere,
            center_x_sphere_in_grain,
            center_y_sphere_in_grain,
            radius_sphere_in_grain,
            center_x_ellipsoid,
            center_y_ellipsoid,
            radius_x_ellipsoid,
            radius_y_ellipsoid,
            center_x_rectangular,
            center_y_rectangular,
            size_x_rectangular,
            size_y_rectangular,
            angle_deg_rectangular,
            center_x_cylinder,
            center_y_cylinder,
            radius_cylinder,
            length_cylinder,
            axis_cylinder,
            center_x_paraboloid,
            center_y_paraboloid,
            radius_paraboloid,
            groove_width_thermal,
            groove_depth_thermal,
            ngrains_voronoi,
            seed_voronoi,
            center_x_blobby,
            center_y_blobby,
            base_radius_blobby,
            max_amplitude_blobby,
            num_bumps_blobby,
            seed_blobby,
        ):
            from ui.initializations_explorer import DEFAULTS_BY_METHOD, build_initializations_view

            method = method or "quasi-random-nuclei"
            defaults = DEFAULTS_BY_METHOD.get(method, DEFAULTS_BY_METHOD["quasi-random-nuclei"])()
            settings = {"method": method, "nx": int(nx if nx is not None else defaults["nx"]), "ny": int(ny if ny is not None else defaults["ny"])}

            if method == "quasi-random-nuclei":
                settings.update({
                    "offset_x": int(offset_x if offset_x is not None else defaults["offset_x"]),
                    "offset_y": int(offset_y if offset_y is not None else defaults["offset_y"]),
                    "spacing_x": int(spacing_x if spacing_x is not None else defaults["spacing_x"]),
                    "spacing_y": int(spacing_y if spacing_y is not None else defaults["spacing_y"]),
                    "deviation_x": int(deviation_x if deviation_x is not None else defaults["deviation_x"]),
                    "deviation_y": int(deviation_y if deviation_y is not None else defaults["deviation_y"]),
                    "threshold": float(threshold if threshold is not None else defaults["threshold"]),
                    "seed": int(seed if seed is not None else defaults["seed"]),
                })
                return build_initializations_view(method, settings, reroll_clicks or 0)

            if method == "quasi-random-spheres":
                settings.update({
                    "dist": int(dist_spheres if dist_spheres is not None else defaults["dist"]),
                    "radius1": float(radius1_spheres if radius1_spheres is not None else defaults["radius1"]),
                    "radius2": float(radius2_spheres if radius2_spheres is not None else defaults["radius2"]),
                    "probability1": float(probability1_spheres if probability1_spheres is not None else defaults["probability1"]),
                    "offset": int(offset_spheres if offset_spheres is not None else defaults["offset"]),
                    "seed": int(seed_spheres if seed_spheres is not None else defaults["seed"]),
                })
            elif method == "random-nuclei":
                settings.update({
                    "n_particles": int(n_particles_random if n_particles_random is not None else defaults["n_particles"]),
                    "on_plane": on_plane_random if on_plane_random is not None else defaults["on_plane"],
                    "seed": int(seed_random if seed_random is not None else defaults["seed"]),
                })
            elif method == "sectional-plane":
                settings.update({
                    "point_x": float(point_x_section if point_x_section is not None else defaults["point_x"]),
                    "point_y": float(point_y_section if point_y_section is not None else defaults["point_y"]),
                    "orientation_x": float(orientation_x_section if orientation_x_section is not None else defaults["orientation_x"]),
                    "orientation_y": float(orientation_y_section if orientation_y_section is not None else defaults["orientation_y"]),
                })
            elif method == "layer":
                settings.update({
                    "point_x": float(point_x if point_x is not None else defaults["point_x"]),
                    "point_y": float(point_y if point_y is not None else defaults["point_y"]),
                    "orientation_x": float(orientation_x if orientation_x is not None else defaults["orientation_x"]),
                    "orientation_y": float(orientation_y if orientation_y is not None else defaults["orientation_y"]),
                    "thickness": float(thickness if thickness is not None else defaults["thickness"]),
                })
            elif method == "fractional":
                settings.update({"minority_thickness": float(minority_thickness if minority_thickness is not None else defaults["minority_thickness"])})
            elif method == "three-fractionals":
                settings.update({
                    "majority_thickness": float(majority_thickness if majority_thickness is not None else defaults["majority_thickness"]),
                    "minority1_thickness": float(minority1_thickness if minority1_thickness is not None else defaults["minority1_thickness"]),
                })
            elif method == "two-walls":
                settings.update({"walls_thickness": float(walls_thickness_two if walls_thickness_two is not None else defaults["walls_thickness"])})
            elif method == "two-different-walls":
                settings.update({"walls_thickness": float(walls_thickness_different if walls_thickness_different is not None else defaults["walls_thickness"])})
            elif method == "sphere":
                settings.update({"center_x": float(center_x_sphere if center_x_sphere is not None else defaults["center_x"]), "center_y": float(center_y_sphere if center_y_sphere is not None else defaults["center_y"]), "radius": float(radius_sphere if radius_sphere is not None else defaults["radius"])})
            elif method == "sphere-in-grain":
                settings.update({"center_x": float(center_x_sphere_in_grain if center_x_sphere_in_grain is not None else defaults["center_x"]), "center_y": float(center_y_sphere_in_grain if center_y_sphere_in_grain is not None else defaults["center_y"]), "radius": float(radius_sphere_in_grain if radius_sphere_in_grain is not None else defaults["radius"])})
            elif method == "ellipsoid":
                settings.update({"center_x": float(center_x_ellipsoid if center_x_ellipsoid is not None else defaults["center_x"]), "center_y": float(center_y_ellipsoid if center_y_ellipsoid is not None else defaults["center_y"]), "radius_x": float(radius_x_ellipsoid if radius_x_ellipsoid is not None else defaults["radius_x"]), "radius_y": float(radius_y_ellipsoid if radius_y_ellipsoid is not None else defaults["radius_y"])})
            elif method == "rectangular":
                settings.update({"center_x": float(center_x_rectangular if center_x_rectangular is not None else defaults["center_x"]), "center_y": float(center_y_rectangular if center_y_rectangular is not None else defaults["center_y"]), "size_x": float(size_x_rectangular if size_x_rectangular is not None else defaults["size_x"]), "size_y": float(size_y_rectangular if size_y_rectangular is not None else defaults["size_y"]), "angle_deg": float(angle_deg_rectangular if angle_deg_rectangular is not None else defaults["angle_deg"])})
            elif method == "cylinder":
                settings.update({"center_x": float(center_x_cylinder if center_x_cylinder is not None else defaults["center_x"]), "center_y": float(center_y_cylinder if center_y_cylinder is not None else defaults["center_y"]), "radius": float(radius_cylinder if radius_cylinder is not None else defaults["radius"]), "length": float(length_cylinder if length_cylinder is not None else defaults["length"]), "axis": int(axis_cylinder if axis_cylinder is not None else defaults["axis"])})
            elif method == "paraboloid":
                settings.update({"center_x": float(center_x_paraboloid if center_x_paraboloid is not None else defaults["center_x"]), "center_y": float(center_y_paraboloid if center_y_paraboloid is not None else defaults["center_y"]), "radius": float(radius_paraboloid if radius_paraboloid is not None else defaults["radius"])})
            elif method == "thermal-grooving":
                settings.update({"groove_width": float(groove_width_thermal if groove_width_thermal is not None else defaults["groove_width"]), "groove_depth": float(groove_depth_thermal if groove_depth_thermal is not None else defaults["groove_depth"])})
            elif method == "voronoi-tessellation":
                settings.update({"ngrains": int(ngrains_voronoi if ngrains_voronoi is not None else defaults["ngrains"]), "seed": int(seed_voronoi if seed_voronoi is not None else defaults["seed"])})
            elif method == "blobby-auto":
                settings.update({"center_x": float(center_x_blobby if center_x_blobby is not None else defaults["center_x"]), "center_y": float(center_y_blobby if center_y_blobby is not None else defaults["center_y"]), "base_radius": float(base_radius_blobby if base_radius_blobby is not None else defaults["base_radius"]), "max_amplitude": float(max_amplitude_blobby if max_amplitude_blobby is not None else defaults["max_amplitude"]), "num_bumps": int(num_bumps_blobby if num_bumps_blobby is not None else defaults["num_bumps"]), "seed": int(seed_blobby if seed_blobby is not None else defaults["seed"])})

            return build_initializations_view(method, settings, reroll_clicks or 0)

        self._track_callback(update_view)
