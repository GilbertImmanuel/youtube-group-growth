# Loop A: collaboration extraction

Karpathy loop (PROJECT_PLAN 8.3). The metric is optimised against a fixed evaluation
set. This file is human-edited instructions; `log.md` records every attempt.

## File under edit

`src/features/collabs.py`, the description and title parser only. Nothing else changes
during the loop.

## Metric

F1 of extracted cohort collaborators against the viewing-based validation set,
micro-averaged over collaborator instances (sum TP, FP, FN across all labelled videos,
then one precision and recall). Higher is better.

## Command

    python -m src.features.collabs --eval

Bounded runtime: reads one parquet and one label CSV, no network. Prints N, TP, FP, FN,
precision, recall, F1.

## Keep or discard

Keep an edit only if F1 rises against the previous best. Discard otherwise. Log every
attempt in `log.md` with the timestamp, the change, the F1, and the decision.

## Ground truth

`data/validation/labels.csv`: `video_id`, `collaborator_channel_ids` (';'-separated
cohort channel IDs), `hand_checked`. Labels come from viewing (the caption transcript,
with frames pulled for ambiguous cases), never from the description, so the ground truth
is independent of the parser under test. A cohort channel is a collaborator when the
video content shows it participating, excluding the uploader's own channel. Handles
resolve to channel IDs through `config/cohort_handles.json` (cohort customUrl map, one
API unit to build).

## Out of scope for the loop

The frozen validation set does not change during the loop. Regenerating or relabelling
against the parser's output is forbidden. If F1 stalls below 0.75, stop and fall back per
Section 12 (Sidemen-only hand labels, narrow Q3 to Sidemen, state the restriction).
