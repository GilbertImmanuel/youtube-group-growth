"""Offline tests for the Phase 3 cleaning functions. No network, no raw data."""

import pandas as pd
import pytest
from pandera.errors import SchemaErrors

from src.clean.dedupe import dedupe
from src.clean.deleted_rate import deleted_rate, extract_video_ids
from src.clean.schemas import validate_videos
from src.clean.shorts import long_form_mask, parse_duration_seconds


def test_parse_duration_seconds():
    s = parse_duration_seconds(pd.Series(["PT2H13M22S", "PT40S", "PT0S", "P0D", ""]))
    assert list(s[:4]) == [8002.0, 40.0, 0.0, 0.0]
    assert pd.isna(s.iloc[4])  # empty duration is unparseable, not zero


def test_long_form_boundaries():
    seconds = pd.Series([60.0, 61.0, 180.0, 181.0])
    # At or below the threshold is a short, so the split is a strict greater-than.
    assert list(long_form_mask(seconds, 60)) == [False, True, True, True]
    assert list(long_form_mask(seconds, 180)) == [False, False, False, True]


def _df(rows):
    return pd.DataFrame(rows)


def test_dedupe_exact_id_keeps_freshest():
    # Same video_id appended twice; the later row has fresher view_count.
    df = _df([
        {"video_id": "a", "channel_id": "c1", "title": "t", "duration_seconds": 100.0,
         "published_at": pd.Timestamp("2020-01-01", tz="UTC"), "view_count": 10},
        {"video_id": "a", "channel_id": "c1", "title": "t", "duration_seconds": 100.0,
         "published_at": pd.Timestamp("2020-01-01", tz="UTC"), "view_count": 99},
    ])
    out = dedupe(df)
    assert len(out) == 1
    assert out.iloc[0]["view_count"] == 99


def test_dedupe_reupload_keeps_earliest():
    # Distinct IDs, identical channel+title+duration: a re-upload. Keep the first.
    df = _df([
        {"video_id": "orig", "channel_id": "c1", "title": "same", "duration_seconds": 300.0,
         "published_at": pd.Timestamp("2019-06-01", tz="UTC"), "view_count": 5},
        {"video_id": "repost", "channel_id": "c1", "title": "same", "duration_seconds": 300.0,
         "published_at": pd.Timestamp("2021-06-01", tz="UTC"), "view_count": 5},
    ])
    out = dedupe(df)
    assert len(out) == 1
    assert out.iloc[0]["video_id"] == "orig"


def _valid_video_df():
    return _df([
        {"video_id": "v1", "channel_id": "c1", "published_at": "2020-01-01T00:00:00Z",
         "duration": "PT5M", "view_count": 10, "like_count": 1, "title": "t", "description": "d"},
        {"video_id": "v2", "channel_id": "c1", "published_at": "2020-02-01T00:00:00Z",
         "duration": "PT6M", "view_count": 20, "like_count": 2, "title": "u", "description": "e"},
    ])


def test_schema_accepts_valid():
    validate_videos(_valid_video_df())  # coerces and passes


def test_schema_rejects_negative_count():
    bad = _valid_video_df()
    bad.loc[0, "view_count"] = -1
    with pytest.raises(SchemaErrors):
        validate_videos(bad)


def test_schema_rejects_null_id():
    bad = _valid_video_df()
    bad.loc[0, "video_id"] = None
    with pytest.raises(SchemaErrors):
        validate_videos(bad)


def test_schema_rejects_duplicate_id():
    bad = _valid_video_df()
    bad.loc[1, "video_id"] = "v1"
    with pytest.raises(SchemaErrors):
        validate_videos(bad)


def test_age_filter_boundary():
    ref = pd.Timestamp("2026-08-02", tz="UTC")
    published = pd.to_datetime(
        pd.Series(["2026-02-03", "2026-02-04"]), utc=True  # 180 and 179 days before ref
    )
    age_days = (ref - published).dt.days
    passes = age_days >= 180
    assert list(age_days) == [180, 179]
    assert list(passes) == [True, False]


def test_extract_video_ids():
    html = (
        'href="/watch?v=abcdefghijk" '
        'href="/shorts/ABCDEFGHIJK" '
        '{"videoId":"0123456789_"}'
    )
    assert extract_video_ids(html) == {"abcdefghijk", "ABCDEFGHIJK", "0123456789_"}


def test_deleted_rate():
    collected = {"alive1", "alive2"}
    archived = {"alive1", "gone1", "gone2"}  # two absent from the pull
    rate, n, missing = deleted_rate(collected, archived)
    assert (n, missing) == (3, 2)
    assert rate == pytest.approx(2 / 3)
