"""
Phase 11 - Cohort Retention Table

Pivots the Phase 10 monthly activity table into the classic cohort
retention matrix: rows = cohort month, columns = months since
acquisition (M0, M1, M2, ...), values = % of the cohort active in that
month.

CRITICAL RULE: a cell is only computed if that (cohort, month-offset)
combination has actually occurred within the observed data window. If a
cohort hasn't existed long enough to reach a given month offset yet (e.g.
the 2011-12 cohort can't have an M12 -- that would require data from
December 2012, which doesn't exist), the cell is set to NaN ("not yet
observable"), never 0. A cell that legitimately has 0% retention (the
cohort existed long enough, but nobody purchased) is a different,
meaningful value and must not be confused with "we don't have the data."

ADDITIONAL CAVEAT: the last observed calendar month, 2011-12, only
contains 9 days of data (up to 2011-12-09, per Phase 1's measured max
date) rather than a full month. Any retention percentage computed using
2011-12 as the activity month is based on a shorter purchase window than
every other month and should be read with that in mind -- flagged
explicitly here rather than silently averaged in as if it were comparable.
"""

import pandas as pd
import numpy as np
from pathlib import Path

ACTIVITY_PKL = Path("data/processed/monthly_activity.pkl")
COHORT_PKL = Path("data/processed/cohort_assignment.pkl")
OUTPUT_COUNTS_PKL = Path("data/processed/cohort_retention_counts.pkl")
OUTPUT_PCT_PKL = Path("data/processed/cohort_retention_pct.pkl")

LAST_OBSERVED_MONTH = pd.Period("2011-12", freq="M")
MAX_OFFSET = 24  # Dec 2009 to Dec 2011 spans 24 months


def build_retention_matrix(activity: pd.DataFrame, cohort_assignment: pd.DataFrame):
    cohort_sizes = cohort_assignment.groupby("cohort_month").size()
    cohort_months = sorted(cohort_assignment["cohort_month"].unique())

    # Count of active customers per (cohort_month, months_since_first_purchase)
    counts = (
        activity.groupby(["cohort_month", "months_since_first_purchase"])["customer_id"]
        .nunique()
        .unstack(fill_value=0)
    )
    counts = counts.reindex(index=cohort_months, columns=range(0, MAX_OFFSET + 1), fill_value=0)

    # Determine, for each cohort, the maximum offset that has actually
    # occurred within the observed data window.
    max_available_offset = {}
    for cm in cohort_months:
        span = (LAST_OBSERVED_MONTH.year - cm.year) * 12 + (LAST_OBSERVED_MONTH.month - cm.month)
        max_available_offset[cm] = span

    # Mask cells beyond what's observable as NaN
    counts_masked = counts.astype(float).copy()
    for cm in cohort_months:
        max_offset = max_available_offset[cm]
        if max_offset < MAX_OFFSET:
            counts_masked.loc[cm, max_offset + 1:] = np.nan

    pct = counts_masked.div(cohort_sizes.reindex(cohort_months), axis=0) * 100

    return counts_masked, pct, cohort_sizes


def manual_validation(activity: pd.DataFrame, cohort_assignment: pd.DataFrame,
                        counts: pd.DataFrame, sample_cohort: str = "2011-06"):
    """Recompute one cohort's M0/M1/M2 counts directly from the raw
    activity table (bypassing the pivot/groupby machinery) and compare."""
    cm = pd.Period(sample_cohort, freq="M")
    cohort_customers = set(cohort_assignment.loc[cohort_assignment["cohort_month"] == cm, "customer_id"])
    cohort_size = len(cohort_customers)

    results = {}
    for offset in [0, 1, 2]:
        active = set(
            activity.loc[
                (activity["cohort_month"] == cm) & (activity["months_since_first_purchase"] == offset),
                "customer_id",
            ]
        )
        assert active.issubset(cohort_customers), "active customers must be a subset of the cohort"
        manual_count = len(active)
        pivot_count = int(counts.loc[cm, offset])
        assert manual_count == pivot_count, f"M{offset} mismatch: manual={manual_count}, pivot={pivot_count}"
        results[f"M{offset}"] = manual_count

    return cohort_size, results


def main():
    activity = pd.read_pickle(ACTIVITY_PKL)
    cohort_assignment = pd.read_pickle(COHORT_PKL)

    counts, pct, cohort_sizes = build_retention_matrix(activity, cohort_assignment)

    print("Cohort sizes:")
    print(cohort_sizes)

    print("\nRetention % matrix (first 8 columns, first 10 cohorts):")
    print(pct.iloc[:10, :8].round(1))

    # M0 must always be exactly 100% by construction
    assert (pct[0] == 100.0).all(), "M0 must be 100% retention for every cohort by definition"
    print("\nM0 = 100% for every cohort: confirmed")

    # Manual validation on a sample cohort
    cohort_size, manual_results = manual_validation(activity, cohort_assignment, counts, "2011-06")
    print(f"\nManual validation, cohort 2011-06 (size={cohort_size}): {manual_results}")

    counts.to_pickle(OUTPUT_COUNTS_PKL)
    pct.to_pickle(OUTPUT_PCT_PKL)
    print(f"\nSaved -> {OUTPUT_COUNTS_PKL}")
    print(f"Saved -> {OUTPUT_PCT_PKL}")

    return counts, pct, cohort_sizes


if __name__ == "__main__":
    main()
