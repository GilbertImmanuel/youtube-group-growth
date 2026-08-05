"""search.list (100 units) is banned project-wide (PROJECT_PLAN Section 5).
The collector must reach uploads playlists without it. This fails if the
search endpoint is reintroduced."""

import pathlib

# The ban is on YouTube's search.list, so it applies to the API client, not to
# unrelated endpoints elsewhere (Wayback CDX also has a /search path).
API = pathlib.Path(__file__).resolve().parents[1] / "src" / "collect" / "youtube_api.py"


def test_no_search_endpoint():
    # get() takes the endpoint as its first argument, e.g. get("videos", ...).
    # A search call would be get("search", ...); the quoted token only appears
    # if the endpoint is invoked, not where the ban is documented in prose.
    src = API.read_text(encoding="utf-8")
    assert '"search"' not in src, "youtube_api.py invokes the banned search endpoint"
    assert "'search'" not in src, "youtube_api.py invokes the banned search endpoint"
