"""Offline tests for the panel and control matching. Small in-memory frames only."""

import numpy as np
import pandas as pd

import src.features.panel as panel
from src.features.panel import (
    build_panel,
    match_controls,
    matching_balance,
    pretreatment_covariates,
)

TD = pd.Timestamp("2020-01-01", tz="UTC")


def _chan(dates, views):
    return pd.DataFrame({"published_at": pd.to_datetime(dates, utc=True), "view_count": views})


def test_pretreatment_covariates_window_and_log():
    # Window is [2019-01-01, 2020-01-01): the 2018 and 2020 videos fall outside it.
    chan = _chan(["2019-06-01", "2019-12-31", "2018-01-01", "2020-02-01"], [100, 1000, 5, 5])
    cov = pretreatment_covariates(chan, TD, months=12)
    assert cov["n_uploads"] == 2.0
    assert abs(cov["mean_log_views"] - (np.log(100) + np.log(1000)) / 2) < 1e-9
    # An empty window yields None.
    assert pretreatment_covariates(_chan(["2015-01-01"], [10]), TD, months=12) is None


def test_match_controls_k_nearest_and_weights():
    lf = {
        "T": _chan(["2019-06-01"], [100]),
        "C1": _chan(["2019-06-01"], [110]),      # near the treated on views
        "C2": _chan(["2019-06-01"], [1_000_000]),  # far
    }
    candidates = pd.DataFrame({"control_channel_id": ["C1", "C2"]})
    one = match_controls("T", TD, candidates, lf, months=12, k=1)
    assert one == {"C1": 1.0}
    two = match_controls("T", TD, candidates, lf, months=12, k=2)
    assert set(two) == {"C1", "C2"}
    assert abs(sum(two.values()) - 1.0) < 1e-9


def _patch(monkeypatch, treated, controls):
    monkeypatch.setattr(panel, "load_treated", lambda: treated)
    monkeypatch.setattr(panel, "load_controls", lambda: controls)


def test_matching_balance_zero_when_identical(monkeypatch):
    treated = pd.DataFrame({
        "channel_id": ["T1", "T2"], "channel_name": ["a", "b"], "group": ["G", "G"],
        "treatment_date": [TD, TD], "censor_date": [pd.NaT, pd.NaT]})
    controls = pd.DataFrame({"treated_channel_id": ["T1", "T2"],
                             "control_channel_id": ["C1", "C2"]})
    # Each control's pre-treatment history matches its treated unit exactly.
    videos = pd.concat([
        _mk("T1", "2019-06-01", 100), _mk("C1", "2019-06-01", 100),
        _mk("T2", "2019-06-01", 5000), _mk("C2", "2019-06-01", 5000)], ignore_index=True)
    _patch(monkeypatch, treated, controls)
    r = matching_balance(videos=videos, months=12)
    assert r["mean_abs_smd"] == 0.0


def _mk(cid, date, views):
    return pd.DataFrame({"channel_id": [cid], "published_at": pd.to_datetime([date], utc=True),
                         "view_count": pd.array([views], dtype="Int64"), "is_long_form": [True]})


def test_build_panel_censors_and_marks_controls(monkeypatch):
    treated = pd.DataFrame({
        "channel_id": ["T"], "channel_name": ["a"], "group": ["G"],
        "treatment_date": [TD], "censor_date": [pd.Timestamp("2020-06-01", tz="UTC")]})
    controls = pd.DataFrame({"treated_channel_id": ["T"], "control_channel_id": ["C"]})

    def row(cid, vid, date, views):
        return pd.DataFrame({
            "video_id": [vid], "channel_id": [cid],
            "published_at": pd.to_datetime([date], utc=True),
            "view_count": pd.array([views], dtype="Int64"),
            "is_long_form": [True], "passes_age": [True]})

    videos = pd.concat([
        row("T", "t1", "2019-06-01", 100),   # pre-treatment, kept, also feeds covariates
        row("T", "t2", "2020-03-01", 200),   # post-treatment, pre-censor, kept
        row("T", "t3", "2020-09-01", 300),   # post-censor, dropped
        row("C", "c1", "2019-06-01", 90),
        row("C", "c2", "2020-03-01", 180)], ignore_index=True)
    _patch(monkeypatch, treated, controls)
    p = build_panel(videos=videos, months=12)
    assert "t3" not in set(p["video_id"])              # censored video dropped
    assert p.loc[p["channel_id"] == "T", "cohort"].notna().all()
    assert p.loc[p["channel_id"] == "C", "cohort"].isna().all()  # never-treated control
