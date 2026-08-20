"""Attention concentration per ecosystem per month (Q1).

For each group, an ecosystem is its cohort channels, both the group-role channels and
the member-role individual channels (config/cohort_groups.csv). For each calendar month
the module computes the HHI and Gini of monthly views across those channels, where a
channel's monthly views is the sum of view_count over the videos it published that month.
All videos count, not long-form only: data/processed/videos.parquet keeps every row so
Q1 (all videos) and Q4 (long-form) read the same file through different masks (see
src/clean/build.py).

view_count is cumulative at a single snapshot, so older videos have accrued longer. The
metrics here are within-month cross-channel shares, so the accrual factor common to all
channels active in a month largely cancels in the share. The series is descriptive, not a
causal quantity, and is read alongside the SCOPE 4.1 accrual argument.

Usage:
    python -m src.features.concentration
"""

import os

import pandas as pd

PROCESSED = os.path.join("data", "processed", "videos.parquet")
COHORT = os.path.join("config", "cohort_groups.csv")
OUT = os.path.join("data", "processed", "concentration.parquet")


def hhi(values):
    """Herfindahl-Hirschman index of a list of non-negative values, range 1/n to 1."""
    total = sum(values)
    if total == 0:
        return 0.0
    return sum((v / total) ** 2 for v in values)


def gini(values):
    """Gini coefficient of non-negative values, 0 when equal, rising with concentration."""
    xs = sorted(values)
    n = len(xs)
    total = sum(xs)
    if n == 0 or total == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * total) - (n + 1) / n


def concentration(videos, group_of):
    """One row per (group, month): channel count, total views, HHI, Gini of monthly views."""
    df = videos[videos["channel_id"].isin(group_of)].copy()
    df["group"] = df["channel_id"].map(group_of)
    # tz dropped before to_period: months are UTC wall-time, tz-agnostic by construction.
    df["month"] = df["published_at"].dt.tz_localize(None).dt.to_period("M")
    per_channel = (
        df.groupby(["group", "month", "channel_id"])["view_count"].sum().reset_index()
    )
    rows = []
    for (group, month), g in per_channel.groupby(["group", "month"]):
        views = [v for v in g["view_count"].tolist() if v > 0]
        rows.append(
            {
                "group": group,
                "month": month.to_timestamp(),
                "n_active_channels": len(views),
                "total_views": int(sum(views)),
                "hhi": hhi(views),
                "gini": gini(views),
            }
        )
    return pd.DataFrame(rows).sort_values(["group", "month"]).reset_index(drop=True)


def load_group_of(path=COHORT):
    """channel_id -> group, for every cohort channel."""
    c = pd.read_csv(path)
    return dict(zip(c["channel_id"], c["group"]))


def main():
    group_of = load_group_of()
    videos = pd.read_parquet(PROCESSED, columns=["channel_id", "published_at", "view_count"])
    out = concentration(videos, group_of)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_parquet(OUT, index=False)
    months = out["month"]
    print(f"wrote {OUT}: {len(out)} rows, {out['group'].nunique()} groups, "
          f"{months.min():%Y-%m} to {months.max():%Y-%m}")


if __name__ == "__main__":
    main()
