# Hypotheses

Pre-registered 2026-08-04, before any estimation. Not revised once analysis begins.

## Expected signs

Expected direction for each research question, recorded before estimation. The
"supports KSI if" column states the direction that would support KSI's claim. The
reasoning column is the prior, not a result.

| ID | Question | Expected sign | Reasoning (prior) | Supports KSI if |
|---|---|---|---|---|
| Q1 | Attention concentration (HHI, Gini) after formation | Rises | The group channel accrues a large view share, concentrating attention across the ecosystem | Concentration rises after formation |
| Q2 | Solo uploads per month after joining | Falls | Time and content divert to the group channel | Falls after joining |
| Q3 | External pair collaborations per quarter after joining | Falls | Collaboration substitutes toward same-group members | Falls after joining |
| Q4 | log(views) per long-form video after joining | Near zero, imprecise | The average masks heterogeneity. If group exposure helps the typical smaller member slightly, the mean is weakly positive, with a wide interval that cannot be distinguished from zero | Post-join coefficient negative |
| Q5 | Q4 sign by pre-join subscriber percentile | Negative for large, positive for small | Group membership subsidises small members with exposure they could not get alone, and taxes large members whose views the group channel cannibalises | Negative for large, positive for small |

The Q5 split is the substantive prior: if it holds, KSI's claim is correct for
large members such as himself and incorrect as a general law.

## DiD specification (Q4, Q5)

Fixed before estimation and not changed afterward.

- Estimator: Callaway and Sant'Anna staggered DiD (fallback Sun and Abraham).
- Outcome: log(views) per long-form video on the member's own channel.
- Fixed effects: channel and calendar-month.
- Covariates: none beyond the channel and calendar-month fixed effects. The fixed effects absorb the view-accrual bias, and adding covariates would invite specification search.
- Event window: from `config/params.yaml` (`event_window_months`).
- Clustering level: group level via wild cluster bootstrap (see limitation 2).
- Censoring: observations after a member's `censor_date` (the `leave_date` in `config/cohort_groups.csv`) are dropped from Q4 and Q5, because Callaway and Sant'Anna assumes absorbing treatment. Four eligible members exited: Fedmyster, Mopi, Pokimane, KSI.

## Limitations

These constrain what the estimates can claim. Counts are from
`config/cohort_groups.csv`.

### 1. Founder versus joiner

Under treatment_date, most treated creators are treated at their group's formation
timing rather than by a later external join. For a founder or an early member,
treatment is the creation of the group channel, which is endogenous to the member's
own trajectory rather than an external shock. Only three of the 30 eligible
creators are clean late joiners, meaning the join postdates the group channel: Kai
Cenat, Michael Reeves, QuarterJade. W2S is not one, because the Sidemen channel was
created on 2015-06-14, after his January 2014 join, so his treatment_date is the
channel creation. Yvonnie was listed in error: her channel was created on her join
date, so she has no pre-treatment period and is excluded by the 12-month rule. The
main estimate therefore covers co-founding and early joining. The late-joiner
robustness check now covers three creators and is correspondingly imprecise.

### 2. Treatment timing and clustering

The main cohort has five distinct treatment cohorts, dated by treatment_date:
Sidemen 2015-06-14, OfflineTV 2017-07-03, Beta Squad 2019-02-14, 2HYPE 2019-05-12,
AMP 2020-01-24. Two fall in 2019 (February and May) and AMP in January 2020, so the
five cohorts span 2015 to 2020. Clustering: group level via wild cluster bootstrap.
Group-level clustering with conventional standard errors is invalid at about six
clusters, and channel-level clustering understates standard errors because treatment
is assigned at the group level.

### 3. Channels without a pre-treatment period

Q4 and Q5 require at least 12 months of channel history before treatment_date.
Applied to all 32 main-cohort members, the rule excludes two: Agent 00, whose
channel was recreated 2022-08-24 after his 2019 join, and Yvonnie, whose channel
was created on her 2018-09-19 join date. 30 of 32 are retained. Retain Agent 00 for
Q1 if the AMP group-channel data is intact. Duke Dennis keeps a pre-treatment period
because he was switched to his Gaming channel (created 2013-02-16), which predates
treatment.

### 4. Subscriber matching date

Section 4.3 specifies matching on subscriber band at join time.
`config/cohort_controls.csv` matched on `control_subs_2019` for every treated unit,
because YouNiverse was reduced to `df_channels_en.tsv.gz` and no per-date subscriber
series is held. For Sidemen, whose treatment_date is 2015-06-14, the 2019 band is
six years later. The match is on a single fixed-year subscriber snapshot, not on
size at treatment, which biases control selection toward channels of similar 2019
size regardless of growth path.
