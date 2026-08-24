"""
Phase 8 - Tests for segment validation.

Run with: python3 -m pytest src/test_validate_segments.py -v
"""

import pandas as pd
import pytest
from validate_segments import load_data, levene_tests, kruskal_tests, dunn_posthoc


@pytest.fixture
def seg():
    return load_data()


def test_levene_confirms_unequal_variance(seg):
    """This is a documentation test: confirms the ANOVA-assumption
    violation that justifies using Kruskal-Wallis instead."""
    results = levene_tests(seg)
    for metric, res in results.items():
        assert res["p_value"] < 0.05, f"{metric} unexpectedly has equal variance across segments"


def test_kruskal_wallis_significant_for_all_metrics(seg):
    results = kruskal_tests(seg)
    for metric, res in results.items():
        assert res["significant"], f"{metric} not significantly different across segments"


def test_champions_recency_better_than_hibernating(seg):
    """Sanity check in the correct direction, not just 'a difference exists'."""
    champions_recency = seg.loc[seg["segment"] == "Champions", "recency_days"].median()
    hibernating_recency = seg.loc[seg["segment"] == "Hibernating", "recency_days"].median()
    assert champions_recency < hibernating_recency


def test_champions_monetary_higher_than_new_customers(seg):
    champions_monetary = seg.loc[seg["segment"] == "Champions", "monetary"].median()
    new_monetary = seg.loc[seg["segment"] == "New Customers", "monetary"].median()
    assert champions_monetary > new_monetary


def test_at_risk_and_need_attention_differ_on_recency_not_other_metrics(seg):
    """Documents a specific finding: these two segments are statistically
    indistinguishable on frequency/monetary/active_months but differ
    sharply on recency -- confirming they encode a real, distinct signal
    (urgency) rather than being redundant labels."""
    dunn_recency = dunn_posthoc(seg, "recency_days")
    dunn_freq = dunn_posthoc(seg, "frequency")
    p_recency = dunn_recency.loc["At Risk", "Need Attention"]
    p_freq = dunn_freq.loc["At Risk", "Need Attention"]
    assert p_recency < 0.05, "expected At Risk vs Need Attention to differ significantly on recency"
    assert p_freq >= 0.05, "expected At Risk vs Need Attention to NOT differ significantly on frequency"


def test_dunn_posthoc_diagonal_is_one(seg):
    """A segment compared to itself should have p=1.0 (or very close)."""
    dunn = dunn_posthoc(seg, "monetary")
    for s in dunn.columns:
        assert dunn.loc[s, s] >= 0.99
