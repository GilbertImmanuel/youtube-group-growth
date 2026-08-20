"""Video-level causal panel and control matching (Q4, Q5).

Two products, one file:

1. build_panel assembles the video-level panel for the Callaway and Sant'Anna staggered
   DiD (run in Phase 6, not here). One row per long-form, age-passing video on an eligible
   treated member's channel or a matched control's channel: log(views), the channel's
   treatment cohort (the treatment month, null for never-treated controls), the calendar
   month, and the matching weight. A censored member's videos after its censor_date are
   dropped because Callaway and Sant'Anna assumes absorbing treatment.

2. match_controls plus matching_balance are the Karpathy Loop B target (PROJECT_PLAN 8.3).
   The metric is the mean absolute standardised difference between treated members and their
   matched controls on two pre-treatment covariates measured over the 12 months before
   treatment: mean log(views) per long-form video and long-form upload count. The matching
   function selects and weights within the frozen 10-candidate pool per treated
   (config/cohort_controls.csv); it never adds controls, which stay frozen at 0d44234.

Usage:
    python -m src.features.panel                 # write data/processed/panel.parquet
    python -m src.features.panel --eval-matching # print the Loop B metric
"""

import argparse
import math
import os

import numpy as np
import pandas as pd
import yaml

from src.clean.schemas import PANEL_SCHEMA

PROCESSED = os.path.join("data", "processed", "videos.parquet")
COHORT = os.path.join("config", "cohort_groups.csv")
CONTROLS = os.path.join("config", "cohort_controls.csv")
PARAMS = os.path.join("config", "params.yaml")
OUT = os.path.join("data", "processed", "panel.parquet")

_COVARIATES = ["mean_log_views", "n_uploads"]


def load_params(path=PARAMS):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_treated(path=COHORT):
    """Eligible treated members with treatment and censor timing, UTC-aligned."""
    g = pd.read_csv(path)
    t = g[(g["role"] == "member") & (g["eligible_q4q5"])].copy()
    t["treatment_date"] = pd.to_datetime(t["treatment_date"], utc=True)
    t["censor_date"] = pd.to_datetime(t["censor_date"], utc=True)
    return t[["channel_id", "channel_name", "group", "treatment_date", "censor_date"]]


def load_controls(path=CONTROLS):
    """treated_channel_id -> candidate control rows (control_channel_id, distance, flags)."""
    return pd.read_csv(path)


def longform_by_channel(videos):
    """channel_id -> its long-form videos (published_at, view_count), for covariate windows."""
    lf = videos[videos["is_long_form"]][["channel_id", "published_at", "view_count"]]
    return {cid: sub for cid, sub in lf.groupby("channel_id")}


def pretreatment_covariates(chan_videos, treatment_date, months):
    """(mean_log_views, n_uploads) over the months before treatment_date, or None if empty."""
    if chan_videos is None:
        return None
    start = treatment_date - pd.DateOffset(months=months)
    win = chan_videos[(chan_videos["published_at"] >= start)
                      & (chan_videos["published_at"] < treatment_date)]
    if win.empty:
        return None
    views = win["view_count"].clip(lower=1).astype("float64")
    return {"mean_log_views": float(np.log(views).mean()), "n_uploads": float(len(win))}


def match_controls(treated_id, treatment_date, candidates, lf, months, k):
    """Equal weights over the k frozen candidates nearest the treated unit, summing to 1.

    Loop B target. Keeps only candidates with a computable pre-treatment window, ranks
    them by standardised covariate distance to the treated unit, and keeps the k nearest
    (k from config/params.yaml). k=1 is nearest-neighbour matching. When the treated unit
    itself has no pre-treatment covariates, falls back to all usable candidates equally.
    """
    t_cov = pretreatment_covariates(lf.get(treated_id), treatment_date, months)
    usable = []
    for c in candidates.itertuples():
        cov = pretreatment_covariates(lf.get(c.control_channel_id), treatment_date, months)
        if cov is not None:
            usable.append((c.control_channel_id, cov))
    if not usable:
        return {}
    if t_cov is None:
        return {cid: 1.0 / len(usable) for cid, _ in usable}

    # Standardise each covariate across the usable candidates so both contribute distance
    # on a common scale, then keep the k nearest.
    scale = {c: (np.std([cov[c] for _, cov in usable]) or 1.0) for c in _COVARIATES}
    ranked = sorted(usable, key=lambda uc: math.sqrt(
        sum(((uc[1][c] - t_cov[c]) / scale[c]) ** 2 for c in _COVARIATES)))
    kept = ranked[:k]
    return {cid: 1.0 / len(kept) for cid, _ in kept}


def _weighted_mean(pairs):
    """Weighted mean of (value, weight) pairs."""
    total = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / total if total else float("nan")


