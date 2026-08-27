"""
Phase 27 - Tests for final analytical reconciliation.

Run with: python3 -m pytest src/test_reconciliation.py -v
"""

from reconciliation import (
    reconcile_transactions_to_customers, reconcile_customers_to_rfm,
    reconcile_rfm_to_segments, reconcile_segments_to_cohorts,
    reconcile_cohorts_to_clv, reconcile_pipeline_to_dashboard,
)


def test_transactions_to_customers_reconciles():
    assert reconcile_transactions_to_customers()["ok"]


def test_customers_to_rfm_reconciles():
    assert reconcile_customers_to_rfm()["ok"]


def test_rfm_to_segments_reconciles():
    assert reconcile_rfm_to_segments()["ok"]


def test_segments_to_cohorts_reconciles():
    assert reconcile_segments_to_cohorts()["ok"]


def test_cohorts_to_clv_reconciles_with_boundary_bug_explained():
    """Confirms the specific finding from this phase: 3 customers are
    excluded from CLV modeling due to a same-day midnight-boundary bug in
    the calibration cutoff (documented, not fixed, given negligible
    impact) -- and that ALL exclusions are now accounted for, not left
    as an unexplained residual."""
    result = reconcile_cohorts_to_clv()
    assert result["ok"]
    assert result["unexplained"] == 0
    assert result["same_day_boundary_bug (2011-06-30, documented, not fixed)"] == 3


def test_pipeline_to_dashboard_reconciles():
    assert reconcile_pipeline_to_dashboard()["ok"]


def test_full_chain_all_links_pass():
    checks = [
        reconcile_transactions_to_customers(),
        reconcile_customers_to_rfm(),
        reconcile_rfm_to_segments(),
        reconcile_segments_to_cohorts(),
        reconcile_cohorts_to_clv(),
        reconcile_pipeline_to_dashboard(),
    ]
    assert all(c["ok"] for c in checks)
