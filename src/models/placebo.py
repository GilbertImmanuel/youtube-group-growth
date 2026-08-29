"""Placebo checks for the Q4 and Q5 estimate. Protected from deletion (PROJECT_PLAN 8.4).

Placebo and pre-trend checks are the evidence that the estimate can be read causally, so this
module is not scaffolding and ponytail must not cut it. Two placebos reuse the Sun and Abraham
estimator in src.models.did without change:

1. fake_join_dates: each treated channel keeps only its true pre-treatment videos and is given a
   fake join month drawn at random inside that pre-period, so any estimated effect is spurious. A
   distribution that sits off zero signals that the machinery, or a pre-trend, manufactures an
   effect where none can exist.
2. controls_only: control channels are split at random into fake-treated and fake-control, the
   fake-treated get random join months, and no channel is truly treated. The estimate should
   centre on zero; a shift off zero signals a spurious-detection problem in the design.

The real overall ATT from src.models.did is located against each distribution and reported as the
share of placebo draws at least as extreme.

Usage:
    python -m src.models.placebo
"""

import os

import numpy as np
import pandas as pd

from src.features.panel import load_params
from src.models.did import FIGURES, TABLES, load_panel, overall_point


def _ts(month_int):
    """Calendar-month integer (year*12 + month) back to a UTC month-start timestamp."""
    y, m = divmod(int(month_int) - 1, 12)
    return pd.Timestamp(year=y, month=m + 1, day=1, tz="UTC")


def _month_int(published_month):
    pm = pd.to_datetime(published_month)
    return pm.dt.year * 12 + pm.dt.month


def _fake_cohort(pm_ints, rng, margin):
    """A random join month strictly inside [min+margin, max-margin], or None if the span is short."""
    lo, hi = int(pm_ints.min()) + margin, int(pm_ints.max()) - margin
    if hi <= lo:
        return None
    return int(rng.integers(lo, hi + 1))


def _pre_frames(panel):
    """Per treated channel, its videos strictly before its true join, and the pm span for draws."""
    pm = _month_int(panel["published_month"])
    coh = pd.to_datetime(panel["cohort"], utc=True).dt.tz_localize(None)
    coh_int = coh.dt.year * 12 + coh.dt.month
    frames = {}
    for cid, sub in panel[panel["treated"]].groupby("channel_id"):
        idx = sub.index
        pre = sub[pm[idx] < int(coh_int[idx].iloc[0])]
        if len(pre) >= 2:
            frames[cid] = pre.assign(treated=True)
    return frames


def fake_join_dates(panel, lo, hi, iters, seed, margin):
    """Overall ATT under fake pre-period join dates, treated channels keep only pre-true videos."""
    controls = panel[~panel["treated"]]
    frames = {cid: (f, _month_int(f["published_month"])) for cid, f in _pre_frames(panel).items()}
    rng = np.random.default_rng(seed)

    out = []
    for _ in range(iters):
        parts = [controls]
        for cid, (f, pmints) in frames.items():
            fake = _fake_cohort(pmints, rng, margin)
            if fake is not None:
                parts.append(f.assign(cohort=_ts(fake)))
        out.append(overall_point(pd.concat(parts, ignore_index=True), lo, hi))
    return np.array(out, float)


def controls_only(panel, lo, hi, iters, seed, margin):
    """Overall ATT when only control channels are used, half assigned fake treatment at random."""
    controls = panel[~panel["treated"]].copy()
    ids = controls["channel_id"].unique()
    frames = {cid: (sub, _month_int(sub["published_month"]))
              for cid, sub in controls.groupby("channel_id")}
    rng = np.random.default_rng(seed)

    out = []
    for _ in range(iters):
        fake_treated = set(rng.permutation(ids)[: len(ids) // 2])
        parts = []
        for cid, (sub, pmints) in frames.items():
            fake = _fake_cohort(pmints, rng, margin) if cid in fake_treated else None
            if fake is None:
                parts.append(sub.assign(cohort=pd.NaT, treated=False))
            else:
                parts.append(sub.assign(cohort=_ts(fake), treated=True))
        out.append(overall_point(pd.concat(parts, ignore_index=True), lo, hi))
    return np.array(out, float)


def _summary(name, draws, real):
    d = draws[~np.isnan(draws)]
    return {"placebo": name, "n_draws": int(len(d)),
            "mean": float(d.mean()), "sd": float(d.std(ddof=1)),
            "q025": float(np.percentile(d, 2.5)), "q975": float(np.percentile(d, 97.5)),
            "real_att": float(real),
            "share_ge_real": float(np.mean(np.abs(d) >= abs(real)))}


def _figure(dists, real, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(dists), figsize=(9, 3.6), sharey=True)
    for ax, (name, d) in zip(np.atleast_1d(axes), dists.items()):
        d = d[~np.isnan(d)]
        ax.hist(d, bins=30, color="C0", alpha=0.7)
        ax.axvline(0, color="0.6", lw=0.8)
        ax.axvline(real, color="C3", lw=1.5, label="real ATT")
        ax.set_title(f"{name}\n(n={len(d)})")
        ax.set_xlabel("overall ATT on log(views)")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def main():
    os.makedirs(FIGURES, exist_ok=True)
    os.makedirs(TABLES, exist_ok=True)
    params = load_params()
    lo, hi = params["event_window_months"]
    iters = params["placebo_iterations"]
    seed = params["rng_seed"]
    margin = params["matching_pretreatment_months"]
    panel = load_panel()

    real = overall_point(panel, lo, hi)
    fake = fake_join_dates(panel, lo, hi, iters, seed, margin)
    ctrl = controls_only(panel, lo, hi, iters, seed, margin)

    rows = [_summary("fake_join_dates", fake, real), _summary("controls_only", ctrl, real)]
    pd.DataFrame(rows).to_csv(os.path.join(TABLES, "placebo_summary.csv"), index=False)
    _figure({"fake join dates": fake, "controls only": ctrl}, real,
            os.path.join(FIGURES, "placebo_distribution.svg"))

    for r in rows:
        print(f"{r['placebo']}: mean={r['mean']:.4f} sd={r['sd']:.4f} "
              f"95%=[{r['q025']:.4f}, {r['q975']:.4f}] real={r['real_att']:.4f} "
              f"share|>=|real={r['share_ge_real']:.3f} n={r['n_draws']}")


if __name__ == "__main__":
    main()
