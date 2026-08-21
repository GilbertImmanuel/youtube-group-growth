"""Descriptive analysis for Q1 to Q3 plus attention share and the reciprocity ledger.

Phase 5, descriptive only. No causal claim is made here (STYLE rule A): the outputs are
associations and event-time coincidences read alongside the SCOPE 4.1 accrual argument, not
treatment effects. Every function reads a frozen feature parquet (data/processed/) and the
cohort file; none recomputes a feature by hand. Thresholds come from config/params.yaml
through src.features.panel.load_params, so the event window is defined in one place.

Five products, each returning a tidy frame plus a per-period summary, with main() writing the
summaries to outputs/tables/ (SVG figures are src/viz/descriptive.py):

1. q1_concentration  HHI and Gini per ecosystem, event-time months around formation.
2. q2_uploads        long-form uploads per month, treated members vs matched controls.
3. q3_external       cross-group collaboration counts, Sidemen ecosystem only (F1-restricted).
4. attention_share   group-channel view share by video publish year.
5. reciprocity_ledger member-to-group vs group-to-member appearances per group.

Usage:
    python -m src.models.descriptive
"""

import os

import numpy as np
import pandas as pd

from src.features.panel import (
    load_controls,
    load_params,
    load_treated,
    longform_by_channel,
    match_controls,
)

VIDEOS = os.path.join("data", "processed", "videos.parquet")
CONCENTRATION = os.path.join("data", "processed", "concentration.parquet")
EXTERNAL = os.path.join("data", "processed", "external_collabs.parquet")
EDGES = os.path.join("data", "processed", "collab_edges.parquet")
COHORT = os.path.join("config", "cohort_groups.csv")
TABLES = os.path.join("outputs", "tables")

# Estimation ecosystems for Q1 and attention share. Dude Perfect (contrast, members have no
# solo channels) and Team 10 (case-study only) carry no member-vs-group contrast, so both are
# excluded here per SCOPE 2.3.
ESTIMATION_GROUPS = ["Sidemen", "OfflineTV", "Beta Squad", "2HYPE", "AMP"]


def relative_period(dates, treatment_date, unit):
    """Signed month or quarter offset of each date from treatment_date, on wall time.

    Timezone is dropped before differencing so an event-time index is UTC wall-time, matching
    the month and quarter buckets built in concentration.py and collabs.py.
    """
    d = pd.DatetimeIndex(pd.to_datetime(dates))
    if d.tz is not None:
        d = d.tz_localize(None)
    t = pd.Timestamp(treatment_date)
    if t.tz is not None:
        t = t.tz_localize(None)
    if unit == "M":
        return (d.year - t.year) * 12 + (d.month - t.month)
    if unit == "Q":
        return (d.year - t.year) * 4 + (d.quarter - t.quarter)
    raise ValueError(f"unit must be 'M' or 'Q', got {unit!r}")


def group_treatment_dates(path=COHORT):
    """group -> formation treatment_date, from the primary group-role row."""
    g = pd.read_csv(path)
    gr = g[(g["role"] == "group") & (g["is_primary"])]
    return {r.group: pd.Timestamp(r.treatment_date) for r in gr.itertuples()}


def _roles(path=COHORT):
    """(channel_id -> role, channel_id -> group) for every cohort channel."""
    g = pd.read_csv(path)
    return dict(zip(g["channel_id"], g["role"])), dict(zip(g["channel_id"], g["group"]))


