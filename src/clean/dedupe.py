"""Collapse duplicate video IDs and exact re-uploads.

Two sources of duplication:

1. Exact video_id repeats. The raw pull is append-only, so a re-run or a video
   reachable from more than one pulled playlist writes the same ID twice. Keep
   the last-written row, which carries the freshest cumulative stats.
2. Re-uploads. The same content posted again under a new video_id. Collapsed on
   an exact (channel_id, title, duration_seconds) match, keeping the earliest
   publish so treatment timing is not shifted later by a re-post.

Requires a duration_seconds column (added by shorts.parse_duration_seconds).
"""

REUPLOAD_KEY = ["channel_id", "title", "duration_seconds"]


def dedupe(df):
    """Return df with exact-ID duplicates and exact re-uploads removed."""
    out = df.drop_duplicates("video_id", keep="last")
    # ponytail: exact title+duration match only. Fuzzy near-titles (Part 1/Part 2,
    # weekly series) are not merged; add token matching if a validation set exists.
    out = out.sort_values("published_at").drop_duplicates(REUPLOAD_KEY, keep="first")
    return out.reset_index(drop=True)
