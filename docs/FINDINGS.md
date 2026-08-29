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

# Causal analysis (Q4 and Q5)

Recorded 2026-08-29. Results for Q4 (does membership change individual video performance) and
Q5 (does the sign depend on pre-join size), from Phase 6 Stage 1 (commit 3ca4091). Every number
below is read from the committed tables in `outputs/tables/`; the figures are in
`outputs/figures/`.

The pre-trend test fails (reported below). Parallel trends is the identifying assumption for a
causal reading, so with it violated the Q4 and Q5 estimates are associations, not treatment
effects. The text uses "associated with", never a causal verb (STYLE rule A). Per PROJECT_PLAN
Section 12, a failed pre-trend is the finding, and the specification is not changed in response.

## Estimator

Produced by `python -m src.models.did`. The pre-registered primary, Callaway and Sant'Anna via
the `differences` package, runs point estimates and the event study on pandas 3.0.5, but its
group-level clustering path is broken by a pandas-3 API change inside the package. The
pre-registered fallback, Sun and Abraham interaction-weighted event study, is used at the SCOPE
4.1 video level: a weighted OLS of log(views) on channel and calendar-month fixed effects plus
cohort-by-relative-period interactions, with never-treated and not-yet-treated channels as the
comparison. The estimator change is logged in `docs/DECISIONS.md` (2026-08-27). Inference is a
group-level wild cluster bootstrap over the five ecosystems with Webb six-point weights,
`wild_bootstrap_iterations` 999 from `config/params.yaml`.

## Identifying assumptions

A causal reading requires parallel trends: absent treatment, treated and control channels would
follow the same log(views) path. The pre-trend test below rejects it, so the assumption does not
hold at the observed precision, and the estimates are reported as associations.

The design carries the SCOPE 4.1 accrual argument. A single API snapshot returns cumulative
views, so older videos have accrued longer. Within a channel, video age is a deterministic
function of publish date, so age and calendar time are collinear, and calendar-month fixed
effects absorb the accrual common to treated and control at each month. The residual assumption
is that accrual curves do not differ systematically between treated and control channels. Phase 9
METHODS.md carries the fuller confound treatment and the genre-matched accrual check.

Four limitations from `docs/HYPOTHESES.md` constrain the estimates:

1. Founder versus joiner. Most treated creators are treated at their group's formation rather
   than by a later external join, so treatment is endogenous to the member's own trajectory. Only
   three of the 30 eligible creators are clean late joiners, and that robustness check is
   correspondingly imprecise.
2. Treatment timing and clustering. Five treatment cohorts span 2015 to 2020. Group-level
   clustering with conventional standard errors is invalid at five clusters, and channel-level
   clustering understates standard errors because treatment is assigned at the group level.
   Inference uses the wild cluster bootstrap for this reason.
3. Channels without a pre-treatment period. Q4 and Q5 require at least 12 months of channel
   history before treatment. The rule retains 30 of 32 main-cohort members.
4. Subscriber matching date. Controls were matched on `control_subs_2019` rather than size at
   treatment, which biases control selection toward channels of similar 2019 size regardless of
   growth path.

## Pre-trend

Produced by `src.models.did`, table `outputs/tables/did_pretrend_test.csv`, figure
`outputs/figures/did_event_study.svg`. The sup-t statistic across the 23 pre-periods over
relative months [-24, -2] is 7.672 with p 0.001 (5 ecosystem clusters). Before treatment the
event-study path in `outputs/tables/did_event_study.csv` is not flat: the relative-period
coefficient runs from -1.030 at month -23 up to 0.308 at month -8. Rejecting the null of no
pre-trend violates parallel trends, so Q4 and Q5 are read as associations.

## Q4 overall association

Produced by `src.models.did`, table `outputs/tables/did_overall_att.csv`, figure
`outputs/figures/did_event_study.svg`. The overall post-treatment estimate is 0.339 log points,
95% confidence interval [0.194, 0.485], standard error 0.088, over 5 ecosystem clusters, 30
treated channels, and 12342 videos. Its interval excludes zero, so membership is associated with
higher log(views) per video on average. The pre-registered prior was near zero and imprecise
(HYPOTHESES Q4); the observed estimate is positive with an interval excluding zero, though the
violated pre-trend caps what the sign can be read to mean.

