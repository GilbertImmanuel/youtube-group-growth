"""Page 3: event-aligned results with counterfactuals (Q2, Q4, Q5, placebo, Q6)."""

import altair as alt
import pandas as pd
import streamlit as st

import lib

st.set_page_config(page_title="Event study", page_icon="📊", layout="wide")

lib.page_header(
    "Q2, Q4, Q5, and Q6",
    "Event study",
    "Five outcomes aligned to a treatment event and read against a counterfactual: solo output "
    "(Q2), video performance (Q4), its split by pre-join size (Q5), the placebo checks, and two "
    "synthetic-control cases (Q6).",
)

lib.caveat(
    "The pre-trend test rejects the null of no pre-trend (sup-t 7.672, p 0.001, over 23 "
    "pre-periods and 5 clusters). Parallel trends is the identifying assumption a causal reading "
    "requires, so with it violated the Q4 and Q5 estimates are reported as associations rather "
    "than treatment effects. Following the project stopping rule, a failed pre-trend is treated "
    "as the finding, and the specification is not changed in response."
)
st.write("")

# ---- Q2 uploads -----------------------------------------------------------------

st.subheader("Q2 Solo output around joining")
q2 = lib.load("q2_uploads")
q2["lo"] = q2["mean_uploads"] - q2["std_uploads"].fillna(0)
q2["hi"] = q2["mean_uploads"] + q2["std_uploads"].fillna(0)
q2["arm"] = q2["arm"].map({"treated": "Treated", "control": "Control"})

arm_color = alt.Color("arm:N", title="Arm",
                      scale=alt.Scale(domain=["Treated", "Control"],
                                      range=[lib.ACCENT, lib.COUNTERFACTUAL]))
area = alt.Chart(q2).mark_area(opacity=0.15).encode(
    x=alt.X("rel_month:Q", title="Months from treatment"),
    y=alt.Y("lo:Q", title="Long-form uploads per month"), y2="hi:Q", color=arm_color)
line = alt.Chart(q2).mark_line(strokeWidth=2).encode(
    x="rel_month:Q", y="mean_uploads:Q", color=arm_color,
    tooltip=["arm", "rel_month", alt.Tooltip("mean_uploads:Q", format=".2f")])
zero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(
    color="#c3c2b7", strokeDash=[4, 4]).encode(x="z:Q")
lib.show((area + line + zero).properties(height=300,
         title="Treated and matched controls, uploads per month"))
lib.takeaway(
    "Treated channels average 9.31 long-form uploads per month before treatment and 8.24 after, "
    "while matched controls average 9.95 before and 8.37 after. Because both arms decline by a "
    "similar amount, a treated-specific reduction cannot be separated from the secular decline "
    "the controls also show.",
    "outputs/tables/q2_uploads.csv, FINDINGS Q2",
)

st.divider()

# ---- Q4 DiD event study ---------------------------------------------------------

st.subheader("Q4 Video performance, staggered DiD")
es = lib.load("did_event_study")
att = lib.load("did_overall_att").iloc[0]

lib.stat_row([
    ("Overall post ATT", lib.fmt(att["att"])),
    ("95% interval", lib.ci(att["ci_low"], att["ci_high"])),
    ("Std error", lib.fmt(att["se"])),
    ("Ecosystem clusters", int(att["n_clusters"])),
    ("Treated channels", int(att["n_treated_channels"])),
    ("Videos", f"{int(att['n_videos']):,}"),
])

pre = es[es["rel_period"] < 0]
band = alt.Chart(es).mark_area(opacity=0.18, color=lib.ACCENT).encode(
    x=alt.X("rel_period:Q", title="Months from treatment"),
    y=alt.Y("ci_low:Q", title="log(views) coefficient"), y2="ci_high:Q")
path = alt.Chart(es).mark_line(color=lib.ACCENT, strokeWidth=2).encode(
    x="rel_period:Q", y="att:Q",
    tooltip=["rel_period", alt.Tooltip("att:Q", format=".3f"),
             alt.Tooltip("ci_low:Q", format=".3f"), alt.Tooltip("ci_high:Q", format=".3f")])
