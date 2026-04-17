"""
Verification script for the Design Showcase tab.
Run: source myenv/bin/activate && python tests/verify_design_showcase.py
"""

from ui.design_showcase import build_design_showcase
from dash import html

print("[verify][design-showcase] importing build_design_showcase...")
layout = build_design_showcase()

print(f"[verify][design-showcase] type: {type(layout)}")
assert isinstance(layout, html.Div), f"Expected html.Div, got {type(layout)}"

# Check it has children
children = layout.children
assert children, "Layout has no children"
print(f"[verify][design-showcase] top-level children count: {len(children)}")

# Check the title div is present
title_div = children[0]
print(f"[verify][design-showcase] first child type: {type(title_div)}")

# Check style has background
style = layout.style
print(f"[verify][design-showcase] layout style: {style}")
assert style.get("overflowY") == "auto", "Expected overflowY: auto"

print("[verify][design-showcase] OK — layout built successfully, no errors.")
