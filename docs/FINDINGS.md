# Descriptive findings (Q1 to Q3)

Recorded 2026-08-21. Descriptive results for research questions Q1 to Q3, plus attention
share and the reciprocity ledger, from Phase 5 Stage 1 (commit 551a05c). Every number below
is reproduced by `python -m src.models.descriptive` and stored in `outputs/tables/`; the
figures are `python -m src.viz.descriptive` in `outputs/figures/`.

These are associations and event-time coincidences, not treatment effects. The write-up uses
"associated with" and "after formation", never a causal verb (STYLE rule A). Per rule E,
KSI's claim is reported per sub-claim with the precision achieved, and is neither proven nor
refuted here. KSI's four sub-claims (BACKGROUND 1.1) are: (1) pair collaborations are
reciprocal, (2) group collaborations are not reciprocal, (3) members receive exposure
without traffic because the group channel captures the views, (4) groups suppress individual
growth and concentrate it.

Event-time figures align each group to its `treatment_date` (formation) over the
`config/params.yaml` window of 24 months on each side.

## Q1 Attention concentration

Produced by `src.models.descriptive.q1_concentration`, table
`outputs/tables/q1_concentration.csv`, figure `outputs/figures/q1_concentration.svg`. Metric:
HHI and Gini of monthly views across each ecosystem's cohort channels, five estimation groups
(Sidemen, OfflineTV, Beta Squad, 2HYPE, AMP), N=5 groups per relative month.

Cross-group mean HHI is 0.422 at relative month -24, 0.356 at formation, and 0.414 at
relative month +24. Gini is 0.474 and 0.473 at the two window ends. The cross-group
dispersion is wide, with per-period standard deviation between 0.03 and 0.30. The series does
not move in the pre-registered "rises" direction and cannot be distinguished from flat at this
dispersion. Months in which fewer than two cohort channels are active carry HHI=1 by
construction and are flagged as mechanical in the table, not read as concentration.

Expected sign was a rise (HYPOTHESES). The channel-level concentration measure is consistent
with sub-claim 4 only if it rises, which it does not at the observed precision.

## Attention share by upload year

Produced by `src.models.descriptive.attention_share`, table
`outputs/tables/attention_share.csv`, figure `outputs/figures/attention_share.svg`. Metric:
the group-role channels' share of summed ecosystem views by video publish year, per ecosystem.

The group-channel share is near 0 in the years before each group's formation, when only member
channels exist, and reaches these values in 2026: Sidemen 0.456 across 3 group and 6 member
channels, Beta Squad 0.693, AMP 0.632, OfflineTV 0.253, and 2HYPE 0.000 with its group
channel inactive that year. At the ecosystem level the group channel commanding a plurality to
majority share is consistent with sub-claim 3 (the group channel captures a large view share).
`view_count` is cumulative at one snapshot, so the level carries the accrual caveat in
SCOPE 4.1; the within-year cross-channel share largely cancels the common accrual factor.

## Q2 Solo output

Produced by `src.models.descriptive.q2_uploads`, table `outputs/tables/q2_uploads.csv`, figure
`outputs/figures/q2_uploads.svg`. Metric: long-form uploads per month on a member's own
channel, treated eligible members against their nearest-neighbour matched controls, aligned to
the member's `treatment_date`.

Treated long-form uploads per month average 9.31 before treatment and 8.24 after; matched
controls average 9.95 before and 8.37 after. Per-period standard deviation is between 11 and
13. Treated N is 27 to 30 channels per period, control N is 40 to 51. Both arms are lower after
the event by a similar amount, so a treated-specific reduction cannot be separated from the
secular decline in upload frequency that the controls also show. The pre-registered "falls"
direction is present in the treated level, but not against the counterfactual at this
precision.

## Q3 External collaborations

Produced by `src.models.descriptive.q3_external`, table
`outputs/tables/q3_external_collabs.csv`, figure `outputs/figures/q3_external_collabs.svg`.
Metric: distinct cross-group cohort collaboration partners per creator-quarter, Sidemen
members only, aligned to Sidemen formation, N=7 members per quarter.

The mean is near 0 across the window, between 0.00 and 0.571 external partners per
creator-quarter. Two restrictions bound this measure. Collaboration extraction reached F1
0.6634 against the validation set, below the 0.75 target (`loops/collabs/log.md`), so per
PROJECT_PLAN Section 12 the measure is Sidemen-ecosystem only and cohort-observable. The other
cohort groups were formed in 2019 or later, after the 2013 to 2017 window around Sidemen
formation, so a Sidemen member's cohort-observable cross-group count is a structural floor
rather than a measured decline. Sub-claim 1 (substitution away from external pair
collaborations) is not testable at this coverage.

## Reciprocity ledger

Produced by `src.models.descriptive.reciprocity_ledger`, table
`outputs/tables/reciprocity_ledger.csv`, figure `outputs/figures/reciprocity_ledger.svg`.
Metric: same-group appearance counts by direction. member to group counts videos uploaded by a
group-role channel with a member present; group to member counts videos uploaded by a
member-role channel with the group-role channel present.

| Group | member to group | group to member |
|---|---|---|
| Sidemen | 17822 | 7 |
| OfflineTV | 829 | 2 |
| Beta Squad | 820 | 75 |
| AMP | 490 | 5 |
| 2HYPE | 274 | 569 |

Totals are 20235 member-to-group against 658 group-to-member. The asymmetry is consistent with
sub-claims 1 and 2 (pair reciprocity present, group reciprocity absent) for four of the five
groups. 2HYPE reverses, with its group channel inactive in recent years. Detection is
alias-based and Sidemen-dense, so the group-to-member direction is a floor observation, not a
proven absence of reciprocal group-to-member content.

## Per sub-claim reading

| Sub-claim | Evidence | Consistent | Precision |
|---|---|---|---|
| 1 pair reciprocity | reciprocity ledger member-to-group direction | Yes for 4 of 5 groups | Alias detection, Sidemen-dense |
| 2 group non-reciprocity | reciprocity ledger group-to-member near zero | Yes for 4 of 5 groups | Floor, not proven absence |
| 3 exposure without traffic | attention share, group channel 0.253 to 0.693 in 2026 | Yes at ecosystem level | Cumulative-view accrual caveat |
| 4 growth suppression | Q1 concentration, Q4 and Q5 | Not addressed here | Requires the Phase 6 estimate |

## What this does not establish

The descriptive results are event-time coincidences and cross-sectional shares, not treatment
effects. Whether membership changes individual video performance (Q4), and whether the sign
depends on pre-join size (Q5), are estimated in Phase 6 with the Callaway and Sant'Anna
staggered DiD, its pre-trend plot, and the placebo check. A causal reading of KSI's sub-claim 4
is deferred to that phase. Per rule E, no claim here is stated as proven or refuted.

## Reproduce

```
python -m src.models.descriptive
python -m src.viz.descriptive
```

Figures require the activated `projects` conda environment; the bare interpreter loads pandas
but crashes on the matplotlib render step for want of the environment's native libraries.
