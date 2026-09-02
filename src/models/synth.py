"""Synthetic control for the two named Q6 cases (SCOPE 3, PROJECT_PLAN Phase 7).

Abadie synthetic control on log(views) per long-form video, collapsed to a channel-month
mean series. Two cases:

  KSI exit from the Sidemen, 2026-05-31. Described case only. Under the frozen 180-day age
  filter (SCOPE 4.2) every post-exit long-form video is unobservable, so the post window
  relaxes the age filter for the treated channel and the donors alike (owner decision,
  2026-09-02). The post window runs about 10 weeks to the 2026-08-07 snapshot and no
  conclusion is drawn from it. It carries the SCOPE 4.1 accrual caveat: recent videos have
  accrued few days of views, which depresses the level in the same calendar months for the
  treated channel and its synthetic together.

  Team 10 collapse, treated unit Jake Paul, 2019-09-01 (his config leave_date, just after
  the reported August 2019 raid; owner decision, 2026-09-02). Estimated case. Jake Paul is
  the only Team 10 member with a usable pre-period; Erika Costell has none before her join.

The specification is fixed and not tuned against the post outcome (PROJECT_PLAN 8.3, SCOPE
4.4). Donor selection is by pre-period level proximity, fixed before the post gap is seen.
Inference is an in-space placebo permutation: single-treated-unit conventional standard
errors are not valid, so the treated unit's post/pre RMSPE ratio is ranked against the
donor placebos and reported as a rank and p = rank / n_units.

Usage:
    python -m src.models.synth              # write tables and figures
    python -m src.models.synth --self-check # run the assert-based demo only
"""

import argparse
import os

import numpy as np
import pandas as pd
from scipy.optimize import nnls

from src.features.panel import load_params

VIDEOS = os.path.join("data", "processed", "videos.parquet")
CONTROLS = os.path.join("config", "cohort_controls.csv")
COHORT = os.path.join("config", "cohort_groups.csv")
FIGURES = os.path.join("outputs", "figures")
TABLES = os.path.join("outputs", "tables")

# Frozen age-filter reference date (max published_at, docs/DECISIONS.md 2026-08-10). The KSI
# post window is measured in weeks against it.
SNAPSHOT = pd.Timestamp("2026-08-07")

# Named cases. channel_id and event_date are sourced facts (config/cohort_groups.csv) plus
# the owner decisions of 2026-09-02. first_post_month is the first fully post-event month:
# the KSI exit falls on a month-end so May 2026 is still pre, the Team 10 collapse is dated
# to a month start. relax_post_age lifts the 180-day filter on the post window, KSI only.
# These identify the two cases; they are not tunable thresholds.
CASES = [
    {"name": "KSI", "channel_id": "UCGmnsW623G1r-Chmo5RB4Yw",
     "event_date": "2026-05-31", "first_post_month": "2026-06", "relax_post_age": True},
    {"name": "Team 10", "channel_id": "UCcgVECVN4OKV6DH1jLkqmcA",
     "event_date": "2019-09-01", "first_post_month": "2019-09", "relax_post_age": False},
]


def _monthly(videos, use_age):
    """(channel_id, month) -> mean log(views) over that channel's long-form videos that month."""
    s = videos[videos["is_long_form"]]
    if use_age:
        s = s[s["passes_age"]]
    m = s["published_at"].dt.tz_convert("UTC").dt.tz_localize(None).dt.to_period("M")
    lv = np.log(s["view_count"].clip(lower=1).astype("float64"))
    df = pd.DataFrame({"channel_id": s["channel_id"].to_numpy(),
                       "m": m.to_numpy(), "lv": lv.to_numpy()})
    return df.groupby(["channel_id", "m"])["lv"].mean()


def _chan(monthly, cid):
    """One channel's month -> mean log(views), empty Series if the channel is absent."""
    try:
        return monthly.loc[cid]
    except KeyError:
        return pd.Series(dtype="float64")


