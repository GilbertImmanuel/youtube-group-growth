"""Page 2: reciprocity ledger and external collaborations (sub-claims 1, 2, and Q3)."""

import altair as alt
import pandas as pd
import streamlit as st

import lib

st.set_page_config(page_title="Reciprocity", page_icon="📊", layout="wide")

lib.page_header(
    "Sub-claims 1, 2, and Q3",
    "Reciprocity",
    "Whether the appearances members give the group channel are returned by it, and whether "
    "membership coincides with fewer external collaborations. Detection is alias-based and "
    "Sidemen-dense, so the group-to-member direction is read as a floor rather than a proven "
    "absence.",
)

# ---- Reciprocity ledger ---------------------------------------------------------

st.subheader("Appearance ledger by direction")
led = lib.load("reciprocity_ledger")
led = led[led["group"].isin(lib.ECOSYSTEM_ORDER)]

t = st.columns(2)
t[0].metric("Member-to-group appearances, total", f"{int(led['member_to_group'].sum()):,}")
t[1].metric("Group-to-member appearances, total", f"{int(led['group_to_member'].sum()):,}")

long = led.melt(
    id_vars="group",
    value_vars=["member_to_group", "group_to_member"],
    var_name="direction", value_name="count",
)
label = {"member_to_group": "Member to group", "group_to_member": "Group to member"}
long["direction"] = long["direction"].map(label)

y = alt.Y("group:N", sort=lib.ECOSYSTEM_ORDER, title=None)
dcolor = alt.Color("direction:N", title="Direction",
                   scale=alt.Scale(domain=["Member to group", "Group to member"],
                                   range=[lib.ACCENT, lib.COUNTERFACTUAL]))
connector = alt.Chart(led).mark_rule(color="#3a3a38", strokeWidth=2).encode(
    y=y,
    x=alt.X("member_to_group:Q", scale=alt.Scale(type="log"), title="Appearances (log scale)"),
    x2="group_to_member:Q",
)
dots = alt.Chart(long).mark_circle(size=140).encode(
    y=y,
    x=alt.X("count:Q", scale=alt.Scale(type="log")),
    color=dcolor,
    tooltip=["group", "direction", "count"],
)
lib.show((connector + dots).properties(height=280,
         title="Member-to-group far exceeds group-to-member, four of five groups"))

lib.takeaway(
    "Across the five groups, member-to-group appearances total 20235 against 658 in the reverse "
    "direction. The asymmetry is consistent with pair reciprocity present and group reciprocity "
    "absent for four of the five groups, and only 2HYPE reverses it, its group channel having "
    "been inactive in recent years.",
    "outputs/tables/reciprocity_ledger.csv, FINDINGS reciprocity ledger",
)
lib.inference(
    "On the log scale, the distance between the two dots on each row spans three to four orders of "
    "magnitude for four of the five groups, so the exchange is one-directional rather than merely "
    "tilted, and 2HYPE is the single row where the dots swap sides.")

with st.expander("Table view"):
    st.dataframe(led[["group", "member_to_group", "group_to_member", "ratio_m2g_over_g2m"]],
                 hide_index=True)

st.divider()

# ---- Q3 external collaborations -------------------------------------------------

st.subheader("External collaborations around formation")
q3 = lib.load("q3_external_collabs")
q3["lo"] = q3["mean_external_partners"] - q3["std_external_partners"].fillna(0)
q3["hi"] = q3["mean_external_partners"] + q3["std_external_partners"].fillna(0)

chart = lib.band_line(q3, "rel_quarter", "mean_external_partners", "lo", "hi",
                      lib.ECOSYSTEM_COLOR["Sidemen"], "Quarters from formation",
                      "Distinct cross-group partners per creator", point=True)
zero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(
    color=lib.COUNTERFACTUAL, strokeDash=[4, 4]).encode(x="z:Q")
lib.show((chart + zero).properties(height=300,
         title="Cross-group collaboration counts, Sidemen ecosystem only"))

lib.caveat(
    "Two restrictions bound this measure. Collaboration extraction reached an F1 of 0.6634, below "
    "the 0.75 target, so the measure is limited to the Sidemen ecosystem. Furthermore, the other "
    "cohort groups formed in 2019 or later, after this window, so the cross-group count is a "
    "structural floor rather than a measured decline, and sub-claim 1 is not testable at this "
    "coverage."
)
lib.takeaway(
    "The mean stays near 0 across the window, between 0.00 and 0.571 external partners per "
    "creator-quarter, at N=7 Sidemen members per quarter.",
    "outputs/tables/q3_external_collabs.csv, FINDINGS Q3",
)
lib.inference(
    "The line sits on the floor for the whole window, which is what a measure with no room to fall "
    "looks like, so the flatness reflects the coverage limit rather than a decline in "
    "collaboration.")
