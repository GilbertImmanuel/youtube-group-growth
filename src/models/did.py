"""Staggered DiD for Q4 and Q5: Sun and Abraham interaction-weighted event study.

Estimator choice (docs/DECISIONS.md, 2026-08-27). The pre-registered primary, Callaway and
Sant'Anna via the `differences` package, runs its point estimates and event study on pandas
3.0.5 but its group-level clustering path is broken by a pandas-3 API change inside the package.
The pre-registered fallback, Sun and Abraham, is used instead at the SCOPE 4.1 video level. It is
a saturated weighted OLS of log(views) on channel and calendar-month fixed effects plus
cohort-by-relative-period interaction indicators; the interaction coefficients are the CATT(c, e)
that aggregate to the event study. Never-treated and not-yet-treated channels are the comparison.

Nothing here is tuned against the estimate (PROJECT_PLAN 8.3, SCOPE 4.4). The specification is
fixed: outcome log_views, channel and calendar-month fixed effects, no covariates, event window
from config/params.yaml, matching weight from the panel, clustering at the ecosystem level. If
the pre-trend fails, that is the finding (PROJECT_PLAN 12): it is reported, not respecified.

Inference is a group-level wild cluster bootstrap over the five ecosystems (a control clusters
with the group it backs). Webb six-point weights are used because 2^5 Rademacher draws are too
few at this cluster count. With five clusters the bootstrap is coarse; the cluster count travels
with every interval as part of N (STYLE rule C) and the precision limit is stated (rule D).

Usage:
    python -m src.models.did
"""

import os

import numpy as np
import pandas as pd
from scipy import sparse

from src.features.panel import (
    load_params,
    load_treated,
    longform_by_channel,
    pretreatment_covariates,
)

PANEL = os.path.join("data", "processed", "panel.parquet")
VIDEOS = os.path.join("data", "processed", "videos.parquet")
FIGURES = os.path.join("outputs", "figures")
TABLES = os.path.join("outputs", "tables")

# Webb six-point weights, mean 0 and variance 1, for the wild cluster bootstrap.
_WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def load_panel(path=PANEL):
    return pd.read_parquet(path)


def prep(panel, lo, hi):
    """Add relative period and ecosystem cluster; drop treated videos outside the window.

    Relative period is published month minus cohort month, in months. Controls carry no cohort,
    so their relative period is undefined and they stay in as the never-treated comparison.
    Treated videos outside [lo, hi] are dropped so they do not enter the baseline; the reference
    period -1 is kept and omitted from the interaction terms.
    """
    p = panel.copy()
    pm = pd.to_datetime(p["published_month"])
    p["pm_int"] = pm.dt.year * 12 + pm.dt.month
    coh = pd.to_datetime(p["cohort"], utc=True).dt.tz_localize(None)
    p["coh_int"] = coh.dt.year * 12 + coh.dt.month
    p["rel"] = p["pm_int"] - p["coh_int"]
    drop = p["treated"].to_numpy() & ~p["rel"].between(lo, hi).to_numpy()
    p = p[~drop].copy()
    p["cluster"] = p["group"].str.replace(" control", "", regex=False)
    return p.reset_index(drop=True)


def collapse(p):
    """Collapse the video panel to channel-month cells, the sufficient statistics for the fit.

    Every video in a (channel, month) shares the same channel, calendar month, cohort, and
    relative period, so the regressors are constant within the cell. Weighted OLS on the cells
    (outcome = weighted mean log_views, weight = summed video weight) is algebraically identical
    to weighted OLS on the videos, for the coefficients and for the cluster scores that drive the
    wild bootstrap. The estimand stays the video-level effect; N is reported as the video count.
    """
    d = p.assign(_wy=p["weight"] * p["log_views"])
    g = d.groupby(["channel_id", "pm_int"], sort=False)
    cells = g[["coh_int", "rel", "cluster", "treated"]].first()
    cells["weight"] = g["weight"].sum()
    cells["log_views"] = g["_wy"].sum() / cells["weight"]
    cells["n_videos"] = g.size()
    return cells.reset_index()


