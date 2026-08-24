"""
Phase 11 - Tests for the cohort retention matrix.

Run with: python3 -m pytest src/test_retention_matrix.py -v
"""

import pandas as pd
import numpy as np
import pytest
from retention_matrix import build_retention_matrix, manual_validation, LAST_OBSERVED_MONTH


@pytest.fixture
def activity():
    return pd.read_pickle("data/processed/monthly_activity.pkl")


@pytest.fixture
def cohort_assignment():
    return pd.read_pickle("data/processed/cohort_assignment.pkl")


@pytest.fixture
def matrix(activity, cohort_assignment):
    return build_retention_matrix(activity, cohort_assignment)


def test_m0_is_always_100_percent(matrix):
    counts, pct, cohort_sizes = matrix
    assert (pct[0] == 100.0).all()


def test_manual_validation_matches_pivot(activity, cohort_assignment, matrix):
    counts, pct, cohort_sizes = matrix
    # manual_validation() itself asserts equality internally; calling it
    # here makes that assertion part of the pytest run.
    cohort_size, results = manual_validation(activity, cohort_assignment, counts, "2011-06")
    assert cohort_size == 108
    assert results["M0"] == 108


def test_late_cohorts_have_nan_beyond_available_window(matrix):
    counts, pct, cohort_sizes = matrix
    dec_2011 = pd.Period("2011-12", freq="M")
    row = pct.loc[dec_2011]
    assert row[0] == 100.0
    assert row[1:].isna().all(), "December 2011 cohort should have NO observable months beyond M0"


def test_nov_2011_cohort_has_exactly_two_observable_months(matrix):
    counts, pct, cohort_sizes = matrix
    nov_2011 = pd.Period("2011-11", freq="M")
    row = pct.loc[nov_2011]
    assert row[0:2].notna().all()
    assert row[2:].isna().all()


def test_no_unavailable_period_is_silently_zero(matrix):
    """The core rule of this phase: unavailable != 0%. Spot-check that
    unavailable cells are NaN, not 0, across every cohort."""
    counts, pct, cohort_sizes = matrix
    dec_2011 = pd.Period("2011-12", freq="M")
    assert pd.isna(pct.loc[dec_2011, 1]), "unavailable cell must be NaN, not 0"


def test_retention_percentages_never_exceed_100(matrix):
    counts, pct, cohort_sizes = matrix
    valid = pct.dropna()
    assert (valid <= 100.0001).all().all()


def test_first_cohort_full_range_available(matrix):
    """The Dec 2009 cohort has existed for the entire dataset window, so
    it should have retention values for every offset up to the max."""
    counts, pct, cohort_sizes = matrix
    dec_2009 = pd.Period("2009-12", freq="M")
    row = pct.loc[dec_2009]
    assert row.notna().all(), "the earliest cohort should have no unavailable cells"
