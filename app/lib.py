"""Shared loaders, palette, and layout helpers for the Phase 8 dashboard.

The app is a window onto frozen findings. It reads committed derived tables only
(outputs/tables/*.csv and data/snapshots/channel_stats.csv), never a live API and
never the gitignored parquet. Every number it shows is formatted from a committed
table to the precision docs/FINDINGS.md uses, so the two agree character for
character (STYLE rule B).
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
SNAPSHOTS = ROOT / "data" / "snapshots"

# Colours. The red accent is reserved for the treated series and key emphasis so it
# never collides with an ecosystem colour (dataviz: categorical hues distinct from the
# accent). The counterfactual is a neutral grey, not a second hue, so a control or
# synthetic line reads as the baseline rather than as another category.
ACCENT = "#e5484d"          # treated / group-role / event highlight
COUNTERFACTUAL = "#8a8f98"  # control / synthetic / null baseline

# One categorical palette for the ecosystems, reused on every page. Hues are the
# dataviz reference palette's dark steps, slots 1-4 and 7, all clear of the red accent.
ECOSYSTEM_ORDER = ["Sidemen", "Beta Squad", "AMP", "OfflineTV", "2HYPE"]
ECOSYSTEM_COLOR = {
    "Sidemen": "#3987e5",
    "Beta Squad": "#199e70",
    "AMP": "#9085e9",
    "OfflineTV": "#d95926",
    "2HYPE": "#c98500",
}

# Signed splits use a diverging read (dataviz: diverging only where data is signed).
LARGE_ARM = "#3987e5"
SMALL_ARM = "#d95926"

# Every table the app reads, with the columns each page depends on. The self-check
# asserts these are present so a schema change upstream fails loudly here.
EXPECTED = {
    "q1_concentration": ["rel_month", "mean_hhi", "std_hhi", "mean_gini", "std_gini"],
    "attention_share": ["group", "year", "group_share", "member_share"],
    "q2_uploads": ["arm", "rel_month", "n_channels", "mean_uploads", "std_uploads"],
    "q3_external_collabs": ["rel_quarter", "n_creators", "mean_external_partners", "std_external_partners"],
    "reciprocity_ledger": ["group", "member_to_group", "group_to_member", "ratio_m2g_over_g2m"],
    "did_event_study": ["rel_period", "att", "ci_low", "ci_high", "se", "n_videos"],
    "did_overall_att": ["estimate", "att", "ci_low", "ci_high", "se", "n_clusters", "n_treated_channels", "n_videos"],
    "did_pretrend_test": ["test", "periods", "n_pre_periods", "sup_t", "p_value", "n_clusters"],
    "did_q5_heterogeneity": ["arm", "n_treated_channels", "size_proxy_median", "att", "ci_low", "ci_high", "se", "n_clusters", "n_videos"],
    "placebo_summary": ["placebo", "n_draws", "mean", "sd", "q025", "q975", "real_att", "share_ge_real"],
    "synth_fit": ["case", "n_donors", "n_pre_months", "n_post_months", "post_len_weeks", "pre_rmspe", "mean_post_gap", "treated_rank", "n_units", "p"],
    "synth_gap": ["case", "month", "rel_month", "treated", "synthetic", "gap"],
    "synth_placebo": ["case", "unit", "is_treated", "post_pre_rmspe_ratio", "treated_rank", "n_units", "p"],
    "synth_weights": ["case", "donor_channel_id", "donor_name", "weight"],
}


@st.cache_data
def load(name):
    """Read one committed table by stem name."""
    return pd.read_csv(TABLES / f"{name}.csv")


def fmt(x, n=3):
    """Format a number to the FINDINGS precision. Fixed decimals, no thousands."""
    return f"{x:.{n}f}"


def ci(low, high, n=3):
    return f"[{fmt(low, n)}, {fmt(high, n)}]"


# ---- layout helpers -------------------------------------------------------------

# Streamlit's wide layout leaves wide side padding, which narrows the content column.
# Trimming the side padding widens every section (prose and charts) so none is forced
# below a comfortable reading width. Injected once per page via page_header.
_WIDEN_CSS = (
    "<style>[data-testid='stMainBlockContainer'],.block-container"
    "{padding-left:1rem;padding-right:1rem;}</style>"
)


def page_header(kicker, title, standfirst):
    st.markdown(_WIDEN_CSS, unsafe_allow_html=True)
    st.markdown(
        f"<div style='border-left:3px solid {ACCENT};padding-left:14px;margin-bottom:8px'>"
        f"<div style='color:{ACCENT};font-size:0.78rem;letter-spacing:0.08em;"
        f"text-transform:uppercase'>{kicker}</div>"
        f"<h1 style='margin:2px 0 0 0;font-size:1.9rem'>{title}</h1></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<p style='color:#c3c2b7;max-width:150ch'>{standfirst}</p>", unsafe_allow_html=True)
    st.divider()


def stat_row(items):
    """A row of label/value stats that wraps instead of truncating, so a wide value
    such as an interval or an N triple is never clipped (st.metric truncates)."""
    cells = "".join(
        f"<div style='flex:1 1 130px'>"
        f"<div style='color:#898781;font-size:0.78rem'>{label}</div>"
        f"<div style='font-size:1.5rem;color:#f2f2ef;font-variant-numeric:tabular-nums'>{value}</div>"
        f"</div>"
        for label, value in items
    )
    st.markdown(
        f"<div style='display:flex;gap:26px;flex-wrap:wrap;margin:2px 0 10px'>{cells}</div>",
        unsafe_allow_html=True,
    )


def takeaway(text, source):
    """One-line plain-language reading under a chart, quoting FINDINGS, with its source."""
    st.markdown(
        f"<div style='border-left:2px solid {COUNTERFACTUAL};padding:2px 0 2px 12px;"
        f"color:#c3c2b7;font-size:0.92rem'>{text}"
        f"<span style='color:#898781;font-size:0.8rem'> &nbsp;Source: {source}</span></div>",
        unsafe_allow_html=True,
    )


def caveat(text):
    st.markdown(
        f"<div style='background:#2a1416;border:1px solid {ACCENT}55;border-radius:6px;"
        f"padding:10px 14px;color:#f2d6d7;font-size:0.9rem'>{text}</div>",
        unsafe_allow_html=True,
    )


def show(chart):
    st.altair_chart(chart, use_container_width=True, theme="streamlit")


def _base(df, height=300):
    return alt.Chart(df).properties(height=height)


def band_line(df, x, y, lo, hi, color, x_title, y_title, point=False):
    """A mean line with a shaded uncertainty band. Honest axes: y is not zero-forced,
    but no truncation is applied beyond the data range."""
    enc_x = alt.X(f"{x}:Q", title=x_title)
    area = _base(df).mark_area(opacity=0.18, color=color).encode(
        x=enc_x,
        y=alt.Y(f"{lo}:Q", title=y_title),
        y2=f"{hi}:Q",
    )
    line = _base(df).mark_line(color=color, strokeWidth=2, point=point).encode(
        x=enc_x, y=alt.Y(f"{y}:Q", title=y_title),
    )
    return area + line


# ---- self-check -----------------------------------------------------------------

def _self_check():
    tables = {name: load(name) for name in EXPECTED}
    for name, cols in EXPECTED.items():
        missing = [c for c in cols if c not in tables[name].columns]
        assert not missing, f"{name} missing columns {missing}"
    assert (SNAPSHOTS / "channel_stats.csv").exists(), "channel_stats.csv absent"

    # The app must not reach into collection or analysis code. Guard against an
    # accidental import by scanning actual import statements, not string mentions.
    for py in Path(__file__).parent.rglob("*.py"):
        for line in py.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            assert not stripped.startswith(("import src", "from src")), f"{py.name} imports src"

    # Headline numbers must format to exactly what FINDINGS.md prints (STYLE rule B).
    att = tables["did_overall_att"].iloc[0]
    assert fmt(att["att"]) == "0.339", fmt(att["att"])
    assert ci(att["ci_low"], att["ci_high"]) == "[0.194, 0.485]"
    assert fmt(att["se"]) == "0.088"
    pre = tables["did_pretrend_test"].iloc[0]
    assert fmt(pre["sup_t"]) == "7.672"
    q5 = tables["did_q5_heterogeneity"].set_index("arm")
    assert fmt(q5.loc["large", "att"]) == "0.145"
    assert fmt(q5.loc["small", "att"]) == "0.579"
    fit = tables["synth_fit"].set_index("case")
    assert fmt(fit.loc["KSI", "pre_rmspe"]) == "0.932"
    assert fmt(fit.loc["KSI", "mean_post_gap"]) == "0.318"
    assert fmt(fit.loc["Team 10", "mean_post_gap"]) == "-0.195"
    print("self-check ok:", len(EXPECTED), "tables, columns and headline numbers verified")


if __name__ == "__main__":
    _self_check()
