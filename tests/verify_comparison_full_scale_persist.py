from comparisonmgr.helpers import comparison_handle_range_slider_change


def main():
    print("[verify][comparison-range] case 1: full_scale_checked=True slider=[10, 20]")
    out = comparison_handle_range_slider_change(
        slider_values=[10, 20],
        default_lo=0,
        default_hi=100,
        full_scale_checked=True,
    )
    print(f"[verify][comparison-range] out={out}")

    print("[verify][comparison-range] case 2: full_scale_checked=False slider=[20, 10] (unsorted)")
    out = comparison_handle_range_slider_change(
        slider_values=[20, 10],
        default_lo=None,
        default_hi=None,
        full_scale_checked=False,
    )
    print(f"[verify][comparison-range] out={out}")

    print("[verify][comparison-range] case 3: invalid slider -> None")
    out = comparison_handle_range_slider_change(
        slider_values=[10],
        default_lo=0,
        default_hi=100,
        full_scale_checked=True,
    )
    print(f"[verify][comparison-range] out={out}")


if __name__ == "__main__":
    main()
