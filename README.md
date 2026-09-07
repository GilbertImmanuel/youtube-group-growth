# YouTube group growth

This study sets out to test a public claim by KSI that YouTube group membership suppresses individual creator growth and turns the space into a monopoly. Its descriptive premises hold in the data: across the five estimation groups member appearances on the group channel exceed returns from it by 20235 to 658, and the group channel commands between 0.253 and 0.693 of ecosystem views in 2026 (docs/FINDINGS.md; outputs/tables/reciprocity_ledger.csv, outputs/tables/attention_share.csv). The central prediction does not hold: the staggered-DiD association for individual video performance is positive at 0.339 log points, 95 percent interval [0.194, 0.485], N 12342 videos over 30 channels and 5 clusters, the small-member arm is larger than the large-member arm, and because the pre-trend test rejects parallel trends (sup-t 7.672, p 0.001) these are associations rather than treatment effects, so the claim is neither proven nor refuted (docs/FINDINGS.md; outputs/tables/did_overall_att.csv, outputs/tables/did_pretrend_test.csv, outputs/tables/did_q5_heterogeneity.csv).

## The claim under test

On 2026-05-31 KSI announced his exit from the Sidemen, and in late July 2026 he published a YouTube community post, reshared to an Instagram story, arguing that group collaborations differ from pair collaborations. Pair collaborations are reciprocal: creator A appears on creator B's channel and creator B appears on creator A's channel, so both channels gain. Group collaborations, in his account, are not: members appear on the group channel, the group channel rarely returns content to the members, and members therefore receive exposure without the traffic a reciprocal pair collaboration would carry. Stated as a general law, that YouTube groups suppress individual growth and concentrate it, the argument decomposes into four sub-claims that can resolve differently. It is worth measuring because it is empirical, specific, and testable: upload dates, view counts, video durations, description links, and membership dates are all publicly available at zero cost. Its full framing is in docs/BACKGROUND.md.

Positionality is disclosed as a prior. The owner followed these creators as individual channels before the Sidemen channel was created on 2015-06-14, and long-term attachment to one group in the sample is the reason the hypotheses in docs/HYPOTHESES.md were fixed before any model was run.

## What the analysis finds

The reciprocity ledger and the attention share are consistent with the descriptive half of the claim, subject to alias-based detection and the cumulative-view accrual caveat. Growth suppression is where the data and the claim diverge: the Q4 and Q5 associations are positive rather than negative, and neither Q6 synthetic-control case recovers the release of views an exit or a collapse would predict under the general law. Because parallel trends is violated, the reading is associational and settles the claim in neither direction. Per-question results are in docs/FINDINGS.md, the argument in docs/WRITEUP.md, and the identification strategy, confounds, placebo results, and limitations in METHODS.md.

A live dashboard presents the same frozen results one page per question: https://youtube-group-growth.streamlit.app/

## How to reproduce

The analysis reads its inputs from committed configuration and the raw pull, and writes tables to `outputs/tables/` and figures to `outputs/figures/`. Rendering the figures requires the activated `projects` conda environment, because the bare interpreter loads pandas but crashes on the matplotlib render step for want of the environment's native libraries.

1. Activate the environment.

```bash
conda activate projects
```

2. Run the descriptive analysis (Q1 to Q3, attention share, reciprocity ledger) and its figures.

```bash
python -m src.models.descriptive
python -m src.viz.descriptive
```

3. Run the causal analysis (Q4, Q5), the placebo checks, and the synthetic controls (Q6).

```bash
python -m src.models.did
python -m src.models.placebo
python -m src.models.synth
```

The dashboard runs no model and reads only the committed `outputs/tables/*.csv` and `data/snapshots/channel_stats.csv`. To serve it locally:

```bash
streamlit run app/streamlit_app.py
```

## Documents

- `METHODS.md`: identification strategy, the accrual argument, confounds, placebo results, and limitations.
- `docs/WRITEUP.md`: the argument across the six questions, with four figures.
- `docs/FINDINGS.md`: every estimate with its interval and N.
- `docs/SCOPE.md`, `docs/DECISIONS.md`, `docs/HYPOTHESES.md`: the frozen scope, the decision log, and the pre-registered signs.

## Reporting rules

Every number in this repository is read from a committed table in `outputs/tables/` or from `docs/FINDINGS.md`. Correlational results are reported as associated with an event, not caused by it, because the pre-trend test rejects parallel trends. A null is reported as an estimate with its interval and its precision limit, not as an absence of effect. KSI's claim is reported per sub-claim with the precision achieved, and no sub-claim is stated as proven or refuted.
