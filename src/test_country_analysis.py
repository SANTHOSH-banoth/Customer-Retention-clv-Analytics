"""
Phase 21 - Tests for country analysis.

Run with: python3 -m pytest src/test_country_analysis.py -v
"""

import pandas as pd
from scipy import stats
import pytest
from country_analysis import build_country_table, country_summary, MIN_SAMPLE_SIZE, OTHER_LABEL


@pytest.fixture
def df():
    merged = pd.read_pickle("data/processed/rfm_clv_combined.pkl")
    customers = pd.read_pickle("data/processed/customers.pkl")
    return build_country_table(merged, customers)


def test_small_countries_grouped_not_dropped(df):
    grouped = df[df["country_group"] == OTHER_LABEL]
    assert len(grouped) > 0
    assert len(grouped) == len(df) - df[df["country_group"] != OTHER_LABEL].shape[0]


def test_qualifying_countries_all_meet_threshold(df):
    counts = df[df["country_group"] != OTHER_LABEL]["country_group"].value_counts()
    assert (counts >= MIN_SAMPLE_SIZE).all()


def test_uk_is_the_dominant_qualifying_country(df):
    counts = df["country_group"].value_counts()
    assert counts.idxmax() == "United Kingdom"
    assert counts["United Kingdom"] / len(df) > 0.85


def test_no_customer_lost_in_grouping(df):
    merged = pd.read_pickle("data/processed/rfm_clv_combined.pkl")
    assert len(df) == len(merged)


def test_recency_differs_significantly_across_qualifying_countries(df):
    """Confirms the Phase 21 finding directly: non-UK qualifying
    countries show significantly different (better) recency behavior."""
    qualifying = ["United Kingdom", "Germany", "France", "Spain"]
    sub = df[df["country"].isin(qualifying)]
    groups = [sub.loc[sub["country"] == c, "recency_days"] for c in qualifying]
    stat, p = stats.kruskal(*groups)
    assert p < 0.05


def test_germany_and_france_more_recently_active_than_uk(df):
    uk_active = df.loc[df["country"] == "United Kingdom", "is_recently_active"].mean()
    de_active = df.loc[df["country"] == "Germany", "is_recently_active"].mean()
    fr_active = df.loc[df["country"] == "France", "is_recently_active"].mean()
    assert de_active > uk_active
    assert fr_active > uk_active


def test_country_summary_revenue_sums_to_total(df):
    summary = country_summary(df)
    assert abs(summary["total_revenue"].sum() - df["monetary"].sum()) < 1.0
