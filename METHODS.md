# Methods

This document sets out the identification strategy, the accrual argument the design rests on, the confounds, the placebo results, and the limitations that bound every estimate. Numbers are read from the committed tables in `outputs/tables/` and from `docs/FINDINGS.md`, and each is cited to its source. Results are reported as associations, because the pre-trend test rejects the assumption a causal reading requires.

## Identification strategy

Observations are individual long-form videos on a member's own channel, with log(views) as the outcome (docs/SCOPE.md 4.1). The pre-registered primary estimator is the Callaway and Sant'Anna staggered difference-in-differences via the `differences` package. Its point estimates and event study run on pandas 3.0.5, but its group-level clustering path is broken by a pandas-3 API change inside the package, so the analysis uses the pre-registered fallback, the Sun and Abraham interaction-weighted event study, recorded in docs/DECISIONS.md (2026-08-27). Estimation is a weighted OLS of log(views) on channel and calendar-month fixed effects together with cohort-by-relative-period interactions, with never-treated and not-yet-treated channels as the comparison. Inference is a group-level wild cluster bootstrap over the five ecosystems using Webb six-point weights, with 999 iterations from `config/params.yaml`.

Fixed effects are channel and calendar-month, and no covariate is added beyond them, because the fixed effects absorb the accrual bias described below and adding covariates would invite specification search (docs/HYPOTHESES.md). Observations after a member's leave date are censored, because the estimator assumes absorbing treatment and four eligible members exited (Fedmyster, Mopi, Pokimane, KSI). Q4 and Q5 require at least 12 months of channel history before treatment, a rule that retains 30 of 32 main-cohort members.

## The accrual argument

A single API snapshot returns cumulative views, so an older video has accrued views for longer than a newer one. Within a channel, video age is a deterministic function of publish date, so age and calendar time are collinear. In a difference-in-differences, treated and control channels are compared at the same calendar month, and the accrual bias at any given month is common to both, so calendar-month fixed effects absorb it (docs/SCOPE.md 4.1). The residual assumption is that accrual curves do not differ systematically between treated and control channels, which the design checks partially on genre-matched pairs rather than asserting.

Two consequences follow. Subscriber counts are never used as an outcome, because the API rounds `statistics.subscriberCount` to three significant figures, which at 21 million subscribers is a granularity of 100000. Sample size rises from thousands of channel-months to hundreds of thousands of videos, since the unit is the video rather than the channel-month.

## Confounds and identifying assumption

A causal reading requires parallel trends: absent treatment, treated and control channels would follow the same log(views) path. The pre-trend test rejects it. Its sup-t statistic across the 23 pre-periods over relative months [-24, -2] is 7.672 with p 0.001 at 5 ecosystem clusters, and the event-study path in `outputs/tables/did_event_study.csv` runs from -1.030 at month -23 up to 0.308 at month -8, so it is not flat before treatment (docs/FINDINGS.md; outputs/tables/did_pretrend_test.csv). With the assumption violated at the observed precision, Q4 and Q5 are read as associations, and per PROJECT_PLAN Section 12 a failed pre-trend is the finding and the specification is not changed in response.

Four limitations from docs/HYPOTHESES.md constrain what the estimates can claim.

1. Founder versus joiner. Most treated creators are treated at their group's formation rather than by a later external join, so treatment is endogenous to the member's own trajectory. Only three of the 30 eligible creators are clean late joiners (Kai Cenat, Michael Reeves, QuarterJade), which makes that robustness check correspondingly imprecise.
2. Treatment timing and clustering. Five treatment cohorts span 2015 to 2020 (Sidemen 2015-06-14, OfflineTV 2017-07-03, Beta Squad 2019-02-14, 2HYPE 2019-05-12, AMP 2020-01-24). At five clusters, group-level clustering with conventional standard errors is invalid, and channel-level clustering understates standard errors because treatment is assigned at the group level, which is why inference uses the wild cluster bootstrap.
3. Channels without a pre-treatment period. The 12-month history rule excludes Agent 00, whose channel was recreated 2022-08-24 after his 2019 join, and Yvonnie, whose channel was created on her 2018-09-19 join date, and retains 30 of 32.
4. Subscriber matching date. Controls were matched on `control_subs_2019` rather than size at treatment, which biases control selection toward channels of similar 2019 size regardless of growth path.

