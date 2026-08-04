"""Verify channel IDs in cohort_groups.csv against the YouTube Data API.

Costs 1 quota unit per 50 IDs. Reports missing IDs, name mismatches, and
channel creation dates needed to check the join_date column.

Usage: python verify_cohort.py config/cohort_groups.csv
"""

import csv
import os
import sys
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3/channels"


def fetch(ids, key):
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(ids),
        "key": key,
        "maxResults": 50,
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as r:
        import json

        return json.load(r)


def main(path):
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        sys.exit("YOUTUBE_API_KEY not set")

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    expected = {r["channel_id"]: r for r in rows}
    ids = list(expected)
    print(f"rows: {len(rows)}  unique ids: {len(ids)}")

    if len(rows) != len(ids):
        print("WARNING: duplicate channel_id values present")

    found = {}
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        data = fetch(batch, key)
        for item in data.get("items", []):
            found[item["id"]] = item
        print(f"call {i // 50 + 1}: requested {len(batch)}, returned {len(data.get('items', []))}")

    print("\n--- MISSING (id does not resolve) ---")
    missing = [i for i in ids if i not in found]
    for i in missing:
        print(f"  {i}  expected: {expected[i]['channel_name']}")
    if not missing:
        print("  none")

    print("\n--- NAME MISMATCH (id resolves to a different channel) ---")
    mismatch = 0
    for cid, item in found.items():
        actual = item["snippet"]["title"]
        want = expected[cid]["channel_name"]
        if want.lower().replace(" ", "") not in actual.lower().replace(" ", ""):
            print(f"  {cid}\n    csv:  {want}\n    live: {actual}")
            mismatch += 1
    if not mismatch:
        print("  none")

    print("\n--- CHANNEL CREATION vs JOIN DATE ---")
    for cid, item in found.items():
        created = item["snippet"]["publishedAt"][:10]
        join = expected[cid]["join_date"]
        flag = "  <-- join_date precedes channel creation" if join and join < created else ""
        print(f"  {expected[cid]['channel_name']:<22} created {created}  join {join}{flag}")

    print("\n--- SUBSCRIBER ROUNDING CHECK ---")
    for cid, item in list(found.items())[:5]:
        subs = item["statistics"].get("subscriberCount", "hidden")
        print(f"  {expected[cid]['channel_name']:<22} {subs}")

    print("\n--- UPLOADS PLAYLIST IDS (for the collection step) ---")
    for cid, item in found.items():
        pl = item["contentDetails"]["relatedPlaylists"]["uploads"]
        print(f"  {expected[cid]['channel_name']:<22} {pl}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "config/cohort_groups.csv")