def q1_concentration():
    """Event-time HHI and Gini per ecosystem, aligned to formation over the params window.

    Returns (tidy, summary). tidy carries one row per (group, rel_month) with a mechanical
    flag for months where fewer than two cohort channels are active, since HHI is 1 there by
    construction rather than by concentration. summary is the cross-group mean and dispersion
    per relative month, computed over non-mechanical rows only, with the contributing group
    count as N.
    """
    lo, hi = load_params()["event_window_months"]
    con = pd.read_parquet(CONCENTRATION)
    treat = group_treatment_dates()
    con = con[con["group"].isin(ESTIMATION_GROUPS)].copy()

    parts = []
    for grp, sub in con.groupby("group"):
        sub = sub.copy()
        sub["rel_month"] = relative_period(sub["month"], treat[grp], "M")
        parts.append(sub)
    con = pd.concat(parts, ignore_index=True)
    con = con[(con["rel_month"] >= lo) & (con["rel_month"] <= hi)].copy()
    con["mechanical"] = con["n_active_channels"] < 2

    tidy = con[["group", "rel_month", "hhi", "gini", "n_active_channels", "mechanical"]] \
        .sort_values(["group", "rel_month"]).reset_index(drop=True)

    # Mask mechanical points so they neither raise the mean nor count toward N.
    hhi_v = tidy["hhi"].where(~tidy["mechanical"])
    gini_v = tidy["gini"].where(~tidy["mechanical"])
    summary = tidy.assign(hhi_v=hhi_v, gini_v=gini_v).groupby("rel_month").agg(
        n_groups=("group", "nunique"),
        n_valid=("hhi_v", "count"),
        mean_hhi=("hhi_v", "mean"), std_hhi=("hhi_v", "std"),
        mean_gini=("gini_v", "mean"), std_gini=("gini_v", "std"),
    ).reset_index()
    return tidy, summary


def _longform_month_counts(videos):
    """(channel_id, month Period) -> long-form upload count, and the global last month."""
    lf = videos[videos["is_long_form"]].copy()
    lf["month"] = lf["published_at"].dt.tz_localize(None).dt.to_period("M")
    counts = lf.groupby(["channel_id", "month"]).size()
    return counts, lf["month"].max()


def _aligned_uploads(counts, channel_id, treatment_date, lo, hi, max_month):
    """(rel_month, uploads) for one channel, 0-filled only where the channel is observable.

    A month before the channel's first long-form upload or after the snapshot's last month is
    not observable, so it is omitted rather than counted as zero output. Observable months with
    no upload are zeros, which keeps the mean from being biased upward by dropping quiet months.
    """
    if channel_id not in counts.index.get_level_values(0):
        return []
    series = counts.loc[channel_id]
    first_month = series.index.min()
    tp = pd.Timestamp(treatment_date).tz_localize(None).to_period("M")
    out = []
    for rel in range(lo, hi + 1):
        cal = tp + rel
        if cal < first_month or cal > max_month:
            continue
        out.append((rel, int(series.get(cal, 0))))
    return out


def q2_uploads(videos=None):
    """Event-time long-form uploads per month, treated members vs their matched controls.

    Controls are the nearest-neighbour matches selected by src.features.panel.match_controls,
    each aligned to the treatment_date of the member it backs. Returns (tidy, summary); summary
    carries the per-arm mean, dispersion, and channel count N per relative month.
    """
    params = load_params()
    lo, hi = params["event_window_months"]
    pre = params["matching_pretreatment_months"]
    k = params["matching_neighbors"]
    if videos is None:
        videos = pd.read_parquet(VIDEOS, columns=["channel_id", "published_at",
                                                  "view_count", "is_long_form"])
    treated = load_treated()
    controls = load_controls()
    lf = longform_by_channel(videos)
    counts, max_month = _longform_month_counts(videos)

    rows = []
    for t in treated.itertuples():
        for rel, n in _aligned_uploads(counts, t.channel_id, t.treatment_date, lo, hi, max_month):
            rows.append(("treated", t.channel_id, rel, n))
        cand = controls[controls["treated_channel_id"] == t.channel_id]
        weights = match_controls(t.channel_id, t.treatment_date, cand, lf, pre, k)
        for cid in weights:
            for rel, n in _aligned_uploads(counts, cid, t.treatment_date, lo, hi, max_month):
                rows.append(("control", cid, rel, n))

    tidy = pd.DataFrame(rows, columns=["arm", "channel_id", "rel_month", "uploads"])
    summary = tidy.groupby(["arm", "rel_month"]).agg(
        n_channels=("channel_id", "nunique"),
        mean_uploads=("uploads", "mean"),
        std_uploads=("uploads", "std"),
    ).reset_index()
    return tidy, summary


