"""Wayback Machine CDX client. No API key required.

Two uses in this project (both Phase 3): sampling archived watch pages for a
channel to estimate the deleted-video rate, and spot-checking a join-date URL
against its earliest capture.

Usage:
    python -m src.collect.wayback "youtube.com/watch*"
"""

import json
import sys
import urllib.parse
import urllib.request

CDX = "http://web.archive.org/cdx/search/cdx"


def captures(url_pattern, **filters):
    """Return CDX rows as dicts. matchType=prefix on a trailing *, else exact.
    Extra filters pass straight to the CDX API (e.g. from_='2019', collapse=...).
    """
    params = {"url": url_pattern, "output": "json"}
    if url_pattern.endswith("*"):
        params["url"] = url_pattern[:-1]
        params["matchType"] = "prefix"
    # CDX uses `from`/`to`, reserved words in Python, so accept from_/to.
    for k, v in filters.items():
        params[k.rstrip("_")] = v
    url = f"{CDX}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as r:
        rows = json.load(r)
    if not rows:
        return []
    header, *data = rows  # first row is column names
    return [dict(zip(header, row)) for row in data]


if __name__ == "__main__":
    pat = sys.argv[1] if len(sys.argv) > 1 else "en.wikipedia.org/wiki/Sidemen"
    rows = captures(pat, limit=5)
    assert isinstance(rows, list), "captures must return a list"
    for row in rows:
        print(row.get("timestamp"), row.get("original"), row.get("statuscode"))
    print(f"{len(rows)} captures")
