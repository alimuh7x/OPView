"""
Source-level regression tests for Mechanical Loads Explorer wiring.
"""

from __future__ import annotations

import pathlib
import unittest


MECHANICAL_LOADS_UI = pathlib.Path(__file__).resolve().parents[1] / "ui" / "mechanical_loads_explorer.py"
MECHANICAL_LOADS_MANAGER = pathlib.Path(__file__).resolve().parents[1] / "callbacks" / "mechanical_loads_manager.py"
TAB_MANAGER = pathlib.Path(__file__).resolve().parents[1] / "callbacks" / "tab_manager.py"
MECHANICAL_LOADS_UTILS = pathlib.Path(__file__).resolve().parents[1] / "utils" / "mechanical_loads_explorer.py"
CALLBACKS_MANAGER = pathlib.Path(__file__).resolve().parents[1] / "callbacks" / "manager.py"
OPVIEW_MAIN = pathlib.Path(__file__).resolve().parents[1] / "OPView.py"
CALLBACKS_INIT = pathlib.Path(__file__).resolve().parents[1] / "callbacks" / "__init__.py"


class MechanicalLoadsSourceTests(unittest.TestCase):
    def test_load_card_uses_supplied_trigger_and_bc_defaults(self):
        source = MECHANICAL_LOADS_UI.read_text(encoding="utf-8")

        self.assertIn('value=default_trigger_val', source)
        self.assertIn('debounce=True', source)
        self.assertIn('"width": "100%"', source)
        self.assertIn('"width": "150px"', source)
        self.assertIn('"width": "220px"', source)
        self.assertIn('value=default_trigger_idx', source)
        self.assertIn('value=bc_type', source)
        self.assertIn('value=bc_value', source)
        self.assertIn('load["trigger_on_val"]', source)
        self.assertIn('load["trigger_on_idx"]', source)
        self.assertIn('load["trigger_off_val"]', source)
        self.assertIn('load["trigger_off_idx"]', source)
        self.assertIn('load["bc_types"][c]', source)
        self.assertIn('load["bc_values"][c]', source)
        self.assertIn('"ml-remove-load-btn"', source)
        self.assertIn('className="mechanical-remove-load-btn"', source)
        self.assertIn('"width": "100%"', source)

    def test_update_load_list_preserves_existing_load_state_and_logs_trigger(self):
        source = MECHANICAL_LOADS_MANAGER.read_text(encoding="utf-8")

        self.assertIn('State({"type": "ml-trigger-on", "index": ALL}, "value")', source)
        self.assertIn('State({"type": "ml-bc-type", "index": ALL}, "value")', source)
        self.assertIn("existing_count = max(", source)
        self.assertIn("reconstruct_loads(", source)
        self.assertIn('triggered = ctx.triggered_id', source)
        self.assertIn('_debug_print(', source)
        self.assertIn('"update_load_list"', source)
        self.assertIn('"update_view"', source)
        self.assertIn('Output("ml-step-figure", "figure")', source)
        self.assertIn('Output("ml-export-output", "value")', source)
        self.assertIn('build_load_step_figure', source)
        self.assertIn('build_opstudio_export_text', source)
        self.assertIn('"add_load:enter"', source)
        self.assertIn('"toggle_on_inputs"', source)
        self.assertIn('"toggle_off_inputs"', source)
        self.assertIn('"remove_load"', source)
        self.assertIn('if not remove_clicks or all((click or 0) < 1 for click in remove_clicks):', source)
        self.assertIn('"remove_load:skip_no_click"', source)
        self.assertIn('Output({"type": "ml-bc-val", "index": ALL}, "step")', source)
        self.assertIn('Output("ml-dt", "step")', source)
        self.assertIn('step_from_value', source)
        self.assertIn('"sync_numeric_steps"', source)
        self.assertIn('"update_load_list:error"', source)
        self.assertIn('"update_view:error"', source)
        self.assertIn('Output("ml-debug-output", "children")', source)
        self.assertIn('"debug_panel"', source)
        self.assertIn('Input("vtk-folder-tabs", "value")', source)
        self.assertIn('Input({"type": "ml-remove-load-btn", "index": ALL}, "n_clicks")', source)

    def test_mechanical_tab_and_ui_expose_full_debug_surface(self):
        ui_source = MECHANICAL_LOADS_UI.read_text(encoding="utf-8")
        tab_source = TAB_MANAGER.read_text(encoding="utf-8")

        self.assertIn('id="ml-preset"', ui_source)
        self.assertIn('"Creep"', ui_source)
        self.assertIn('"Fatigue"', ui_source)
        self.assertIn('"Stress / Strain"', ui_source)
        self.assertIn('print("[mechanical-loads] build_mechanical_loads_explorer panel_radius=10px"', ui_source)
        self.assertIn('"[mechanical-loads] _trigger_row "', ui_source)
        self.assertIn('"[mechanical-loads] _bc_component_row "', ui_source)
        self.assertIn('"[mechanical-loads] build_load_card "', ui_source)
        self.assertIn('"gridTemplateColumns": "repeat(3, minmax(0, 1fr))"', ui_source)
        self.assertIn('"alignItems": "stretch"', ui_source)
        self.assertIn('id="ml-debug-output"', ui_source)
        self.assertIn('id="ml-step-figure"', ui_source)
        self.assertIn('id="ml-export-output"', ui_source)
        self.assertIn('id="ml-export-copy"', ui_source)
        self.assertIn('"OPStudio Export"', ui_source)
        self.assertIn('"Applied Load History (Timesteps)"', ui_source)
        self.assertIn('"flexWrap": "wrap"', ui_source)
        self.assertIn('"maxWidth": "420px"', ui_source)
        self.assertIn('"width": "100%"', ui_source)
        self.assertIn('"minWidth": "0"', ui_source)
        self.assertIn('"Mechanical Loads debug: waiting for events"', ui_source)
        self.assertIn('[mechanical-loads] render_active_tab trigger=', tab_source)
        self.assertIn('[mechanical-loads] render_active_tab:enter triggered=', tab_source)

    def test_mechanical_utils_and_registration_are_debug_printed(self):
        utils_source = MECHANICAL_LOADS_UTILS.read_text(encoding="utf-8")
        callbacks_manager_source = CALLBACKS_MANAGER.read_text(encoding="utf-8")
        mech_manager_source = MECHANICAL_LOADS_MANAGER.read_text(encoding="utf-8")

        self.assertIn('"[mechanical-loads] default_load_structure"', utils_source)
        self.assertIn('"[mechanical-loads] reconstruct_loads:start "', utils_source)
        self.assertIn('"[mechanical-loads] reconstruct_loads:done loads=', utils_source)
        self.assertIn('"[mechanical-loads] build_load_figure loads=', utils_source)
        self.assertIn('"[mechanical-loads] build_load_step_figure loads=', utils_source)
        self.assertIn('"[mechanical-loads] build_opstudio_export_text loads=', utils_source)
        self.assertIn('"[mechanical-loads] step_from_value value=', utils_source)
        self.assertIn('"[mechanical-loads] build_trigger_timeline loads=', utils_source)
        self.assertIn('"[mechanical-loads] build_loads_summary loads=', utils_source)
        self.assertIn('"[mechanical-loads] summarize_load idx=', utils_source)
        self.assertIn('[mechanical-loads] about to register Mechanical Loads Explorer callbacks...', callbacks_manager_source)
        self.assertIn('[mechanical-loads] finished registering Mechanical Loads Explorer callbacks.', callbacks_manager_source)
        self.assertIn('register:before_add_load', mech_manager_source)
        self.assertIn('register:after_debug_panel', mech_manager_source)
        self.assertIn('register:before_sync_numeric_steps', mech_manager_source)
        self.assertIn('_register_apply_preset', mech_manager_source)
        self.assertIn('Input("ml-preset", "value")', mech_manager_source)
        self.assertIn('"apply_preset:skip_custom"', mech_manager_source)
        self.assertIn('if preset_value == "custom":', mech_manager_source)
        self.assertIn('"trigger_off_val": 100.0', mech_manager_source)
        self.assertIn('"bc_values": [350.0, 0.0, 0.0, 0.0, 0.0, 0.0]', mech_manager_source)
        self.assertIn('"trigger_off_val": 0.01', mech_manager_source)
        self.assertIn('"bc_values": [0.001, 0.0, 0.0, 0.0, 0.0, 0.0]', mech_manager_source)
        self.assertIn('"bc_values": [-0.001, 0.0, 0.0, 0.0, 0.0, 0.0]', mech_manager_source)
        self.assertIn('"repeat": 5', mech_manager_source)
        self.assertIn('"trigger_off_val": 0.05', mech_manager_source)
        self.assertIn('"bc_values": [0.005, 0.0, 0.0, 0.0, 0.0, 0.0]', mech_manager_source)

    def test_standalone_opview_registers_mechanical_loads_callbacks(self):
        opview_source = OPVIEW_MAIN.read_text(encoding="utf-8")
        callbacks_init_source = CALLBACKS_INIT.read_text(encoding="utf-8")

        self.assertIn("MechanicalLoadsCallbackManager", callbacks_init_source)
        self.assertIn("MechanicalLoadsCallbackManager", opview_source)
        self.assertIn("mechanical_loads_cb_manager = MechanicalLoadsCallbackManager(app, app_context)", opview_source)
        self.assertIn("mechanical_loads_cb_manager.register()", opview_source)


if __name__ == "__main__":
    unittest.main()
