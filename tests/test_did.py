"""Checks for the Sun and Abraham DiD estimator and the placebo machinery (Phase 6).

Data-independent: every test builds a small synthetic staggered panel, so the suite runs without
the gitignored data/processed parquets. The estimator must recover a planted effect, the interval
must bracket the point, the median split must halve the units, and the controls-only placebo must
centre near zero.
"""

import numpy as np
import pandas as pd

from src.models import did, placebo


def _panel(effect=0.8, n_per_arm=6, seed=0, two_cohort=True):
    """Synthetic staggered panel: treated channels gain `effect` after their cohort month."""
    rng = np.random.default_rng(seed)
    specs = [("Sidemen", 2016 * 12 + 6)]
    if two_cohort:
        specs.append(("Beta Squad", 2018 * 12 + 6))
    rows = []
    for eco, coh in specs:
        for ci in range(n_per_arm):
            fe = rng.normal(0, 1)
            for m in range(coh - 30, coh + 30):
                rel = m - coh
                if not -24 <= rel <= 24:
                    continue
                y = fe + (effect if rel >= 0 else 0.0) + rng.normal(0, 0.3)
                rows.append((f"{eco[:3]}t{ci}m{m}", f"{eco[:3]}t{ci}", eco, True,
                             pd.Timestamp(f"{coh // 12}-{coh % 12 or 12:02d}-01", tz="UTC"),
                             pd.Timestamp(f"{m // 12}-{m % 12 or 12:02d}-01"), y, 1.0))
        for ci in range(n_per_arm):
            fe = rng.normal(0, 1)
            for m in range(coh - 30, coh + 30):
                y = fe + rng.normal(0, 0.3)
                rows.append((f"{eco[:3]}c{ci}m{m}", f"{eco[:3]}c{ci}", eco + " control", False,
                             pd.NaT, pd.Timestamp(f"{m // 12}-{m % 12 or 12:02d}-01"), y, 1.0))
    return pd.DataFrame(rows, columns=["video_id", "channel_id", "group", "treated", "cohort",
                                       "published_month", "log_views", "weight"])


def test_recovers_planted_effect_with_bracketing_interval():
    r = did.estimate(_panel(effect=0.8), -24, 24, iters=199, seed=1)
    o = r["overall"].iloc[0]
    assert abs(o["att"] - 0.8) < 0.1, o["att"]
    assert o["ci_low"] <= o["att"] <= o["ci_high"]
    assert o["se"] > 0 and np.isfinite(o["se"])
    ev = r["event"]
    assert (ev["rel_period"].min(), ev["rel_period"].max()) == (-24, 24)
    assert ev["rel_period"].is_unique


def test_median_split_halves_the_units():
    proxy = {f"c{i}": float(i) for i in range(10)}
    arms, med = did._median_split(proxy)
    assert med == 4.5
    assert sum(a == "large" for a in arms.values()) == 5
    assert sum(a == "small" for a in arms.values()) == 5


def test_controls_only_placebo_centres_near_zero():
    draws = placebo.controls_only(_panel(effect=0.8), -24, 24, iters=20, seed=3, margin=6)
    draws = draws[~np.isnan(draws)]
    assert len(draws) > 0
    assert abs(np.mean(draws)) < 0.3, np.mean(draws)
