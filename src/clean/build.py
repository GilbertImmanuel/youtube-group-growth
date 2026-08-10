"""Build data/processed/videos.parquet from the raw pull.

Pipeline: load the append-only raw jsonl, coerce dtypes, parse durations, remove
duplicate IDs and re-uploads, validate against the pandera contract, add the
long-form and age flags at the config thresholds, and write one parquet. The
output keeps every deduped row with derived flag columns rather than dropping
rows, so Q1 (all videos) and Q4 (long-form, aged) read the same file through
different masks. Re-runnable: the parquet is overwritten each run.

Every threshold comes from config/params.yaml. The age reference date is the
newest publish date in the data, printed so the number is reproducible per style
rule B.

Usage:
    python -m src.clean.build
"""

import json
import os

import pandas as pd
import yaml

from src.clean.dedupe import dedupe
from src.clean.schemas import validate_channels, validate_videos
from src.clean.shorts import long_form_mask, parse_duration_seconds

RAW_DIR = os.path.join("data", "raw")
RAW_VIDEOS = os.path.join(RAW_DIR, "videos.jsonl")
RAW_CHANNELS = os.path.join(RAW_DIR, "channel_meta.jsonl")
PROCESSED = os.path.join("data", "processed", "videos.parquet")
PARAMS = os.path.join("config", "params.yaml")

_COUNTS = ["view_count", "like_count"]


def load_params():
    with open(PARAMS, encoding="utf-8") as f:
        return yaml.safe_load(f)


def iter_raw(path):
    """Yield one dict per jsonl line. Used where only a few fields are needed."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def _coerce_videos(df):
    # ISO8601, not a fixed format: some timestamps carry fractional seconds.
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, format="ISO8601")
    for col in _COUNTS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("video_id", "channel_id", "duration", "title"):
        df[col] = df[col].astype("string")
    df["description"] = df["description"].astype("string")
    return df


def build(params, reference_date=None):
    df = pd.read_json(RAW_VIDEOS, lines=True, dtype=False, convert_dates=False)
    raw_n = len(df)
    df = _coerce_videos(df)
    df["duration_seconds"] = parse_duration_seconds(df["duration"])

    df = dedupe(df)
    deduped_n = len(df)
    validate_videos(df)

    thr = params["shorts_threshold_seconds"]
    thr_sens = params["shorts_threshold_sensitivity_seconds"]
    df["is_long_form"] = long_form_mask(df["duration_seconds"], thr)
    df["is_long_form_sensitivity"] = long_form_mask(df["duration_seconds"], thr_sens)

    ref = pd.Timestamp(reference_date, tz="UTC") if reference_date else df["published_at"].max()
    df["age_days"] = (ref - df["published_at"]).dt.days
    df["passes_age"] = df["age_days"] >= params["min_video_age_days"]

    longform_n = int(df["is_long_form"].sum())
    aged_n = int((df["is_long_form"] & df["passes_age"]).sum())

    os.makedirs(os.path.dirname(PROCESSED), exist_ok=True)
    df.to_parquet(PROCESSED, index=False)

    print(f"reference date: {ref.date()}")
    print(f"raw:          {raw_n}")
    print(f"deduped:      {deduped_n}")
    print(f"long-form:    {longform_n}  (> {thr}s)")
    print(f"age-filtered: {aged_n}  (long-form and >= {params['min_video_age_days']} days)")
    print(f"wrote {PROCESSED}")
    return df


def validate_channel_meta():
    ch = pd.DataFrame(iter_raw(RAW_CHANNELS))
    ch = ch.drop_duplicates("channel_id", keep="last")
    ch["published_at"] = pd.to_datetime(ch["published_at"], utc=True, format="ISO8601")
    for col in ("channel_id", "title"):
        ch[col] = ch[col].astype("string")
    for col in ("subscriber_count", "view_count", "video_count"):
        ch[col] = pd.to_numeric(ch[col], errors="coerce").astype("Int64")
    validate_channels(ch)
    print(f"channels validated: {len(ch)}")


def main():
    params = load_params()
    validate_channel_meta()
    build(params)


if __name__ == "__main__":
    main()
