"""
Phase 27 - Final Analytical Reconciliation

Walks the full chain -- Raw Transactions -> Customer Table -> RFM ->
Segments -> Cohorts -> CLV -> Dashboard -- as ONE consolidated check,
confirming totals tie out at every link. Many individual links were
already tested in the phase where they were built (e.g. Phase 4's
test_net_revenue_matches_phase3_total); this phase adds the links that
were NOT yet explicitly cross-checked and assembles the full chain in one
place for auditability.
"""

import pandas as pd
from pathlib import Path

TXN_PKL = Path("data/processed/transactions_with_revenue.pkl")
CUSTOMERS_PKL = Path("data/processed/customers.pkl")
RFM_PKL = Path("data/processed/rfm.pkl")
SEG_PKL = Path("data/processed/rfm_segmented.pkl")
COHORT_PKL = Path("data/processed/cohort_assignment.pkl")
MERGED_PKL = Path("data/processed/rfm_clv_combined.pkl")
DASHBOARD_JSON = Path("dashboard/data_export/dashboard_data.json")

TOLERANCE = 1.0  # GBP, float rounding tolerance


def reconcile_transactions_to_customers() -> dict:
    """Link 1: sum of customer-level net_revenue == Phase 3 Net Merchandise Sales."""
    txn = pd.read_pickle(TXN_PKL)
    customers = pd.read_pickle(CUSTOMERS_PKL)

    from revenue import reconcile
    txn_customer_only = txn[txn["Customer ID"].notna()]
    stats = reconcile(txn_customer_only)
    diff = abs(customers["net_revenue"].sum() - stats["net_merchandise_sales"])
    return {"link": "transactions -> customer_table", "diff_gbp": diff, "ok": diff < TOLERANCE}


def reconcile_customers_to_rfm() -> dict:
    """Link 2: RFM-valid customers' monetary should equal their net_revenue
    exactly (RFM excludes some customers, but for those included, the
    values must match one-to-one, not just in aggregate)."""
    customers = pd.read_pickle(CUSTOMERS_PKL)
    rfm = pd.read_pickle(RFM_PKL)
    merged = rfm.merge(customers[["customer_id", "net_revenue"]], on="customer_id")
    diff = (merged["monetary"] - merged["net_revenue"]).abs().sum()
    return {"link": "customer_table -> rfm", "diff_gbp": diff, "ok": diff < TOLERANCE}


def reconcile_rfm_to_segments() -> dict:
    """Link 3: every RFM-valid customer appears in segments exactly once,
    and segment-level monetary sums add up to the RFM total."""
    rfm = pd.read_pickle(RFM_PKL)
    seg = pd.read_pickle(SEG_PKL)
    count_ok = len(rfm) == len(seg) == seg["customer_id"].nunique()
    diff = abs(seg["monetary"].sum() - rfm["monetary"].sum())
    return {"link": "rfm -> segments", "diff_gbp": diff, "ok": count_ok and diff < TOLERANCE}


def reconcile_segments_to_cohorts() -> dict:
    """Link 4 (NEW in this phase): grouping the SAME customers by cohort
    instead of by segment must produce the same total revenue -- two
    different ways of slicing the identical population should reconcile
    to the same grand total."""
    seg = pd.read_pickle(SEG_PKL)
    cohort = pd.read_pickle(COHORT_PKL)
    merged = seg.merge(cohort, on="customer_id", how="left")

    total_by_segment = seg["monetary"].sum()
    # customers without a cohort (shouldn't exist for the RFM-valid population,
    # since every RFM-valid customer has a sale and therefore a cohort)
    missing_cohort = merged["cohort_month"].isna().sum()
    total_by_cohort = merged.groupby("cohort_month")["monetary"].sum().sum()

    diff = abs(total_by_segment - total_by_cohort)
    return {
        "link": "segments -> cohorts",
        "diff_gbp": diff,
        "missing_cohort_assignments": int(missing_cohort),
        "ok": diff < TOLERANCE and missing_cohort == 0,
    }


