"""
Phase 13 - Tests for cohort interpretation.

Run with: python3 -m pytest src/test_interpret_cohorts.py -v
"""

import pytest
from interpret_cohorts import (
    load_excl, early_drop_stats, paired_m1_vs_m12,
    cohort_time_trend, seasonal_effect,
)


@pytest.fixture
def excl():
    return load_excl()


def test_left_censored_cohort_excluded(excl):
    import pandas as pd
    assert pd.Period("2009-12", "M") not in excl.index


def test_early_drop_is_large(excl):
    """Confirms the M0->M1 drop is a real, large phenomenon, not noise."""
    stats_d = early_drop_stats(excl)
    assert stats_d["avg_drop_pts"] > 70


def test_no_significant_long_term_decay_within_cohorts(excl):
    """Documents the (non-)finding: paired M1 vs M12 comparison on the
    same 12 cohorts is NOT statistically significant, so we do not claim
    a proven long-term decline beyond the initial post-M0 drop."""
    result = paired_m1_vs_m12(excl)
    assert result["n_cohorts"] == 12
    assert not result["significant"]


def test_no_significant_cohort_time_trend(excl):
    """Documents the (non-)finding: no statistically significant
    correlation between acquisition order and early retention -- directly
    guards against an unsupported 'later cohorts retain worse' claim."""
    for m in [1, 3]:
        result = cohort_time_trend(excl, m)
        assert not result["significant"], (
            f"M{m} unexpectedly shows a significant time trend -- "
            f"the business narrative in the report would need updating"
        )


def test_no_significant_seasonal_retention_effect(excl):
    """Documents the (non-)finding: holiday-acquired cohorts do not
    retain significantly differently in their first month."""
    result = seasonal_effect(excl)
    assert not result["significant"]
