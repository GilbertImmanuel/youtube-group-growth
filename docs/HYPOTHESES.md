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

## Limitations

These constrain what the estimates can claim. Counts are from
`config/cohort_groups.csv`.

### 1. Founder versus joiner

27 of the 32 treated creators in the main cohort (Sidemen, Beta Squad, AMP, 2HYPE,
OfflineTV) have `join_date` equal to their group's formation date. For a founder,
treatment is the creation of the group, which is endogenous to the founder's own
trajectory rather than an external shock. Only five are clean late joiners: W2S,
Kai Cenat, Michael Reeves, Yvonnie, QuarterJade. The main estimate therefore covers
"co-founded or joined". Report a late-joiner-only robustness check on those five.

### 2. Treatment timing and clustering

The main cohort has five distinct group-formation cohorts: Sidemen 2013-10-19,
OfflineTV 2017-07-03, Beta Squad 2019-02-14, 2HYPE 2019-05-12, AMP 2019-10-01.
Three fall in 2019 (February, May, October), spanning eight months, so cohort
variation is thin. Clustering: group level via wild cluster bootstrap. Group-level
clustering with conventional standard errors is invalid at about six clusters, and
channel-level clustering understates standard errors because treatment is assigned
at the group level.

### 3. Channels without a pre-treatment period

Agent 00's channel was recreated 2022-08-24, after his 2019 join, so there is no
pre-treatment video history. Exclude Agent 00 from Q4 and Q5. Retain him for Q1 if
the AMP group-channel data is intact. Duke Dennis was switched to his Gaming channel
(created 2013-02-16), which predates the join, so he keeps a pre-treatment period.
