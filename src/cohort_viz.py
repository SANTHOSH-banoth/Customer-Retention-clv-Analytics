"""
Phase 12 - Cohort Visualization

Generates the three cohort retention visualizations. Every chart respects
the NaN-vs-zero distinction from Phase 11: unavailable future periods are
rendered as visually distinct (gray, in the heatmap) or simply absent
(in the bar charts, which only plot cohorts that actually have a value)
-- never plotted as a misleading zero.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

PCT_PKL = Path("data/processed/cohort_retention_pct.pkl")
FIG_DIR = Path("reports/figures")

LEFT_CENSORED_COHORT = "2009-12"


def plot_heatmap(pct: pd.DataFrame, out_path: Path):
    fig, ax = plt.subplots(figsize=(16, 9))
    masked = np.ma.masked_invalid(pct.values)

    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad(color="#f0f0f0")  # unavailable cells: light gray, not a color on the scale

    im = ax.imshow(masked, aspect="auto", cmap=cmap, vmin=0, vmax=60)
    ax.set_yticks(range(len(pct.index)))
    ax.set_yticklabels([str(p) for p in pct.index])
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"M{i}" for i in range(0, 25, 2)])
    ax.set_xlabel("Months since acquisition")
    ax.set_ylabel("Cohort (acquisition month)")
    ax.set_title("Cohort Retention Heatmap (% active) -- gray = not yet observable, not 0%")
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("% of cohort active")

    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_retention_curves(pct: pd.DataFrame, cohorts: list, out_path: Path):
    fig, ax = plt.subplots(figsize=(10, 6))
    for c in cohorts:
        row = pct.loc[pd.Period(c, "M")].dropna()
        label = c + (" (left-censored, see caveat)" if c == LEFT_CENSORED_COHORT else "")
        ax.plot(row.index, row.values, marker="o", label=label)
    ax.set_xlabel("Months since acquisition")
    ax.set_ylabel("% of cohort active")
    ax.set_title("Retention Curves for Selected Cohorts")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_milestone_comparison(pct: pd.DataFrame, milestones: list, out_path: Path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for ax, m in zip(axes.flat, milestones):
        available = pct[m].dropna()
        colors = ["#DD8452" if str(idx) == LEFT_CENSORED_COHORT else "#4C72B0" for idx in available.index]
        ax.bar([str(i) for i in available.index], available.values, color=colors)
        ax.set_title(f"M{m} Retention by Cohort ({len(available)}/{len(pct)} cohorts have data)")
        ax.set_ylabel("% active")
        ax.tick_params(axis="x", rotation=90, labelsize=7)
        ax.axhline(available.mean(), color="gray", linestyle="--", linewidth=1, label=f"mean={available.mean():.1f}%")
        ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def main():
    pct = pd.read_pickle(PCT_PKL)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    plot_heatmap(pct, FIG_DIR / "phase12_cohort_heatmap.png")
    plot_retention_curves(pct, ["2009-12", "2010-06", "2011-01", "2011-06"], FIG_DIR / "phase12_retention_curves.png")
    plot_milestone_comparison(pct, [1, 3, 6, 12], FIG_DIR / "phase12_milestone_comparison.png")

    print("Saved 3 figures to", FIG_DIR)


if __name__ == "__main__":
    main()
