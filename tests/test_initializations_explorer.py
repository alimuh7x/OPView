import unittest


class QuasiRandomNucleiTests(unittest.TestCase):
    def test_same_seed_produces_same_result(self):
        from utils.initializations_explorer import simulate_quasi_random_nuclei_2d

        first = simulate_quasi_random_nuclei_2d(
            nx=20,
            ny=16,
            offset=(2, 3),
            spacing=(5, 4),
            deviation=(1, 2),
            threshold=0.45,
            seed=42,
        )
        second = simulate_quasi_random_nuclei_2d(
            nx=20,
            ny=16,
            offset=(2, 3),
            spacing=(5, 4),
            deviation=(1, 2),
            threshold=0.45,
            seed=42,
        )

        self.assertEqual(first["origin"], second["origin"])
        self.assertEqual(first["final_points"], second["final_points"])

    def test_origin_falls_back_to_zero_when_offset_or_spacing_exceeds_domain(self):
        from utils.initializations_explorer import simulate_quasi_random_nuclei_2d

        data = simulate_quasi_random_nuclei_2d(
            nx=10,
            ny=12,
            offset=(15, 7),
            spacing=(15, 3),
            deviation=(0, 0),
            threshold=0.0,
            seed=7,
        )

        self.assertEqual(data["origin"], (0, 7))

    def test_zero_deviation_keeps_points_on_the_candidate_lattice(self):
        from utils.initializations_explorer import simulate_quasi_random_nuclei_2d

        data = simulate_quasi_random_nuclei_2d(
            nx=18,
            ny=18,
            offset=(1, 2),
            spacing=(4, 5),
            deviation=(0, 0),
            threshold=0.0,
            seed=3,
        )

        self.assertEqual(data["rejected_out_of_bounds_count"], 0)
        for point in data["final_points"]:
            self.assertEqual(point["x"], point["base_x"])
            self.assertEqual(point["y"], point["base_y"])

    def test_threshold_one_accepts_no_points(self):
        from utils.initializations_explorer import simulate_quasi_random_nuclei_2d

        data = simulate_quasi_random_nuclei_2d(
            nx=16,
            ny=16,
            offset=(0, 0),
            spacing=(4, 4),
            deviation=(2, 2),
            threshold=1.0,
            seed=9,
        )

        self.assertEqual(data["accepted_count"], 0)
        self.assertEqual(data["final_count"], 0)

    def test_final_points_stay_inside_domain(self):
        from utils.initializations_explorer import simulate_quasi_random_nuclei_2d

        data = simulate_quasi_random_nuclei_2d(
            nx=8,
            ny=8,
            offset=(0, 0),
            spacing=(2, 2),
            deviation=(3, 3),
            threshold=0.0,
            seed=11,
        )

        for point in data["final_points"]:
            self.assertGreaterEqual(point["x"], 0)
            self.assertLess(point["x"], 8)
            self.assertGreaterEqual(point["y"], 0)
            self.assertLess(point["y"], 8)


class LayerInitializationTests(unittest.TestCase):
    def test_layer_centerline_has_full_phase_value(self):
        from utils.initializations_explorer import simulate_layer_2d

        data = simulate_layer_2d(
            nx=21,
            ny=21,
            position=(10.0, 10.0),
            orientation=(0.0, 1.0),
            thickness=6.0,
        )

        self.assertAlmostEqual(data["field"][10][10], 1.0)
        self.assertAlmostEqual(data["field"][0][10], 0.0)

    def test_layer_is_symmetric_about_the_center_plane(self):
        from utils.initializations_explorer import simulate_layer_2d

        data = simulate_layer_2d(
            nx=21,
            ny=21,
            position=(10.0, 10.0),
            orientation=(0.0, 1.0),
            thickness=8.0,
        )

        self.assertAlmostEqual(data["field"][7][10], data["field"][13][10])
        self.assertIn(data["field"][7][10], (0.0, 1.0))
        self.assertIn(data["field"][13][10], (0.0, 1.0))

    def test_layer_contains_only_one_phase_mask(self):
        from utils.initializations_explorer import simulate_layer_2d

        data = simulate_layer_2d(
            nx=15,
            ny=15,
            position=(7.0, 7.0),
            orientation=(1.0, 0.0),
            thickness=5.0,
        )

        for row in data["field"]:
            for value in row:
                self.assertIn(value, (0.0, 1.0))


