"""
Phase 10 - Tests for cohort definition.

Run with: python3 -m pytest src/test_cohorts.py -v
"""

import pandas as pd
import pytest
from cohorts import build_cohort_assignment, build_monthly_activity


@pytest.fixture
def customers():
    return pd.read_pickle("data/processed/customers.pkl")


@pytest.fixture
def txn():
    return pd.read_pickle("data/processed/transactions_with_revenue.pkl")


@pytest.fixture
def cohort_assignment(customers):
    return build_cohort_assignment(customers)


@pytest.fixture
def activity(txn, cohort_assignment):
    return build_monthly_activity(txn, cohort_assignment)


def test_cohort_assignment_excludes_customers_without_sale(customers, cohort_assignment):
    n_no_sale = customers["first_purchase_date"].isna().sum()
    assert len(cohort_assignment) == len(customers) - n_no_sale


def test_every_customer_active_at_month_zero(cohort_assignment, activity):
    m0 = activity[activity["months_since_first_purchase"] == 0]
    assert set(m0["customer_id"]) == set(cohort_assignment["customer_id"])


def test_no_negative_months_since_first_purchase(activity):
    """A customer cannot be active before their own first purchase."""
    assert (activity["months_since_first_purchase"] >= 0).all()


def test_cohort_month_matches_first_purchase_month(customers, cohort_assignment):
    merged = cohort_assignment.merge(customers[["customer_id", "first_purchase_date"]], on="customer_id")
    expected = merged["first_purchase_date"].dt.to_period("M")
    assert (merged["cohort_month"] == expected).all()


def test_first_cohort_is_anomalously_large(cohort_assignment):
    """Documents the left-censoring finding: the first observed cohort
    absorbs pre-existing customers, not just genuinely new December 2009
    acquisitions, so it's roughly 3x a typical early cohort."""
    sizes = cohort_assignment.groupby("cohort_month").size()
    first_cohort_size = sizes.iloc[0]
    typical_early_size = sizes.iloc[1:6].mean()
    assert first_cohort_size > 2 * typical_early_size


def test_no_customer_appears_in_two_cohorts(cohort_assignment):
    assert cohort_assignment["customer_id"].is_unique


def test_cancellation_only_activity_does_not_count_as_active_month(txn, cohort_assignment):
    """A month where a customer ONLY has cancellation rows (no sale) must
    NOT appear in the activity table for that customer."""
    sales_months = build_monthly_activity(txn, cohort_assignment)

    cancel_only = txn[
        (txn["transaction_type"] == "cancellation") & (txn["Customer ID"].notna())
    ].copy()
    cancel_only["Customer ID"] = cancel_only["Customer ID"].astype("int64")
    cancel_only["month"] = cancel_only["InvoiceDate"].dt.to_period("M")

    # pick a customer+month combo that has a cancellation but check it's
    # not counted as active unless a sale also exists that month
    for _, row in cancel_only.head(50).iterrows():
        cust_sales_this_month = sales_months[
            (sales_months["customer_id"] == row["Customer ID"])
            & (sales_months["activity_month"] == row["month"])
        ]
        cust_actual_sales = txn[
            (txn["Customer ID"] == row["Customer ID"])
            & (txn["transaction_type"] == "sale")
            & (txn["InvoiceDate"].dt.to_period("M") == row["month"])
        ]
        if len(cust_actual_sales) == 0:
            assert len(cust_sales_this_month) == 0
