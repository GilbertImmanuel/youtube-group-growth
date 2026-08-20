# Loop B attempt log

Karpathy loop (PROJECT_PLAN 8.3). Metric: mean absolute standardised difference between the 30
eligible treated members and their matched controls, over two pre-treatment covariates (mean
log(views) per long-form video, long-form upload count) in the 12 months before treatment.
Command: `python -m src.features.panel --eval-matching`. Keep an edit only if the metric falls.
Only `match_controls` changes across attempts; the candidate pool stays frozen at 0d44234.
Interpreter: `miniconda3/envs/projects/python.exe` (pandas 3.0.5). 27 of 30 treated are scored;
3 have no long-form videos inside their pre-treatment window, so they carry no balance covariates.

| # | Timestamp (GMT+7) | Change | mean_log_views SMD | n_uploads SMD | mean \|SMD\| | Decision |
|---|---|---|---|---|---|---|
| 0 | 2026-08-20 15:25 | Baseline: all 10 candidates, equal weight | 0.808 | 0.357 | 0.5826 | keep (baseline) |
| 1 | 2026-08-20 15:27 | Keep only match_rank 1 (frozen subscriber-nearest) | 0.486 | 0.087 | 0.2864 | keep |
| 2 | 2026-08-20 15:29 | Inverse standardised covariate distance, all usable candidates | 0.524 | 0.008 | 0.2658 | keep |
| 3 | 2026-08-20 15:31 | Drop weak_match rows, else equal weight | 0.808 | 0.357 | 0.5826 | discard (no weak_match rows in the pool; no change) |
| 4 | 2026-08-20 15:33 | k nearest by standardised covariate distance, k=5 | 0.512 | 0.085 | 0.2986 | discard (rises vs 0.2658) |
| 5 | 2026-08-20 15:34 | k nearest, k=3 | 0.295 | 0.110 | 0.2023 | keep |
| 6 | 2026-08-20 15:35 | k nearest, k=1 (nearest-neighbour matching) | 0.108 | 0.010 | 0.0590 | keep |

Kept: 5 (baseline, attempts 1, 2, 5, 6). Discarded: 2 (attempts 3, 4).

Best mean |SMD| = 0.0590 (mean_log_views 0.108, n_uploads 0.010, n_treated=27), produced by
`python -m src.features.panel --eval-matching` with `matching_neighbors: 1`.

## Bias-variance note

k=1 minimises the balance metric but is 1:1 nearest-neighbour matching, so the control group is one
channel per treated unit. A larger k trades balance for control-group size (k=3 gives mean |SMD|
0.2023 with three controls per treated). The neighbour count is exposed as `matching_neighbors` in
`config/params.yaml`, so Phase 6 can raise it if the DiD needs a wider control group for precision;
the shipped value is the balance-optimal k=1. The frozen candidate pool is unchanged either way.
