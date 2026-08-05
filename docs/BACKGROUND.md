# Background

## The trigger

On 2026-05-31 KSI (Olajide Olatunji) published a video announcing his exit from
the Sidemen. Press reported the tenure as 13 years (Forbes 2026-05-31, Deadline
2026-06-01, CNN 2026-06-01). cohort_groups.csv dates the formation to 2013-10-19,
which is 12 years before the exit. The remaining six members stated publicly that
the exit was unexpected.

In late July 2026 KSI published a YouTube community post, reshared to an Instagram
story, arguing that YouTube groups suppress individual creator growth. The
argument, in his terms:

1. Pair collaborations are reciprocal. Creator A appears on Creator B's channel,
   Creator B appears on Creator A's channel. Both channels gain.
2. Group collaborations are not reciprocal. Creators A, B, and C appear on the
   group channel. The group channel rarely produces content for the members'
   individual channels.
3. Members therefore receive exposure without traffic. The group channel captures
   the views.
4. Conclusion in his words: YouTube groups kill growth in this space and turn it
   into a monopoly.

The archived screenshot `docs/source/ksi_story_2026-07.png` captures the Instagram
reshare of the community post. Secondary reference:
https://x.com/evenprimeodd/status/2082389214264725719/photo/1

## Why this is worth measuring

The claim is empirical, specific, and stated as a general law. It has never been
tested with data. It is also testable: every input (upload dates, view counts,
video durations, description links, group membership dates) is publicly available
at zero cost.

The claim decomposes into four sub-claims that can resolve differently. Sub-claim
2 is close to true by construction and carries little information. Sub-claims 3
and 4 are the substantive ones.

A fifth question, which KSI does not raise, is the likely location of the actual
finding: whether the sign of the effect depends on the member's size before
joining. If group membership subsidises small members and taxes large ones, the
claim is correct about KSI specifically and incorrect as a general law.

## Personal motivation and positionality

I began watching these creators before the Sidemen channel was created on
2015-06-14 (source channels.list), following the members as individual channels
first. My viewing has declined in recent years due to other responsibilities. The
exit announcement prompted the question.

This positionality is disclosed as a prior. It explains why the Sidemen ecosystem
is the primary case rather than an arbitrary starting point, and it discloses that
I am a long-term viewer of one group in the sample. The analysis is held to the
pre-registered hypotheses in `docs/HYPOTHESES.md` rather than to intuition about
what the answer should be.

That my viewing predates the group channel is analytically relevant, not just
biographical. It matches the structure of the claim under test: members had
individual channels first, and the group channel was added on top.

The Sidemen channel's creation date from channels.list is 2015-06-14, the basis
for the pre-channel viewing statement above.

## What this project is not

Not a Sidemen retrospective. Not a ranking of creators. Not a prediction of who
grows next. The output is an estimate, its precision, and the assumptions required
to read it causally.
