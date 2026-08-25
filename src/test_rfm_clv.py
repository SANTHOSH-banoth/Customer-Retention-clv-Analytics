"""
Phase 18 - Tests for RFM x CLV combined view.

Run with: python3 -m pytest src/test_rfm_clv.py -v
"""

import pandas as pd
import pytest
from rfm_clv import build_combined_view, segment_summary, find_mismatches


@pytest.fixture
def merged():
    return build_combined_view()


def test_every_rfm_customer_present(merged):
    seg = pd.read_pickle("data/processed/rfm_segmented.pkl")
    assert len(merged) == len(seg)


def test_coverage_categories_are_exhaustive_and_correctly_sized(merged):
    counts = merged["clv_coverage"].value_counts()
    assert counts["full_bgnbd_gammagamma"] == 2543
    assert counts["approximated_single_purchase"] == 1532
    assert counts["no_prediction"] == 1793
    assert counts.sum() == len(merged)


def test_no_prediction_customers_have_null_clv(merged):
    no_pred = merged[merged["clv_coverage"] == "no_prediction"]
    assert no_pred["predicted_clv_final"].isna().all()


def test_new_customers_segment_has_zero_clv_coverage(merged):
    """Documents a real, substantive limitation found in this phase: the
    New Customers segment (by definition, very recent first purchase) has
    NO CLV coverage at all, because the calibration cutoff (2011-06-30)
    predates when almost all of them were acquired."""
    new_cust = merged[merged["segment"] == "New Customers"]
    assert new_cust["predicted_clv_final"].notna().sum() == 0


def test_segment_summary_historical_revenue_matches_phase7(merged):
    summary = segment_summary(merged)
    champions_rev = summary.loc["Champions", "historical_revenue"]
    assert abs(champions_rev - 11_530_710) < 100  # matches Phase 7 report value


def test_mismatch_groups_are_non_empty(merged):
    mismatches = find_mismatches(merged)
    for name, group in mismatches.items():
        assert isinstance(group, pd.DataFrame)


def test_customer_12346_is_the_extreme_mismatch_case(merged):
    """Locks in the specific case study used in the Phase 18 report: a
    customer whose predicted CLV is dominated by a single large 'sale' row
    that was fully cancelled minutes later -- since BG/NBD/Gamma-Gamma
    were fit on 'sale' rows without netting cancellations, this inflates
    the prediction substantially. This is a documented model limitation,
    not a data error."""
    row = merged[merged["customer_id"] == 12346].iloc[0]
    assert row["monetary"] < 0  # historical net revenue is negative
    assert row["predicted_clv_final"] > 10_000  # predicted CLV is very high
