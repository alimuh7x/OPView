"""
Behavioral tests for Mechanical Loads time-history previews.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest


UTILS_PATH = pathlib.Path(__file__).resolve().parents[1] / "utils" / "mechanical_loads_explorer.py"


class _FakeTrace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _FakeFigure:
    def __init__(self):
        self.data = []
        self.layout = {}
        self.annotations = []

    def add_trace(self, trace):
        self.data.append(trace)

    def add_annotation(self, **kwargs):
        self.annotations.append(kwargs)

    def update_layout(self, **kwargs):
        self.layout.update(kwargs)


def _load_module_with_plotly_stub():
    fake_plotly = types.ModuleType("plotly")
    fake_go = types.ModuleType("plotly.graph_objects")
    fake_go.Figure = _FakeFigure
    fake_go.Bar = lambda **kwargs: _FakeTrace(**kwargs)
    fake_go.Scatter = lambda **kwargs: _FakeTrace(**kwargs)
    fake_plotly.graph_objects = fake_go

    sys.modules["plotly"] = fake_plotly
    sys.modules["plotly.graph_objects"] = fake_go

    spec = importlib.util.spec_from_file_location("mechanical_loads_history_test_module", UTILS_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load mechanical loads explorer module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MechanicalLoadHistoryTests(unittest.TestCase):
    def test_stress_bc_becomes_stress_vs_time_pulse(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "TIME"
        load["trigger_on_val"] = 0.0
        load["trigger_off"] = "TIME"
        load["trigger_off_val"] = 2.0
        load["bc_types"][0] = "STRESS"
        load["bc_values"][0] = 100.0

        traces = module.build_load_history_traces([load])

        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["bc_type"], "STRESS")
        self.assertEqual(traces[0]["component"], "XX")
        self.assertEqual(traces[0]["x"], [0.0, 0.0, 2.0, 2.0, None])
        self.assertEqual(traces[0]["y"], [0.0, 100.0, 100.0, 0.0, None])

    def test_strainrate_bc_repeats_as_reset_and_ramp(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "TIME"
        load["trigger_on_val"] = 0.0
        load["trigger_off"] = "TIME"
        load["trigger_off_val"] = 2.0
        load["repeat"] = 3
        load["bc_types"][0] = "STRAINRATE"
        load["bc_values"][0] = 0.5

        traces = module.build_load_history_traces([load])

        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["bc_type"], "STRAINRATE")
        self.assertEqual(traces[0]["component"], "XX")
        self.assertEqual(traces[0]["x"], [0.0, 2.0, 2.0, None, 2.0, 4.0, 4.0, None, 4.0, 6.0, 6.0, None])
        self.assertEqual(traces[0]["y"], [0.0, 1.0, 0.0, None, 0.0, 1.0, 0.0, None, 0.0, 1.0, 0.0, None])

    def test_time_based_histories_switch_main_plot_to_time_axis(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "TIME"
        load["trigger_on_val"] = 1.0
        load["trigger_off"] = "TIME"
        load["trigger_off_val"] = 3.0
        load["bc_types"][2] = "STRAIN"
        load["bc_values"][2] = 0.02

        figure = module.build_load_figure([load])

        self.assertEqual(figure.layout["xaxis_title"], "Time")
        self.assertEqual(figure.layout["yaxis_title"], "Applied Stress / Strain")
        self.assertEqual(len(figure.data), 1)

    def test_time_based_histories_can_be_rendered_in_timesteps(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "TIME"
        load["trigger_on_val"] = 0.0
        load["trigger_off"] = "TIME"
        load["trigger_off_val"] = 2.0
        load["bc_types"][0] = "STRAINRATE"
        load["bc_values"][0] = 0.5

        figure = module.build_load_step_figure([load], dt=0.25)

        self.assertEqual(figure.layout["xaxis_title"], "Timestep")
        self.assertEqual(figure.layout["yaxis_title"], "Applied Stress / Strain")
        self.assertEqual(len(figure.data), 1)
        self.assertEqual(figure.data[0].x, [0.0, 8.0, None])
        self.assertEqual(figure.data[0].y, [0.0, 1.0, None])

    def test_timestep_trigger_uses_dt_to_convert_to_time(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "TIMESTEP"
        load["trigger_on_val"] = 10.0
        load["trigger_off"] = "TIMESTEP"
        load["trigger_off_val"] = 30.0
        load["bc_types"][0] = "STRESS"
        load["bc_values"][0] = 5.0

        traces = module.build_load_history_traces([load], dt=0.2)

        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["x"], [2.0, 2.0, 6.0, 6.0, None])

    def test_trigger_timeline_adds_horizontal_padding_for_edge_labels(self):
        module = _load_module_with_plotly_stub()
        load_a = module.default_load_structure()
        load_a["trigger_on"] = "STRAIN"
        load_a["trigger_on_val"] = 0.0
        load_a["trigger_off"] = "STRAIN"
        load_a["trigger_off_val"] = 0.01

        load_b = module.default_load_structure()
        load_b["trigger_on"] = "STRAIN"
        load_b["trigger_on_val"] = 0.01
        load_b["trigger_off"] = "STRAIN"
        load_b["trigger_off_val"] = 0.0

        figure = module.build_trigger_timeline([load_a, load_b], dt=1.0)

        self.assertIn("xaxis", figure.layout)
        self.assertEqual(figure.layout["xaxis"]["range"], [-0.001, 0.011])
        self.assertGreaterEqual(figure.layout["height"], 220)
        self.assertGreaterEqual(figure.layout["margin"]["t"], 40)
        on_markers = [trace for trace in figure.data if getattr(trace, "marker", {}).get("color") == "#10b981"]
        off_markers = [trace for trace in figure.data if getattr(trace, "marker", {}).get("color") == "#ef4444"]
        self.assertTrue(on_markers)
        self.assertTrue(off_markers)
        self.assertEqual(on_markers[0].marker["symbol"], "diamond")
        self.assertEqual(off_markers[0].marker["symbol"], "square")
        self.assertIn(on_markers[0].textposition, {"middle left", "middle right"})
        self.assertIn(off_markers[0].textposition, {"middle left", "middle right"})
        self.assertEqual(figure.layout["yaxis"]["autorange"], "reversed")

    def test_opstudio_export_omits_unused_fields_and_always_includes_repeat(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "TIMESTEP"
        load["trigger_on_val"] = 5000
        load["trigger_off"] = "TIMESTEP"
        load["trigger_off_val"] = 100000000
        load["repeat"] = 1
        load["bc_types"][0] = "STRESS"
        load["bc_values"][0] = 350e6

        text = module.build_opstudio_export_text([load])

        self.assertIn("$Load_0", text)
        self.assertIn("$TriggerON_0", text)
        self.assertIn("$TriggerONvalue_0", text)
        self.assertIn("$TriggerOFF_0", text)
        self.assertIn("$TriggerOFFvalue_0", text)
        self.assertIn("$Repeat_0", text)
        self.assertIn("$BCX_0", text)
        self.assertIn("$BCValueX_0", text)
        self.assertNotIn("$ONindex_0", text)
        self.assertNotIn("$OFFindex_0", text)
        self.assertNotIn("$BCY_0", text)
        colon_positions = {
            line.index(":")
            for line in text.splitlines()
            if line.strip()
        }
        self.assertEqual(len(colon_positions), 1)

    def test_opstudio_export_includes_component_indices_for_stress_or_strain_triggers(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "STRAIN"
        load["trigger_on_val"] = 0.0
        load["trigger_on_idx"] = 2
        load["trigger_off"] = "STRESS"
        load["trigger_off_val"] = 12.0
        load["trigger_off_idx"] = 4
        load["repeat"] = 3

        text = module.build_opstudio_export_text([load])

        self.assertIn("$ONindex_0", text)
        self.assertIn("ZZ", text)
        self.assertIn("$OFFindex_0", text)
        self.assertIn("XZ", text)
        self.assertIn("$Repeat_0", text)

    def test_opstudio_export_handles_multiple_loads_with_separator_lines(self):
        module = _load_module_with_plotly_stub()
        load_a = module.default_load_structure()
        load_a["trigger_on"] = "TIME"
        load_a["trigger_on_val"] = 0.0
        load_a["trigger_off"] = "TIME"
        load_a["trigger_off_val"] = 1.0
        load_a["repeat"] = 1

        load_b = module.default_load_structure()
        load_b["trigger_on"] = "TIME"
        load_b["trigger_on_val"] = 1.0
        load_b["trigger_off"] = "TIME"
        load_b["trigger_off_val"] = 2.0
        load_b["repeat"] = 2

        text = module.build_opstudio_export_text([load_a, load_b])

        self.assertIn("$Load_0", text)
        self.assertIn("$Load_1", text)
        self.assertIn("\n\n$Load_1", text)

    def test_strain_triggered_strainrate_derives_time_from_delta_strain(self):
        module = _load_module_with_plotly_stub()
        load = module.default_load_structure()
        load["trigger_on"] = "STRAIN"
        load["trigger_on_val"] = 0.0
        load["trigger_off"] = "STRAIN"
        load["trigger_off_val"] = 1.0
        load["repeat"] = 2
        load["bc_types"][0] = "STRAINRATE"
        load["bc_values"][0] = 0.25

        traces = module.build_load_history_traces([load])

        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["x"], [0.0, 4.0, 4.0, None, 4.0, 8.0, 8.0, None])
        self.assertEqual(traces[0]["y"], [0.0, 1.0, 0.0, None, 0.0, 1.0, 0.0, None])

    def test_sequential_strain_triggered_strainrate_loads_continue_from_prior_level(self):
        module = _load_module_with_plotly_stub()
        load_a = module.default_load_structure()
        load_a["trigger_on"] = "STRAIN"
        load_a["trigger_on_val"] = 0.0
        load_a["trigger_off"] = "STRAIN"
        load_a["trigger_off_val"] = 2.0
        load_a["bc_types"][0] = "STRAINRATE"
        load_a["bc_values"][0] = 0.01

        load_b = module.default_load_structure()
        load_b["trigger_on"] = "STRAIN"
        load_b["trigger_on_val"] = 2.0
        load_b["trigger_off"] = "STRAIN"
        load_b["trigger_off_val"] = 0.0
        load_b["bc_types"][0] = "STRAINRATE"
        load_b["bc_values"][0] = -0.01

        traces = module.build_load_history_traces([load_a, load_b])

        self.assertEqual(len(traces), 2)
        self.assertEqual(traces[0]["x"], [0.0, 200.0, None])
        self.assertEqual(traces[0]["y"], [0.0, 2.0, None])
        self.assertEqual(traces[1]["x"], [200.0, 400.0, None])
        self.assertEqual(traces[1]["y"], [2.0, 0.0, None])

    def test_third_sequential_strain_triggered_strainrate_load_starts_after_first_two(self):
        module = _load_module_with_plotly_stub()
        load_a = module.default_load_structure()
        load_a["trigger_on"] = "STRAIN"
        load_a["trigger_on_val"] = 0.0
        load_a["trigger_off"] = "STRAIN"
        load_a["trigger_off_val"] = 1.0
        load_a["bc_types"][0] = "STRAINRATE"
        load_a["bc_values"][0] = 0.01

        load_b = module.default_load_structure()
        load_b["trigger_on"] = "STRAIN"
        load_b["trigger_on_val"] = 1.0
        load_b["trigger_off"] = "STRAIN"
        load_b["trigger_off_val"] = 0.0
        load_b["bc_types"][0] = "STRAINRATE"
        load_b["bc_values"][0] = -0.01

        load_c = module.default_load_structure()
        load_c["trigger_on"] = "STRAIN"
        load_c["trigger_on_val"] = 0.0
        load_c["trigger_off"] = "STRAIN"
        load_c["trigger_off_val"] = 1.0
        load_c["bc_types"][0] = "STRAINRATE"
        load_c["bc_values"][0] = 0.01

        traces = module.build_load_history_traces([load_a, load_b, load_c])

        self.assertEqual(len(traces), 3)
        self.assertEqual(traces[0]["x"], [0.0, 100.0, None])
        self.assertEqual(traces[1]["x"], [100.0, 200.0, None])
        self.assertEqual(traces[2]["x"], [200.0, 300.0, None])
        self.assertEqual(traces[2]["y"], [0.0, 1.0, None])

    def test_step_from_value_matches_decimal_precision(self):
        module = _load_module_with_plotly_stub()

        self.assertEqual(module.step_from_value(0.01), 0.01)
        self.assertEqual(module.step_from_value(0.003), 0.001)
        self.assertEqual(module.step_from_value(2.0), 1.0)
        self.assertEqual(module.step_from_value(350000000.0), 1.0)


if __name__ == "__main__":
    unittest.main()