def _unit_series(cid, first_post, relax, m_age, m_all):
    """Pre months from the age-filtered series; post months relaxed to all long-form for KSI."""
    pre = _chan(m_age, cid)
    pre = pre[pre.index < first_post]
    post_src = _chan(m_all, cid) if relax else _chan(m_age, cid)
    post = post_src[post_src.index >= first_post]
    return pd.concat([pre, post])


def _rmspe(resid):
    return float(np.sqrt(np.mean(resid ** 2)))


def _fit(y, X, ridge):
    """Synthetic-control weights: simplex-constrained least squares on the pre-period.

    Minimises ||y - Xw||^2 + ridge||w||^2 subject to w >= 0 and sum(w) = 1. Non-negative least
    squares (scipy, already a dependency via src/models/did.py) solves the w >= 0 part; the
    sum-to-1 constraint is a heavy penalty row and the ridge a set of shrinkage rows appended
    to the design, then the result is renormalised. SLSQP is avoided because it crashes
    natively on this Windows scipy build. The tiny ridge only stabilises the weights.
    """
    d = X.shape[1]
    pen = 1e6  # ponytail: large vs the log-views scale (~10-16), so sum(w) lands at 1
    A = np.vstack([X, pen * np.ones((1, d)), np.sqrt(ridge) * np.eye(d)])
    b = np.concatenate([y, [pen], np.zeros(d)])
    w, _ = nnls(A, b, maxiter=2000)
    return w / w.sum() if w.sum() > 0 else np.full(d, 1.0 / d)


def _select_donors(case, params, m_age, m_all):
    """Pre/post month grids, the treated series, and the capped donor matrices.

    A donor is eligible if it is observed in every pre-grid and post-grid month, so the pre
    and post matrices are rectangular. Of the eligible donors the synth_donor_count nearest
    the treated unit by pre-window mean log(views) are kept, a rule fixed before the post gap
    is seen. Full pre-and-post coverage yields 62 (KSI) and 87 (Team 10) eligible donors
    against a cap of 40, so no gap imputation is needed. ponytail: add mean imputation only if
    a future case drops below the cap on coverage.
    """
    first_post = pd.Period(case["first_post_month"], freq="M")
    pre_w = params["synth_pre_window_months"]
    post_w = params["synth_post_window_months"]
    cap = params["synth_donor_count"]

    treated = _unit_series(case["channel_id"], first_post, case["relax_post_age"], m_age, m_all)
    pre = sorted(m for m in treated.index if first_post - pre_w <= m < first_post)
    post = sorted(m for m in treated.index if first_post <= m <= first_post + post_w)
    tpre = treated.reindex(pre).to_numpy()
    tpost = treated.reindex(post).to_numpy()
    tpre_mean = float(np.mean(tpre))

    controls = pd.read_csv(CONTROLS)
    cohort_ids = set(pd.read_csv(COHORT)["channel_id"])
    pool = sorted(set(controls["control_channel_id"]) - cohort_ids - {case["channel_id"]})
    grid = set(pre) | set(post)

    cand = []
    for cid in pool:
        s = _unit_series(cid, first_post, case["relax_post_age"], m_age, m_all)
        if grid <= set(s.index):
            cand.append((cid, float(s.reindex(pre).to_numpy().mean()),
                         s.reindex(pre).to_numpy(), s.reindex(post).to_numpy()))
    cand.sort(key=lambda t: (abs(t[1] - tpre_mean), t[0]))
    cand = cand[:cap]

    ids = [c[0] for c in cand]
    Xpre = np.column_stack([c[2] for c in cand])
    Xpost = np.column_stack([c[3] for c in cand])
    return {"first_post": first_post, "pre": pre, "post": post,
            "tpre": tpre, "tpost": tpost, "ids": ids, "Xpre": Xpre, "Xpost": Xpost}


def _ratio(y_pre, y_post, Xpre, Xpost, ridge):
    """Fit weights on the pre-period and return (weights, pre_rmspe, post/pre RMSPE ratio)."""
    w = _fit(y_pre, Xpre, ridge)
    pre = _rmspe(y_pre - Xpre @ w)
    post = _rmspe(y_post - Xpost @ w)
    ratio = post / pre if pre > 0 else np.inf
    return w, pre, ratio


