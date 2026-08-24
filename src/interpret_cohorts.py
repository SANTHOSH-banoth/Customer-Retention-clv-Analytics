"""
Phase 13 - Cohort Interpretation

Turns the Phase 11/12 retention matrix into tested findings, each
following Observation -> Evidence -> Possible Explanation -> Business
Implication. No causal claims are made without a statistical test behind
them, and alternative explanations are considered before concluding
anything from a visual pattern.

The December 2009 cohort is excluded from every "typical cohort" analysis
in this phase, consistent with the left-censoring finding from Phase 10.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

PCT_PKL = Path("data/processed/cohort_retention_pct.pkl")
COUNTS_PKL = Path("data/processed/cohort_retention_counts.pkl")

LEFT_CENSORED_COHORT = pd.Period("2009-12", freq="M")


def load_excl():
    pct = pd.read_pickle(PCT_PKL)
    return pct.drop(index=LEFT_CENSORED_COHORT)


def early_drop_stats(excl: pd.DataFrame) -> dict:
    m1 = excl[1].dropna()
    return {
        "mean_m1": m1.mean(), "median_m1": m1.median(),
        "min_m1": m1.min(), "max_m1": m1.max(),
        "avg_drop_pts": 100 - m1.mean(),
    }


def paired_m1_vs_m12(excl: pd.DataFrame) -> dict:
    both = excl[[1, 12]].dropna()
    stat, p = stats.wilcoxon(both[1], both[12])
    return {
        "n_cohorts": len(both), "mean_m1": both[1].mean(), "mean_m12": both[12].mean(),
        "wilcoxon_stat": stat, "p_value": p, "significant": p < 0.05,
    }


def cohort_time_trend(excl: pd.DataFrame, milestone: int) -> dict:
    series = excl[milestone].dropna()
    time_idx = np.array([p.ordinal for p in series.index])
    corr, p = stats.spearmanr(time_idx, series.values)
    return {"milestone": milestone, "n": len(series), "spearman_rho": corr, "p_value": p, "significant": p < 0.05}


def seasonal_effect(excl: pd.DataFrame, holiday_months=(10, 11, 12)) -> dict:
    m1 = excl[1].dropna()
    is_holiday = [p.month in holiday_months for p in m1.index]
    holiday = m1[is_holiday]
    other = m1[[not h for h in is_holiday]]
    stat, p = stats.mannwhitneyu(holiday, other)
    return {
        "n_holiday": len(holiday), "mean_holiday": holiday.mean(),
        "n_other": len(other), "mean_other": other.mean(),
        "p_value": p, "significant": p < 0.05,
    }


def cohort_size_seasonality() -> pd.Series:
    counts = pd.read_pickle(COUNTS_PKL)[0].drop(index=LEFT_CENSORED_COHORT)
    return counts.groupby([p.month for p in counts.index]).mean()


def main():
    excl = load_excl()

    print("1. EARLY RETENTION DROP")
    print(early_drop_stats(excl))

    print("\n2. PAIRED M1 vs M12 (same cohorts, Wilcoxon signed-rank)")
    print(paired_m1_vs_m12(excl))

    print("\n3. COHORT-TO-COHORT TIME TREND")
    for m in [1, 3]:
        print(f"  M{m}:", cohort_time_trend(excl, m))

    print("\n4. SEASONAL EFFECT (holiday-acquired vs other, M1 retention)")
    print(seasonal_effect(excl))

    print("\n5. COHORT SIZE SEASONALITY (mean cohort size by calendar month)")
    print(cohort_size_seasonality().round(0))


if __name__ == "__main__":
    main()
