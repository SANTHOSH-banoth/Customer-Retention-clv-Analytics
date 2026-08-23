"""
Phase 2 - Tests for transaction classification.

Run with: python3 -m pytest src/test_clean.py -v
"""

import pandas as pd
import pytest
from clean import classify, NON_MERCHANDISE_CODES

VALID_LABELS = {
    "bad_debt_adjustment", "non_merchandise", "cancellation",
    "stock_correction", "free_item", "sale", "stock_inbound_no_customer",
    "unclassified",
}


@pytest.fixture
def raw_df():
    return pd.read_pickle("data/raw/online_retail_ii_combined.pkl")


def test_every_row_gets_exactly_one_label(raw_df):
    df = classify(raw_df)
    assert df["transaction_type"].notna().all()
    assert set(df["transaction_type"].unique()).issubset(VALID_LABELS)
    # classify() adds exactly one new column
    assert len(df) == len(raw_df)


def test_no_unclassified_rows(raw_df):
    df = classify(raw_df)
    unclassified = (df["transaction_type"] == "unclassified").sum()
    assert unclassified == 0, f"{unclassified} rows fell through all rules -- investigate"


def test_cancellations_are_all_negative_or_flagged(raw_df):
    df = classify(raw_df)
    cancellations = df[df["transaction_type"] == "cancellation"]
    non_negative = (cancellations["Quantity"] >= 0).sum()
    # We know from Phase 1 there is exactly 1 known exception (Manual/M row
    # with no Customer ID on a C-invoice). Fail if new exceptions appear.
    assert non_negative <= 1, (
        f"{non_negative} cancellation rows have non-negative quantity, "
        f"expected at most 1 known exception"
    )


def test_stock_correction_always_zero_price_and_negative_qty(raw_df):
    df = classify(raw_df)
    sc = df[df["transaction_type"] == "stock_correction"]
    assert (sc["Price"] == 0).all()
    assert (sc["Quantity"] < 0).all()
    assert sc["Customer ID"].isna().all()


def test_sale_rows_are_positive_qty_and_price(raw_df):
    df = classify(raw_df)
    sales = df[df["transaction_type"] == "sale"]
    assert (sales["Quantity"] > 0).all()
    assert (sales["Price"] > 0).all()


def test_bad_debt_rows_are_stockcode_b(raw_df):
    df = classify(raw_df)
    bd = df[df["transaction_type"] == "bad_debt_adjustment"]
    assert (bd["StockCode"] == "B").all()


def test_row_count_reconciles(raw_df):
    """The sum of category row counts must equal the raw row count exactly."""
    df = classify(raw_df)
    assert df["transaction_type"].value_counts().sum() == len(raw_df)


def test_manual_stockcode_not_treated_as_non_merchandise():
    """M/m (Manual) rows should NOT be swept into non_merchandise -- they
    were found in Phase 2 investigation to be real manually-entered sales."""
    assert "M" not in NON_MERCHANDISE_CODES
    assert "m" not in NON_MERCHANDISE_CODES