## Placebo checks

Two placebo runs test the timing design, each with 200 draws from `config/params.yaml` (docs/FINDINGS.md; outputs/tables/placebo_summary.csv).

Fake join dates reassign treatment timing at random and give a placebo estimate with mean 0.740, standard deviation 0.181, and central 95 percent range [0.389, 1.062]. 98 percent of these draws sit at or above the real overall ATT of 0.339, which places the real estimate near the 2nd percentile. Sitting far from zero, the placebo distribution indicates the timing design attributes a large estimate even to randomised dates, a further reason not to read the main estimate causally.

Controls-only draws assign fake treatment among control channels alone and give a placebo estimate with mean 0.028, standard deviation 0.226, and central 95 percent range [-0.389, 0.461]. Read as a null, the controls-only placebo is an estimate of 0.028 with interval [-0.389, 0.461] that cannot be distinguished from zero at 200 draws and 5 clusters. It is imprecise, not an established zero.

## Synthetic control and precision

Each Q6 case fits an Abadie synthetic control on the treated channel's monthly mean log(views) per long-form video, with donor weights that are non-negative and sum to one and reproduce the pre-event monthly path over a 24-month window (docs/FINDINGS.md; outputs/tables/synth_fit.csv). A single treated unit has no valid conventional standard error, so inference is an in-space placebo permutation: each donor is reassigned the treatment date, its own synthetic is fit from the remaining donors, and the treated unit's post-to-pre RMSPE ratio is ranked among all 41 units (STYLE rules C and D). The DiD bootstrap runs over 5 ecosystem clusters, and at this count the Webb wild cluster bootstrap is coarse, so the cluster count, not the video count, bounds the precision.

## Collaboration measurement and coverage

Collaboration is extracted from description links and handles, validated against hand-viewed ground truth rather than the native collaborator tag. The tag was tested only for validation, because it carries about 12 months of coverage against a 2013 to 2026 window, is absent from the `videos.list` resource, and is consent-based and therefore endogenous to the reciprocity being measured (docs/DECISIONS.md 2026-08-04, 2026-08-11). Extraction reached F1 0.6634 against the validation set, below the 0.75 target (loops/collabs/log.md), so per PROJECT_PLAN Section 12 the external-collaboration measure (Q3) is restricted to the Sidemen ecosystem and reported as a floor.

Deleted and privatised videos are unobservable at snapshot time, so any per-channel count is a count of survivors. The gap is bounded above at 0.174 on a Wayback sample of 138 archived IDs across 6 channels, and all 24 absent IDs come from Dude Perfect, a contrast case excluded from all estimation (docs/coverage.md). That rate is disclosed as an upper-bound coverage limit, not applied as a correction.

## Per sub-claim reading

KSI's claim decomposes into four sub-claims, each reported with the precision achieved. Per STYLE rule E, the claim is neither proven nor refuted.

| Sub-claim | Evidence | Reading | Precision |
|---|---|---|---|
| 1 pair reciprocity | Reciprocity ledger, member-to-group direction | Consistent for 4 of 5 groups | Alias detection, Sidemen-dense |
| 2 group non-reciprocity | Reciprocity ledger, group-to-member near zero | Consistent for 4 of 5 groups | Floor, not proven absence |
| 3 exposure without traffic | Attention share, group channel 0.253 to 0.693 in 2026 | Consistent at ecosystem level | Cumulative-view accrual caveat |
| 4 growth suppression | Q1 concentration, Q4 and Q5 associations, Q6 cases | Q4 and Q5 positive, not the negative sign the claim predicts | Pre-trend violated, 5 clusters, association only |

## Limitations in summary

The estimates are associations under a violated parallel-trends assumption, not treatment effects, and the general-law form of the claim requires large members to lose views, which the large arm (0.145, [0.011, 0.280], 14 channels, 7056 videos) does not show (docs/FINDINGS.md; outputs/tables/did_q5_heterogeneity.csv). Precision is bounded by the five ecosystem clusters, the pre-trend fails, collaboration coverage is restricted to one ecosystem, and the KSI post window is 9.7 weeks under a relaxed age filter and is described rather than estimated. What the analysis returns is an estimate, its interval, and the assumptions required to read it, and on those terms the claim is settled in neither direction.