def run_case(case, params, m_age, m_all):
    """Fit the case, run the in-space placebo, and return tidy frames plus plotting arrays."""
    d = _select_donors(case, params, m_age, m_all)
    ridge = params["synth_ridge"]
    ids, Xpre, Xpost = d["ids"], d["Xpre"], d["Xpost"]

    w, pre_rmspe, treated_ratio = _ratio(d["tpre"], d["tpost"], Xpre, Xpost, ridge)
    synth_pre = Xpre @ w
    synth_post = Xpost @ w
    post_rmspe = _rmspe(d["tpost"] - synth_post)

    # In-space placebo: each donor as placebo-treated, synthetic from the remaining donors.
    n = len(ids)
    placebo_ratios = np.empty(n)
    placebo_gaps = []
    for j in range(n):
        others = [k for k in range(n) if k != j]
        wj, _, rj = _ratio(Xpre[:, j], Xpost[:, j], Xpre[:, others], Xpost[:, others], ridge)
        placebo_ratios[j] = rj
        gap_j = np.concatenate([Xpre[:, j] - Xpre[:, others] @ wj,
                                Xpost[:, j] - Xpost[:, others] @ wj])
        placebo_gaps.append(gap_j)

    ratios_all = np.concatenate([[treated_ratio], placebo_ratios])
    rank = int((ratios_all >= treated_ratio).sum())
    n_units = len(ratios_all)
    p = rank / n_units

    name = case["name"]
    names = pd.read_csv(CONTROLS).drop_duplicates("control_channel_id") \
        .set_index("control_channel_id")["control_name"]
    weights = pd.DataFrame({"case": name, "donor_channel_id": ids,
                            "donor_name": [names.get(c, "") for c in ids], "weight": w})
    weights = weights[weights["weight"] > 1e-4].sort_values("weight", ascending=False)

    # Weeks of post window actually observed: event date to the earlier of the snapshot and
    # the last post-grid month end. For KSI this is the ~10 weeks the exit leaves before the
    # snapshot; for Team 10 it is the capped multi-year post window.
    post_end = min(SNAPSHOT, d["post"][-1].end_time) if d["post"] else SNAPSHOT
    post_weeks = (post_end - pd.Timestamp(case["event_date"])).days / 7.0
    fit = pd.DataFrame([{"case": name, "n_donors": n, "n_pre_months": len(d["pre"]),
                         "n_post_months": len(d["post"]), "post_len_weeks": round(post_weeks, 1),
                         "pre_rmspe": pre_rmspe, "post_rmspe": post_rmspe,
                         "rmspe_ratio": treated_ratio, "mean_post_gap": float(np.mean(d["tpost"] - synth_post)),
                         "treated_rank": rank, "n_units": n_units, "p": p}])

    grid = d["pre"] + d["post"]
    fp = d["first_post"]
    treated_vals = np.concatenate([d["tpre"], d["tpost"]])
    synth_vals = np.concatenate([synth_pre, synth_post])
    gap = pd.DataFrame({"case": name, "month": [str(m) for m in grid],
                        "rel_month": [(m - fp).n for m in grid],
                        "treated": treated_vals, "synthetic": synth_vals,
                        "gap": treated_vals - synth_vals})

    placebo = pd.DataFrame({"case": name, "unit": ids, "is_treated": False,
                            "post_pre_rmspe_ratio": placebo_ratios})
    placebo = pd.concat([pd.DataFrame([{"case": name, "unit": case["channel_id"],
                                        "is_treated": True, "post_pre_rmspe_ratio": treated_ratio,
                                        "treated_rank": rank, "n_units": n_units, "p": p}]),
                         placebo], ignore_index=True)

    plot = {"rel": np.array([(m - fp).n for m in grid]), "treated": treated_vals,
            "synth": synth_vals, "treated_gap": treated_vals - synth_vals,
            "placebo_gaps": placebo_gaps, "name": name, "pre_rmspe": pre_rmspe}
    return {"weights": weights, "fit": fit, "gap": gap, "placebo": placebo, "plot": plot}


