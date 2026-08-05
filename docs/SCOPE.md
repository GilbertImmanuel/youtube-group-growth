## 2. Scope

### 2.1 Inclusion rule (amended 2026-08-04)

A group qualifies if all three hold:

1. The group operates a channel that publishes original long-form video as a major product.
2. Members maintain separate individual channels.
3. A formation date or join date is documentable from a citable source.

Clause 1 read "primary product" until 2026-08-04. It was aligned to "a major product" so it is consistent with the amended 2.2 test below. See decision log.

### 2.2 Exclusion rule (amended 2026-08-04)

A group is excluded if its group channel does not publish original long-form video as a major product. Primary platform is not the test. What matters is whether the mechanism under test exists: members produce video for a group channel, and the views land on that channel.

This replaces the earlier test, which excluded esports organisations, content houses, streamer collectives, label rosters, and management brands whose primary product is livestream, merchandise, or representation. That test was platform-based and inconsistent: it excluded AMP and OfflineTV, which operate qualifying long-form group channels, on the ground that their members primarily stream on Twitch. The amended test turns on the mechanism, not the platform. See decision log 2026-08-04.

### 2.3 Included groups (starting list, extend in Phase 1)

| Group | Region | Notes |
|---|---|---|
| Sidemen | UK | Primary case. Includes MoreSidemen, SidemenReacts, Sidemen Shorts |
| Beta Squad | UK | |
| AMP | US | Retained under the amended 2.2 test. Twitch-first, but operates a qualifying long-form group channel |
| 2Hype | US | |
| OfflineTV | US | Added in Phase 1 under the amended 2.2 test. Streamer collective operating a qualifying long-form group channel |
| Team 10 | US | Case-study only (Q6). Collapsed. Formation 2016-08-05 |
| Dude Perfect | US | Contrast case only, excluded from all estimation Q1 to Q6: members have no meaningful solo channels |

Vlog Squad was on this list until 2026-08-04. It was removed and excluded: it has no distinct group channel, so it fails inclusion clause 2.1.1. See `config/exclusions.csv`.

### 2.4 Excluded, with reason (goes in `config/exclusions.csv`)

| Entity | Reason | Revisit |
|---|---|---|
| CORE | Group channel terminated 2026-05-01, one day after launch, so it publishes no long-form. Announced 2026-04-30, six members: Adapt, Silky, JasonTheWeen, Lacy, Marlon, Stable Ronaldo. Post-period is 9 weeks as of 2026-08-04 | 2027-06-01 |
| FaZe Clan | Organisation. No group channel carrying original long-form member video as a major product | No |
| 100 Thieves | Organisation. Same reason as FaZe Clan | No |
| OTK | Group channel does not publish original long-form member video as a major product. Excluded on group-channel composition under the amended 2.2 mechanism test, the same inspection basis used to admit AMP and OfflineTV | No |
| Vlog Squad | No distinct group channel; content on David Dobrik's personal channel. Fails 2.1.1 | No |

OfflineTV was on this exclusion list until 2026-08-04. Under the amended 2.2 test it qualifies, so it moved to the cohort in Section 2.3.

CORE is recorded as a prospective cohort, not an estimation unit. PlaqueBoyMax and YourRAGE are FaZe alumni who did not join CORE. YourRAGE stated the decision publicly on 2026-04-30. The FaZe diaspora is a candidate natural experiment for a follow-up study once 12 months of post-period exist.

---

## 3. Research questions (FROZEN)

Write the expected sign for each before running any model. Record it in `docs/HYPOTHESES.md` in Phase 1.

| ID | Question | Outcome | Method | Supports KSI if |
|---|---|---|---|---|
| Q1 | Is attention concentrating inside group ecosystems | HHI and Gini of monthly views across group plus member channels | Descriptive | Concentration rises after formation |
| Q2 | Does membership reduce solo output | Uploads per month on member's own channel | Event study | Falls after joining |
| Q3 | Does membership reduce external pair collaborations | Count of non-group collaborations per quarter | Event study on collaboration graph | Falls after joining |
| Q4 | Does membership change individual video performance | log(views) per long-form video | Staggered DiD (Callaway and Sant'Anna) | Post-join coefficient negative |
| Q5 | Does the sign flip with pre-join size | Q4 interacted with pre-join subscriber percentile | Heterogeneity split | Negative for large, positive for small |
| Q6 | Named case studies | log(views) per video | Synthetic control | Case-specific |

Q6 cases: KSI exit (2026-05-31), Team 10 collapse. Two cases. Vlog Squad decline was a third case until 2026-08-04; it was removed with the group from the sample.

---

## 4. Design (FROZEN)

### 4.1 Primary specification

Unit of observation: the individual video, not the channel-month.

Outcome: `log(views)` for long-form videos on a member's own channel.

Fixed effects: channel and calendar-month.

Reason this works: a single API snapshot returns cumulative views, so older videos have accrued longer. Within a channel, video age is a deterministic function of publish date, so age and calendar time are collinear. In a DiD, treated and control channels are compared at the same calendar month, and the accrual bias at any given month is common to both. Calendar-month fixed effects absorb it. The remaining assumption is that accrual curves do not differ systematically between treated and control channels. State this assumption in `METHODS.md`. Partially check it on genre-matched pairs.

Consequences of this design:

- Subscriber counts are never used as an outcome. The YouTube Data API rounds `statistics.subscriberCount` down to three significant figures above 1,000 subscribers. At 21M subscribers the granularity is 100,000.
- The YouNiverse weekly time series is not required for the main estimate. Its role reduces to control sampling and pre-2019 validation.
- Sample size increases from thousands of channel-months to hundreds of thousands of videos.

### 4.2 Sample restrictions

- Long-form only. Split on `contentDetails.duration`. Threshold in `config/params.yaml`, default 60 seconds, sensitivity check at 180 seconds.
- Videos at least 180 days old at snapshot time.
- Deleted and privated videos are unobservable. Quantify the gap on a Wayback sample and report it.

### 4.3 Control construction

Sampling frame: `df_channels_en.tsv.gz` from YouNiverse (6.0 MB).

Match each treated creator to 8 to 10 controls on subscriber band at join time, channel creation year, country, and primary category. Freeze `config/cohort_controls.csv` before any model runs. Regenerating the control list after seeing results is forbidden.

### 4.4 Forbidden

- No specification search against the Q4 or Q5 estimate. The DiD spec is fixed in Phase 1 and does not change after Phase 6 begins.
- No naive two-way fixed effects with staggered treatment timing. Use Callaway and Sant'Anna, or Sun and Abraham.
- No dropping of cohort members after seeing their trajectory.