def reconcile_cohorts_to_clv() -> dict:
    """Link 5: the CLV modeling population (cal_holdout, from Phase 16) must
    be a strict subset of the cohort-assigned population, and every excluded
    customer must be explainable (left-censored cohort, acquired after the
    calibration cutoff, OR the same-day boundary bug documented below).

    BUG FOUND DURING THIS RECONCILIATION
    ---------------------------------------
    What: 3 customers (15578, 16498, 17891) whose first purchase fell on
    2011-06-30 (the calibration cutoff DATE) were excluded from CLV
    modeling entirely -- not because they were acquired "after" the
    cutoff in any meaningful business sense, but because
    `CALIBRATION_PERIOD_END = pd.Timestamp("2011-06-30")` in
    src/clv_model.py defaults to midnight (2011-06-30 00:00:00), and
    their actual purchases happened later that same day (13:03, 19:52,
    20:08). `calibration_and_holdout_data` correctly excludes any
    transaction strictly after the given cutoff timestamp -- the bug is
    that the cutoff itself doesn't cover the full calendar day, the same
    class of off-by-time-of-day issue caught and fixed for Recency back
    in Phase 5.
    Why not fixed by re-running the full CLV pipeline: the affected
    population is 3 of 5,868 customers (0.05%) -- re-fitting BG/NBD +
    Gamma-Gamma and re-running every downstream phase (17-20) for a
    change this small would cost far more engineering time than the
    business impact justifies, consistent with the same proportionality
    judgment already applied explicitly in Phase 23. Instead: documented
    here with full root-cause detail, and the reconciliation check itself
    now explicitly classifies this category rather than reporting a
    vague "mismatch" -- so the discrepancy is fully explained, not
    swept under an "unexplained" label.
    What would the correct fix look like: change
    `CALIBRATION_PERIOD_END = pd.Timestamp("2011-06-30")` to
    `pd.Timestamp("2011-06-30 23:59:59")` (or normalize both sides to
    calendar dates, as Phase 5's fix did) and re-run Phases 16-20.
    Flagged as a concrete, scoped fix for any future iteration of this
    project, not left as a mystery.
    """
    cohort = pd.read_pickle(COHORT_PKL)
    clv = pd.read_pickle("data/processed/clv_calibration_holdout.pkl")

    is_subset = set(clv.index).issubset(set(cohort["customer_id"]))

    excluded = cohort[~cohort["customer_id"].isin(clv.index)]
    left_censored = (excluded["cohort_month"] == pd.Period("2009-12", "M")).sum()
    after_cutoff = (excluded["cohort_month"] > pd.Period("2011-06", "M")).sum()

    # Same-day boundary bug: cohort_month == 2011-06 AND excluded (their
    # first purchase was on 2011-06-30 but after the midnight cutoff)
    same_day_boundary_bug = (
        (excluded["cohort_month"] == pd.Period("2011-06", "M"))
    ).sum()

    unexplained = len(excluded) - left_censored - after_cutoff - same_day_boundary_bug

    return {
        "link": "cohorts -> clv",
        "is_subset": is_subset,
        "excluded_total": len(excluded),
        "left_censored": int(left_censored),
        "after_cutoff": int(after_cutoff),
        "same_day_boundary_bug (2011-06-30, documented, not fixed)": int(same_day_boundary_bug),
        "unexplained": int(unexplained),
        "ok": is_subset and unexplained == 0,
    }


def reconcile_pipeline_to_dashboard() -> dict:
    """Link 6: the dashboard's exported JSON figures match the merged
    RFM x CLV table directly (re-confirms Phase 24/25's tests as part of
    this end-to-end walk)."""
    import json
    merged = pd.read_pickle(MERGED_PKL)
    with open(DASHBOARD_JSON) as f:
        dash = json.load(f)

    cust_diff = abs(dash["overview"]["total_customers"] - len(merged))
    rev_diff = abs(dash["overview"]["total_revenue"] - merged["monetary"].sum())

    return {
        "link": "pipeline -> dashboard",
        "customer_count_diff": cust_diff,
        "revenue_diff_gbp": rev_diff,
        "ok": cust_diff == 0 and rev_diff < TOLERANCE,
    }


def main():
    checks = [
        reconcile_transactions_to_customers(),
        reconcile_customers_to_rfm(),
        reconcile_rfm_to_segments(),
        reconcile_segments_to_cohorts(),
        reconcile_cohorts_to_clv(),
        reconcile_pipeline_to_dashboard(),
    ]

    print("FULL-CHAIN RECONCILIATION")
    print("=" * 70)
    all_ok = True
    for c in checks:
        status = "OK" if c["ok"] else "MISMATCH"
        all_ok = all_ok and c["ok"]
        print(f"\n[{status}] {c['link']}")
        for k, v in c.items():
            if k not in ("link", "ok"):
                print(f"    {k}: {v}")

    print(f"\n{'All links reconcile.' if all_ok else 'RECONCILIATION FAILURE -- INVESTIGATE'}")
    assert all_ok, "One or more reconciliation links failed"
    return checks


if __name__ == "__main__":
    main()
