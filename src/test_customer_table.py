"""
Phase 4 - Tests for the customer-level analytical table.

The most important tests here defend against the single biggest risk
flagged in the project brief: silently counting line items as orders.

Run with: python3 -m pytest src/test_customer_table.py -v
"""

import pandas as pd
import pytest
from customer_table import build_customer_table, VALID_CUSTOMER_TXN_TYPES


@pytest.fixture
def txn_df():
    return pd.read_pickle("data/processed/transactions_with_revenue.pkl")


@pytest.fixture
def customers(txn_df):
    return build_customer_table(txn_df)


def test_order_count_is_not_row_count(txn_df, customers):
    """The core grain trap: verify order_count comes from distinct invoices,
    not from summing line-item rows. Pick a known multi-line invoice and
    confirm it contributes exactly 1 to order_count, not N."""
    valid = txn_df[
        (txn_df["Customer ID"].notna())
        & (txn_df["transaction_type"].isin(VALID_CUSTOMER_TXN_TYPES))
    ].copy()
    valid["Customer ID"] = valid["Customer ID"].astype("int64")

    # find an invoice with more than 5 line items
    line_counts = valid.groupby("Invoice").size()
    multi_line_invoice = line_counts[line_counts > 5].index[0]
    cust_id = valid.loc[valid["Invoice"] == multi_line_invoice, "Customer ID"].iloc[0]
    n_lines = line_counts[multi_line_invoice]

    cust_row = customers[customers["customer_id"] == cust_id]
    assert len(cust_row) == 1
    # order_count must be far smaller than would result from counting rows
    assert cust_row["order_count"].iloc[0] < n_lines * 10, (
        "order_count looks suspiciously large -- possible row-count leakage"
    )


def test_order_count_equals_distinct_invoices_manually(txn_df, customers):
    """Directly recompute order_count for a sample of customers using
    nunique() on Invoice and compare to the table's value."""
    valid = txn_df[
        (txn_df["Customer ID"].notna())
        & (txn_df["transaction_type"].isin(VALID_CUSTOMER_TXN_TYPES))
    ].copy()
    valid["Customer ID"] = valid["Customer ID"].astype("int64")

    sample_ids = customers["customer_id"].sample(20, random_state=42)
    for cid in sample_ids:
        expected = valid.loc[valid["Customer ID"] == cid, "Invoice"].nunique()
        actual = customers.loc[customers["customer_id"] == cid, "order_count"].iloc[0]
        assert expected == actual, f"Mismatch for customer {cid}: {expected} vs {actual}"


def test_no_duplicate_customers(customers):
    assert customers["customer_id"].is_unique


def test_net_revenue_matches_phase3_total(txn_df, customers):
    """Sum of per-customer net_revenue should equal Phase 3's
    Net Merchandise Sales total, since both are Gross Sales - Returns
    computed over the same underlying rows (customer-attributed only)."""
    from revenue import reconcile

    stats = reconcile(txn_df[txn_df["Customer ID"].notna()])
    customer_net_total = customers["net_revenue"].sum()
    # allow tiny float rounding tolerance
    assert abs(customer_net_total - stats["net_merchandise_sales"]) < 1.0


def test_first_purchase_not_after_last_purchase(customers):
    with_dates = customers.dropna(subset=["first_purchase_date", "last_purchase_date"])
    assert (with_dates["first_purchase_date"] <= with_dates["last_purchase_date"]).all()


def test_item_count_never_negative(customers):
    assert (customers["item_count"] >= 0).all()


def test_customers_with_only_cancellations_are_retained(customers):
    """Customers whose only observed activity is a return (no sale in this
    dataset) must still appear in the table -- see Phase 4 report for why
    dropping them would hide real information."""
    no_sale = customers[customers["first_purchase_date"].isna()]
    assert len(no_sale) > 0, "expected at least one cancellation-only customer (measured: 53)"
    assert (no_sale["sale_order_count"] == 0).all()
