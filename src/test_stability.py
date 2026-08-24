"""
Phase 9 - Tests for segment stability.

Run with: python3 -m pytest src/test_stability.py -v
"""

import pandas as pd
import pytest
from stability import (
    variant_quartiles, variant_gross_revenue, variant_snapshot_shift,
    variant_winsorized_monetary, compare_to_baseline,
)


@pytest.fixture
def rfm():
    return pd.read_pickle("data/processed/rfm.pkl").sort_values("customer_id").reset_index(drop=True)


@pytest.fixture
def customers():
    return pd.read_pickle("data/processed/customers.pkl")


@pytest.fixture
def baseline():
    b = pd.read_pickle("data/processed/rfm_segmented.pkl")
    return b.sort_values("customer_id").reset_index(drop=True)


def test_snapshot_shift_produces_zero_segment_changes(rfm, baseline):
    variant = variant_snapshot_shift(rfm, 30)
    res = compare_to_baseline(baseline["segment"], variant, rfm["customer_id"])
    assert res["pct_customers_changed"] == 0.0


def test_winsorizing_monetary_produces_zero_segment_changes(rfm, baseline):
    variant = variant_winsorized_monetary(rfm)
    res = compare_to_baseline(baseline["segment"], variant, rfm["customer_id"])
    assert res["pct_customers_changed"] == 0.0


def test_gross_vs_net_revenue_impact_is_small(rfm, customers, baseline):
    """Confirms Phase 3's net-revenue decision doesn't materially change
    segmentation, even though it matters for accurate reporting."""
    variant = variant_gross_revenue(rfm, customers)
    res = compare_to_baseline(baseline["segment"], variant, rfm["customer_id"])
    assert res["pct_customers_changed"] < 2.0


def test_quartile_vs_quintile_is_the_most_sensitive_dimension(rfm, baseline):
    """Documents the single largest instability found in this phase."""
    variant = variant_quartiles(rfm)
    res = compare_to_baseline(baseline["segment"], variant, rfm["customer_id"])
    assert res["pct_customers_changed"] > 15.0  # confirms this IS the sensitive case


def test_quartile_instability_concentrated_in_boundary_scores(rfm, baseline):
    """Confirms the mechanism: Champions requires r_score>=4, but 'score 4'
    means a different percentile depending on whether there are 4 or 5
    bins. This test locks in that finding so it can't silently regress."""
    r5 = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    r4 = pd.qcut(rfm["recency_days"], 4, labels=[4, 3, 2, 1]).astype(int)
    champions_mask = baseline["segment"] == "Champions"
    demoted_pct = ((r5[champions_mask] >= 4) & (r4[champions_mask] < 4)).mean() * 100
    assert demoted_pct > 20.0, "expected a substantial scale-mismatch effect on Champions"
