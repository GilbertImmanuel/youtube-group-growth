"""Page 5: the six questions with the answer reached for each. No charts."""

import streamlit as st

import lib

st.set_page_config(page_title="Questions", page_icon="📊", layout="wide")

lib.page_header(
    "Q1 to Q6",
    "Questions",
    "The six pre-registered questions, with the answer reached for each. Some resolve as "
    "descriptive associations, one is not answerable at the coverage reached, and the two case "
    "studies resolve unevenly. Where a question cannot be answered, the reason is given, and the "
    "change that would answer it is listed among the suggestions on the Conclusion page.",
)

ANSWERED = "#199e70"
BOUNDED = "#c98500"
UNANSWERABLE = lib.ACCENT


def question(qid, text, status, color, body):
    st.markdown(f"#### {qid}. {text}")
    st.markdown(
        f"<span style='display:inline-block;background:{color}22;color:{color};"
        f"border:1px solid {color}66;border-radius:999px;padding:1px 10px;font-size:0.78rem;"
        f"font-weight:600'>{status}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(body)
    st.divider()


question(
    "Q1", "Is attention concentrating inside group ecosystems?",
    "Answered, no rise", ANSWERED,
    "Cross-group mean HHI moves from 0.422 at month -24 to 0.356 at formation and 0.414 at month "
    "+24, and Gini holds at 0.474 and 0.473 at the window ends. Concentration does not rise as "
    "the claim predicts, and at the observed dispersion it cannot be distinguished from flat "
    "(outputs/tables/q1_concentration.csv).",
)

question(
    "Q2", "Does membership reduce solo output?",
    "Answered, not identified", BOUNDED,
    "Treated channels average 9.31 long-form uploads per month before treatment and 8.24 after, "
    "while matched controls decline in parallel, from 9.95 to 8.37. The treated level falls in "
    "the predicted direction, yet the fall cannot be separated from the secular decline the "
    "controls also show (outputs/tables/q2_uploads.csv).",
)

question(
    "Q3", "Does membership reduce external pair collaborations?",
    "Not answerable at current coverage", UNANSWERABLE,
    "This question is not answerable at the coverage reached. Collaboration extraction reached an "
    "F1 of 0.6634, below the 0.75 target, so the measure is limited to the Sidemen ecosystem, "
    "where the mean stays between 0.00 and 0.571 external partners per creator-quarter. Because "
    "the other cohort groups formed in 2019 or later, after the Sidemen window, the cross-group "
    "count is a structural floor rather than a measured decline. Raising the extractor's F1 above "
    "0.75 would extend the measure to the other ecosystems; see the suggestions on the Conclusion "
    "page (outputs/tables/q3_external_collabs.csv, loops/collabs/log.md).",
)

question(
    "Q4", "Does membership change individual video performance?",
    "Answered as an association", BOUNDED,
    "The overall post-treatment estimate is a positive 0.339 log points, interval [0.194, 0.485], "
    "across 30 channels and 12342 videos. The pre-trend test rejects parallel trends, so the "
    "estimate is read as an association rather than a treatment effect, and its positive sign is "
    "the opposite of the negative direction the claim predicts "
    "(outputs/tables/did_overall_att.csv, did_pretrend_test.csv).",
)

question(
    "Q5", "Does the sign flip with pre-join size?",
    "Answered as an association", BOUNDED,
    "Split at the median, the large arm is 0.145, interval [0.011, 0.280], and the small arm is "
    "0.579, interval [0.416, 0.748]. Both arms are positive and the small arm is larger, so the "
    "small-member direction matches the prior while the large-member direction does not, since "
    "the general law requires large members to lose views. Under the violated pre-trend both arms "
    "remain associations (outputs/tables/did_q5_heterogeneity.csv).",
)

question(
    "Q6", "Named case studies (KSI exit, Team 10 collapse).",
    "One not interpretable, one null", BOUNDED,
    "The two cases resolve differently. The KSI exit is not interpretable: its post window spans "
    "9.7 weeks and 3 observations, the pre-fit RMSPE is 0.932, and the recent videos carry an "
    "accrual caveat, so the 0.318 log-point gap is described rather than read. The Team 10 "
    "collapse yields a negative gap of -0.195 log points that ranks 15 of 41 in the placebo "
    "distribution (p 0.366), a null that is imprecise at a single treated unit rather than an "
    "established zero. Observing the KSI post window after twelve months clear the 180-day age "
    "filter would make that case interpretable; see the suggestions on the Conclusion page "
    "(outputs/tables/synth_fit.csv, synth_placebo.csv).",
)
