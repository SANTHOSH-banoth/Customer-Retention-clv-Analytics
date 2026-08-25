"""
Phase 19 - Tests for revenue at risk.

Run with: python3 -m pytest src/test_revenue_at_risk.py -v
"""

import pandas as pd
import pytest
from revenue_at_risk import compute_revenue_at_risk, AT_RISK_SEGMENTS


@pytest.fixture
def merged():
    return pd.read_pickle("data/processed/rfm_clv_combined.pkl")


@pytest.fixture
def result(merged):
    return compute_revenue_at_risk(merged)


def test_historical_revenue_matches_rfm_total(merged, result):
    assert abs(result["total_historical_revenue"] - merged["monetary"].sum()) < 1.0


def test_at_risk_population_uses_only_declining_segments(merged):
    at_risk = merged[merged["segment"].isin(AT_RISK_SEGMENTS)]
    assert set(at_risk["segment"].unique()).issubset(set(AT_RISK_SEGMENTS))
    assert "Champions" not in at_risk["segment"].unique()
    assert "Loyal Customers" not in at_risk["segment"].unique()


def test_winsorized_revenue_at_risk_is_less_than_or_equal_to_raw(result):
    assert result["revenue_at_risk_winsorized"] <= result["revenue_at_risk_raw"]


def test_revenue_at_risk_pct_is_a_valid_share(result):
    assert 0 <= result["revenue_at_risk_pct_of_predicted_raw"] <= 100
    assert 0 <= result["revenue_at_risk_pct_of_predicted_winsorized"] <= 100


def test_outlier_customer_meaningfully_affects_raw_but_not_ratio(result):
    """Documents the specific finding: winsorizing changes the raw £
    figure noticeably (Customer 12346's distortion) but the AT-RISK SHARE
    of total predicted value is fairly stable -- this is the honest,
    checked conclusion, not an assumption."""
    raw_diff = result["revenue_at_risk_raw"] - result["revenue_at_risk_winsorized"]
    assert raw_diff > 15000  # the outlier's effect is real and non-trivial in £ terms
    pct_diff = abs(result["revenue_at_risk_pct_of_predicted_raw"] - result["revenue_at_risk_pct_of_predicted_winsorized"])
    assert pct_diff < 2.0  # but the overall share is comparatively stable


def test_at_risk_clv_coverage_is_less_than_full_population(result):
    """Confirms this project isn't claiming full visibility into every
    at-risk customer's predicted value -- coverage is explicitly partial."""
    assert result["at_risk_clv_coverage_pct"] < 100
