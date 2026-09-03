"""Page 4: methods, identifying assumptions, and limitations. No charts."""

import streamlit as st

import lib

st.set_page_config(page_title="Methods", page_icon="📊", layout="wide")

lib.page_header(
    "Identification and limits",
    "Methods",
    "The estimator, the assumptions a causal reading requires, the reason the main estimates are "
    "reported as associations, and the limitations that bound every figure on the other pages.",
)

st.subheader("Estimator")
st.markdown(
    "The pre-registered primary estimator, Callaway and Sant'Anna via the differences package, "
    "runs the point estimates and the event study, but its group-level clustering path is broken "
    "by a pandas-3 API change inside the package. The analysis therefore uses the pre-registered "
    "fallback, a Sun and Abraham interaction-weighted event study, at the video level: a weighted "
    "OLS of log(views) on channel and calendar-month fixed effects together with "
    "cohort-by-relative-period interactions, and with never-treated and not-yet-treated channels "
    "as the comparison. Inference is a group-level wild cluster bootstrap over the five "
    "ecosystems, using Webb six-point weights."
)

st.subheader("Identifying assumptions")
st.markdown(
    "A causal reading requires parallel trends, meaning that absent treatment the treated and "
    "control channels would follow the same log(views) path. The pre-trend test rejects this "
    "(sup-t 7.672, p 0.001, 5 clusters), so the assumption does not hold at the observed "
    "precision and the estimates are reported as associations.\n\n"
    "The design also carries an accrual argument. Because a single API snapshot returns "
    "cumulative views, older videos have accrued for longer. Within a channel, video age is a "
    "deterministic function of publish date, so age and calendar time are collinear, and "
    "calendar-month fixed effects absorb the accrual common to treated and control channels in "
    "each month. The residual assumption is that accrual curves do not differ systematically "
    "between the two groups."
)

st.subheader("Four limitations")
st.markdown(
    "1. **Founder versus joiner.** Most treated creators are treated at their group's formation "
    "rather than through a later external join, so treatment is endogenous to the member's own "
    "trajectory. Only three of the 30 eligible creators are clean late joiners, which makes that "
    "robustness check correspondingly imprecise.\n\n"
    "2. **Treatment timing and clustering.** The five treatment cohorts span 2015 to 2020. At "
    "five clusters, group-level clustering with conventional standard errors is invalid, and "
    "channel-level clustering understates the standard errors because treatment is assigned at "
    "the group level, which is why inference uses the wild cluster bootstrap.\n\n"
    "3. **Channels without a pre-treatment period.** Q4 and Q5 require at least 12 months of "
    "channel history before treatment, a rule that retains 30 of 32 main-cohort members.\n\n"
    "4. **Subscriber matching date.** Controls were matched on 2019 size rather than on size at "
    "treatment, which biases control selection toward channels of similar 2019 size regardless "
    "of their growth path."
)

st.subheader("Synthetic control and precision")
st.markdown(
    "Each Q6 case fits an Abadie synthetic control on the treated channel's monthly mean "
    "log(views), with donor weights that are non-negative and sum to one. Because a single "
    "treated unit has no valid conventional standard error, inference is an in-space placebo "
    "permutation, and the treated unit's placebo rank serves as the inference. The DiD bootstrap "
    "runs over 5 ecosystem clusters, and at this count the Webb wild cluster bootstrap is coarse, "
    "so the cluster count, not the video count, bounds the precision."
)

st.subheader("Per sub-claim reading")
st.markdown(
    "KSI's claim decomposes into four sub-claims, each reported with the precision achieved. "
    "Following the project reporting rule, the claim is neither proven nor refuted."
)
st.table({
    "Sub-claim": [
        "1 pair reciprocity",
        "2 group non-reciprocity",
        "3 exposure without traffic",
        "4 growth suppression",
    ],
    "Evidence": [
        "Reciprocity ledger, member-to-group direction",
        "Reciprocity ledger, group-to-member near zero",
        "Attention share, group channel 0.253 to 0.693 in 2026",
        "Q1 concentration, Q4 and Q5 associations, Q6 cases",
    ],
    "Reading": [
        "Consistent for 4 of 5 groups",
        "Consistent for 4 of 5 groups",
        "Consistent at ecosystem level",
        "Q4 and Q5 positive, not the negative sign the claim predicts",
    ],
    "Precision": [
        "Alias detection, Sidemen-dense",
        "Floor, not proven absence",
        "Cumulative-view accrual caveat",
        "Pre-trend violated, 5 clusters, association only",
    ],
})

st.divider()
st.subheader("Data provenance")
st.markdown(
    "Every figure is read from a committed derived table in outputs/tables/ (14 tables) together "
    "with data/snapshots/channel_stats.csv, and the dashboard calls no API and reads no raw or "
    "processed video data. Views are cumulative at a single snapshot whose maximum published date "
    "is 2026-08-07, and long-form videos are at least 180 days old at that time, with the "
    "exception of the relaxed KSI post window. The findings text is docs/FINDINGS.md, and the "
    "design and decisions are recorded in docs/SCOPE.md and docs/DECISIONS.md."
)
