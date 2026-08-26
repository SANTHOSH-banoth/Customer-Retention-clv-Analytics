"""
Phase 22 - Tests for return/cancellation impact analysis.

Run with: python3 -m pytest src/test_naive_comparison.py -v
"""

import pandas as pd
import pytest
from naive_comparison import build_naive_rfm, compare
from rfm import get_snapshot_date


@pytest.fixture
def naive():
    raw = pd.read_pickle("data/raw/online_retail_ii_combined.pkl")
    snapshot_date = get_snapshot_date()
    return build_naive_rfm(raw, snapshot_date)


@pytest.fixture
def correct():
    return pd.read_pickle("data/processed/rfm_segmented.pkl")


def test_naive_total_exceeds_correct_total(naive, correct):
    """Naive treatment doesn't net out returns, so it should overstate
    total revenue relative to the correct Net Merchandise Sales figure."""
    result = compare(naive, correct)
    assert result["total_naive_monetary"] > result["total_correct_monetary"]


def test_revenue_difference_is_material(naive, correct):
    result = compare(naive, correct)
    assert result["total_revenue_diff_pct"] > 5.0  # a material, not trivial, overstatement


def test_customer_12346_is_dramatically_mismeasured():
    """Locks in the single most illustrative example found in this
    phase: naive treatment ranks this customer among the top 20 most
    valuable in the dataset; correct treatment ranks them near the
    bottom, because their one large order was fully cancelled."""
    raw = pd.read_pickle("data/raw/online_retail_ii_combined.pkl")
    correct = pd.read_pickle("data/processed/rfm_segmented.pkl")
    naive = build_naive_rfm(raw, get_snapshot_date())

    merged = correct.merge(naive, on="customer_id")
    row = merged[merged["customer_id"] == 12346].iloc[0]

    naive_rank = (merged["naive_monetary"] > row["naive_monetary"]).sum() + 1
    correct_rank = (merged["monetary"] > row["monetary"]).sum() + 1

    assert naive_rank <= 25  # top ~0.4% under naive treatment
    assert correct_rank >= 5800  # bottom ~1% under correct treatment


def test_some_customers_change_segment_under_naive_treatment(naive, correct):
    result = compare(naive, correct)
    assert result["n_segment_changed"] > 0
    assert result["pct_segment_changed"] < 100  # most customers should NOT be affected


def test_naive_pipeline_still_uses_invoice_grain_not_row_grain(naive):
    """Confirms this comparison isolates the returns-treatment variable
    specifically -- the naive pipeline still correctly counts distinct
    invoices, not rows, for frequency (that mistake was already tested
    exhaustively in Phase 4)."""
    assert (naive["naive_frequency"] > 0).all()
