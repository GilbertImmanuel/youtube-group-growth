"""Page 6: conclusion and suggestions. No charts."""

import streamlit as st

import lib

st.set_page_config(page_title="Conclusion", page_icon="📊", layout="wide")

lib.page_header(
    "Synthesis",
    "Conclusion",
    "What the six questions together say about the claim, and where the analysis stops. The "
    "reading is associational, and it settles the claim in neither direction.",
)

st.subheader("Conclusion")
st.markdown(
    "This study set out to test a public claim that YouTube group membership suppresses "
    "individual creator growth and concentrates it. Read across the six questions, the evidence "
    "is associational, and the analysis does not establish the claim as proven or refuted. The "
    "reciprocity ledger records member appearances on the group channel far exceeding returns "
    "from it for four of the five estimation groups, and at the ecosystem level the group channel "
    "commands a plurality to majority share of 2026 views. Both patterns are consistent with the "
    "exposure-without-traffic mechanism the claim describes, subject to alias-based detection and "
    "the cumulative-view accrual caveat."
)
st.markdown(
    "Growth suppression is where the data and the claim diverge. Specifically, the staggered-DiD "
    "associations for video performance are positive rather than negative, the small-member arm "
    "is larger than the large-member arm, and the pre-trend test rejects parallel trends, so the "
    "negative direction the general law requires is absent at the observed precision. Neither "
    "synthetic-control case recovers the release of views that an exit or a collapse would "
    "predict under that law: the KSI post window is too short and too accrual-contaminated to "
    "read, and the Team 10 gap sits inside its placebo distribution. Taken together, the results "
    "are consistent with the descriptive premises of the claim and inconsistent with its central "
    "prediction, though the violated identifying assumption keeps the reading an association "
    "rather than a treatment effect, and the claim remains unsettled either way."
)
st.caption(
    "Read against docs/FINDINGS.md. Figures and intervals are on the Ecosystem explorer, "
    "Reciprocity, and Event study pages; the identifying assumptions and limitations are on the "
    "Methods page; the per-question answers are on the Questions page."
)

st.divider()

st.subheader("Suggestions")
st.markdown(
    "Each direction below targets a limit the current data imposes, and none reopens a frozen "
    "result."
)
st.markdown(
    "1. Reconstruct daily view velocity from the committed snapshot series in "
    "data/snapshots/channel_stats.csv, which a single cumulative snapshot cannot recover, so the "
    "accrual caveat that bounds Q3, the attention share, and the KSI case can be narrowed.\n\n"
    "2. Revisit the KSI exit once twelve months of post-exit long-form clear the 180-day age "
    "filter; the observed window is 9.7 weeks and three monthly observations (synth_fit.csv), "
    "which is too short to interpret.\n\n"
    "3. Treat the FaZe diaspora (CORE) as a candidate natural experiment from 2027-06-01, once a "
    "post-period exists (docs/SCOPE.md 2.4).\n\n"
    "4. Raise collaboration-extraction F1 above the 0.75 target, from the 0.6634 reached "
    "(loops/collabs/log.md), so Q3 can extend beyond the Sidemen ecosystem.\n\n"
    "5. Add treatment clusters or adopt a design that is stable at few clusters, since the "
    "five-ecosystem wild bootstrap, not the video count, bounds the precision."
)
