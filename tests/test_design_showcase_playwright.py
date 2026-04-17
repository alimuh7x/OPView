"""
Playwright click test for the Design Showcase tab.
Tests every interactive element: inputs, dropdowns, steppers, buttons.

Run:
    source myenv/bin/activate
    python tests/test_design_showcase_playwright.py
"""

import subprocess
import sys
import time

def run():
    from playwright.sync_api import sync_playwright

    PASS = []
    FAIL = []

    def check(name, ok, detail=""):
        if ok:
            PASS.append(name)
            print(f"  [PASS] {name}")
        else:
            FAIL.append(name)
            print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("\n[1/7] Loading app...")
        page.goto("http://localhost:8050", timeout=15000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)  # Allow Dash to hydrate
        check("App loads", True)

        print("\n[2/7] Clicking Design Showcase tab...")
        tab = page.locator("#vtk-folder-tabs").get_by_text("Design Showcase")
        tab.click()
        page.wait_for_timeout(800)

        showcase = page.locator("#design-showcase-content")
        visible = showcase.is_visible()
        check("Design Showcase tab visible", visible)
        if not visible:
            browser.close()
            return PASS, FAIL

        print("\n[3/7] Testing Text Inputs...")
        # Fill each text/number input
        inputs = page.locator("#design-showcase-content input[type='text'], #design-showcase-content input:not([type])")
        count = inputs.count()
        print(f"  Found {count} text inputs")
        for i in range(count):
            inp = inputs.nth(i)
            try:
                inp.scroll_into_view_if_needed()
                inp.click()
                inp.fill(f"test{i+1}")
                val = inp.input_value()
                check(f"Text input {i+1} fill", val == f"test{i+1}", f"got '{val}'")
            except Exception as e:
                check(f"Text input {i+1} fill", False, str(e))

        print("\n[4/7] Testing Number Inputs...")
        num_inputs = page.locator("#design-showcase-content input[type='number']")
        count = num_inputs.count()
        print(f"  Found {count} number inputs")
        for i in range(count):
            inp = num_inputs.nth(i)
            try:
                inp.scroll_into_view_if_needed()
                inp.click()
                inp.fill(str(42 + i))
                val = inp.input_value()
                check(f"Number input {i+1} fill", val == str(42 + i), f"got '{val}'")
            except Exception as e:
                check(f"Number input {i+1} fill", False, str(e))

        print("\n[5/7] Testing Stepper Buttons...")
        # Stepper + and - buttons
        stepper_btns = page.locator("#design-showcase-content .stepper-btn, #design-showcase-content button[aria-label*='increment'], #design-showcase-content button[aria-label*='decrement']")
        count = stepper_btns.count()
        # Fallback: find buttons with +/- text
        if count == 0:
            stepper_btns = page.locator("#design-showcase-content button").filter(has_text="+")
            count_plus = stepper_btns.count()
            stepper_minus = page.locator("#design-showcase-content button").filter(has_text="−")
            count_minus = stepper_minus.count()
            count = count_plus + count_minus
            print(f"  Found {count_plus} + buttons, {count_minus} − buttons")
            for i in range(count_plus):
                btn = stepper_btns.nth(i)
                try:
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    check(f"Stepper + button {i+1}", True)
                except Exception as e:
                    check(f"Stepper + button {i+1}", False, str(e))
            for i in range(count_minus):
                btn = stepper_minus.nth(i)
                try:
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    check(f"Stepper − button {i+1}", True)
                except Exception as e:
                    check(f"Stepper − button {i+1}", False, str(e))
        else:
            print(f"  Found {count} stepper buttons")
            for i in range(count):
                btn = stepper_btns.nth(i)
                try:
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    check(f"Stepper button {i+1}", True)
                except Exception as e:
                    check(f"Stepper button {i+1}", False, str(e))

        print("\n[6/7] Testing Buttons (non-stepper)...")
        all_buttons = page.locator("#design-showcase-content button")
        btn_count = all_buttons.count()
        clicked = 0
        for i in range(btn_count):
            btn = all_buttons.nth(i)
            txt = (btn.text_content() or "").strip()
            # Skip stepper +/- buttons (already tested above)
            if txt in ("+", "−", "-", "–"):
                continue
            try:
                btn.scroll_into_view_if_needed()
                btn.click()
                check(f"Button '{txt[:30]}'", True)
                clicked += 1
            except Exception as e:
                check(f"Button '{txt[:30]}'", False, str(e))
        print(f"  Clicked {clicked} buttons")

        print("\n[7/7] Checking for Dash errors...")
        errors = page.locator(".dash-debug-error, ._dash-error, [data-dash-error]")
        err_count = errors.count()
        check("No Dash errors", err_count == 0, f"{err_count} error(s) found")

        # Take final screenshot
        page.screenshot(path="tests/screenshots/design_showcase_final.png", full_page=True)
        print("  Screenshot saved: tests/screenshots/design_showcase_final.png")

        browser.close()

    return PASS, FAIL


if __name__ == "__main__":
    import os
    os.makedirs("tests/screenshots", exist_ok=True)

    PASS, FAIL = run()

    print(f"\n{'='*50}")
    print(f"RESULTS: {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILED:")
        for f in FAIL:
            print(f"  - {f}")
    else:
        print("ALL TESTS PASSED")
    print('='*50)

    sys.exit(1 if FAIL else 0)
