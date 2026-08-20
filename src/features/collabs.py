"""Extract collaborator channel references from video descriptions and titles.

This is the file Karpathy Loop A edits (PROJECT_PLAN 8.3). The metric is F1 of the
extracted cohort collaborators against the viewing-based validation set in
data/validation/labels.csv, computed by `--eval` and wired as `make eval-collabs`.

Ground truth is independent of this parser: labels come from viewing the video
(transcript plus frames), never from the description. So a high F1 means the
description and title text recovers the collaborations that viewing confirms.

Collaborators surface four ways in real cohort descriptions: /channel/UC... links,
/@handle and bare @handle mentions, legacy /c/ and /user/ links, and member names.
Handles resolve to channel IDs through a cohort-only map (config/cohort_handles.json,
one API unit to build via channels.list customUrl). Scoring restricts predictions to
cohort channels, so non-cohort noise (sponsor @tags, instagram and twitter handles)
drops out without special-casing.

The name path (ALIASES) is what Loop A added. Sidemen group videos rarely hyperlink
members; each video ends with a fixed "SIDEMEN" roster footer naming members by first
name ("JOSH (Zerkaa)") with bare vanity URLs the URL regex above does not match. Matching
member real names and nicknames recovers those. The footer is a static roster, not a cast
list, so it names members who are absent from a given video; that is the false-positive
floor and the reason F1 stalls at 0.6634 (see loops/collabs/log.md). Aliases are cohort
reference facts (public names and nicknames), independent of the viewing-based labels.

Usage:
    python -m src.features.collabs --eval
"""

import argparse
import itertools
import json
import os
import re

import networkx as nx
import pandas as pd

PROCESSED = os.path.join("data", "processed", "videos.parquet")
LABELS = os.path.join("data", "validation", "labels.csv")
HANDLE_MAP = os.path.join("config", "cohort_handles.json")
COHORT = os.path.join("config", "cohort_groups.csv")
EDGES_OUT = os.path.join("data", "processed", "collab_edges.parquet")
EXTERNAL_OUT = os.path.join("data", "processed", "external_collabs.parquet")

# A channel ID is UC followed by 22 url-safe base64 characters.
_CHANNEL_ID = re.compile(r"/channel/(UC[\w-]{22})")
# youtube.com/@handle, /c/slug, /user/name. Handles allow letters, digits, dot,
# underscore, hyphen. Capturing dots keeps "@ksi.irl" (a tiktok handle) distinct
# from the cohort handle "ksi" rather than truncating it to a false match.
_URL_HANDLE = re.compile(r"youtube\.com/(?:@|c/|user/)([A-Za-z0-9_.-]+)", re.IGNORECASE)
# Bare @mention not part of an email or a longer path token.
_BARE_HANDLE = re.compile(r"(?<![\w/@.])@([A-Za-z0-9_.-]+)")

# Cohort member real names and nicknames, mapped to channel ID. Complements the handle
# map: handles are matched above, these are the names a description uses in prose or in
# the roster footer. Kept to the Sidemen seven plus guests who recur in the validation
# ecosystem; short common-word first names (Simon, Josh, Ethan, Harry) are included
# because in this cohort the precision cost is small and the recall gain is large.
ALIASES = {
    "UCGmnsW623G1r-Chmo5RB4Yw": ("jj", "olajide", "olatunji"),          # KSI
    "UCWZmCMB7mmKWcXJSIPRhzZw": ("simon", "minter"),                    # Miniminter
    "UCvwgF_0NOZe2vN4Q3g1bY-A": ("vik", "vikk", "vikram"),              # Vikkstar123
    "UChntGq8THlUokhc1tT-M2wA": ("josh", "zerk"),                       # Zerkaa
    "UCHhfSXoDG6gSgpOvLH4wrRw": ("ethan",),                             # Behzinga
    "UCfNWN9s_s8kRTCadk04WWJA": ("tobi", "tobjizzle"),                  # TBJZL
    "UCjtLOfx1yt1NlnFIDyAX3Ug": ("harry", "wroetoshaw", "wroe"),        # W2S
    "UCdcUmdOxMrhRjKMw-BX19AA": ("omilana",),                           # Niko Omilana
}
_ALIAS_RE = {
    cid: re.compile(r"\b(?:" + "|".join(re.escape(a) for a in al) + r")\b", re.IGNORECASE)
    for cid, al in ALIASES.items()
}