def _absorb(mat, c1, c2, w, iters=500, tol=1e-8):
    """Partial two-way fixed effects out of every column by weighted alternating projection.

    Sparse group-indicator matmuls demean by c1 then c2 until the residual group means fall
    below tol. Both fixed effects are removed exactly at convergence, which is the Frisch-Waugh
    step that lets the reduced design carry only the interaction coefficients.
    """
    g1, g2 = int(c1.max()) + 1, int(c2.max()) + 1
    s1 = sparse.csr_matrix((np.ones(len(c1)), (np.arange(len(c1)), c1)), shape=(len(c1), g1))
    s2 = sparse.csr_matrix((np.ones(len(c2)), (np.arange(len(c2)), c2)), shape=(len(c2), g2))
    ws1 = np.asarray(s1.T @ w).ravel()
    ws2 = np.asarray(s2.T @ w).ravel()
    wv = w[:, None]
    for it in range(iters):
        m1 = (s1.T @ (wv * mat)) / ws1[:, None]
        mat = mat - s1 @ m1
        m2 = (s2.T @ (wv * mat)) / ws2[:, None]
        mat = mat - s2 @ m2
        if it % 5 == 0:
            resid = (s1.T @ (wv * mat)) / ws1[:, None]
            if np.max(np.abs(resid)) < tol:
                break
    return mat


def fit_sa(p):
    """Fit the Sun and Abraham saturated model; return CATT(c, e) and bootstrap ingredients.

    The reduced design holds one column per treated (cohort, relative period) cell other than the
    reference period -1. Fixed effects are absorbed first, then a weighted normal-equation solve
    gives the interaction coefficients. The per-cluster score vectors and the inverse cross-
    product are kept so the wild cluster bootstrap is a linear recombination, not a refit.
    """
    w = p["weight"].to_numpy(float)
    y = p["log_views"].to_numpy(float).reshape(-1, 1)
    ch = pd.factorize(p["channel_id"])[0]
    mo = pd.factorize(p["pm_int"])[0]
    cl = pd.factorize(p["cluster"])[0]

    tr = (p["treated"].to_numpy() & (p["rel"] != -1).to_numpy() & p["rel"].notna().to_numpy())
    coh = p["coh_int"].to_numpy()
    rel = p["rel"].to_numpy()
    keys = [(int(coh[i]), int(rel[i])) for i in np.where(tr)[0]]
    cols = sorted(set(keys))
    col_of = {k: j for j, k in enumerate(cols)}
    n, k = len(p), len(cols)
    D = np.zeros((n, k))
    for i, key in zip(np.where(tr)[0], keys):
        D[i, col_of[key]] = 1.0

    stacked = _absorb(np.hstack([y, D]), ch, mo, w)
    yt, Dt = stacked[:, :1], stacked[:, 1:]

    # Drop cells with no support left after absorption (collinear with the fixed effects).
    norms = np.sqrt((Dt * Dt * w[:, None]).sum(axis=0))
    live = norms > 1e-8 * max(norms.max(), 1.0)
    Dt, live_cols = Dt[:, live], [c for c, keep in zip(cols, live) if keep]
    col_of = {c: j for j, c in enumerate(live_cols)}

    xtx = Dt.T @ (w[:, None] * Dt)
    xtx += 1e-10 * np.eye(xtx.shape[0])  # ponytail: tiny ridge for a stable inverse, negligible vs scale
    ainv = np.linalg.inv(xtx)
    beta = ainv @ (Dt.T @ (w * yt.ravel()))
    resid = yt.ravel() - Dt @ beta

    # Per-cluster score vectors s_g = sum_{i in g} w_i resid_i Dt_i,: for the bootstrap.
    scores = np.zeros((int(cl.max()) + 1, len(live_cols)))
    contrib = (w * resid)[:, None] * Dt
    np.add.at(scores, cl, contrib)

    return {"beta": beta, "cols": live_cols, "col_of": col_of, "ainv": ainv,
            "scores": scores, "n_clusters": int(cl.max()) + 1}


def _agg_matrix(cols, col_of, lo, hi, cohort_counts):
    """Rows mapping CATT(c, e) to ATT(e) and to the overall post ATT, by cohort share.

    ATT(e) is the cohort-share-weighted mean of CATT(c, e) over cohorts observed at e, the Sun and
    Abraham interaction weighting. The overall row is the equal-weight mean of the post-period
    ATT(e) for e in [0, hi]. Returns (L, periods) where L rows align with periods then 'overall'.
    """
    periods = sorted({e for (_, e) in cols})
    rows = []
    for e in periods:
        cs = [(c, e) for (c, e2) in cols if e2 == e]
        tot = sum(cohort_counts[(c, e)] for (c, e) in cs)
        row = np.zeros(len(cols))
        for (c, ee) in cs:
            row[col_of[(c, ee)]] = cohort_counts[(c, ee)] / tot if tot else 0.0
        rows.append(row)
    post = [i for i, e in enumerate(periods) if e >= 0]
    overall = np.mean([rows[i] for i in post], axis=0) if post else np.zeros(len(cols))
    return np.vstack(rows + [overall]), periods


def _cohort_counts(p):
    """(cohort, rel) -> number of distinct treated channels contributing a video there."""
    tr = p[p["treated"] & (p["rel"] != -1) & p["rel"].notna()]
    g = tr.groupby([tr["coh_int"].astype(int), tr["rel"].astype(int)])["channel_id"].nunique()
    return {(int(a), int(b)): int(v) for (a, b), v in g.items()}


