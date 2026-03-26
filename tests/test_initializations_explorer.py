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


if __name__ == "__main__":
    unittest.main()
