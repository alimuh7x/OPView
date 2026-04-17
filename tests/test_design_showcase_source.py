"""
Source-level regression checks for the Design Showcase tab.
"""

from __future__ import annotations

import pathlib
import unittest


SHOWCASE_UI = pathlib.Path(__file__).resolve().parents[1] / "ui" / "design_showcase.py"


class DesignShowcaseSourceTests(unittest.TestCase):
    def test_design_showcase_tracks_agents_md_standards(self):
        source = SHOWCASE_UI.read_text(encoding="utf-8")

        self.assertIn('"padding": "8px 11px"', source)
        self.assertIn('"background": "linear-gradient(180deg, #ffffff 0%, #fafbfc 100%)"', source)
        self.assertIn('"borderRadius": "7px"', source)
        self.assertIn('"minHeight": "32px"', source)
        self.assertIn('"Small dropdowns — inline in a multi-field row"', source)
        self.assertIn('className="opview-image-add-btn"', source)
        self.assertIn('className="opview-image-close-btn"', source)
        self.assertIn('src="/assets/Reset.png"', source)
        self.assertIn('print("[debug][design-showcase] _typography_section:start"', source)
        self.assertIn('print("[debug][design-showcase] _graph_section:done"', source)


if __name__ == "__main__":
    unittest.main()