def _fig_path(plot, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axvline(-0.5, color="0.6", lw=0.8, ls="--")
    ax.plot(plot["rel"], plot["treated"], "o-", ms=3, color="C0", label=plot["name"])
    ax.plot(plot["rel"], plot["synth"], "s--", ms=3, color="C1", label="synthetic")
    ax.set_xlabel("months relative to event")
    ax.set_ylabel("mean log(views) per long-form video")
    ax.set_title(f"{plot['name']} synthetic control, pre-period RMSPE {plot['pre_rmspe']:.3f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def _fig_placebo(plot, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhline(0, color="0.6", lw=0.8)
    ax.axvline(-0.5, color="0.6", lw=0.8, ls="--")
    for g in plot["placebo_gaps"]:
        ax.plot(plot["rel"], g, color="0.75", lw=0.6, alpha=0.7)
    ax.plot(plot["rel"], plot["treated_gap"], color="C3", lw=1.8, label=plot["name"])
    ax.set_xlabel("months relative to event")
    ax.set_ylabel("gap in mean log(views), treated minus synthetic")
    ax.set_title(f"{plot['name']} gap against donor placebos")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def main():
    os.makedirs(FIGURES, exist_ok=True)
    os.makedirs(TABLES, exist_ok=True)
    params = load_params()
    videos = pd.read_parquet(VIDEOS, columns=["channel_id", "published_at",
                                              "is_long_form", "passes_age", "view_count"])
    m_age = _monthly(videos, True)
    m_all = _monthly(videos, False)

    weights, fits, gaps, placebos = [], [], [], []
    for case in CASES:
        r = run_case(case, params, m_age, m_all)
        weights.append(r["weights"]); fits.append(r["fit"])
        gaps.append(r["gap"]); placebos.append(r["placebo"])
        slug = "ksi" if case["name"] == "KSI" else "team10"
        _fig_path(r["plot"], os.path.join(FIGURES, f"synth_{slug}_path.svg"))
        _fig_placebo(r["plot"], os.path.join(FIGURES, f"synth_{slug}_placebo.svg"))
        f = r["fit"].iloc[0]
        print(f"{case['name']}: donors={int(f['n_donors'])} pre_rmspe={f['pre_rmspe']:.3f} "
              f"post_rmspe={f['post_rmspe']:.3f} ratio={f['rmspe_ratio']:.3f} "
              f"rank={int(f['treated_rank'])}/{int(f['n_units'])} p={f['p']:.3f} "
              f"post_weeks={f['post_len_weeks']}")

    pd.concat(weights, ignore_index=True).to_csv(os.path.join(TABLES, "synth_weights.csv"), index=False)
    pd.concat(fits, ignore_index=True).to_csv(os.path.join(TABLES, "synth_fit.csv"), index=False)
    pd.concat(gaps, ignore_index=True).to_csv(os.path.join(TABLES, "synth_gap.csv"), index=False)
    pd.concat(placebos, ignore_index=True).to_csv(os.path.join(TABLES, "synth_placebo.csv"), index=False)


def demo():
    """Assert-based self-check: exact reconstruction and placebo-rank behaviour."""
    # A donor equal to the treated pre-series takes weight ~1 and drives pre RMSPE to ~0.
    y = np.array([10.0, 11.0, 12.0, 13.0])
    X = np.column_stack([y, np.ones(4), np.linspace(0.0, 1.0, 4)])
    w = _fit(y, X, 1e-6)
    assert abs(w.sum() - 1.0) < 1e-6 and (w >= -1e-9).all(), w
    assert w[0] > 0.98, w
    assert _rmspe(y - X @ w) < 1e-3

    # A treated unit with the largest post/pre RMSPE ratio ranks 1, so p = 1 / n_units.
    ratios = np.array([5.0, 0.4, 0.7, 1.1])  # index 0 is the treated unit
    rank = int((ratios >= ratios[0]).sum())
    assert rank == 1 and abs(rank / len(ratios) - 0.25) < 1e-12
    print("synth self-check passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-check", action="store_true", help="run the assert-based demo only")
    args = ap.parse_args()
    if args.self_check:
        demo()
    else:
        main()
