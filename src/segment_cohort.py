"""
Phase 14 - Segment x Cohort Analysis

Connects the Phase 7 RFM segments to the Phase 10 cohort assignment, and
directly quantifies the "cohort maturity" confound before drawing any
conclusion about cohort quality: since Frequency and Monetary (Phase 5)
are CUMULATIVE measures, a cohort's segment composition is mechanically
correlated with how long it has existed, independent of any real
difference in underlying customer engagement rate.
"""

import pandas as pd
from scipy import stats
from pathlib import Path

SEG_PKL = Path("data/processed/rfm_segmented.pkl")
COHORT_PKL = Path("data/processed/cohort_assignment.pkl")

LEFT_CENSORED_COHORT = pd.Period("2009-12", freq="M")
SNAPSHOT_MONTH = pd.Period("2011-12", freq="M")


def merge_segment_cohort() -> pd.DataFrame:
    seg = pd.read_pickle(SEG_PKL)
    cohort = pd.read_pickle(COHORT_PKL)
    merged = seg.merge(cohort, on="customer_id")
    merged["cohort_age_months"] = merged["cohort_month"].apply(
        lambda c: (SNAPSHOT_MONTH.year - c.year) * 12 + (SNAPSHOT_MONTH.month - c.month)
    )
    return merged


def segment_composition_by_cohort(merged: pd.DataFrame) -> pd.DataFrame:
    return pd.crosstab(merged["cohort_month"], merged["segment"], normalize="index") * 100


def cohort_age_confound(merged: pd.DataFrame) -> dict:
    excl = merged[merged["cohort_month"] != LEFT_CENSORED_COHORT]
    agg = excl.groupby("cohort_month").agg(
        cohort_age_months=("cohort_age_months", "first"),
        pct_champions=("segment", lambda s: (s == "Champions").mean() * 100),
        pct_hibernating=("segment", lambda s: (s == "Hibernating").mean() * 100),
        avg_monetary=("monetary", "mean"),
    )

    full_corr_champ, full_p_champ = stats.spearmanr(agg["cohort_age_months"], agg["pct_champions"])
    full_corr_mon, full_p_mon = stats.spearmanr(agg["cohort_age_months"], agg["avg_monetary"])

    mature = agg[agg["cohort_age_months"] >= 12]
    mature_corr_champ, mature_p_champ = stats.spearmanr(mature["cohort_age_months"], mature["pct_champions"])
    mature_corr_mon, mature_p_mon = stats.spearmanr(mature["cohort_age_months"], mature["avg_monetary"])

    return {
        "full_sample": {
            "n": len(agg), "corr_champions": full_corr_champ, "p_champions": full_p_champ,
            "corr_monetary": full_corr_mon, "p_monetary": full_p_mon,
        },
        "mature_only_12mo_plus": {
            "n": len(mature), "corr_champions": mature_corr_champ, "p_champions": mature_p_champ,
            "corr_monetary": mature_corr_mon, "p_monetary": mature_p_mon,
        },
    }


def main():
    merged = merge_segment_cohort()
    comp = segment_composition_by_cohort(merged)
    confound = cohort_age_confound(merged)

    print("Segment composition by cohort (Champions/Loyal/At Risk/Hibernating/New):")
    print(comp[["Champions", "Loyal Customers", "At Risk", "Hibernating", "New Customers"]].round(1))

    print("\nCohort-age confound check:")
    for scope, res in confound.items():
        print(f"  {scope}: n={res['n']}")
        print(f"    corr(age, %Champions)={res['corr_champions']:.3f}, p={res['p_champions']:.2e}")
        print(f"    corr(age, avg monetary)={res['corr_monetary']:.3f}, p={res['p_monetary']:.4f}")

    assert confound["mature_only_12mo_plus"]["p_champions"] < 0.05, (
        "expected the age-Champions correlation to remain significant even among mature cohorts"
    )

    return comp, confound


if __name__ == "__main__":
    main()
