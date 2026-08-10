"""Quantify unobserved deleted and privatised videos on a Wayback sample.

The API only returns videos that are live now. Videos deleted or privatised
before the snapshot are invisible, which biases any per-channel count. This
measures the size of that gap: enumerate a channel's videos from archived
/videos captures, then report the fraction not present in the pull.

Method and its ceiling: archived channel grids also contain recommendation and
sidebar links to other channels, so an ID absent from the whole pull may be a
deleted cohort video or a link to a non-cohort channel. IDs that resolve to any
collected channel are dropped as alive, but non-cohort recommendations remain in
the numerator. The reported rate is therefore an upper bound on a small sample,
disclosed as illustrative (owner decision 2026-08-10), not a correction applied
to the estimate.

Usage:
    python -m src.clean.deleted_rate
"""

import csv
import os
import re
import socket
import sys
import time
import urllib.request

# The uploads grid and its ytInitialData sit near the top of the archived page,
# so a bounded read avoids pulling multi-MB captures in full.
_MAX_BYTES = 3_000_000
_TIMEOUT = 20

from src.clean.build import RAW_VIDEOS, iter_raw
from src.collect.wayback import captures

GROUPS_CSV = os.path.join("config", "cohort_groups.csv")

# YouTube IDs are 11 chars from [A-Za-z0-9_-]. Match watch, shorts, and the
# ytInitialData "videoId" form so both old and recent captures are covered.
_ID = r"[A-Za-z0-9_-]{11}"
_ID_PATTERNS = [
    re.compile(r"watch\?v=(" + _ID + r")"),
    re.compile(r"/shorts/(" + _ID + r")"),
    re.compile(r'"videoId":"(' + _ID + r')"'),
]


def extract_video_ids(html):
    """Return the set of YouTube video IDs referenced in an archived page."""
    ids = set()
    for pat in _ID_PATTERNS:
        ids.update(pat.findall(html))
    return ids


def deleted_rate(collected_ids, archived_ids):
    """Fraction of archived IDs absent from the collected pull, with counts.
    Returns (rate, n_archived, n_missing)."""
    missing = archived_ids - collected_ids
    n = len(archived_ids)
    return (len(missing) / n if n else 0.0), n, len(missing)


def _videos_page_urls(channel_id, channel_name):
    # /@handle and /user forms carry far fewer captures than /channel, so CDX
    # answers them without timing out.
    name = channel_name.replace(" ", "")
    return [
        f"youtube.com/@{name}/videos",
        f"youtube.com/user/{name}/videos",
        f"youtube.com/channel/{channel_id}/videos",
    ]


def _retry(fn, label, tries=2):
    """Wayback times out intermittently under load. Retry with backoff, then
    give up on this call and let the caller move on."""
    for attempt in range(tries):
        try:
            return fn()
        except Exception as e:
            if attempt == tries - 1:
                print(f"  {label}: {e}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)


def _fetch_archived(timestamp, original):
    # id_ returns the raw archived response without the Wayback toolbar rewrite.
    url = f"http://web.archive.org/web/{timestamp}id_/{original}"
    with urllib.request.urlopen(url, timeout=_TIMEOUT) as r:
        return r.read(_MAX_BYTES).decode("utf-8", "replace")


def archived_ids_for_channel(channel_id, channel_name, max_captures=2):
    """Extract video IDs from a few /videos captures of one channel. No CDX
    filter: filters force a full index scan that times out on these URLs, so
    non-200 captures are dropped in Python instead."""
    ids = set()
    for page in _videos_page_urls(channel_id, channel_name):
        rows = _retry(lambda: captures(page, limit=max_captures), f"cdx {page}")
        for row in (rows or []):
            if row.get("statuscode") != "200":
                continue
            html = _retry(lambda: _fetch_archived(row["timestamp"], row["original"]),
                          f"fetch {row['timestamp']}")
            if html:
                ids |= extract_video_ids(html)
            time.sleep(1)  # be polite to the archive
        if ids:
            break  # first URL form that archives cleanly is enough
    return ids


def _collected_ids():
    return {rec["video_id"] for rec in iter_raw(RAW_VIDEOS)}


def _sample_channels(n):
    with open(GROUPS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # One group channel per distinct ecosystem: group channels archive well, and
    # spreading the sample across groups avoids a Sidemen-only estimate.
    picked, seen = [], set()
    for r in rows:
        if r.get("role") == "group" and r["group"] not in seen:
            picked.append(r)
            seen.add(r["group"])
    return (picked or rows)[:n]


def main(n_channels=5):
    socket.setdefaulttimeout(_TIMEOUT)  # bound CDX and archive calls globally
    all_ids = _collected_ids()
    total_archived, total_missing = 0, 0
    for r in _sample_channels(n_channels):
        cid, name = r["channel_id"], r["channel_name"]
        archived = archived_ids_for_channel(cid, name)
        # Drop IDs alive anywhere in the pull; the remainder is the upper-bound gap.
        rate, n, missing = deleted_rate(all_ids, archived)
        total_archived += n
        total_missing += missing
        print(f"{name}: archived={n} missing={missing} rate={rate:.3f}")
    overall = total_missing / total_archived if total_archived else 0.0
    print(f"\nunobserved-deleted upper bound: {overall:.3f} "
          f"(N={total_archived} archived IDs, {n_channels} channels sampled)")


if __name__ == "__main__":
    main()