class FractionalInitializationTests(unittest.TestCase):
    def test_fractional_returns_two_phase_fields_that_sum_to_one(self):
        from utils.initializations_explorer import simulate_fractional_2d

        data = simulate_fractional_2d(nx=12, ny=12, minority_layer_thickness=4.0)

        for row_major, row_minority in zip(data["majority"], data["minority"]):
            for major, minor in zip(row_major, row_minority):
                self.assertAlmostEqual(major + minor, 1.0, places=6)
                self.assertIn(major, (0.0, 1.0))
                self.assertIn(minor, (0.0, 1.0))

    def test_fractional_has_minority_phase_below_the_layer_offset(self):
        from utils.initializations_explorer import simulate_fractional_2d

        data = simulate_fractional_2d(nx=10, ny=10, minority_layer_thickness=3.0)

        self.assertGreater(data["minority"][1][5], 0.99)
        self.assertGreater(data["majority"][8][5], 0.99)

    def test_fractional_region_map_has_only_two_labels(self):
        from utils.initializations_explorer import simulate_fractional_2d

        data = simulate_fractional_2d(nx=10, ny=10, minority_layer_thickness=3.0)

        labels = {value for row in data["phase_map"] for value in row}
        self.assertEqual(labels, {0, 1})


class ThreeFractionalsInitializationTests(unittest.TestCase):
    def test_three_fractionals_tracks_three_regions(self):
        from utils.initializations_explorer import simulate_three_fractionals_2d

        data = simulate_three_fractionals_2d(
            nx=12,
            ny=16,
            majority_phase_layer_thickness=4.0,
            minority_phase_layer_thickness1=5.0,
        )

        self.assertGreater(data["phase1"][1][6], 0.99)
        self.assertGreater(data["phase2"][6][6], 0.99)
        self.assertGreater(data["phase3"][13][6], 0.99)

    def test_three_fractionals_fields_sum_to_one(self):
        from utils.initializations_explorer import simulate_three_fractionals_2d

        data = simulate_three_fractionals_2d(
            nx=8,
            ny=12,
            majority_phase_layer_thickness=3.0,
            minority_phase_layer_thickness1=4.0,
        )

        for r1, r2, r3 in zip(data["phase1"], data["phase2"], data["phase3"]):
            for p1, p2, p3 in zip(r1, r2, r3):
                self.assertAlmostEqual(p1 + p2 + p3, 1.0, places=6)
                self.assertIn(p1, (0.0, 1.0))
                self.assertIn(p2, (0.0, 1.0))
                self.assertIn(p3, (0.0, 1.0))

    def test_three_fractionals_region_map_has_three_labels(self):
        from utils.initializations_explorer import simulate_three_fractionals_2d

        data = simulate_three_fractionals_2d(
            nx=8,
            ny=12,
            majority_phase_layer_thickness=3.0,
            minority_phase_layer_thickness1=4.0,
        )

        labels = {value for row in data["phase_map"] for value in row}
        self.assertEqual(labels, {0, 1, 2})


class AdditionalInitializationExplorerTests(unittest.TestCase):
    def test_single_fills_entire_domain_with_one_phase(self):
        from utils.initializations_explorer import simulate_single_2d

        data = simulate_single_2d(nx=8, ny=6)
        labels = {value for row in data["phase_map"] for value in row}
        self.assertEqual(labels, {0})

    def test_sectional_plane_splits_domain(self):
        from utils.initializations_explorer import simulate_sectional_plane_2d

        data = simulate_sectional_plane_2d(
            nx=10,
            ny=10,
            point=(5.0, 5.0),
            orientation=(0.0, 1.0),
        )

        self.assertEqual(data["phase_map"][2][5], 1)
        self.assertEqual(data["phase_map"][8][5], 0)

    def test_two_walls_use_same_phase_on_both_sides(self):
        from utils.initializations_explorer import simulate_two_walls_2d

        data = simulate_two_walls_2d(nx=12, ny=12, walls_thickness=2.0)

        self.assertEqual(data["phase_map"][0][4], 0)
        self.assertEqual(data["phase_map"][11][4], 0)
        self.assertEqual(data["phase_map"][6][4], 1)

    def test_voronoi_uses_one_phase_color_with_boundary_overlay(self):
        from utils.initializations_explorer import simulate_voronoi_tessellation_2d

        data = simulate_voronoi_tessellation_2d(nx=20, ny=20, ngrains=5, seed=1)

        labels = {value for row in data["phase_map"] for value in row}
        self.assertEqual(labels, {0})
        self.assertEqual(len(data["markers"]), 5)
        self.assertGreater(len(data["boundary_points"]), 0)


if __name__ == "__main__":
    unittest.main()
