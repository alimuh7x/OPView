"""
OPPre — lightweight pre-processing tools app for OPView.

This app intentionally contains ONLY:
- Initializations Explorer
- Mechanical Loads Explorer

It shares the same backend code (ui/, callbacks/, utils/, assets/) as OPView,
but does not include viewer / comparison / graphs / notebook / formula UI.
"""

from __future__ import annotations

import os
import time
from typing import Any

from dash import Dash, Input, Output, dcc, html
import dash_mantine_components as dmc

from callbacks.initializations_explorer_manager import InitializationsExplorerCallbackManager
from callbacks.mechanical_loads_manager import MechanicalLoadsCallbackManager
from ui.initializations_explorer import METHOD_OPTIONS, build_initializations_explorer
from ui.mechanical_loads_explorer import MECHANICAL_LOAD_PRESET_OPTIONS, build_mechanical_loads_explorer


def _dbg(message: str, **kv: Any) -> None:
    parts = " ".join([f"{k}={v!r}" for k, v in kv.items()])
    print(f"[debug][oppre] {message} {parts}".rstrip(), flush=True)


def build_oppre_layout() -> html.Div:
    _dbg("build_oppre_layout:enter")
    layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Img(src="/assets/OP_Logo_main.png", className="app-logo", alt="OP logo"),
                                    html.H1(
                                        [
                                            "OPP",
                                            html.Span("re", className="app-title-sub"),
                                        ],
                                        className="app-title",
                                    ),
                                ],
                                className="app-title-card",
                            )
                        ],
                        className="top-left",
                    ),
                    html.Div(
                        [
                            html.A("Documentation", href="/docs", target="_blank", className="doc-link"),
                        ],
                        className="top-right",
                    ),
                ],
                className="app-header top-bar",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("OPPre", className="vtk-folder-badge"),
                            html.Span("Tabs", className="vtk-folder-heading-text"),
                        ],
                        className="vtk-folder-heading",
                    ),
                    dcc.Tabs(
                        id="vtk-folder-tabs",
                        value="initializations-explorer",
                        className="vtk-tabs",
                        children=[
                            dcc.Tab(
                                label="Initializations Explorer",
                                value="initializations-explorer",
                                className="vtk-tab",
                                selected_className="vtk-tab--selected",
                            ),
                            dcc.Tab(
                                label="Mechanical Loads Explorer",
                                value="mechanical-loads-explorer",
                                className="vtk-tab",
                                selected_className="vtk-tab--selected",
                            ),
                        ],
                    ),
                    html.Div(id="oppre-feedback", className="project-feedback"),
                ],
                className="vtk-folder-row",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            # Sidebar sections required by existing managers
                            html.Div(
                                [
                                    html.Span("METHOD", className="sidebar-projects-title"),
                                    dcc.RadioItems(
                                        id="sidebar-init-method",
                                        options=METHOD_OPTIONS,
                                        value="quasi-random-nuclei",
                                        className="sidebar-radio-list",
                                        labelStyle={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "padding": "3px 0",
                                            "cursor": "pointer",
                                        },
                                        inputStyle={"marginRight": "8px", "cursor": "pointer"},
                                    ),
                                ],
                                id="sidebar-initializations-section",
                                className="sidebar-projects-section",
                                style={"display": "block"},
                            ),
                            html.Div(
                                [
                                    html.Span("PRESETS", className="sidebar-projects-title"),
                                    dcc.RadioItems(
                                        id="sidebar-ml-preset",
                                        options=MECHANICAL_LOAD_PRESET_OPTIONS,
                                        value="custom",
                                        className="sidebar-radio-list",
                                        labelStyle={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "padding": "3px 0",
                                            "cursor": "pointer",
                                        },
                                        inputStyle={"marginRight": "8px", "cursor": "pointer"},
                                    ),
                                ],
                                id="sidebar-mechanical-loads-section",
                                className="sidebar-projects-section",
                                style={"display": "none"},
                            ),
                        ],
                        className="sidebar",
                        style={"flex": "0 0 320px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                id="initializations-content",
                                children=[build_initializations_explorer()],
                                style={"display": "block"},
                            ),
                            html.Div(
                                id="mechanical-loads-content",
                                children=[build_mechanical_loads_explorer()],
                                style={"display": "none"},
                            ),
                        ],
                        className="main-panel",
                        style={"flex": "1 1 auto", "minWidth": "0"},
                    ),
                ],
                className="layout-shell",
            ),
        ],
        id="app-container",
        style={"backgroundColor": "#eef2f7", "minHeight": "100vh"},
    )
    _dbg("build_oppre_layout:exit")
    return layout


def create_app() -> Dash:
    _dbg("create_app:enter")
    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        external_stylesheets=[dmc.styles.ALL],
    )
    app.title = "OPPre"
    _dbg("create_app:dash_created")

    app.layout = build_oppre_layout()
    _dbg("create_app:layout_set")

    # Lightweight tab switcher for OPPre (show/hide sidebar sections + content).
    @app.callback(
        Output("sidebar-initializations-section", "style"),
        Output("sidebar-mechanical-loads-section", "style"),
        Output("initializations-content", "style"),
        Output("mechanical-loads-content", "style"),
        Input("vtk-folder-tabs", "value"),
        prevent_initial_call=False,
    )
    def _switch_tab(active_tab: str):
        _dbg("switch_tab:enter", active_tab=active_tab)
        init_visible = active_tab == "initializations-explorer"
        ml_visible = active_tab == "mechanical-loads-explorer"
        init_style = {"display": "block"} if init_visible else {"display": "none"}
        ml_style = {"display": "block"} if ml_visible else {"display": "none"}
        init_content_style = {"display": "block"} if init_visible else {"display": "none"}
        ml_content_style = {"display": "block"} if ml_visible else {"display": "none"}
        _dbg("switch_tab:exit", init_visible=init_visible, ml_visible=ml_visible)
        return init_style, ml_style, init_content_style, ml_content_style

    _dbg("create_app:registering_initializations_manager")
    init_mgr = InitializationsExplorerCallbackManager(app, context=None)
    init_mgr.register()
    _dbg("create_app:registered_initializations_manager", callbacks=init_mgr.count())

    print("  [mechanical-loads] about to register Mechanical Loads Explorer callbacks...", flush=True)
    ml_mgr = MechanicalLoadsCallbackManager(app, context=None)
    ml_mgr.register()
    print("  [mechanical-loads] finished registering Mechanical Loads Explorer callbacks.", flush=True)
    _dbg("create_app:registered_mechanical_loads_manager", callbacks=ml_mgr.count())

    _dbg("create_app:exit")
    return app


if __name__ == "__main__":
    started = time.time()
    host = os.environ.get("OPVIEW_HOST", "127.0.0.1")
    port = int(os.environ.get("OPVIEW_PORT", "8051"))
    _dbg("main:enter", host=host, port=port)
    app = create_app()
    _dbg("main:running", startup_s=f"{time.time() - started:.3f}")
    app.run(debug=True, use_reloader=False, host=host, port=port)
