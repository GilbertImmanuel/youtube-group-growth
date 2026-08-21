"""Checks for the descriptive analysis helpers (Phase 5).

Guards the three pieces of non-trivial logic: event-time offset arithmetic, the observable
zero-fill that keeps quiet months from being dropped, and the reciprocity direction rule.
The five aggregate functions read frozen parquets and are exercised by running the module.
"""

import pandas as pd

from src.models.descriptive import (
    _aligned_uploads,
    _reciprocity_rows,
    relative_period,
)


def test_relative_period_month_and_quarter():
    t = pd.Timestamp("2020-01-15", tz="UTC")
    assert relative_period([pd.Timestamp("2020-01-15", tz="UTC")], t, "M")[0] == 0
    # +32 days crosses exactly one month boundary from mid-January.
    assert relative_period([pd.Timestamp("2020-02-16", tz="UTC")], t, "M")[0] == 1
    # +100 days lands in Q2, one quarter after Q1.
    assert relative_period([pd.Timestamp("2020-04-24", tz="UTC")], t, "Q")[0] == 1
    # Signs are preserved before the event.
    assert relative_period([pd.Timestamp("2019-11-15", tz="UTC")], t, "M")[0] == -2


def test_aligned_uploads_fills_observable_zeros():
    # One channel active from month 0, uploading in months 0 and 3 of a 5-month span.
    months = pd.period_range("2020-01", periods=5, freq="M")
    counts = pd.Series([1, 1], index=pd.MultiIndex.from_tuples(
        [("chan", months[0]), ("chan", months[3])]))
    treatment = pd.Timestamp("2020-01-01", tz="UTC")  # rel 0 is the first upload month
    out = dict(_aligned_uploads(counts, "chan", treatment, 0, 4, months[-1]))
    # The quiet months between and after the two uploads are filled with 0, not dropped.
    assert out == {0: 1, 1: 0, 2: 0, 3: 1, 4: 0}
    assert sum(v == 0 for v in out.values()) == 3
    assert sum(out.values()) == 2


def test_aligned_uploads_omits_unobservable_months():
    months = pd.period_range("2020-03", periods=2, freq="M")
    counts = pd.Series([1, 1], index=pd.MultiIndex.from_tuples(
        [("chan", months[0]), ("chan", months[1])]))
    treatment = pd.Timestamp("2020-03-01", tz="UTC")
    # rel -2, -1 predate the first upload; rel +1.. exceed the max month. Only 0 is observable.
    out = dict(_aligned_uploads(counts, "chan", treatment, -2, 2, months[-1]))
    assert set(out) == {0, 1}


def test_reciprocity_rows_direction():
    role = {"G": "group", "M": "member", "X": "member"}
    grp = {"G": "Sidemen", "M": "Sidemen", "X": "Sidemen"}
    up_map = {"v1": "G", "v2": "M", "v3": "M"}
    participants = {
        "v1": {"G", "M"},   # group uploaded, member present -> member_to_group
        "v2": {"M", "G"},   # member uploaded, group present -> group_to_member
        "v3": {"M", "X"},   # member uploaded, member present -> neither direction
    }
    rows = _reciprocity_rows(participants, up_map, role, grp)
    directions = sorted(d for _, d, _ in rows)
    assert directions == ["group_to_member", "member_to_group"]
