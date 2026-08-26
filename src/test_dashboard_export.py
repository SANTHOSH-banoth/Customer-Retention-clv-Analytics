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
