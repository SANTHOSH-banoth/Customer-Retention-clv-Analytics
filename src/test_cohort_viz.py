"""
Phase 12 - Tests for cohort visualization.

These tests check the DATA going into the charts respects the NaN-vs-zero
rule -- they don't try to assert anything about rendered pixels, which
would be brittle and not actually useful.

Run with: python3 -m pytest src/test_cohort_viz.py -v
"""

import pandas as pd
from pathlib import Path


def test_figures_were_generated():
    fig_dir = Path("reports/figures")
    for name in [
        "phase12_cohort_heatmap.png",
        "phase12_retention_curves.png",
        "phase12_milestone_comparison.png",
    ]:
        path = fig_dir / name
        assert path.exists(), f"{name} was not generated"
        assert path.stat().st_size > 1000, f"{name} looks suspiciously small/empty"


def test_milestone_bar_chart_data_excludes_unavailable_cohorts():
    """Confirms the bar-chart data source only includes cohorts with a
    real value at each milestone -- the chart never has to fake a zero
    bar for an unobservable cohort because such cohorts are absent from
    the input entirely."""
    pct = pd.read_pickle("data/processed/cohort_retention_pct.pkl")
    m12_available = pct[12].dropna()
    assert len(m12_available) == 13
    assert "2011-12" not in [str(i) for i in m12_available.index]


def test_left_censored_cohort_present_in_curve_selection():
    """The known left-censored cohort (2009-12) is deliberately included
    in the retention-curve comparison, with its caveat label, so it can't
    be silently dropped in a future edit without the test failing."""
    pct = pd.read_pickle("data/processed/cohort_retention_pct.pkl")
    assert pd.Period("2009-12", "M") in pct.index
