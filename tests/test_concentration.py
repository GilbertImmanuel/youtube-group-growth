"""Offline tests for the concentration metrics. No data files, small frames only."""

import pandas as pd

from src.features.concentration import concentration, gini, hhi


def test_hhi_single_channel_is_one():
    assert hhi([100]) == 1.0


def test_hhi_known_shares():
    # shares 0.25, 0.25, 0.5 -> 0.0625 + 0.0625 + 0.25
    assert hhi([1, 1, 2]) == 0.375


def test_gini_equal_distribution_is_zero():
    assert gini([5, 5, 5]) == 0.0


def test_gini_rises_with_skew():
    assert gini([0, 0, 10]) > gini([3, 3, 4])


def test_concentration_per_group_month():
    videos = pd.DataFrame({
        "channel_id": ["A", "A", "B", "C"],
        "published_at": pd.to_datetime(
            ["2020-01-05", "2020-01-20", "2020-01-10", "2020-02-01"], utc=True),
        "view_count": [100, 100, 200, 50],
    })
    out = concentration(videos, {"A": "G", "B": "G", "C": "G"})
    jan = out[out["month"] == pd.Timestamp("2020-01-01")].iloc[0]
    # A published 200 in Jan, B published 200: even split.
    assert jan["n_active_channels"] == 2
    assert jan["total_views"] == 400
    assert jan["hhi"] == 0.5
    assert jan["gini"] == 0.0
    feb = out[out["month"] == pd.Timestamp("2020-02-01")].iloc[0]
    assert feb["n_active_channels"] == 1
    assert feb["hhi"] == 1.0