def extract_refs(text):
    """Return normalised channel references found in text.

    Each reference is 'id:<UC...>' for a /channel/ link or 'handle:<lower>' for a
    handle or @mention. Resolution to channel IDs happens in resolve_to_cohort.
    """
    if not text:
        return set()
    refs = set()
    for m in _CHANNEL_ID.finditer(text):
        refs.add("id:" + m.group(1))
    for m in _URL_HANDLE.finditer(text):
        refs.add("handle:" + m.group(1).lower())
    for m in _BARE_HANDLE.finditer(text):
        refs.add("handle:" + m.group(1).lower())
    return refs


def load_handle_map(path=HANDLE_MAP):
    """channel_id -> customUrl handle, inverted to handle(lower, no @) -> channel_id."""
    raw = json.load(open(path, encoding="utf-8"))
    return {v.lstrip("@").lower(): cid for cid, v in raw.items() if v}


def resolve_to_cohort(refs, handle_to_id, cohort_ids):
    """Map references to cohort channel IDs, dropping anything outside the cohort."""
    out = set()
    for ref in refs:
        kind, val = ref.split(":", 1)
        if kind == "id":
            if val in cohort_ids:
                out.add(val)
        else:
            cid = handle_to_id.get(val)
            if cid:
                out.add(cid)
    return out


def name_hits(text):
    """Cohort channel IDs whose member name or nickname appears in text."""
    return {cid for cid, rx in _ALIAS_RE.items() if rx.search(text)}


def video_collaborators(title, description, handle_to_id, cohort_ids, own_id=None):
    """Cohort collaborators referenced in one video, excluding the uploader itself."""
    text = f"{title or ''}\n{description or ''}"
    found = resolve_to_cohort(extract_refs(text), handle_to_id, cohort_ids)
    found |= name_hits(text) & cohort_ids
    found.discard(own_id)
    return found


def load_group_of(path=COHORT):
    """channel_id -> group name, for every cohort channel."""
    c = pd.read_csv(path)
    return dict(zip(c["channel_id"], c["group"]))


def build_collab_graph(df, handle_to_id, cohort_ids):
    """Bipartite creator-video graph over cohort channels (Q3).

    A creator links to a video when it is the cohort uploader or a cohort collaborator
    named in the title or description. Video nodes are prefixed 'v:' and carry the
    publish timestamp; creator nodes are the 'UC...' channel IDs. Only videos with at
    least one named cohort collaborator are added, since a video with no collaborator
    contributes no edge.
    """
    g = nx.Graph()
    for row in df.itertuples():
        own = row.channel_id
        if own not in cohort_ids:
            continue
        collabs = video_collaborators(row.title, row.description, handle_to_id, cohort_ids, own)
        if not collabs:
            continue
        vnode = "v:" + row.video_id
        g.add_node(vnode, kind="video", published_at=row.published_at)
        g.add_edge(own, vnode)
        for c in collabs:
            g.add_edge(c, vnode)
    return g


def collab_edges(graph, group_of):
    """One row per (video, unordered cohort pair) with a cross-group flag.

    A video's creator neighbours in the bipartite graph are its participants; each pair
    of them co-appeared. cross_group is True when the two belong to different groups,
    which is the external-collaboration condition for Q3.
    """
    rows = []
    for node, data in graph.nodes(data=True):
        if data.get("kind") != "video":
            continue
        people = sorted(graph.neighbors(node))
        for a, b in itertools.combinations(people, 2):
            rows.append({"video_id": node[2:], "published_at": data["published_at"],
                         "a": a, "b": b, "cross_group": group_of.get(a) != group_of.get(b)})
    return pd.DataFrame(rows, columns=["video_id", "published_at", "a", "b", "cross_group"])


