"""Resumable YouTube Data API video pull for the treated and control cohorts.

Pulls every video's cumulative statistics for each cohort channel: the uploads
playlist is paged with playlistItems.list, then videos.list returns duration,
view count, title, and description in batches of 50. Both calls cost 1 unit per
50 items. search.list (100 units) is never used; the uploads playlist is derived
from the channel ID without it.

Quota is capped at 9,500 units per run with a hard stop that saves state and
exits, so the pull resumes on the next quota day from data/raw/.pull_state.json.

Usage:
    python -m src.collect.youtube_api --cohort treated
    python -m src.collect.youtube_api --cohort controls
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.googleapis.com/youtube/v3"
QUOTA_STOP = 9500

RAW_DIR = os.path.join("data", "raw")
VIDEOS_PATH = os.path.join(RAW_DIR, "videos.jsonl")
CHANNEL_META_PATH = os.path.join(RAW_DIR, "channel_meta.jsonl")
STATE_PATH = os.path.join(RAW_DIR, ".pull_state.json")

GROUPS_CSV = os.path.join("config", "cohort_groups.csv")
CONTROLS_CSV = os.path.join("config", "cohort_controls.csv")


class QuotaExceeded(Exception):
    """API returned quotaExceeded. Terminal for the day, not retryable."""


def load_env():
    """Read .env into os.environ if YOUTUBE_API_KEY is not already set."""
    if os.environ.get("YOUTUBE_API_KEY"):
        return
    if not os.path.exists(".env"):
        return
    with open(".env", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def get(endpoint, params, tries=4):
    """GET one API resource, return parsed JSON. Retry 5xx and rateLimit with
    backoff. quotaExceeded raises QuotaExceeded so the caller stops cleanly."""
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 403 and "quotaExceeded" in body:
                raise QuotaExceeded(body)
            # 5xx and 403 rateLimitExceeded are transient. Back off and retry.
            if e.code >= 500 or e.code == 403:
                if attempt == tries - 1:
                    raise
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


def uploads_playlist(channel_id):
    # ponytail: UC->UU holds for standard channels; if one ever fails, fall back
    # to a channels.list call for contentDetails.relatedPlaylists.uploads
    return "UU" + channel_id[2:]


class Quota:
    """Per-run unit counter. stop_before signals a save-and-exit before a call
    that would cross QUOTA_STOP."""

    def __init__(self):
        self.units = 0

    def stop_before(self, cost):
        return self.units + cost > QUOTA_STOP

    def spend(self, cost):
        self.units += cost


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)


def load_channel_ids(cohort):
    ids = []
    if cohort in ("treated", "all"):
        with open(GROUPS_CSV, newline="", encoding="utf-8") as f:
            ids += [r["channel_id"] for r in csv.DictReader(f)]
    if cohort in ("controls", "all"):
        with open(CONTROLS_CSV, newline="", encoding="utf-8") as f:
            ids += [r["control_channel_id"] for r in csv.DictReader(f)]
    # dedupe, preserve order
    seen = set()
    return [c for c in ids if not (c in seen or seen.add(c))]


def append_jsonl(path, records):
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def fetch_channel_meta(channel_ids, quota):
    """channels.list for publishedAt and statistics, batched by 50. Records the
    Sidemen 2015-06-14 value used to check the 11-year claim in PROJECT_PLAN 1.3."""
    key = os.environ["YOUTUBE_API_KEY"]
    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i : i + 50]
        if quota.stop_before(1):
            return
        data = get("channels", {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
            "key": key,
            "maxResults": 50,
        })
        quota.spend(1)
        rows = []
        for item in data.get("items", []):
            rows.append({
                "channel_id": item["id"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"],
                "subscriber_count": item["statistics"].get("subscriberCount"),
                "view_count": item["statistics"].get("viewCount"),
                "video_count": item["statistics"].get("videoCount"),
            })
        append_jsonl(CHANNEL_META_PATH, rows)


def page_video_ids(playlist_id, token, quota):
    """One playlistItems page. Returns (video_ids, next_token). Costs 1 unit."""
    key = os.environ["YOUTUBE_API_KEY"]
    params = {
        "part": "contentDetails",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": key,
    }
    if token:
        params["pageToken"] = token
    data = get("playlistItems", params)
    quota.spend(1)
    ids = [it["contentDetails"]["videoId"] for it in data.get("items", [])]
    return ids, data.get("nextPageToken")


def fetch_videos(video_ids, quota):
    """videos.list for one batch of up to 50 ids. Costs 1 unit."""
    key = os.environ["YOUTUBE_API_KEY"]
    data = get("videos", {
        "part": "snippet,contentDetails,statistics",
        "id": ",".join(video_ids),
        "maxResults": 50,
        "key": key,
    })
    quota.spend(1)
    rows = []
    for item in data.get("items", []):
        rows.append({
            "video_id": item["id"],
            "channel_id": item["snippet"]["channelId"],
            "published_at": item["snippet"]["publishedAt"],
            "duration": item["contentDetails"]["duration"],
            "view_count": item["statistics"].get("viewCount"),
            "like_count": item["statistics"].get("likeCount"),
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
        })
    return rows


def pull(cohort):
    os.makedirs(RAW_DIR, exist_ok=True)
    channels = load_channel_ids(cohort)
    state = load_state()
    quota = Quota()

    # Channel-level metadata for any channel not yet recorded. Cheap, and needed
    # for the group publishedAt check.
    todo_meta = [c for c in channels if not state.get(c, {}).get("meta_done")]
    if todo_meta:
        fetch_channel_meta(todo_meta, quota)
        for c in todo_meta:
            state.setdefault(c, {})["meta_done"] = True
        save_state(state)

    for cid in channels:
        st = state.setdefault(cid, {})
        if st.get("done") or st.get("skipped"):
            continue
        playlist = uploads_playlist(cid)
        token = st.get("page_token")
        count = st.get("video_count", 0)
        try:
            while True:
                # Each page costs 1 (playlistItems) + 1 (videos.list) = 2 units.
                if quota.stop_before(2):
                    save_state(state)
                    print(f"quota stop at {quota.units} units; resume next run")
                    return
                ids, next_token = page_video_ids(playlist, token, quota)
                if ids:
                    append_jsonl(VIDEOS_PATH, fetch_videos(ids, quota))
                    count += len(ids)
                token = next_token
                st["page_token"] = token
                st["video_count"] = count
                save_state(state)
                if not token:
                    break
        except urllib.error.HTTPError as e:
            # Uploads playlist not found: channel deleted, terminated, or the
            # UC->UU transform does not hold for it. Record and keep the run
            # going rather than killing the whole pull on one dead channel.
            if e.code != 404:
                raise
            st["skipped"] = "HTTP 404"
            save_state(state)
            print(f"{cid}: skipped, uploads playlist 404")
            continue
        st["done"] = True
        st.pop("page_token", None)
        save_state(state)
        print(f"{cid}: {count} videos  (run total {quota.units} units)")

    print(f"done. {quota.units} units this run")


def main():
    load_env()
    if not os.environ.get("YOUTUBE_API_KEY"):
        sys.exit("YOUTUBE_API_KEY not set")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", choices=["treated", "controls", "all"], default="treated")
    args = ap.parse_args()
    try:
        pull(args.cohort)
    except QuotaExceeded:
        print("API reported quotaExceeded. State saved; resume next quota day.")


if __name__ == "__main__":
    main()