## Q5 heterogeneity by pre-join size

Produced by `src.models.did`, table `outputs/tables/did_q5_heterogeneity.csv`, figure
`outputs/figures/did_q5_split.svg`. Arms split at the median of the pre-treatment 12-month mean
log(views), split value 13.010. The large arm estimate is 0.145, 95% interval [0.011, 0.280],
standard error 0.079, 14 treated channels, 7056 videos. For the small arm the estimate is 0.579,
95% interval [0.416, 0.748], standard error 0.099, 13 treated channels, 5246 videos. Both arms
use 5 ecosystem clusters. The two arms sum to 27 channels against the 30 in the overall estimate;
each table's N is reported as produced. Both arms are positive and the small arm is larger, which
is consistent with exposure benefiting smaller members more. The pre-registered prior was
negative for large and positive for small (HYPOTHESES Q5); the small-member direction matches,
whereas the large-member direction does not, since the large arm is positive rather than
negative. Under a violated pre-trend both arms are associations.

## Placebo checks

Produced by `python -m src.models.placebo`, table `outputs/tables/placebo_summary.csv`, figure
`outputs/figures/placebo_distribution.svg`. `placebo_iterations` is 200 from
`config/params.yaml`.

Fake join dates: 200 draws that reassign treatment timing at random give a placebo estimate with
mean 0.740, standard deviation 0.181, and central 95% range [0.389, 1.062]. 98 percent of these
draws are at or above the real overall ATT of 0.339 (share_ge_real 0.98), which places the real
estimate at about the 2nd percentile. Sitting far from zero, the placebo distribution indicates
the timing design attributes a large estimate even to randomised dates, a further reason not to
read the main estimate causally.

Controls-only: 200 draws that assign fake treatment among control channels only give a placebo
estimate with mean 0.028, standard deviation 0.226, and central 95% range [-0.389, 0.461]. The
distribution is centred near zero and its interval spans zero. Read as a null, the controls-only
placebo is an estimate of 0.028 with interval [-0.389, 0.461] that cannot be distinguished from
zero at 200 draws and 5 clusters; it is imprecise, not an established zero. The real ATT of 0.339
exceeds 88.5 percent of these draws (share_ge_real 0.115).

## Precision limit

The bootstrap runs over 5 ecosystem clusters. At this cluster count the Webb wild cluster
bootstrap is coarse, and every interval above carries that limit as part of its N (STYLE rule C).
The cluster count, not the video count, bounds the precision.

## Per sub-claim reading

Q4 and Q5 bear on sub-claim 4 (groups suppress individual growth) and on the general-law question
in BACKGROUND 1.1. Per rule E, the claim is neither proven nor refuted.

| Sub-claim | Evidence | Reading | Precision |
|---|---|---|---|
| 4 growth suppression | Q4 overall association | Post estimate positive, [0.194, 0.485], not the negative sign sub-claim 4 predicts | Pre-trend violated, association only |
| 4 by size (general law) | Q5 large and small arms | Both positive, small larger; the large-member loss the general law requires is absent | Pre-trend violated, 5 clusters |

The general-law form of the claim requires large members to lose views. At this precision the
large arm is positive, [0.011, 0.280], so the data does not support growth suppression for large
members. Because the identifying assumption is violated, the reading is an association under a
failed pre-trend, not a treatment effect, and the claim is not settled either way.

## What this does not establish

The pre-trend failure means Q4 and Q5 cannot be read as treatment effects. They are associations
under a violated parallel-trends assumption. Case-level evidence for named creators (Q6,
including the KSI exit) is the Phase 7 synthetic-control task and is not estimated here.

## Reproduce

```
python -m src.models.did
python -m src.models.placebo
```

Figures require the activated `projects` conda environment; the bare interpreter loads pandas but
crashes on the matplotlib render step for want of the environment's native libraries.
