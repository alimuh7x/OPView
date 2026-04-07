"""
Callback manager for the Mechanical Loads Explorer tab.
"""

from __future__ import annotations

import json

from dash import Input, Output, State, ctx, ALL, MATCH
from dash.exceptions import PreventUpdate

from .base import BaseCallbackManager

# Styles used when showing the trigger value/component wrapper divs
_WRAP_SHOW = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "4px",
    "alignItems": "stretch",
    "flex": "1 1 0",
    "minWidth": "0",
}
_WRAP_HIDE = {"display": "none"}


def _debug_print(event: str, **payload) -> None:
    """Emit Mechanical Loads callback breadcrumbs for trigger debugging."""
    print(
        f"[mechanical-loads] {event} "
        + " ".join(f"{key}={json.dumps(value, default=str)}" for key, value in payload.items()),
        flush=True,
    )


def _has_pending_numeric_input(
    trigger_on_all,
    trigger_on_val_all,
    trigger_off_all,
    trigger_off_val_all,
    bc_type_all,
    bc_val_all,
) -> bool:
    """Detect transient None values from number inputs that are still being edited."""
    for trigger_type, trigger_val in zip(trigger_on_all or [], trigger_on_val_all or []):
        if trigger_type in {"TIME", "TIMESTEP", "STRESS", "STRAIN"} and trigger_val is None:
            return True
    for trigger_type, trigger_val in zip(trigger_off_all or [], trigger_off_val_all or []):
        if trigger_type in {"TIME", "TIMESTEP", "STRESS", "STRAIN"} and trigger_val is None:
            return True
    for bc_type, bc_val in zip(bc_type_all or [], bc_val_all or []):
        if bc_type not in (None, "NONE") and bc_val is None:
            return True
    return False


