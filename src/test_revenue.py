"""
Phase 3 - Tests for revenue definitions.

Run with: python3 -m pytest src/test_revenue.py -v
"""

import pandas as pd
import pytest
from revenue import add_line_value, reconcile


@pytest.fixture
def classified_df():
    return pd.read_pickle("data/processed/transactions_classified.pkl")


def test_reconciliation_ties_to_penny(classified_df):
    df = add_line_value(classified_df)
    stats = reconcile(df)
    assert abs(stats["reconciliation_diff"]) < 0.01


def test_net_merchandise_sales_is_gross_minus_returns(classified_df):
    df = add_line_value(classified_df)
    stats = reconcile(df)
    assert abs(
        stats["net_merchandise_sales"]
        - (stats["gross_merchandise_sales"] - stats["returns"])
    ) < 0.01


def test_returns_reported_as_positive(classified_df):
    df = add_line_value(classified_df)
    stats = reconcile(df)
    assert stats["returns"] > 0


def test_gross_merchandise_sales_only_uses_sale_rows(classified_df):
    df = add_line_value(classified_df)
    stats = reconcile(df)
    manual_gross = df.loc[df["transaction_type"] == "sale", "line_value"].sum()
    assert abs(stats["gross_merchandise_sales"] - manual_gross) < 0.01


def test_net_merchandise_sales_less_than_naive_raw_total_is_not_assumed():
    """Sanity check that we don't assert an ordering that isn't guaranteed --
    net merchandise sales can legitimately be higher OR lower than the naive
    raw total depending on how much non-merchandise/excluded value existed.
    This test just documents that both directions are handled without error."""
    df = pd.read_pickle("data/processed/transactions_classified.pkl")
    df = add_line_value(df)
    stats = reconcile(df)
    assert isinstance(stats["net_merchandise_sales"] - stats["naive_raw_total"], float)