preband = alt.Chart(pre).mark_rect(opacity=0.08, color=lib.COUNTERFACTUAL).encode(
    x="min(rel_period):Q", x2="max(rel_period):Q")
hzero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color="#c3c2b7").encode(y="z:Q")
vzero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(
    color="#c3c2b7", strokeDash=[4, 4]).encode(x="z:Q")
lib.show((preband + band + path + hzero + vzero).properties(height=320,
         title="Event-study path with wild-cluster bands; shaded region is the pre-period"))
lib.takeaway(
    "The overall post-treatment estimate is 0.339 log points, with a 95% interval of "
    "[0.194, 0.485], across 30 treated channels and 12342 videos. Before treatment the path is "
    "not flat, running from -1.030 at month -23 to 0.308 at month -8, so parallel trends does "
    "not hold and the estimate is read as an association.",
    "outputs/tables/did_event_study.csv, did_overall_att.csv, FINDINGS Q4",
)

st.divider()

# ---- Q5 heterogeneity -----------------------------------------------------------

st.subheader("Q5 Split by pre-join size")
q5 = lib.load("did_q5_heterogeneity")
q5["arm"] = q5["arm"].map({"large": "Large", "small": "Small"})
arm5 = alt.Color("arm:N", title="Pre-join size, split at median",
                 scale=alt.Scale(domain=["Large", "Small"],
                                 range=[lib.LARGE_ARM, lib.SMALL_ARM]))
err = alt.Chart(q5).mark_rule(strokeWidth=2).encode(
    y=alt.Y("arm:N", title=None), x=alt.X("ci_low:Q", title="Association, log(views)"),
    x2="ci_high:Q", color=arm5)
pt = alt.Chart(q5).mark_point(size=160, filled=True).encode(
    y="arm:N", x="att:Q", color=arm5,
    tooltip=["arm", alt.Tooltip("att:Q", format=".3f"),
             alt.Tooltip("ci_low:Q", format=".3f"), alt.Tooltip("ci_high:Q", format=".3f"),
             "n_treated_channels", "n_videos"])
hz = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color="#c3c2b7", strokeDash=[4, 4]).encode(x="z:Q")
lib.show((hz + err + pt).properties(height=180,
         title="Both arms positive, small larger; split value 13.010"))
lib.takeaway(
    "The large arm estimate is 0.145, interval [0.011, 0.280], on 14 channels and 7056 videos, "
    "and the small arm is 0.579, interval [0.416, 0.748], on 13 channels and 5246 videos. The "
    "small-member direction matches the prior, whereas the large-member direction does not, since "
    "that arm is positive rather than negative, and under a violated pre-trend both remain "
    "associations.",
    "outputs/tables/did_q5_heterogeneity.csv, FINDINGS Q5",
)

st.divider()

# ---- Placebo --------------------------------------------------------------------

st.subheader("Placebo checks")
pl = lib.load("placebo_summary")
pl["label"] = pl["placebo"].map({"fake_join_dates": "Fake join dates",
                                 "controls_only": "Controls only"})
rng = alt.Chart(pl).mark_rule(strokeWidth=3, color=lib.COUNTERFACTUAL).encode(
    y=alt.Y("label:N", title=None), x=alt.X("q025:Q", title="Placebo estimate, central 95% range"),
    x2="q975:Q")
mean_pt = alt.Chart(pl).mark_point(size=140, filled=True, color=lib.COUNTERFACTUAL).encode(
    y="label:N", x="mean:Q",
    tooltip=["label", alt.Tooltip("mean:Q", format=".3f"), alt.Tooltip("sd:Q", format=".3f"),
             alt.Tooltip("q025:Q", format=".3f"), alt.Tooltip("q975:Q", format=".3f"),
             alt.Tooltip("share_ge_real:Q", format=".3f")])
real = alt.Chart(pl).mark_rule(color=lib.ACCENT, strokeWidth=2).encode(
    x="real_att:Q", tooltip=[alt.Tooltip("real_att:Q", title="Real ATT", format=".3f")])
lib.show((rng + mean_pt + real).properties(height=170,
         title="Placebo distributions (grey) against the real ATT (red)"))
