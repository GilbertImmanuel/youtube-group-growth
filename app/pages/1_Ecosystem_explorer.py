"""Page 1: ecosystem-level descriptive results (Q1 concentration, attention share)."""

import altair as alt
import streamlit as st

import lib

st.set_page_config(page_title="Ecosystem explorer", page_icon="📊", layout="wide")

lib.page_header(
    "Q1 and attention share",
    "Ecosystem explorer",
    "Two descriptive readings aligned to each group's formation date: whether attention "
    "concentrates inside a group's ecosystem, and how large a share of the ecosystem's views the "
    "group channel commands. Both are associations, not treatment effects.",
)

# ---- Q1 concentration -----------------------------------------------------------

st.subheader("Attention concentration around formation")
q1 = lib.load("q1_concentration")
by_month = q1.set_index("rel_month")

t = st.columns(3)
t[0].metric("Mean HHI, month -24", lib.fmt(by_month.loc[-24, "mean_hhi"]))
t[1].metric("Mean HHI, formation", lib.fmt(by_month.loc[0, "mean_hhi"]))
t[2].metric("Mean HHI, month +24", lib.fmt(by_month.loc[24, "mean_hhi"]))

c1, c2 = st.columns(2)
with c1:
    q1["hhi_lo"] = q1["mean_hhi"] - q1["std_hhi"].fillna(0)
    q1["hhi_hi"] = q1["mean_hhi"] + q1["std_hhi"].fillna(0)
    chart = lib.band_line(q1, "rel_month", "mean_hhi", "hhi_lo", "hhi_hi",
                          lib.ACCENT, "Months from formation", "Mean HHI of monthly views")
    zero = alt.Chart({"values": [{"z": 0}]}).mark_rule(
        color=lib.COUNTERFACTUAL, strokeDash=[4, 4]).encode(x="z:Q")
    lib.show((chart + zero).properties(title="HHI, cross-group mean with dispersion band"))
    st.caption("Band is the per-period cross-group standard deviation. N=5 groups per month.")
with c2:
    q1["gini_lo"] = q1["mean_gini"] - q1["std_gini"].fillna(0)
    q1["gini_hi"] = q1["mean_gini"] + q1["std_gini"].fillna(0)
    chart = lib.band_line(q1, "rel_month", "mean_gini", "gini_lo", "gini_hi",
                          lib.ECOSYSTEM_COLOR["AMP"], "Months from formation", "Mean Gini of monthly views")
    zero = alt.Chart({"values": [{"z": 0}]}).mark_rule(
        color=lib.COUNTERFACTUAL, strokeDash=[4, 4]).encode(x="z:Q")
    lib.show((chart + zero).properties(title="Gini, cross-group mean with dispersion band"))
    st.caption("Gini is 0.474 at month -24 and 0.473 at month +24.")

lib.takeaway(
    "Cross-group mean HHI moves from 0.422 at month -24 to 0.356 at formation and 0.414 at month "
    "+24, and the dispersion stays wide throughout. The series does not follow the pre-registered "
    "rises direction, so at this precision it cannot be distinguished from flat.",
    "outputs/tables/q1_concentration.csv, FINDINGS Q1",
)
lib.inference(
    "Read from the chart, the mean line stays within its dispersion band across the whole window, "
    "so any drift is small next to the spread between ecosystems and should not be read as "
    "concentration building up.")
st.latex(r"\mathrm{HHI} = \sum_{i} s_i^{2}")
st.caption(r"Here $s_i$ is channel $i$'s share of monthly ecosystem views, and HHI is 1 when a "
           r"single channel holds every view.")

st.divider()

# ---- Attention share ------------------------------------------------------------

st.subheader("Group channel share of ecosystem views")
share = lib.load("attention_share")
share = share[share["group"].isin(lib.ECOSYSTEM_ORDER)]

color = alt.Color("group:N", title="Ecosystem",
                  scale=alt.Scale(domain=lib.ECOSYSTEM_ORDER,
                                  range=[lib.ECOSYSTEM_COLOR[g] for g in lib.ECOSYSTEM_ORDER]))

c1, c2 = st.columns([3, 2])
with c1:
    line = alt.Chart(share).mark_line(strokeWidth=2, point=True).encode(
        x=alt.X("year:Q", title="Video publish year", axis=alt.Axis(format="d")),
        y=alt.Y("group_share:Q", title="Group channel share of ecosystem views",
                scale=alt.Scale(domain=[0, 1])),
        color=color,
        tooltip=["group", "year", alt.Tooltip("group_share:Q", format=".3f")],
    ).properties(height=320, title="Group share by year, near 0 before formation")
    lib.show(line)
with c2:
    latest = share[share["year"] == 2026].copy()
    bar = alt.Chart(latest).mark_bar(cornerRadius=3).encode(
        x=alt.X("group_share:Q", title="Group share in 2026", scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("group:N", sort=lib.ECOSYSTEM_ORDER, title=None),
        color=color,
        tooltip=["group", alt.Tooltip("group_share:Q", format=".3f")],
    ).properties(height=320, title="2026 group share by ecosystem")
    text = bar.mark_text(align="left", dx=3, color="#c3c2b7").encode(
        text=alt.Text("group_share:Q", format=".3f"))
    lib.show(bar + text)

lib.takeaway(
    "The group channel's share sits near 0 before formation and, by 2026, reaches 0.456 for "
    "Sidemen, 0.693 for Beta Squad, 0.632 for AMP, 0.253 for OfflineTV, and 0.000 for 2HYPE, "
    "whose group channel was inactive that year. Because view_count is cumulative at a single "
    "snapshot the level carries an accrual caveat, though the within-year cross-channel share "
    "largely cancels the common accrual factor.",
    "outputs/tables/attention_share.csv, FINDINGS attention share",
)
lib.inference(
    "The lines climb from near zero only after each ecosystem forms, so the chart places the rise "
    "in time without showing the group channel caused it; the within-year cross-channel share is "
    "what carries the reading, not the absolute height.")

with st.expander("Table view"):
    st.dataframe(latest[["group", "group_share", "member_share",
                         "n_group_channels", "n_member_channels"]], hide_index=True)