def q3_external():
    """Event-time cross-group collaboration counts for Sidemen members around formation.

    Scope restriction (PROJECT_PLAN 12): Loop A F1 stalled at 0.6634, below the 0.75 target, so
    the collaboration measure is Sidemen-ecosystem only and cohort-observable. External here
    means a cross-group cohort partner. The other cohort groups were formed in 2019 or later,
    after this window (2013 to 2017), so a Sidemen member's cohort-observable external count is
    structurally near zero across the window. The series is reported with that limit stated, not
    as a measured decline. Returns (tidy, summary) with the creator count N per relative quarter.
    """
    lo, hi = load_params()["event_window_months"]
    qlo, qhi = int(lo / 3), int(hi / 3)
    ext = pd.read_parquet(EXTERNAL)
    g = pd.read_csv(COHORT)
    members = g[(g["group"] == "Sidemen") & (g["role"] == "member")]["channel_id"].tolist()
    treat = group_treatment_dates()["Sidemen"]

    rows = []
    for cid in members:
        sub = ext[ext["creator"] == cid]
        have = {}
        if not sub.empty:
            relq = relative_period(sub["quarter"], treat, "Q")
            for rq, val in zip(relq, sub["n_external_partners"]):
                have[int(rq)] = int(val)
        for rq in range(qlo, qhi + 1):
            rows.append((cid, rq, have.get(rq, 0)))

    tidy = pd.DataFrame(rows, columns=["creator", "rel_quarter", "n_external_partners"])
    summary = tidy.groupby("rel_quarter").agg(
        n_creators=("creator", "nunique"),
        mean_external_partners=("n_external_partners", "mean"),
        std_external_partners=("n_external_partners", "std"),
    ).reset_index()
    return tidy, summary


def attention_share(videos=None):
    """Group-channel view share of each ecosystem by video publish year.

    Per ecosystem per publish year, group_share is summed view_count of group-role channels
    over summed view_count of all cohort channels. view_count is cumulative at one snapshot, so
    the level carries the same accrual caveat as Q1; the cross-channel share within a year
    largely cancels the common accrual factor. Returns one tidy frame (no separate summary).
    """
    if videos is None:
        videos = pd.read_parquet(VIDEOS, columns=["channel_id", "published_at", "view_count"])
    role, grp = _roles()
    v = videos[videos["channel_id"].isin(role) & videos["view_count"].notna()].copy()
    v["group"] = v["channel_id"].map(grp)
    v = v[v["group"].isin(ESTIMATION_GROUPS)].copy()
    v["year"] = v["published_at"].dt.tz_localize(None).dt.year
    v["is_group"] = v["channel_id"].map(role) == "group"
    v["group_view"] = v["view_count"].where(v["is_group"], 0)

    agg = v.groupby(["group", "year"]).agg(
        all_views=("view_count", "sum"),
        group_views=("group_view", "sum"),
    ).reset_index()
    gc = v[v["is_group"]].groupby(["group", "year"])["channel_id"].nunique()
    mc = v[~v["is_group"]].groupby(["group", "year"])["channel_id"].nunique()
    agg["n_group_channels"] = agg.set_index(["group", "year"]).index.map(gc).fillna(0).astype(int)
    agg["n_member_channels"] = agg.set_index(["group", "year"]).index.map(mc).fillna(0).astype(int)
    agg["all_views"] = agg["all_views"].astype("int64")
    agg["group_views"] = agg["group_views"].astype("int64")
    agg["group_share"] = agg["group_views"] / agg["all_views"].where(agg["all_views"] > 0)
    agg["member_share"] = 1 - agg["group_share"]
    return agg.sort_values(["group", "year"]).reset_index(drop=True)


