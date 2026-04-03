"""
Source-level regression tests for notebook evaluator conflicts.
"""
from __future__ import annotations

import pathlib
import unittest


NOTEBOOK_EVAL = pathlib.Path(__file__).resolve().parents[1] / "utils" / "notebook_eval.py"


class NotebookEvalSourceTests(unittest.TestCase):
    def test_min_uses_callable_float_wrapper(self):
        source = NOTEBOOK_EVAL.read_text(encoding="utf-8")

        self.assertIn("class _CallableFloat(float):", source)
        self.assertIn('"min": _CallableFloat(UNIT_CONSTANTS["min"], _min_arr)', source)


if __name__ == "__main__":
    unittest.main()
