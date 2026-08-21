"""Figures for the Phase 5 descriptive analysis (Q1 to Q3, attention share, reciprocity).

Each figure reads its numbers from src.models.descriptive, so the plotted values and the
committed CSV tables share one source (STYLE rule B). Figures are descriptive: captions say
"associated with" or "coincides with", never a causal verb (rule A), and event-study panels
carry the per-period N and a dispersion band (rule C). Output is SVG to outputs/figures/.

Usage:
    python -m src.viz.descriptive
"""

import os

import matplotlib
matplotlib.use("Agg")  # no display in the run environment; write files only
import matplotlib.pyplot as plt

from src.models import descriptive as d

FIGURES = os.path.join("outputs", "figures")
SCRIPT = "src/models/descriptive.py"


def _event_axis(ax, x, mean, std, label, color):
    """Mean line with a +/-1 std band on an event-time axis."""
    ax.plot(x, mean, color=color, label=label, linewidth=1.8)
    ax.fill_between(x, mean - std.fillna(0), mean + std.fillna(0), color=color, alpha=0.15)
    ax.axvline(0, color="0.4", linewidth=0.8, linestyle="--")


def fig_q1(tidy, summary):
    """HHI and Gini per ecosystem in event time, per-group lines plus the cross-group mean."""
    fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    for metric, ax in zip(["hhi", "gini"], axes):
        for grp, sub in tidy.groupby("group"):
            ax.plot(sub["rel_month"], sub[metric], alpha=0.35, linewidth=1.0, label=grp)
            mech = sub[sub["mechanical"]]
            ax.scatter(mech["rel_month"], mech[metric], s=14, color="0.5",
                       marker="x", zorder=3)
        mean = summary[f"mean_{metric}"]
        std = summary[f"std_{metric}"]
        _event_axis(ax, summary["rel_month"], mean, std, "cross-group mean", "black")
        ax.set_ylabel(metric.upper())
    axes[0].legend(fontsize=7, ncol=3, loc="upper left")
    axes[1].set_xlabel("months relative to group formation")
    fig.suptitle("Q1 attention concentration across each ecosystem in event time")
    fig.text(0.01, 0.005, f"{SCRIPT} q1_concentration; N groups per period in "
             "outputs/tables/q1_concentration.csv; x marks mechanical HHI=1 (<2 active channels)",
             fontsize=6, color="0.4")
    _save(fig, "q1_concentration.svg")


def fig_q2(summary):
    """Long-form uploads per month, treated members against matched controls, event time."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = {"treated": "#b2182b", "control": "#2166ac"}
    for arm, sub in summary.groupby("arm"):
        sub = sub.sort_values("rel_month")
        _event_axis(ax, sub["rel_month"], sub["mean_uploads"], sub["std_uploads"],
                    arm, colors.get(arm, "black"))
    ax.set_xlabel("months relative to treatment")
    ax.set_ylabel("long-form uploads per month")
    ax.legend(fontsize=8)
    fig.suptitle("Q2 solo long-form output around joining, treated vs matched controls")
    fig.text(0.01, 0.005, f"{SCRIPT} q2_uploads; per-arm N and band in "
             "outputs/tables/q2_uploads.csv", fontsize=6, color="0.4")
    _save(fig, "q2_uploads.svg")


def fig_q3(summary):
    """Cross-group collaboration counts for Sidemen members, event time, F1-restricted."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    _event_axis(ax, summary["rel_quarter"], summary["mean_external_partners"],
                summary["std_external_partners"], "Sidemen members", "#4d4d4d")
    ax.set_xlabel("quarters relative to formation")
    ax.set_ylabel("external partners per creator-quarter")
    ax.legend(fontsize=8)
    fig.suptitle("Q3 external collaboration counts, Sidemen ecosystem only")
    n = int(summary["n_creators"].max())
    fig.text(0.01, 0.005, f"{SCRIPT} q3_external; N={n} Sidemen members per quarter; "
             "cohort-observable external only, F1=0.6634 (loops/collabs/log.md); other cohort "
             "groups postdate the window, so the level is a floor, not a measured decline",
             fontsize=6, color="0.4")
    _save(fig, "q3_external_collabs.svg")


def fig_attention_share(share):
    """Group-channel view share of each ecosystem by video publish year."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for grp, sub in share.groupby("group"):
        sub = sub.sort_values("year")
        ax.plot(sub["year"], sub["group_share"], marker="o", markersize=3, label=grp)
    ax.set_xlabel("video publish year")
    ax.set_ylabel("group-channel share of ecosystem views")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    fig.suptitle("Group-channel share of ecosystem attention by upload year")
    fig.text(0.01, 0.005, f"{SCRIPT} attention_share; outputs/tables/attention_share.csv; "
             "view_count is cumulative at one snapshot (accrual caveat, SCOPE 4.1)",
             fontsize=6, color="0.4")
    _save(fig, "attention_share.svg")


def fig_reciprocity(ledger):
    """Member-to-group against group-to-member appearance counts per group, log scale."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(ledger))
    w = 0.4
    ax.bar([i - w / 2 for i in x], ledger["member_to_group"], w, label="member to group",
           color="#b2182b")
    ax.bar([i + w / 2 for i in x], ledger["group_to_member"], w, label="group to member",
           color="#2166ac")
    ax.set_yscale("symlog")
    ax.set_xticks(list(x))
    ax.set_xticklabels(ledger["group"])
    ax.set_ylabel("appearances (symlog)")
    ax.legend(fontsize=8)
    for i, (m, gm) in enumerate(zip(ledger["member_to_group"], ledger["group_to_member"])):
        ax.text(i - w / 2, m, str(int(m)), ha="center", va="bottom", fontsize=6)
        ax.text(i + w / 2, gm, str(int(gm)), ha="center", va="bottom", fontsize=6)
    fig.suptitle("Reciprocity ledger, appearance counts by direction")
    fig.text(0.01, 0.005, f"{SCRIPT} reciprocity_ledger; outputs/tables/reciprocity_ledger.csv; "
             "detection is alias-based and Sidemen-dense, so group-to-member is a floor",
             fontsize=6, color="0.4")
    _save(fig, "reciprocity_ledger.svg")


def _save(fig, name):
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path = os.path.join(FIGURES, name)
    fig.savefig(path, format="svg")
    plt.close(fig)
    print(f"wrote {path}")


def main():
    os.makedirs(FIGURES, exist_ok=True)
    q1_tidy, q1_summary = d.q1_concentration()
    _, q2_summary = d.q2_uploads()
    _, q3_summary = d.q3_external()
    share = d.attention_share()
    _, ledger = d.reciprocity_ledger()

    fig_q1(q1_tidy, q1_summary)
    fig_q2(q2_summary)
    fig_q3(q3_summary)
    fig_attention_share(share)
    fig_reciprocity(ledger)


if __name__ == "__main__":
    main()
