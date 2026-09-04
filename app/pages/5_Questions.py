"""Page 5: the six questions with the answer reached for each. No charts."""

import streamlit as st

import lib

st.set_page_config(page_title="Questions", page_icon="📊", layout="wide")

lib.page_header(
    "Q1 to Q6",
    "Questions",
    "The six pre-registered questions, with the answer reached for each. Some resolve as "
    "descriptive associations, one is not answerable at the coverage reached, and the two case "
    "studies resolve unevenly. Where a question cannot be answered, the reason is given together "
    "with the change that would answer it in a replication.",
)


def question(qid, text, verdict, body):
    st.markdown(f"#### {qid}. {text}")
    st.markdown(f"**{verdict}**")
    st.markdown(body)
    st.divider()


question(
    "Q1", "Is attention concentrating inside group ecosystems?",
    "The question is answered, and the answer is no.",
    "Cross-group mean HHI moves from 0.422 at month -24 to 0.356 at formation and 0.414 at month "
    "+24, and Gini holds at 0.474 and 0.473 at the two window ends, so the level closes the window "
    "near where it opened. Because the cross-group dispersion stays wide throughout, the small "
    "movement cannot be separated from a flat line, and concentration does not rise in the "
    "direction the claim predicts (outputs/tables/q1_concentration.csv).",
)

question(
    "Q2", "Does membership reduce solo output?",
    "It is answered descriptively, but not identified against a counterfactual.",
    "Treated channels average 9.31 long-form uploads per month before treatment and 8.24 after, "
    "while their matched controls fall in parallel from 9.95 to 8.37. The treated level does move "
    "in the predicted direction, yet because the controls decline by a similar amount, the "
    "reduction reflects a secular fall in upload frequency rather than a membership-specific "
    "effect, and the two cannot be separated at this precision (outputs/tables/q2_uploads.csv).",
)

question(
    "Q3", "Does membership reduce external pair collaborations?",
    "It cannot be answered at the coverage this project reached.",
    "Collaboration extraction reached an F1 of 0.6634, below the 0.75 target, so the measure is "
    "confined to the Sidemen ecosystem, where the mean stays between 0.00 and 0.571 external "
    "partners per creator-quarter. Because the other cohort groups formed in 2019 or later, after "
    "the Sidemen window, their cross-group counts are a structural floor rather than a measured "
    "decline. A replication could answer this question by first lifting the extractor above the "
    "0.75 target, for example by hand-labelling a larger validation set or by adding the native "
    "collaborator tag as a second signal alongside the description-link parser, and then widening "
    "the collaboration graph to every ecosystem so the count is measured rather than bounded "
    "(outputs/tables/q3_external_collabs.csv, loops/collabs/log.md).",
)

question(
    "Q4", "Does membership change individual video performance?",
    "The question is answered, though only as an association.",
    "The overall post-treatment estimate is a positive 0.339 log points, with an interval of "
    "[0.194, 0.485] across 30 channels and 12342 videos, so its sign is the opposite of the "
    "decline the claim predicts. Because the pre-trend test rejects parallel trends, the "
    "identifying assumption behind a causal reading does not hold, and the estimate is reported "
    "as an association rather than a treatment effect "
    "(outputs/tables/did_overall_att.csv, did_pretrend_test.csv).",
)

question(
    "Q5", "Does the sign flip with pre-join size?",
    "It is answered as well, again only as an association.",
    "Split at the median, the large arm is 0.145, interval [0.011, 0.280], and the small arm is "
    "0.579, interval [0.416, 0.748], so both arms are positive and the smaller members gain more. "
    "The small-member direction matches the prior, whereas the large-member direction does not, "
    "since the general law would require large members to lose views. Because the same pre-trend "
    "violation applies, both arms are read as associations rather than effects "
    "(outputs/tables/did_q5_heterogeneity.csv).",
)

question(
    "Q6", "Named case studies (KSI exit, Team 10 collapse).",
    "One case is answered and the other is left open.",
    "The Team 10 collapse yields a negative gap of -0.195 log points that ranks 15 of 41 in the "
    "placebo distribution (p 0.366), a null that is imprecise at a single treated unit rather "
    "than an established zero. By contrast, the KSI exit is not interpretable, because its post "
    "window spans only 9.7 weeks and three monthly observations, the pre-fit RMSPE is 0.932, and "
    "the recent videos still carry an accrual caveat, so the 0.318 log-point gap is described "
    "rather than read. A replication could close the KSI case by waiting until twelve months of "
    "post-exit long-form clear the 180-day age filter, which would lengthen the post window and "
    "let the recent views accrue enough to compare against the synthetic "
    "(outputs/tables/synth_fit.csv, synth_placebo.csv).",
)
