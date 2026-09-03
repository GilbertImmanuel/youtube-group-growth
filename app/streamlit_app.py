"""Home page for the YouTube group-growth dashboard."""

import streamlit as st

import lib

st.set_page_config(
    page_title="Group growth study",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

lib.page_header(
    "YouTube group growth",
    "Does group membership suppress individual creator growth",
    "This dashboard examines a public claim by KSI, that YouTube groups suppress individual "
    "creator growth and turn the space into a monopoly. Every figure is read from a committed "
    "derived table and agrees with docs/FINDINGS.md, and the pages present frozen results "
    "without running a model or calling an API.",
)

st.markdown(
    "#### The claim under test\n"
    "On 2026-05-31 KSI announced his exit from the Sidemen, and in late July 2026 he argued in a "
    "YouTube community post that group collaborations are not reciprocal. Members appear on the "
    "group channel, the group channel rarely returns content to the members, and members "
    "therefore receive exposure without the traffic a reciprocal pair collaboration would carry. "
    "The argument decomposes into four sub-claims, which this study reports one by one with the "
    "precision achieved. Following the project reporting rule, no sub-claim is stated as proven "
    "or refuted."
)

st.markdown(
    "#### The pages\n"
    "Six pages read against one committed set of tables. Ecosystem explorer covers attention "
    "concentration (Q1) and the group channel's yearly share of ecosystem views. Reciprocity "
    "covers the member-to-group against group-to-member appearance ledger and external "
    "collaboration counts (Q3). Event study covers solo output (Q2), the staggered-DiD "
    "association for video performance (Q4) and its split by pre-join size (Q5), the placebo "
    "checks, and the two synthetic-control cases (Q6). Methods sets out the estimator, the "
    "identifying assumptions, and the limitations. Questions lists Q1 through Q6 with "
    "the answer reached for each. Conclusion states what the six questions together support, and "
    "where the analysis stops."
)

st.divider()

st.markdown(
    "#### Positionality\n"
    "The owner followed these creators as individual channels before the Sidemen channel was "
    "created on 2015-06-14, and viewing has declined in recent years. Long-term attachment to "
    "one group in the sample is a prior, disclosed here as the reason the hypotheses were fixed "
    "before any model was run."
)

st.markdown(
    "#### How to read the results\n"
    "Parallel trends, the assumption a causal reading of Q4 and Q5 requires, is violated, so "
    "those estimates are reported as associations rather than treatment effects. Results are "
    "described as associated with an event, never with a causal verb, and a null is reported as "
    "an estimate with its interval and its precision limit rather than as an absence of effect."
)

st.divider()
st.caption(
    "Sources: outputs/tables/*.csv (14 tables) and data/snapshots/channel_stats.csv, committed "
    "to the repository. Findings text: docs/FINDINGS.md. Design and scope: docs/SCOPE.md, "
    "docs/DECISIONS.md."
)
