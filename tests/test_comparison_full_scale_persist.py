from comparisonmgr.helpers import comparison_handle_range_slider_change


def test_slider_change_preserves_full_scale_true():
    out = comparison_handle_range_slider_change(
        slider_values=[10, 20],
        default_lo=0,
        default_hi=100,
        full_scale_checked=True,
    )
    assert out is not None
    assert out[0] == 10.0
    assert out[1] == 20.0
    assert out[6] is True


def test_slider_change_preserves_full_scale_false_and_sorts_range():
    out = comparison_handle_range_slider_change(
        slider_values=[20, 10],
        default_lo=None,
        default_hi=None,
        full_scale_checked=False,
    )
    assert out is not None
    assert out[0] == 10.0
    assert out[1] == 20.0
    assert out[6] is False


def test_slider_change_invalid_returns_none():
    out = comparison_handle_range_slider_change(
        slider_values=[10],
        default_lo=0,
        default_hi=100,
        full_scale_checked=True,
    )
    assert out is None