def external_collab_counts(edges):
    """Per creator per quarter, the count of distinct cross-group collaboration partners."""
    ext = edges[edges["cross_group"]]
    both = pd.concat([
        ext.rename(columns={"a": "creator", "b": "partner"})[["creator", "partner", "published_at"]],
        ext.rename(columns={"b": "creator", "a": "partner"})[["creator", "partner", "published_at"]],
    ], ignore_index=True)
    both["quarter"] = both["published_at"].dt.tz_localize(None).dt.to_period("Q").dt.to_timestamp()
    return (both.groupby(["creator", "quarter"])["partner"].nunique()
                .reset_index().rename(columns={"partner": "n_external_partners"}))


def load_labels(path=LABELS):
    """video_id -> set of collaborator channel IDs. IDs are ';'-separated in one cell."""
    df = pd.read_csv(path, dtype=str).fillna("")
    return {
        r.video_id: {x for x in r.collaborator_channel_ids.split(";") if x}
        for r in df.itertuples()
    }


def evaluate(labels_path=LABELS):
    labels = load_labels(labels_path)
    handle_to_id = load_handle_map()
    cohort_ids = set(pd.read_csv(COHORT)["channel_id"])

    cols = ["video_id", "channel_id", "title", "description"]
    df = pd.read_parquet(PROCESSED, columns=cols)
    df = df[df["video_id"].isin(labels)].set_index("video_id")

    tp = fp = fn = 0
    for vid, truth in labels.items():
        if vid not in df.index:
            continue  # labelled video absent from the pull; skip, it cannot be scored
        row = df.loc[vid]
        own = row["channel_id"]
        truth = truth - {own}
        pred = video_collaborators(row["title"], row["description"], handle_to_id, cohort_ids, own)
        tp += len(pred & truth)
        fp += len(pred - truth)
        fn += len(truth - pred)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    n = sum(1 for vid in labels if vid in df.index)
    return {"precision": precision, "recall": recall, "f1": f1, "n": n,
            "tp": tp, "fp": fp, "fn": fn}


def run_graph():
    """Build the cohort collaboration graph over the full corpus and write Q3 features."""
    handle_to_id = load_handle_map()
    group_of = load_group_of()
    cohort_ids = set(group_of)
    cols = ["video_id", "channel_id", "published_at", "title", "description"]
    df = pd.read_parquet(PROCESSED, columns=cols)

    graph = build_collab_graph(df, handle_to_id, cohort_ids)
    edges = collab_edges(graph, group_of)
    counts = external_collab_counts(edges)

    edges.to_parquet(EDGES_OUT, index=False)
    counts.to_parquet(EXTERNAL_OUT, index=False)
    n_ext = int(edges["cross_group"].sum())
    print(f"wrote {EDGES_OUT}: {len(edges)} cohort pairs, {n_ext} cross-group")
    print(f"wrote {EXTERNAL_OUT}: {len(counts)} creator-quarter rows, "
          f"{counts['creator'].nunique()} creators with an external collaboration")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval", action="store_true", help="score F1 against the validation set")
    ap.add_argument("--graph", action="store_true", help="build the collaboration graph and Q3 features")
    args = ap.parse_args()
    if args.graph:
        run_graph()
        return
    if not args.eval:
        ap.print_help()
        return
    r = evaluate()
    print(f"N={r['n']}  TP={r['tp']} FP={r['fp']} FN={r['fn']}")
    print(f"precision={r['precision']:.4f}  recall={r['recall']:.4f}  f1={r['f1']:.4f}")


if __name__ == "__main__":
    main()
