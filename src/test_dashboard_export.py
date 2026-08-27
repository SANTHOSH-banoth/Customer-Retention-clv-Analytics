"""
Phase 24 - Tests for dashboard data export.

Run with: python3 -m pytest src/test_dashboard_export.py -v
"""

import json
import pandas as pd
from pathlib import Path
from export_dashboard_data import export


def test_export_runs_and_produces_file():
    output = export()
    path = Path("dashboard/data_export/dashboard_data.json")
    assert path.exists()
    with open(path) as f:
        loaded = json.load(f)
    assert loaded["overview"]["total_customers"] == output["overview"]["total_customers"]


def test_dashboard_total_customers_matches_pipeline():
    output = export()
    merged = pd.read_pickle("data/processed/rfm_clv_combined.pkl")
    assert output["overview"]["total_customers"] == len(merged)


def test_dashboard_segment_revenue_matches_phase7():
    output = export()
    champions_idx = output["segments"]["labels"].index("Champions")
    champions_revenue = output["segments"]["revenue"][champions_idx]
    assert abs(champions_revenue - 11_530_710) < 100


def test_dashboard_revenue_at_risk_matches_phase19():
    output = export()
    assert abs(output["revenue_at_risk"]["revenue_at_risk_winsorized"] - 234_622.30) < 1.0


def test_dashboard_html_file_exists_and_is_self_contained():
    """Confirms the dashboard file has no external CDN dependencies --
    Chart.js is inlined, not loaded from a URL -- so it works offline."""
    html_path = Path("dashboard/index.html")
    assert html_path.exists()
    html = html_path.read_text()
    assert "cdnjs.cloudflare.com" not in html
    assert "fonts.googleapis.com" not in html
    assert "Chart.Chart" in html or "class Chart" in html or "var Chart" in html or "Chart=" in html.replace(" ", "")


def test_top_at_risk_targets_excludes_known_artifact_customer():
    """Phase 25 finding: an unwinsorized top-CLV list would put Customer
    12346 (Phase 18/22's known data artifact -- a sold-then-cancelled
    74,215-unit order) at #1. This test locks in the fix: the drill-down
    list excludes negative-historical-monetary customers, so 12346 never
    appears in an actionable target list."""
    output = export()
    target_ids = [c["customer_id"] for c in output["top_at_risk_targets"]]
    assert 12346 not in target_ids


def test_top_at_risk_targets_all_have_positive_historical_value():
    output = export()
    merged = pd.read_pickle("data/processed/rfm_clv_combined.pkl")
    target_ids = [c["customer_id"] for c in output["top_at_risk_targets"]]
    hist = merged[merged["customer_id"].isin(target_ids)]
    assert (hist["monetary"] > 0).all()


def test_rfm_stats_by_segment_covers_all_segments():
    output = export()
    from segment import assign_segment  # noqa: ensures segment module importable
    expected_segments = {
        "Champions", "Loyal Customers", "Potential Loyalists", "New Customers",
        "Need Attention", "At Risk", "About To Sleep", "Hibernating",
    }
    assert set(output["rfm_stats_by_segment"].keys()) == expected_segments


def test_rfm_stats_by_segment_counts_match_phase7_populations():
    output = export()
    at_risk_count = output["rfm_stats_by_segment"]["At Risk"]["recency"]["count"]
    assert int(at_risk_count) == 441
