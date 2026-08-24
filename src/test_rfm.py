"""
Phase 5 - Tests for RFM foundations.

Run with: python3 -m pytest src/test_rfm.py -v
"""

import pandas as pd
import pytest
from rfm import build_rfm, get_snapshot_date


@pytest.fixture
def customers():
    return pd.read_pickle("data/processed/customers.pkl")


@pytest.fixture
def snapshot_date():
    return get_snapshot_date()


def test_snapshot_date_is_day_after_max_invoice_date(snapshot_date):
    txn = pd.read_pickle("data/processed/transactions_with_revenue.pkl")
    max_date = txn["InvoiceDate"].max()
    assert snapshot_date == (max_date + pd.Timedelta(days=1)).normalize()


def test_recency_never_below_one(customers, snapshot_date):
    rfm, _ = build_rfm(customers, snapshot_date)
    assert rfm["recency_days"].min() >= 1


def test_frequency_always_positive_in_valid_population(customers, snapshot_date):
    rfm, _ = build_rfm(customers, snapshot_date)
    assert (rfm["frequency"] > 0).all()


def test_cancellation_only_customers_excluded_not_dropped(customers, snapshot_date):
    rfm, rfm_excluded = build_rfm(customers, snapshot_date)
    assert len(rfm) + len(rfm_excluded) == len(customers)
    assert len(rfm_excluded) == 53
    assert (rfm_excluded["exclusion_reason"] == "no_sale_orders_cancellation_only").all()


def test_no_customer_in_both_valid_and_excluded(customers, snapshot_date):
    rfm, rfm_excluded = build_rfm(customers, snapshot_date)
    overlap = set(rfm["customer_id"]) & set(rfm_excluded["customer_id"])
    assert len(overlap) == 0


def test_monetary_matches_net_revenue_exactly(customers, snapshot_date):
    rfm, _ = build_rfm(customers, snapshot_date)
    merged = rfm.merge(customers[["customer_id", "net_revenue"]], on="customer_id")
    assert (merged["monetary"] == merged["net_revenue"]).all()


def test_monetary_can_be_negative(customers, snapshot_date):
    """Explicitly documents that Monetary is not floored at zero."""
    rfm, _ = build_rfm(customers, snapshot_date)
    assert (rfm["monetary"] < 0).sum() > 0


def test_specific_customer_recency_manual_check(customers, snapshot_date):
    """Manually recompute recency for one real customer and compare."""
    sample = customers[customers["last_purchase_date"].notna()].iloc[0]
    rfm, _ = build_rfm(customers, snapshot_date)
    row = rfm[rfm["customer_id"] == sample["customer_id"]]
    if len(row) == 0:
        pytest.skip("sampled customer happened to be in excluded set")
    expected = (snapshot_date - sample["last_purchase_date"].normalize()).days
    assert row["recency_days"].iloc[0] == expected
