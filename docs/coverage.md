# Deleted-video coverage gap

The YouTube Data API returns only videos that are live at snapshot time. Videos
deleted or set to private before the pull are absent from the uploads playlist,
so any per-channel count is a count of survivors, not of everything published.
Section 4.2 of `docs/SCOPE.md` records this as a known limitation to quantify.

## Pipeline counts

Produced by `src/clean/build.py` on the raw pull `data/raw/videos.jsonl`:

| Stage | Rows |
|---|---|
| raw | 544572 |
| deduped | 542541 |
| long-form (> 60s) | 466698 |
| age-filtered (long-form and >= 180 days) | 432451 |

Reference date for the age filter is 2026-08-07, the newest publish date in the
raw pull, reported by `src/clean/build.py`.

## Deleted-rate sample

Produced by `src/clean/deleted_rate.py`. Method: sample one group channel per
distinct ecosystem, read the video IDs listed on Wayback captures of each
channel's /videos grid, and count the fraction of those IDs not present in the
collected pull. Six channels were sampled.

| Channel | Archived IDs | Absent from pull | Rate |
|---|---|---|---|
| Sidemen | 0 | 0 | n/a |
| Beta Squad | 0 | 0 | n/a |
| AMP | 60 | 0 | 0.000 |
| 2HYPE | 0 | 0 | n/a |
| Dude Perfect | 46 | 24 | 0.522 |
| OfflineTV | 32 | 0 | 0.000 |

Overall: 24 of 138 archived IDs are absent from the pull, an upper-bound
unobserved-deleted rate of 0.174 (N=138 archived IDs across 6 sampled channels),
reported by `src/clean/deleted_rate.py`.

## Reading the number

The 0.174 figure is an upper bound on a small sample, not a correction applied to
the estimate. Three qualifications:

1. Recommendation contamination. Archived grids also carry sidebar and related
   links to other channels. An archived ID absent from the whole pull can be a
   deleted cohort video or a link to a non-cohort channel. All 24 absent IDs come
   from Dude Perfect, whose older grid capture renders many related-video links.
   AMP and OfflineTV, whose captures expose a clean uploads grid, return 0 absent.
2. Sparse archival of modern grids. Three of the six sampled channels returned 0
   archived IDs because their /videos captures are redirects or client-rendered
   pages that store no IDs in the archived HTML. N is therefore small.
3. Dude Perfect is a contrast case excluded from all estimation (Q1 to Q6, per
   `docs/SCOPE.md` 2.3), so its inflated rate does not enter the estimation
   sample.

The gap for the estimation cohort is bounded above by 0.174 and is most likely
well below it. Deleted and privatised videos remain unobservable, so this rate is
disclosed as the coverage limit, not removed from the data.

## Reproduce

```
python -m src.clean.deleted_rate
```

Wayback CDX throttles under load and times out on high-capture URLs, so the
sampled channels and N can vary between runs.