def _reciprocity_rows(participants, up_map, role, grp):
    """(group, direction, video_id) rows classifying same-group appearances by uploader role.

    member_to_group when a group-role channel uploaded and a same-group member is present;
    group_to_member when a member-role channel uploaded and the same-group group-role channel
    is present. Kept pure so the direction logic is testable without the parquets.
    """
    rows = []
    for vid, people in participants.items():
        uploader = up_map.get(vid)
        if uploader is None:
            continue
        up_role, up_grp = role.get(uploader), grp.get(uploader)
        for p in people:
            if p == uploader or grp.get(p) != up_grp:
                continue
            p_role = role.get(p)
            if up_role == "group" and p_role == "member":
                rows.append((up_grp, "member_to_group", vid))
            elif up_role == "member" and p_role == "group":
                rows.append((up_grp, "group_to_member", vid))
    return rows


def reciprocity_ledger():
    """Per group, member-to-group against group-to-member appearance counts.

    For each collaboration video the participant set is the union of its edge endpoints and the
    uploader is the video's own channel. A same-group appearance is member-to-group when a
    group-role channel uploaded and a member is present, and group-to-member when a member
    uploaded and the group-role channel is present. The asymmetry is the reciprocity quantity
    KSI's claim turns on. Detection reliability differs by direction and by group: member names
    are matched by the alias set, which covers the Sidemen roster densely and other groups
    thinly, so a near-zero group-to-member count is a floor observation, not a proven absence.
    Returns (tidy, ledger); ledger is one row per group with both directions and their ratio.
    """
    edges = pd.read_parquet(EDGES, columns=["video_id", "a", "b"])
    up = pd.read_parquet(VIDEOS, columns=["video_id", "channel_id"])
    up_map = dict(zip(up["video_id"], up["channel_id"]))
    role, grp = _roles()

    participants = {}
    for r in edges.itertuples():
        participants.setdefault(r.video_id, set()).update((r.a, r.b))

    tidy = pd.DataFrame(_reciprocity_rows(participants, up_map, role, grp),
                        columns=["group", "direction", "video_id"])
    counts = tidy.groupby(["group", "direction"]).size().unstack(fill_value=0)
    ledger = counts.reindex(index=ESTIMATION_GROUPS, columns=["member_to_group", "group_to_member"],
                            fill_value=0).reset_index()
    m2g = ledger["member_to_group"]
    ledger["ratio_m2g_over_g2m"] = np.where(ledger["group_to_member"] > 0,
                                            m2g / ledger["group_to_member"].where(ledger["group_to_member"] > 0),
                                            np.nan)
    return tidy, ledger


def main():
    os.makedirs(TABLES, exist_ok=True)
    videos = pd.read_parquet(VIDEOS, columns=["channel_id", "published_at",
                                              "view_count", "is_long_form"])

    _, q1 = q1_concentration()
    _, q2 = q2_uploads(videos)
    _, q3 = q3_external()
    share = attention_share(videos)
    _, ledger = reciprocity_ledger()

    outputs = {
        "q1_concentration.csv": q1,
        "q2_uploads.csv": q2,
        "q3_external_collabs.csv": q3,
        "attention_share.csv": share,
        "reciprocity_ledger.csv": ledger,
    }
    for name, df in outputs.items():
        df.to_csv(os.path.join(TABLES, name), index=False)
        print(f"wrote {os.path.join(TABLES, name)}: {len(df)} rows")

    post = q1[q1["rel_month"] == q1["rel_month"].max()].iloc[0]
    print(f"Q1 last period rel_month={int(post['rel_month'])}: "
          f"mean_hhi={post['mean_hhi']:.3f} mean_gini={post['mean_gini']:.3f} n={int(post['n_valid'])}")
    tre = q2[q2["arm"] == "treated"]
    print(f"Q2 treated pre mean uploads={tre[tre['rel_month'] < 0]['mean_uploads'].mean():.2f} "
          f"post={tre[tre['rel_month'] >= 0]['mean_uploads'].mean():.2f}")
    print(f"Q3 Sidemen creators N={q3['n_creators'].max()}, "
          f"total external partner-quarters={int(q3['mean_external_partners'].mul(q3['n_creators']).sum())}")
    print("reciprocity totals: "
          f"member_to_group={int(ledger['member_to_group'].sum())} "
          f"group_to_member={int(ledger['group_to_member'].sum())}")


if __name__ == "__main__":
    main()
