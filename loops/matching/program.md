# Loop B: control matching balance

Karpathy loop (PROJECT_PLAN 8.3). The metric is optimised against a fixed evaluation set.
This file is human-edited instructions; `log.md` records every attempt.

## Function under edit

`match_controls` in `src/features/panel.py`. It returns weights over the frozen candidate
controls for one treated unit. Nothing else changes during the loop. The candidate pool
(`config/cohort_controls.csv`, 10 per treated) is frozen at 0d44234 and is never regenerated;
the function only selects and weights within it.

## Metric

Mean absolute standardised difference between the 30 eligible treated members and their
matched controls, over two pre-treatment covariates measured in the 12 months before
treatment: mean log(views) per long-form video, and long-form upload count. Per covariate,
SMD = |mean_treated - mean_control| / pooled_sd; the metric is the mean of |SMD| across the
two. Lower is better.

## Command

    python -m src.features.panel --eval-matching

Bounded runtime: reads one parquet and two config files, no network. Prints the per-covariate
SMD, the treated count scored, and the mean |SMD|.

## Keep or discard

Keep an edit only if the metric falls against the previous best. Discard otherwise. Log every
attempt in `log.md` with the timestamp, the change, the metric, and the decision.

## Out of scope

The candidate control pool is frozen and does not change during the loop. Section 12 sets no
numeric target for Loop B; iterate to diminishing returns, keep the best, and report the honest
value with its bias-variance tradeoff (a lower neighbour count k improves balance but shrinks the
control group).