lib.takeaway(
    "Fake join dates produce a placebo mean of 0.740, central range [0.389, 1.062], with 98 "
    "percent of draws at or above the real 0.339, which is a further reason not to read the main "
    "estimate causally. The controls-only draws centre near zero at 0.028, range [-0.389, 0.461], "
    "an estimate that is imprecise at 200 draws and 5 clusters rather than an established zero.",
    "outputs/tables/placebo_summary.csv, FINDINGS placebo checks",
)

st.divider()

# ---- Q6 synthetic control -------------------------------------------------------

st.subheader("Q6 Synthetic-control cases")
gap = lib.load("synth_gap")
fit = lib.load("synth_fit").set_index("case")
weights = lib.load("synth_weights")

tabs = st.tabs(["KSI exit", "Team 10 collapse"])
cases = [
    ("KSI", "KSI exit from the Sidemen, 2026-05-31",
     "No conclusion is drawn from the KSI post window. The reading is a 0.318 log-point mean gap "
     "over 9.7 weeks and 3 monthly observations, with a pre-fit RMSPE of 0.932 and a placebo rank "
     "at the bottom of the pool, so it is described rather than read as an effect of the exit.",
     "The observable post window spans 9.7 weeks, over which the videos have accrued 9.7 weeks or "
     "less, so the post level is depressed by accrual in a way the pre-period fit cannot "
     "calibrate. With a pre-fit RMSPE of 0.932 the fit is poor, so the post gap is not "
     "interpretable."),
    ("Team 10", "Team 10 collapse, treated unit Jake Paul, 2019-09-01",
     "Jake Paul's post-collapse path is associated with a negative gap of -0.195 log points that "
     "cannot be distinguished from the donor placebo distribution across 40 donors, 24 pre-months, "
     "and 23 post-months. Read as a null, it is imprecise at a single treated unit rather than an "
     "established zero.",
     None),
]
for tab, (case, title, reading, warn) in zip(tabs, cases):
    with tab:
        g = gap[gap["case"] == case]
        f = fit.loc[case]
        st.markdown(f"**{title}**")
        lib.stat_row([
            ("Pre-event RMSPE", lib.fmt(f["pre_rmspe"])),
            ("Mean post gap", lib.fmt(f["mean_post_gap"])),
            ("Placebo rank", f"{int(f['treated_rank'])} of {int(f['n_units'])}"),
            ("Placebo p", lib.fmt(f["p"], 3)),
        ])

        long = g.melt(id_vars="rel_month", value_vars=["treated", "synthetic"],
                      var_name="series", value_name="log_views")
        long["series"] = long["series"].map({"treated": "Treated", "synthetic": "Synthetic"})
        scolor = alt.Color("series:N", title=None,
                           scale=alt.Scale(domain=["Treated", "Synthetic"],
                                           range=[lib.ACCENT, lib.COUNTERFACTUAL]))
        base = alt.Chart(long).encode(
            x=alt.X("rel_month:Q", title="Months from event"),
            y=alt.Y("log_views:Q", title="Monthly mean log(views)",
                    scale=alt.Scale(zero=False)),
            color=scolor)
        treated_line = base.transform_filter(alt.datum.series == "Treated").mark_line(strokeWidth=2.5)
        synth_line = base.transform_filter(alt.datum.series == "Synthetic").mark_line(
            strokeWidth=2, strokeDash=[5, 3])
        evt = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(
            color="#c3c2b7", strokeDash=[4, 4]).encode(x="z:Q")
        lib.show((treated_line + synth_line + evt).properties(
            height=300, title=f"{case}: treated against synthetic, event at month 0"))

        if warn:
            lib.caveat(warn)
        lib.takeaway(reading, f"outputs/tables/synth_gap.csv, synth_fit.csv, FINDINGS Q6 {case}")
        with st.expander("Donor weights"):
            w = weights[weights["case"] == case][["donor_name", "weight"]]
            w = w[w["weight"] > 0.0005].sort_values("weight", ascending=False)
            st.dataframe(w, hide_index=True,
                         column_config={"weight": st.column_config.NumberColumn(format="%.3f")})
