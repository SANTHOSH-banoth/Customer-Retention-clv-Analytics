"""
Phase 14 - Tests for segment x cohort analysis.

Run with: python3 -m pytest src/test_segment_cohort.py -v
"""

import pandas as pd
import pytest
from segment_cohort import merge_segment_cohort, segment_composition_by_cohort, cohort_age_confound


@pytest.fixture
def merged():
    return merge_segment_cohort()


def test_every_rfm_customer_has_a_cohort(merged):
    seg = pd.read_pickle("data/processed/rfm_segmented.pkl")
    assert len(merged) == len(seg)


def test_composition_rows_sum_to_100(merged):
    comp = segment_composition_by_cohort(merged)
    sums = comp.sum(axis=1)
    assert (abs(sums - 100) < 0.01).all()


def test_no_hibernating_in_very_new_cohorts(merged):
    """Mechanical validity check: a cohort only a few months old cannot
    contain Hibernating customers (R=1 requires very stale recency, which
    is impossible to have accumulated yet). Confirms the segment rules
    behave sensibly given tenure, not a business finding on its own."""
    comp = segment_composition_by_cohort(merged)
    recent_cohorts = comp.loc[comp.index >= pd.Period("2011-06", "M")]
    assert (recent_cohorts["Hibernating"] == 0).all()


def test_cohort_age_strongly_correlates_with_champions_share(merged):
    """This is the core confound this phase exists to surface: Frequency
    and Monetary are cumulative, so older cohorts mechanically look
    'better' even absent any true quality difference."""
    result = cohort_age_confound(merged)
    assert result["full_sample"]["corr_champions"] > 0.7
    assert result["full_sample"]["p_champions"] < 0.001


def test_confound_persists_even_among_mature_cohorts(merged):
    """Confirms the correlation is not purely a 'brand new cohorts have
    had literally zero time' floor effect -- it persists even when
    restricting to cohorts with 12+ months of tenure."""
    result = cohort_age_confound(merged)
    assert result["mature_only_12mo_plus"]["p_champions"] < 0.05


def test_new_customers_segment_concentrated_in_recent_cohorts(merged):
    comp = segment_composition_by_cohort(merged)
    recent = comp.loc[comp.index >= pd.Period("2011-10", "M"), "New Customers"]
    older = comp.loc[comp.index < pd.Period("2011-06", "M"), "New Customers"]
    assert recent.mean() > older.mean()
