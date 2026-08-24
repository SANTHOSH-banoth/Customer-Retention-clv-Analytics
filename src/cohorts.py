"""
Phase 10 - Cohort Definition

Defines customer cohorts and the monthly activity table that Phase 11's
retention matrix will be built from.

DEFINITIONS
-----------
Cohort = the calendar month of a customer's first valid ('sale')
    purchase. Matches customers.first_purchase_date from Phase 4, which
    is itself built from 'sale' rows only (never cancellations).

Active in month M = the customer has at least one 'sale' transaction with
    an InvoiceDate falling in calendar month M. Cancellations do NOT count
    as activity -- a customer who only returned something in a given month
    (with no new purchase) is not counted as active that month. This
    mirrors the Frequency definition from Phase 5 for consistency.

months_since_first_purchase = (activity_month - cohort_month), measured in
    whole calendar months. By definition, every customer has
    months_since_first_purchase = 0 in their own cohort month (this is
    tested explicitly below, since it's the foundation the Phase 11
    retention matrix depends on).

POPULATION
----------
Only the 5,868 customers with a valid first_purchase_date (i.e. the same
RFM-valid population from Phase 5) can be assigned a cohort -- the 53
cancellation-only customers excluded in Phase 5 have no first purchase and
structurally cannot belong to a cohort. This is the same exclusion
decision carried forward, not a new one.
"""

import pandas as pd
from pathlib import Path

CUSTOMERS_PKL = Path("data/processed/customers.pkl")
TXN_PKL = Path("data/processed/transactions_with_revenue.pkl")
OUTPUT_COHORT_ASSIGNMENT_PKL = Path("data/processed/cohort_assignment.pkl")
OUTPUT_ACTIVITY_PKL = Path("data/processed/monthly_activity.pkl")


def build_cohort_assignment(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers[customers["first_purchase_date"].notna()].copy()
    df["cohort_month"] = df["first_purchase_date"].dt.to_period("M")
    return df[["customer_id", "cohort_month"]]


def build_monthly_activity(txn: pd.DataFrame, cohort_assignment: pd.DataFrame) -> pd.DataFrame:
    sales = txn[(txn["transaction_type"] == "sale") & (txn["Customer ID"].notna())].copy()
    sales["Customer ID"] = sales["Customer ID"].astype("int64")
    sales["activity_month"] = sales["InvoiceDate"].dt.to_period("M")

    activity = sales[["Customer ID", "activity_month"]].drop_duplicates()
    activity = activity.rename(columns={"Customer ID": "customer_id"})

    activity = activity.merge(cohort_assignment, on="customer_id", how="inner")
    activity["months_since_first_purchase"] = (
        (activity["activity_month"].dt.year - activity["cohort_month"].dt.year) * 12
        + (activity["activity_month"].dt.month - activity["cohort_month"].dt.month)
    )
    return activity


def main():
    customers = pd.read_pickle(CUSTOMERS_PKL)
    txn = pd.read_pickle(TXN_PKL)

    cohort_assignment = build_cohort_assignment(customers)
    activity = build_monthly_activity(txn, cohort_assignment)

    print(f"Customers assigned to a cohort: {len(cohort_assignment)}")
    print(f"Cohort range: {cohort_assignment['cohort_month'].min()} to {cohort_assignment['cohort_month'].max()}")
    print(f"Number of distinct cohorts: {cohort_assignment['cohort_month'].nunique()}")

    cohort_sizes = cohort_assignment.groupby("cohort_month").size()
    print("\nCohort sizes (first 5 and last 5):")
    print(cohort_sizes.head())
    print("...")
    print(cohort_sizes.tail())

    # Sanity: every customer must be active in month 0 (their own cohort month)
    m0 = activity[activity["months_since_first_purchase"] == 0]
    m0_per_customer = m0.groupby("customer_id").size()
    assert (m0_per_customer == 1).all(), "Every customer should appear exactly once at M0"
    assert set(m0["customer_id"]) == set(cohort_assignment["customer_id"]), (
        "Every cohort-assigned customer must be active at M0"
    )
    print(f"\nM0 sanity check passed: all {len(cohort_assignment)} customers active in their own cohort month.")

    cohort_assignment.to_pickle(OUTPUT_COHORT_ASSIGNMENT_PKL)
    activity.to_pickle(OUTPUT_ACTIVITY_PKL)
    print(f"\nSaved -> {OUTPUT_COHORT_ASSIGNMENT_PKL}")
    print(f"Saved -> {OUTPUT_ACTIVITY_PKL}")

    return cohort_assignment, activity


if __name__ == "__main__":
    main()