def bootstrap(fit, L, iters, seed):
    """Wild cluster bootstrap of L @ beta with Webb weights on the ecosystem clusters.

    Each draw perturbs the per-cluster scores by an independent Webb weight, recombines them
    through the cross-product inverse into a coefficient vector, and maps it through L. Returns a
    (draws, L.rows) array of aggregated statistics.
    """
    rng = np.random.default_rng(seed)
    base = L @ fit["beta"]
    step = (L @ fit["ainv"]) @ fit["scores"].T  # (rows, n_clusters)
    v = rng.choice(_WEBB, size=(iters, fit["n_clusters"]))
    return base + v @ step.T


def estimate(panel, lo, hi, iters, seed):
    """Full event study, overall ATT, and pre-trend test with wild cluster bootstrap intervals.

    Returns a dict of tidy frames plus the raw overall-ATT draws, reused by the placebo module.
    """
    p = prep(panel, lo, hi)
    fit = fit_sa(collapse(p))
    counts = _cohort_counts(p)
    L, periods = _agg_matrix(fit["cols"], fit["col_of"], lo, hi, counts)
    point = L @ fit["beta"]
    draws = bootstrap(fit, L, iters, seed)
    lo_ci, hi_ci = np.percentile(draws, [2.5, 97.5], axis=0)
    se = draws.std(axis=0, ddof=1)

    tr = p[p["treated"] & (p["rel"] != -1) & p["rel"].notna()]
    n_vid = tr.groupby(tr["rel"].astype(int)).size()
    n_ch = tr.groupby(tr["rel"].astype(int))["channel_id"].nunique()
    n_co = tr.groupby(tr["rel"].astype(int))["coh_int"].nunique()

    event = pd.DataFrame({
        "rel_period": periods,
        "att": point[:len(periods)],
        "ci_low": lo_ci[:len(periods)],
        "ci_high": hi_ci[:len(periods)],
        "se": se[:len(periods)],
        "n_videos": [int(n_vid.get(e, 0)) for e in periods],
        "n_channels": [int(n_ch.get(e, 0)) for e in periods],
        "n_cohorts": [int(n_co.get(e, 0)) for e in periods],
    })
    overall = pd.DataFrame({
        "estimate": ["overall_post_att"], "att": [point[-1]],
        "ci_low": [lo_ci[-1]], "ci_high": [hi_ci[-1]], "se": [se[-1]],
        "n_clusters": [fit["n_clusters"]],
        "n_treated_channels": [tr["channel_id"].nunique()],
        "n_videos": [int(len(tr))],
    })

    # Pre-trend sup-t joint test over e in [lo, -2]: is any pre-period ATT distinguishable from 0.
    pre = [i for i, e in enumerate(periods) if e <= -2]
    if pre:
        se_pre = np.where(se[pre] > 0, se[pre], np.nan)
        obs_t = np.nanmax(np.abs(point[pre]) / se_pre)
        null_t = np.nanmax(np.abs(draws[:, pre] - point[pre]) / se_pre, axis=1)
        pval = float((1 + np.sum(null_t >= obs_t)) / (1 + len(null_t)))
    else:
        obs_t, pval = np.nan, np.nan
    pretrend = pd.DataFrame({
        "test": ["pretrend_sup_t"], "periods": [f"[{lo}, -2]"],
        "n_pre_periods": [len(pre)], "sup_t": [obs_t], "p_value": [pval],
        "n_clusters": [fit["n_clusters"]],
    })
    return {"event": event, "overall": overall, "pretrend": pretrend,
            "overall_draws": draws[:, -1], "overall_point": float(point[-1])}


def overall_point(panel, lo, hi):
    """Overall post ATT point estimate only, no bootstrap. The fast path the placebo loop reuses."""
    p = prep(panel, lo, hi)
    if not (p["treated"] & p["rel"].notna()).any():
        return float("nan")
    fit = fit_sa(collapse(p))
    L, _ = _agg_matrix(fit["cols"], fit["col_of"], lo, hi, _cohort_counts(p))
    return float((L @ fit["beta"])[-1])


