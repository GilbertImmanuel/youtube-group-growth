"""Daily channel-stats snapshot for the treated cohort plus the CORE channels.

Daily view velocity cannot be reconstructed after the fact, so this records a
dated row per channel. Contributes nothing to the current analysis; it exists
only so the series exists later (PROJECT_PLAN Phase 2 note). Run by the snapshot
GitHub Action.

Channels: every channel_id in config/cohort_groups.csv plus the extra channels
in config/snapshot_channels.csv (the 6 CORE members, a prospective follow-up
cohort per PROJECT_PLAN 2.4).

Usage:
    python -m src.collect.snapshot
"""

import csv
import datetime
import os

from src.collect.youtube_api import get, load_env

GROUPS_CSV = os.path.join("config", "cohort_groups.csv")
EXTRA_CSV = os.path.join("config", "snapshot_channels.csv")
OUT = os.path.join("data", "snapshots", "channel_stats.csv")
FIELDS = ["date", "channel_id", "title", "subscriber_count", "view_count", "video_count"]


def snapshot_ids():
    ids = []
    with open(GROUPS_CSV, newline="", encoding="utf-8") as f:
        ids += [r["channel_id"] for r in csv.DictReader(f)]
    if os.path.exists(EXTRA_CSV):
        with open(EXTRA_CSV, newline="", encoding="utf-8") as f:
            ids += [r["channel_id"] for r in csv.DictReader(f)]
    seen = set()
    return [c for c in ids if not (c in seen or seen.add(c))]


def main():
    load_env()
    key = os.environ["YOUTUBE_API_KEY"]
    ids = snapshot_ids()
    today = datetime.date.today().isoformat()

    rows = []
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        data = get("channels", {
            "part": "snippet,statistics",
            "id": ",".join(batch),
            "key": key,
            "maxResults": 50,
        })
        for item in data.get("items", []):
            s = item["statistics"]
            rows.append({
                "date": today,
                "channel_id": item["id"],
                "title": item["snippet"]["title"],
                "subscriber_count": s.get("subscriberCount"),
                "view_count": s.get("viewCount"),
                "video_count": s.get("videoCount"),
            })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)
    print(f"{today}: wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
