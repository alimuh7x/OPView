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
        self._register_update_quasi_random_view()

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

    def _register_update_quasi_random_view(self) -> None:
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
            prevent_initial_call=False,
        )
        def update_quasi_random_view(
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
        ):
            from ui.initializations_explorer import build_quasi_random_figure, default_quasi_random_settings

            if method != "quasi-random-nuclei":
                raise PreventUpdate

            defaults = default_quasi_random_settings()
            settings = {
                "method": method,
                "nx": int(nx if nx is not None else defaults["nx"]),
                "ny": int(ny if ny is not None else defaults["ny"]),
                "offset_x": int(offset_x if offset_x is not None else defaults["offset_x"]),
                "offset_y": int(offset_y if offset_y is not None else defaults["offset_y"]),
                "spacing_x": int(spacing_x if spacing_x is not None else defaults["spacing_x"]),
                "spacing_y": int(spacing_y if spacing_y is not None else defaults["spacing_y"]),
                "deviation_x": int(deviation_x if deviation_x is not None else defaults["deviation_x"]),
                "deviation_y": int(deviation_y if deviation_y is not None else defaults["deviation_y"]),
                "threshold": float(threshold if threshold is not None else defaults["threshold"]),
                "seed": int(seed if seed is not None else defaults["seed"]),
            }
            return build_quasi_random_figure(settings, reroll_clicks or 0)

        self._track_callback(update_quasi_random_view)