def q5_size_split(cut="median"):
    """Treated channel_id -> 'large'/'small' by pre-treatment mean log-views, split at the median.

    Size proxy is the mean log(views) per long-form video over the 12 pre-treatment months, the
    same covariate used for control matching (src.features.panel.pretreatment_covariates). The
    pre-registered subscriber percentile is not usable: counts are rounded and only a 2019 control
    snapshot is held (docs/HYPOTHESES.md limitation 4). See docs/DECISIONS.md 2026-08-27.
    """
    videos = pd.read_parquet(VIDEOS, columns=["channel_id", "published_at", "view_count", "is_long_form"])
    lf = longform_by_channel(videos)
    months = load_params()["matching_pretreatment_months"]
    treated = load_treated()
    proxy = {}
    for t in treated.itertuples():
        cov = pretreatment_covariates(lf.get(t.channel_id), t.treatment_date, months)
        if cov is not None:
            proxy[t.channel_id] = cov["mean_log_views"]
    if cut != "median":
        raise ValueError(f"only median split implemented, got {cut!r}")
    return _median_split(proxy)


def _median_split(proxy):
    """channel_id -> 'large'/'small' at the median of the size proxy, and the median value."""
    med = float(np.median(list(proxy.values())))
    return {cid: ("large" if v >= med else "small") for cid, v in proxy.items()}, med


def estimate_q5(panel, lo, hi, iters, seed):
    """Overall ATT per pre-join size arm. Each arm keeps its treated channels plus all controls."""
    arms, med = q5_size_split(load_params().get("q5_split", "median"))
    rows = []
    for arm in ("large", "small"):
        keep_treated = {c for c, a in arms.items() if a == arm}
        sub = panel[(~panel["treated"]) | panel["channel_id"].isin(keep_treated)].copy()
        r = estimate(sub, lo, hi, iters, seed)
        o = r["overall"].iloc[0]
        rows.append({"arm": arm, "n_treated_channels": len(keep_treated),
                     "size_proxy_median": med, "att": o["att"],
                     "ci_low": o["ci_low"], "ci_high": o["ci_high"], "se": o["se"],
                     "n_clusters": int(o["n_clusters"]), "n_videos": int(o["n_videos"])})
    return pd.DataFrame(rows)


def _fig_event(event, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhline(0, color="0.6", lw=0.8)
    ax.axvline(-0.5, color="0.6", lw=0.8, ls="--")
    ax.fill_between(event["rel_period"], event["ci_low"], event["ci_high"], alpha=0.2, color="C0")
    ax.plot(event["rel_period"], event["att"], "o-", ms=3, color="C0")
    ax.set_xlabel("months relative to join")
    ax.set_ylabel("ATT on log(views)")
    ax.set_title("Sun and Abraham event study, 95% wild cluster bootstrap band")
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def _fig_q5(q5, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    y = np.arange(len(q5))
    ax.axvline(0, color="0.6", lw=0.8)
    ax.errorbar(q5["att"], y, xerr=[q5["att"] - q5["ci_low"], q5["ci_high"] - q5["att"]],
                fmt="o", capsize=4, color="C1")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{a} (n={n})" for a, n in zip(q5["arm"], q5["n_treated_channels"])])
    ax.set_xlabel("overall post ATT on log(views)")
    ax.set_title("Q5 overall ATT by pre-join size, 95% band")
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def main():
    os.makedirs(FIGURES, exist_ok=True)
    os.makedirs(TABLES, exist_ok=True)
    params = load_params()
    lo, hi = params["event_window_months"]
    iters = params["wild_bootstrap_iterations"]
    seed = params["rng_seed"]
    panel = load_panel()

    res = estimate(panel, lo, hi, iters, seed)
    q5 = estimate_q5(panel, lo, hi, iters, seed)

    res["event"].to_csv(os.path.join(TABLES, "did_event_study.csv"), index=False)
    res["overall"].to_csv(os.path.join(TABLES, "did_overall_att.csv"), index=False)
    res["pretrend"].to_csv(os.path.join(TABLES, "did_pretrend_test.csv"), index=False)
    q5.to_csv(os.path.join(TABLES, "did_q5_heterogeneity.csv"), index=False)
    _fig_event(res["event"], os.path.join(FIGURES, "did_event_study.svg"))
    _fig_q5(q5, os.path.join(FIGURES, "did_q5_split.svg"))

    o = res["overall"].iloc[0]
    pt = res["pretrend"].iloc[0]
    print(f"overall post ATT={o['att']:.4f} [{o['ci_low']:.4f}, {o['ci_high']:.4f}] "
          f"clusters={int(o['n_clusters'])} treated={int(o['n_treated_channels'])} videos={int(o['n_videos'])}")
    print(f"pretrend sup-t={pt['sup_t']:.4f} p={pt['p_value']:.4f} over {pt['n_pre_periods']} pre-periods")
    for _, r in q5.iterrows():
        print(f"Q5 {r['arm']}: ATT={r['att']:.4f} [{r['ci_low']:.4f}, {r['ci_high']:.4f}] "
              f"n_treated={int(r['n_treated_channels'])}")


if __name__ == "__main__":
    main()