class MechanicalLoadsCallbackManager(BaseCallbackManager):
    """Manage callbacks for the Mechanical Loads Explorer tab."""

    def register(self) -> None:
        _debug_print("register")
        _debug_print("register:before_add_load")
        self._register_add_load()
        _debug_print("register:after_add_load")
        _debug_print("register:before_remove_load")
        self._register_remove_load()
        _debug_print("register:after_remove_load")
        _debug_print("register:before_apply_preset")
        self._register_apply_preset()
        _debug_print("register:after_apply_preset")
        _debug_print("register:before_update_load_list")
        self._register_update_load_list()
        _debug_print("register:after_update_load_list")
        _debug_print("register:before_toggle_trigger_inputs")
        self._register_toggle_trigger_inputs()
        _debug_print("register:after_toggle_trigger_inputs")
        _debug_print("register:before_update_view")
        self._register_update_view()
        _debug_print("register:after_update_view")
        _debug_print("register:before_sync_numeric_steps")
        self._register_sync_numeric_steps()
        _debug_print("register:after_sync_numeric_steps")
        _debug_print("register:before_debug_panel")
        self._register_debug_panel()
        _debug_print("register:after_debug_panel")

    def _register_add_load(self) -> None:
        """Increment ml-num-loads when the Add Load button is clicked (max 8 loads)."""
        _debug_print("_register_add_load")
        @self.app.callback(
            Output("ml-num-loads", "data"),
            Input("ml-add-load-btn", "n_clicks"),
            State("ml-num-loads", "data"),
            prevent_initial_call=True,
        )
        def add_load(n_clicks, current_count):
            _debug_print("add_load:enter", n_clicks=n_clicks, current_count=current_count)
            if not n_clicks:
                raise PreventUpdate
            new_count = min(int(current_count or 1) + 1, 8)
            _debug_print("add_load:exit", new_count=new_count)
            return new_count

        self._track_callback(add_load)

    def _register_apply_preset(self) -> None:
        """Apply canned Mechanical Loads presets."""
        _debug_print("_register_apply_preset")

        @self.app.callback(
            Output("ml-dt", "value"),
            Output("ml-num-loads", "data", allow_duplicate=True),
            Output("ml-loads-list", "children", allow_duplicate=True),
            Input("sidebar-ml-preset", "value"),
            prevent_initial_call=True,
        )
        def apply_preset(preset_value):
            from ui.mechanical_loads_explorer import build_load_card
            from utils.mechanical_loads_explorer import default_load_structure

            if preset_value == "custom":
                _debug_print(
                    "apply_preset:skip_custom",
                    trigger=ctx.triggered_id,
                    preset=preset_value,
                )
                raise PreventUpdate
            if preset_value == "creep":
                loads = [{
                    "dt": 0.1,
                    "trigger_on": "TIME",
                    "trigger_on_val": 0.0,
                    "trigger_on_idx": 0,
                    "trigger_off": "TIME",
                    "trigger_off_val": 100.0,
                    "trigger_off_idx": 0,
                    "repeat": 1,
                    "bc_types": ["STRESS", "NONE", "NONE", "NONE", "NONE", "NONE"],
                    "bc_values": [350.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                }]
                dt_value = 0.1
            elif preset_value == "fatigue":
                loads = [
                    {
                        "dt": 0.1,
                        "trigger_on": "STRAIN",
                        "trigger_on_val": 0.0,
                        "trigger_on_idx": 0,
                        "trigger_off": "STRAIN",
                        "trigger_off_val": 0.01,
                        "trigger_off_idx": 0,
                        "repeat": 1,
                        "bc_types": ["STRAINRATE", "NONE", "NONE", "NONE", "NONE", "NONE"],
                        "bc_values": [0.001, 0.0, 0.0, 0.0, 0.0, 0.0],
                    },
                    {
                        "dt": 0.1,
                        "trigger_on": "STRAIN",
                        "trigger_on_val": 0.01,
                        "trigger_on_idx": 0,
                        "trigger_off": "STRAIN",
                        "trigger_off_val": 0.0,
                        "trigger_off_idx": 0,
                        "repeat": 5,
                        "bc_types": ["STRAINRATE", "NONE", "NONE", "NONE", "NONE", "NONE"],
                        "bc_values": [-0.001, 0.0, 0.0, 0.0, 0.0, 0.0],
                    },
                ]
                dt_value = 0.1
            elif preset_value == "stress_strain":
                loads = [{
                    "dt": 0.1,
                    "trigger_on": "STRAIN",
                    "trigger_on_val": 0.0,
                    "trigger_on_idx": 0,
                    "trigger_off": "STRAIN",
                    "trigger_off_val": 0.05,
                    "trigger_off_idx": 0,
                    "repeat": 1,
                    "bc_types": ["STRAINRATE", "NONE", "NONE", "NONE", "NONE", "NONE"],
                    "bc_values": [0.005, 0.0, 0.0, 0.0, 0.0, 0.0],
                }]
                dt_value = 0.1
            else:
                loads = [default_load_structure()]
                dt_value = 0.1

            cards = [build_load_card(i, load) for i, load in enumerate(loads)]
            _debug_print(
                "apply_preset",
                trigger=ctx.triggered_id,
                preset=preset_value,
                dt=dt_value,
                load_count=len(loads),
                loads=loads,
            )
            return dt_value, len(loads), cards

        self._track_callback(apply_preset)

    def _register_remove_load(self) -> None:
        """Remove a load card while preserving the remaining load state."""
        _debug_print("_register_remove_load")
        @self.app.callback(
            Output("ml-num-loads", "data", allow_duplicate=True),
            Output("ml-loads-list", "children", allow_duplicate=True),
            Input({"type": "ml-remove-load-btn", "index": ALL}, "n_clicks"),
            State({"type": "ml-trigger-on", "index": ALL}, "value"),
            State({"type": "ml-trigger-on-val", "index": ALL}, "value"),
            State({"type": "ml-trigger-on-idx", "index": ALL}, "value"),
            State({"type": "ml-trigger-off", "index": ALL}, "value"),
            State({"type": "ml-trigger-off-val", "index": ALL}, "value"),
            State({"type": "ml-trigger-off-idx", "index": ALL}, "value"),
            State({"type": "ml-repeat", "index": ALL}, "value"),
            State({"type": "ml-bc-type", "index": ALL}, "value"),
            State({"type": "ml-bc-val", "index": ALL}, "value"),
            State("ml-num-loads", "data"),
            prevent_initial_call=True,
        )
        def remove_load(
            remove_clicks,
            trigger_on_all, trigger_on_val_all, trigger_on_idx_all,
            trigger_off_all, trigger_off_val_all, trigger_off_idx_all,
            repeat_all,
            bc_type_all, bc_val_all,
            num_loads,
        ):
            from ui.mechanical_loads_explorer import build_load_card
            from utils.mechanical_loads_explorer import default_load_structure, reconstruct_loads

            if not remove_clicks or all((click or 0) < 1 for click in remove_clicks):
                _debug_print(
                    "remove_load:skip_no_click",
                    trigger=ctx.triggered_id,
                    remove_clicks=remove_clicks,
                    num_loads=num_loads,
                )
                raise PreventUpdate

            triggered = ctx.triggered_id
            if not isinstance(triggered, dict) or triggered.get("type") != "ml-remove-load-btn":
                raise PreventUpdate

            n = int(num_loads or 1)
            loads = reconstruct_loads(
                n,
                trigger_on_all or [],
                trigger_on_val_all or [],
                trigger_on_idx_all or [],
                trigger_off_all or [],
                trigger_off_val_all or [],
                trigger_off_idx_all or [],
                repeat_all or [],
                bc_type_all or [],
                bc_val_all or [],
            )
            remove_index = int(triggered.get("index", 0))
            if 0 <= remove_index < len(loads):
                loads.pop(remove_index)
            if not loads:
                loads = [default_load_structure()]
            cards = [build_load_card(i, load) for i, load in enumerate(loads)]
            _debug_print(
                "remove_load",
                trigger=triggered,
                removed_index=remove_index,
                remaining_count=len(loads),
                loads=loads,
            )
            return len(loads), cards

        self._track_callback(remove_load)

    def _register_update_load_list(self) -> None:
        """Rebuild the load cards list whenever the load count changes."""
        _debug_print("_register_update_load_list")
        @self.app.callback(
            Output("ml-loads-list", "children"),
            Input("ml-num-loads", "data"),
            State({"type": "ml-trigger-on", "index": ALL}, "value"),
            State({"type": "ml-trigger-on-val", "index": ALL}, "value"),
            State({"type": "ml-trigger-on-idx", "index": ALL}, "value"),
            State({"type": "ml-trigger-off", "index": ALL}, "value"),
            State({"type": "ml-trigger-off-val", "index": ALL}, "value"),
            State({"type": "ml-trigger-off-idx", "index": ALL}, "value"),
            State({"type": "ml-repeat", "index": ALL}, "value"),
            State({"type": "ml-bc-type", "index": ALL}, "value"),
            State({"type": "ml-bc-val", "index": ALL}, "value"),
            prevent_initial_call=True,
        )
        def update_load_list(
            num_loads,
            trigger_on_all, trigger_on_val_all, trigger_on_idx_all,
            trigger_off_all, trigger_off_val_all, trigger_off_idx_all,
            repeat_all,
            bc_type_all, bc_val_all,
        ):
            from ui.mechanical_loads_explorer import build_load_card
            from utils.mechanical_loads_explorer import default_load_structure, reconstruct_loads

            n = int(num_loads or 1)
            existing_count = max(
                len(trigger_on_all or []),
                len(trigger_off_all or []),
                len(repeat_all or []),
                len(bc_type_all or []) // 6,
            )
            preserved_loads = reconstruct_loads(
                existing_count,
                trigger_on_all or [],
                trigger_on_val_all or [],
                trigger_on_idx_all or [],
                trigger_off_all or [],
                trigger_off_val_all or [],
                trigger_off_idx_all or [],
                repeat_all or [],
                bc_type_all or [],
                bc_val_all or [],
            )
            loads = preserved_loads[:n]
            while len(loads) < n:
                loads.append(default_load_structure())
            triggered = ctx.triggered_id
            try:
                cards = [build_load_card(i, loads[i]) for i in range(n)]
                _debug_print(
                    "update_load_list",
                    trigger=triggered,
                    requested_count=n,
                    preserved_count=existing_count,
                    rendered_cards=len(cards),
                )
                return cards
            except Exception as exc:
                _debug_print(
                    "update_load_list:error",
                    trigger=triggered,
                    requested_count=n,
                    preserved_count=existing_count,
                    error=repr(exc),
                )
                raise

        self._track_callback(update_load_list)

    def _register_toggle_trigger_inputs(self) -> None:
        """
        Show/hide the 'at value' and 'component' sub-rows when the trigger type changes.
        Uses MATCH so each load's controls update independently.
        """
        _debug_print("_register_toggle_trigger_inputs")
        @self.app.callback(
            Output({"type": "ml-trigger-on-val-wrap",  "index": MATCH}, "style"),
            Output({"type": "ml-trigger-on-idx-wrap",  "index": MATCH}, "style"),
            Input({"type": "ml-trigger-on", "index": MATCH}, "value"),
        )
        def toggle_on_inputs(trigger_type):
            from utils.mechanical_loads_explorer import VALUE_TRIGGERS, INDEX_TRIGGERS
            show_val = trigger_type in VALUE_TRIGGERS if trigger_type else False
            show_idx = trigger_type in INDEX_TRIGGERS if trigger_type else False
            _debug_print(
                "toggle_on_inputs",
                trigger=ctx.triggered_id,
                trigger_type=trigger_type,
                show_val=show_val,
                show_idx=show_idx,
            )
            return (
                _WRAP_SHOW if show_val else _WRAP_HIDE,
                _WRAP_SHOW if show_idx else _WRAP_HIDE,
            )

        self._track_callback(toggle_on_inputs)

        @self.app.callback(
            Output({"type": "ml-trigger-off-val-wrap",  "index": MATCH}, "style"),
            Output({"type": "ml-trigger-off-idx-wrap",  "index": MATCH}, "style"),
            Input({"type": "ml-trigger-off", "index": MATCH}, "value"),
        )
        def toggle_off_inputs(trigger_type):
            from utils.mechanical_loads_explorer import VALUE_TRIGGERS, INDEX_TRIGGERS
            show_val = trigger_type in VALUE_TRIGGERS if trigger_type else False
            show_idx = trigger_type in INDEX_TRIGGERS if trigger_type else False
            _debug_print(
                "toggle_off_inputs",
                trigger=ctx.triggered_id,
                trigger_type=trigger_type,
                show_val=show_val,
                show_idx=show_idx,
            )
            return (
                _WRAP_SHOW if show_val else _WRAP_HIDE,
                _WRAP_SHOW if show_idx else _WRAP_HIDE,
            )

        self._track_callback(toggle_off_inputs)

    def _register_update_view(self) -> None:
        """Update figures, status panel, and summary whenever any load control changes."""
        _debug_print("_register_update_view")
        @self.app.callback(
            Output("ml-figure",      "figure"),
            Output("ml-step-figure", "figure"),
            Output("ml-timeline",    "figure"),
            Output("ml-stats",       "children"),
            Output("ml-load-status", "children"),
            Output("ml-export-output", "value"),
            Input({"type": "ml-trigger-on",  "index": ALL}, "value"),
            Input({"type": "ml-trigger-on-val",  "index": ALL}, "value"),
            Input({"type": "ml-trigger-on-idx",  "index": ALL}, "value"),
            Input({"type": "ml-trigger-off", "index": ALL}, "value"),
            Input({"type": "ml-trigger-off-val", "index": ALL}, "value"),
            Input({"type": "ml-trigger-off-idx", "index": ALL}, "value"),
            Input({"type": "ml-repeat",      "index": ALL}, "value"),
            Input({"type": "ml-bc-type",     "index": ALL}, "value"),
            Input({"type": "ml-bc-val",      "index": ALL}, "value"),
            Input("ml-dt", "value"),
            State("ml-num-loads", "data"),
        )
        def update_view(
            trigger_on_all, trigger_on_val_all, trigger_on_idx_all,
            trigger_off_all, trigger_off_val_all, trigger_off_idx_all,
            repeat_all,
            bc_type_all, bc_val_all,
            dt_value,
            num_loads,
        ):
            from utils.mechanical_loads_explorer import (
                reconstruct_loads,
                build_load_figure,
                build_opstudio_export_text,
                build_load_step_figure,
                build_trigger_timeline,
            )
            from ui.mechanical_loads_explorer import _build_stats, build_load_status

            n = int(num_loads or 1)
            triggered = ctx.triggered_id
            dt = float(dt_value) if dt_value is not None else 1.0

            if _has_pending_numeric_input(
                trigger_on_all,
                trigger_on_val_all,
                trigger_off_all,
                trigger_off_val_all,
                bc_type_all,
                bc_val_all,
            ):
                _debug_print(
                    "update_view:pending_numeric_input",
                    trigger=triggered,
                    num_loads=n,
                    dt=dt,
                    trigger_on_val_all=trigger_on_val_all,
                    trigger_off_val_all=trigger_off_val_all,
                    bc_type_all=bc_type_all,
                    bc_val_all=bc_val_all,
                )
                raise PreventUpdate

            loads = reconstruct_loads(
                n,
                trigger_on_all, trigger_on_val_all, trigger_on_idx_all,
                trigger_off_all, trigger_off_val_all, trigger_off_idx_all,
                repeat_all,
                bc_type_all, bc_val_all,
            )
            try:
                timeline = build_trigger_timeline(loads, dt=dt)
                figure = build_load_figure(loads, dt=dt)
                step_figure = build_load_step_figure(loads, dt=dt)
                stats = _build_stats(loads)
                status = build_load_status(loads)
                export_text = build_opstudio_export_text(loads)
                _debug_print(
                    "update_view",
                    trigger=triggered,
                    num_loads=n,
                    dt=dt,
                    loads=loads,
                    figure_traces=len(getattr(figure, "data", [])),
                    step_figure_traces=len(getattr(step_figure, "data", [])),
                    timeline_traces=len(getattr(timeline, "data", [])),
                    export_lines=len(export_text.splitlines()),
                )
                return (figure, step_figure, timeline, stats, status, export_text)
            except Exception as exc:
                _debug_print(
                    "update_view:error",
                    trigger=triggered,
                    num_loads=n,
                    dt=dt,
                    loads=loads,
                    error=repr(exc),
                )
                raise

        self._track_callback(update_view)

    def _register_sync_numeric_steps(self) -> None:
        """Sync numeric input step sizes so browser +/- follows the current decimal precision."""
        _debug_print("_register_sync_numeric_steps")
        @self.app.callback(
            Output({"type": "ml-trigger-on-val", "index": ALL}, "step"),
            Output({"type": "ml-trigger-off-val", "index": ALL}, "step"),
            Output({"type": "ml-bc-val", "index": ALL}, "step"),
            Output("ml-dt", "step"),
            Input({"type": "ml-trigger-on-val", "index": ALL}, "value"),
            Input({"type": "ml-trigger-off-val", "index": ALL}, "value"),
            Input({"type": "ml-bc-val", "index": ALL}, "value"),
            Input("ml-dt", "value"),
            prevent_initial_call=False,
        )
        def sync_numeric_steps(trigger_on_val_all, trigger_off_val_all, bc_val_all, dt_value):
            from utils.mechanical_loads_explorer import step_from_value

            trigger_on_steps = [step_from_value(value) for value in (trigger_on_val_all or [])]
            trigger_off_steps = [step_from_value(value) for value in (trigger_off_val_all or [])]
            bc_steps = [step_from_value(value) for value in (bc_val_all or [])]
            dt_step = step_from_value(dt_value)
            _debug_print(
                "sync_numeric_steps",
                trigger=ctx.triggered_id,
                trigger_on_steps=trigger_on_steps,
                trigger_off_steps=trigger_off_steps,
                bc_steps=bc_steps,
                dt_step=dt_step,
            )
            return trigger_on_steps, trigger_off_steps, bc_steps, dt_step

        self._track_callback(sync_numeric_steps)

    def _register_debug_panel(self) -> None:
        """Render a lightweight live debug summary inside the Mechanical Loads tab."""
        _debug_print("_register_debug_panel")
        @self.app.callback(
            Output("ml-debug-output", "children"),
            Input("vtk-folder-tabs", "value"),
            Input("ml-num-loads", "data"),
            Input({"type": "ml-trigger-on",  "index": ALL}, "value"),
            Input({"type": "ml-trigger-on-val",  "index": ALL}, "value"),
            Input({"type": "ml-trigger-on-idx",  "index": ALL}, "value"),
            Input({"type": "ml-trigger-off", "index": ALL}, "value"),
            Input({"type": "ml-trigger-off-val", "index": ALL}, "value"),
            Input({"type": "ml-trigger-off-idx", "index": ALL}, "value"),
            Input({"type": "ml-repeat", "index": ALL}, "value"),
            Input({"type": "ml-bc-type", "index": ALL}, "value"),
            Input({"type": "ml-bc-val", "index": ALL}, "value"),
            Input("ml-dt", "value"),
            prevent_initial_call=False,
        )
        def render_debug_panel(
            active_folder,
            num_loads,
            trigger_on_all, trigger_on_val_all, trigger_on_idx_all,
            trigger_off_all, trigger_off_val_all, trigger_off_idx_all,
            repeat_all,
            bc_type_all, bc_val_all,
            dt_value,
        ):
            from utils.mechanical_loads_explorer import reconstruct_loads

            n = int(num_loads or 1)
            dt = float(dt_value) if dt_value is not None else 1.0
            pending_numeric = _has_pending_numeric_input(
                trigger_on_all,
                trigger_on_val_all,
                trigger_off_all,
                trigger_off_val_all,
                bc_type_all,
                bc_val_all,
            )
            loads = reconstruct_loads(
                n,
                trigger_on_all or [],
                trigger_on_val_all or [],
                trigger_on_idx_all or [],
                trigger_off_all or [],
                trigger_off_val_all or [],
                trigger_off_idx_all or [],
                repeat_all or [],
                bc_type_all or [],
                bc_val_all or [],
            )
            triggered = ctx.triggered_id
            summary = (
                f"active_folder={active_folder}\n"
                f"triggered={triggered}\n"
                f"num_loads={n}\n"
                f"dt={dt}\n"
                f"pending_numeric_input={pending_numeric}\n"
                f"trigger_on_all={trigger_on_all}\n"
                f"trigger_on_val_all={trigger_on_val_all}\n"
                f"trigger_on_idx_all={trigger_on_idx_all}\n"
                f"trigger_off_all={trigger_off_all}\n"
                f"trigger_off_val_all={trigger_off_val_all}\n"
                f"trigger_off_idx_all={trigger_off_idx_all}\n"
                f"repeat_all={repeat_all}\n"
                f"bc_type_all={bc_type_all}\n"
                f"bc_val_all={bc_val_all}\n"
                f"loads={json.dumps(loads, default=str, indent=2)}"
            )
            _debug_print(
                "debug_panel",
                active_folder=active_folder,
                trigger=triggered,
                num_loads=n,
                dt=dt,
                pending_numeric=pending_numeric,
            )
            return summary

        self._track_callback(render_debug_panel)