def matching_balance(videos=None, months=None):
    """Mean absolute standardised difference across covariates, treated vs matched controls."""
    if videos is None:
        videos = pd.read_parquet(PROCESSED, columns=["channel_id", "published_at", "view_count", "is_long_form"])
    params = load_params()
    if months is None:
        months = params["matching_pretreatment_months"]
    k = params["matching_neighbors"]
    treated = load_treated()
    controls = load_controls()
    lf = longform_by_channel(videos)

    treated_vals = {c: [] for c in _COVARIATES}
    control_vals = {c: [] for c in _COVARIATES}
    for t in treated.itertuples():
        t_cov = pretreatment_covariates(lf.get(t.channel_id), t.treatment_date, months)
        if t_cov is None:
            continue
        cand = controls[controls["treated_channel_id"] == t.channel_id]
        weights = match_controls(t.channel_id, t.treatment_date, cand, lf, months, k)
        if not weights:
            continue
        cov_by_control = {
            cid: pretreatment_covariates(lf.get(cid), t.treatment_date, months) for cid in weights
        }
        for c in _COVARIATES:
            treated_vals[c].append(t_cov[c])
            control_vals[c].append(_weighted_mean([(cov_by_control[cid][c], w)
                                                   for cid, w in weights.items()]))

    smd = {}
    for c in _COVARIATES:
        tv, cv = np.array(treated_vals[c]), np.array(control_vals[c])
        pooled = math.sqrt((tv.var(ddof=1) + cv.var(ddof=1)) / 2)
        smd[c] = abs(tv.mean() - cv.mean()) / pooled if pooled > 0 else 0.0
    return {"mean_abs_smd": float(np.mean(list(smd.values()))), "per_covariate": smd,
            "n_treated": len(treated_vals[_COVARIATES[0]])}


def build_panel(videos=None, months=None):
    """Video-level panel: treated members and their weighted matched controls."""
    if videos is None:
        videos = pd.read_parquet(
            PROCESSED, columns=["video_id", "channel_id", "published_at", "view_count",
                                "is_long_form", "passes_age"])
    params = load_params()
    if months is None:
        months = params["matching_pretreatment_months"]
    k = params["matching_neighbors"]
    treated = load_treated()
    controls = load_controls()
    lf = longform_by_channel(videos)

    # channel_id -> (treated?, group, cohort month, censor_date, weight)
    meta = {}
    for t in treated.itertuples():
        meta[t.channel_id] = {"treated": True, "group": t.group,
                              "cohort": t.treatment_date, "censor": t.censor_date, "weight": 1.0}
        cand = controls[controls["treated_channel_id"] == t.channel_id]
        weights = match_controls(t.channel_id, t.treatment_date, cand, lf, months, k)
        cgroup = t.group + " control"
        for cid, w in weights.items():
            if meta.get(cid, {}).get("treated"):
                continue  # channel is itself treated; never relabel it as a control
            # A control can back several treated; keep its largest assigned weight.
            if cid not in meta or w > meta[cid]["weight"]:
                meta[cid] = {"treated": False, "group": cgroup,
                             "cohort": pd.NaT, "censor": pd.NaT, "weight": w}

    keep = videos[videos["is_long_form"] & videos["passes_age"]
                  & videos["channel_id"].isin(meta)
                  & videos["view_count"].notna()].copy()  # no outcome without a view count
    keep["treated"] = keep["channel_id"].map(lambda c: meta[c]["treated"])
    keep["group"] = keep["channel_id"].map(lambda c: meta[c]["group"])
    keep["cohort"] = keep["channel_id"].map(lambda c: meta[c]["cohort"])
    keep["weight"] = keep["channel_id"].map(lambda c: meta[c]["weight"])
    censor = keep["channel_id"].map(lambda c: meta[c]["censor"])
    keep = keep[censor.isna() | (keep["published_at"] <= censor)]

    keep["log_views"] = np.log(keep["view_count"].clip(lower=1).astype("float64"))
    keep["published_month"] = keep["published_at"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
    panel = keep[["video_id", "channel_id", "group", "treated", "cohort",
                  "published_month", "log_views", "weight"]].reset_index(drop=True)
    return panel


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval-matching", action="store_true", help="print the Loop B balance metric")
    args = ap.parse_args()
    if args.eval_matching:
        r = matching_balance()
        per = "  ".join(f"{k}={v:.4f}" for k, v in r["per_covariate"].items())
        print(f"n_treated={r['n_treated']}  {per}")
        print(f"mean_abs_smd={r['mean_abs_smd']:.4f}")
        return
    panel = build_panel()
    PANEL_SCHEMA.validate(panel)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    panel.to_parquet(OUT, index=False)
    months = panel["published_month"]
    print(f"wrote {OUT}: {len(panel)} rows, "
          f"{panel[panel['treated']]['channel_id'].nunique()} treated / "
          f"{panel[~panel['treated']]['channel_id'].nunique()} control channels, "
          f"{panel['cohort'].dropna().nunique()} cohorts, "
          f"{months.min():%Y-%m} to {months.max():%Y-%m}")


if __name__ == "__main__":
    main()
