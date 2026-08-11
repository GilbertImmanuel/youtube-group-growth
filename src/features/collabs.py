"""Extract collaborator channel references from video descriptions and titles.

This is the file Karpathy Loop A edits (PROJECT_PLAN 8.3). The metric is F1 of the
extracted cohort collaborators against the viewing-based validation set in
data/validation/labels.csv, computed by `--eval` and wired as `make eval-collabs`.

Ground truth is independent of this parser: labels come from viewing the video
(transcript plus frames), never from the description. So a high F1 means the
description and title text recovers the collaborations that viewing confirms.

Collaborators surface three ways in real cohort descriptions: /channel/UC... links,
/@handle and bare @handle mentions, and legacy /c/ and /user/ links. Handles resolve
to channel IDs through a cohort-only map (config/cohort_handles.json, one API unit to
build via channels.list customUrl). Scoring restricts predictions to cohort channels, so non-cohort noise
(sponsor @tags, instagram and twitter handles) drops out without special-casing.

Usage:
    python -m src.features.collabs --eval
"""

import argparse
import json
import os
import re

import pandas as pd

PROCESSED = os.path.join("data", "processed", "videos.parquet")
LABELS = os.path.join("data", "validation", "labels.csv")
HANDLE_MAP = os.path.join("config", "cohort_handles.json")
COHORT = os.path.join("config", "cohort_groups.csv")

# A channel ID is UC followed by 22 url-safe base64 characters.
_CHANNEL_ID = re.compile(r"/channel/(UC[\w-]{22})")
# youtube.com/@handle, /c/slug, /user/name. Handles allow letters, digits, dot,
# underscore, hyphen. Capturing dots keeps "@ksi.irl" (a tiktok handle) distinct
# from the cohort handle "ksi" rather than truncating it to a false match.
_URL_HANDLE = re.compile(r"youtube\.com/(?:@|c/|user/)([A-Za-z0-9_.-]+)", re.IGNORECASE)
# Bare @mention not part of an email or a longer path token.
_BARE_HANDLE = re.compile(r"(?<![\w/@.])@([A-Za-z0-9_.-]+)")


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


def video_collaborators(title, description, handle_to_id, cohort_ids, own_id=None):
    """Cohort collaborators referenced in one video, excluding the uploader itself."""
    text = f"{title or ''}\n{description or ''}"
    found = resolve_to_cohort(extract_refs(text), handle_to_id, cohort_ids)
    found.discard(own_id)
    return found


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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval", action="store_true", help="score F1 against the validation set")
    args = ap.parse_args()
    if not args.eval:
        ap.print_help()
        return
    r = evaluate()
    print(f"N={r['n']}  TP={r['tp']} FP={r['fp']} FN={r['fn']}")
    print(f"precision={r['precision']:.4f}  recall={r['recall']:.4f}  f1={r['f1']:.4f}")


if __name__ == "__main__":
    main()
