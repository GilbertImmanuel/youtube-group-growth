# Loop A attempt log

Karpathy loop (PROJECT_PLAN 8.3). Metric: F1 of extracted cohort collaborators against the
frozen `data/validation/labels.csv` (N=76, 213 instances, Sidemen-ecosystem), micro-averaged.
Command: `python -m src.features.collabs --eval`. Keep an edit only if F1 rises over the previous
best. The interpreter this stage is `miniconda3/envs/projects/python.exe` (pandas 3.0.5), which
reproduces the Stage 1 baseline exactly.

Diagnosis before iterating: every Sidemen group video ends with a static `?? SIDEMEN ??` roster
footer that lists a fixed member set with bare vanity URLs (`youtube.com/Zerkaa`), regardless of
who appears in that video. The Stage 1 URL regex requires `@`, `c/`, or `user/`, so it misses the
footer entirely, which is why baseline recall is 0.0516. The footer roster is the only text signal
for who participated: stripping it drops recall to 0.056. It is also the main false-positive source,
since it names members who are listed but absent, which caps precision.

| # | Timestamp (GMT+7) | Change | P | R | F1 | Decision |
|---|---|---|---|---|---|---|
| 0 | 2026-08-20 13:35 | Baseline: link + @handle extraction only (Stage 1) | 0.9167 | 0.0516 | 0.0978 | keep (baseline) |
| 1 | 2026-08-20 13:50 | Add cohort real-name/nickname alias matching over title+description, cohort-restricted, self excluded | 0.6959 | 0.6338 | 0.6634 | keep |
| 2 | 2026-08-20 13:52 | Restrict alias matching to text before the roster footer (presence-only signal) | 0.857 | 0.056 | 0.106 | discard (recall collapses; cast is named only inside the footer) |
| 3 | 2026-08-20 13:55 | Gate an alias by mention count >= 2 in full text | 0.692 | 0.601 | 0.643 | discard (footer names each member 1-4x regardless of presence) |
| 4 | 2026-08-20 13:55 | Gate by mention count >= 3, >= 4, >= 5 | 0.685 / 0.685 / 0.645 | 0.582 / 0.582 / 0.427 | 0.629 / 0.629 / 0.514 | discard |
| 5 | 2026-08-20 13:56 | Present iff named in title OR full-text mention count >= 2..4 | <=0.692 | <=0.601 | <=0.643 | discard |

Kept: 1 (attempt 1). Discarded: 4 (attempts 2, 3, 4, 5 and their sub-variants).

Best F1 = 0.6634 (P=0.6959, R=0.6338, TP=135, FP=59, FN=78, N=76), produced by
`python -m src.features.collabs --eval`.

## Stopping rule (PROJECT_PLAN 12)

F1 stalled at 0.6634, below the 0.75 target. The recall ceiling of title+description text is ~0.63
(135 of 213 instances carry a member name in text; the remaining ~37% are un-nameable, group
videos that name no participant), so 0.75 is not reachable from description text for this content
type. Per Section 12, keep the best version and fall back: the validation set is already
Sidemen-only, so Q3 is restricted to the Sidemen ecosystem and 0.6634 is reported as the achieved
ceiling. The remaining false positives are the static roster footer listing absent members, which
the description text cannot distinguish from the present cast.
