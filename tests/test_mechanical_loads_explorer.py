"""
Tests for the Mechanical Loads Explorer utilities.
"""

import unittest

from utils.mechanical_loads_explorer import (
    COMPONENT_LABELS,
    build_load_figure,
    build_loads_summary,
    build_trigger_timeline,
    default_load_structure,
    reconstruct_loads,
    summarize_load,
)


class TestDefaultLoadStructure(unittest.TestCase):
    def test_fields_present(self):
        load = default_load_structure()
        for key in ("trigger_on", "trigger_off", "trigger_on_val", "trigger_off_val",
                    "trigger_on_idx", "trigger_off_idx", "repeat", "bc_types", "bc_values"):
            self.assertIn(key, load)

    def test_defaults(self):
        load = default_load_structure()
        self.assertEqual(load["trigger_on"], "USER")
        self.assertEqual(load["trigger_off"], "USER")
        self.assertEqual(load["repeat"], 1)
        self.assertEqual(load["bc_types"], ["NONE"] * 6)
        self.assertEqual(load["bc_values"], [0.0] * 6)

    def test_six_bc_components(self):
        load = default_load_structure()
        self.assertEqual(len(load["bc_types"]), 6)
        self.assertEqual(len(load["bc_values"]), 6)


class TestBuildLoadFigure(unittest.TestCase):
    def test_empty_loads(self):
        fig = build_load_figure([])
        self.assertIsNotNone(fig)
        # No traces expected
        self.assertEqual(len(fig.data), 0)

    def test_single_load_no_bcs(self):
        load = default_load_structure()
        fig = build_load_figure([load])
        # All NONE → no bars, but annotation present
        self.assertEqual(len(fig.data), 0)

    def test_single_load_stress_bc(self):
        load = default_load_structure()
        load["bc_types"][0] = "STRESS"  # XX = stress
        load["bc_values"][0] = 100.0
        fig = build_load_figure([load])
        self.assertGreater(len(fig.data), 0)
        # First trace should have XX as x value
        self.assertIn("XX", list(fig.data[0].x))

    def test_multiple_bc_types(self):
        load = default_load_structure()
        load["bc_types"][0] = "STRESS"
        load["bc_values"][0] = 50.0
        load["bc_types"][1] = "STRAIN"
        load["bc_values"][1] = 0.001
        load["bc_types"][2] = "STRAINRATE"
        load["bc_values"][2] = 0.01
        fig = build_load_figure([load])
        # Should have 3 traces (one per BC type)
        self.assertEqual(len(fig.data), 3)


class TestBuildTriggerTimeline(unittest.TestCase):
    def test_no_value_triggers(self):
        load = default_load_structure()  # USER/USER → no timeline
        fig = build_trigger_timeline([load])
        # Empty figure (annotation only, no data traces)
        self.assertEqual(len(fig.data), 0)

    def test_time_trigger_on(self):
        load = default_load_structure()
        load["trigger_on"] = "TIME"
        load["trigger_on_val"] = 1.5
        fig = build_trigger_timeline([load])
        self.assertGreater(len(fig.data), 0)

    def test_timestep_trigger_both(self):
        load = default_load_structure()
        load["trigger_on"] = "TIMESTEP"
        load["trigger_on_val"] = 100
        load["trigger_off"] = "TIMESTEP"
        load["trigger_off_val"] = 500
        fig = build_trigger_timeline([load])
        # Expects ON marker + OFF marker + connecting line
        self.assertGreaterEqual(len(fig.data), 2)


class TestBuildLoadsSummary(unittest.TestCase):
    def test_empty(self):
        summary = build_loads_summary([])
        self.assertEqual(dict(summary)["Loads"], "0")

    def test_counts(self):
        load = default_load_structure()
        load["bc_types"][0] = "STRESS"
        load["bc_types"][1] = "STRAIN"
        load["bc_types"][2] = "STRAINRATE"
        summary = dict(build_loads_summary([load]))
        self.assertEqual(summary["Loads"], "1")
        self.assertEqual(summary["Stress BCs"], "1")
        self.assertEqual(summary["Strain BCs"], "1")
        self.assertEqual(summary["Strain Rate BCs"], "1")


class TestReconstructLoads(unittest.TestCase):
    def test_single_default(self):
        load = default_load_structure()
        trigger_on_all = [load["trigger_on"]]
        trigger_on_val_all = [load["trigger_on_val"]]
        trigger_on_idx_all = [load["trigger_on_idx"]]
        trigger_off_all = [load["trigger_off"]]
        trigger_off_val_all = [load["trigger_off_val"]]
        trigger_off_idx_all = [load["trigger_off_idx"]]
        repeat_all = [load["repeat"]]
        bc_type_all = load["bc_types"][:]
        bc_val_all = load["bc_values"][:]

        loads = reconstruct_loads(
            1,
            trigger_on_all, trigger_on_val_all, trigger_on_idx_all,
            trigger_off_all, trigger_off_val_all, trigger_off_idx_all,
            repeat_all, bc_type_all, bc_val_all,
        )
        self.assertEqual(len(loads), 1)
        self.assertEqual(loads[0]["trigger_on"], "USER")
        self.assertEqual(loads[0]["bc_types"], ["NONE"] * 6)

    def test_handles_none_values(self):
        loads = reconstruct_loads(
            1,
            [None], [None], [None],
            [None], [None], [None],
            [None],
            [None] * 6, [None] * 6,
        )
        self.assertEqual(len(loads), 1)
        self.assertEqual(loads[0]["trigger_on"], "USER")
        self.assertEqual(loads[0]["repeat"], 1)


class TestSummarizeLoad(unittest.TestCase):
    def test_user_triggers(self):
        load = default_load_structure()
        text = summarize_load(load, 0)
        self.assertIn("Load 0", text)
        self.assertIn("USER", text)

    def test_active_bc_shown(self):
        load = default_load_structure()
        load["bc_types"][0] = "STRESS"
        load["bc_values"][0] = 100.0
        text = summarize_load(load, 1)
        self.assertIn("XX", text)
        self.assertIn("100", text)

    def test_no_bcs_message(self):
        load = default_load_structure()
        text = summarize_load(load, 0)
        self.assertIn("(none)", text)


if __name__ == "__main__":
    unittest.main()
