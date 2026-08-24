"""
Phase 7 - Tests for RFM segmentation.

Run with: python3 -m pytest src/test_segment.py -v
"""

import pandas as pd
import pytest
from segment import build_segments, score_recency, score_frequency, score_monetary


@pytest.fixture
def rfm():
    return pd.read_pickle("data/processed/rfm.pkl")


def test_every_customer_gets_a_segment(rfm):
    seg = build_segments(rfm)
    assert seg["segment"].notna().all()
    assert len(seg) == len(rfm)


def test_no_near_empty_segments(rfm):
    seg = build_segments(rfm)
    assert seg["segment"].value_counts().min() >= 10


def test_scores_are_in_valid_range(rfm):
    seg = build_segments(rfm)
    for col in ["r_score", "f_score", "m_score"]:
        assert seg[col].between(1, 5).all()


def test_most_recent_customer_gets_highest_recency_score(rfm):
    seg = build_segments(rfm)
    most_recent = seg.loc[seg["recency_days"].idxmin()]
    assert most_recent["r_score"] == 5


def test_least_recent_customer_gets_lowest_recency_score(rfm):
    seg = build_segments(rfm)
    least_recent = seg.loc[seg["recency_days"].idxmax()]
    assert least_recent["r_score"] == 1


def test_single_purchase_customers_all_get_frequency_score_one(rfm):
    seg = build_segments(rfm)
    single = seg[seg["frequency"] == 1]
    assert (single["f_score"] == 1).all()


def test_highest_monetary_customer_gets_highest_score(rfm):
    seg = build_segments(rfm)
    top = seg.loc[seg["monetary"].idxmax()]
    assert top["m_score"] == 5


def test_champions_segment_has_high_scores_on_all_three(rfm):
    seg = build_segments(rfm)
    champions = seg[seg["segment"] == "Champions"]
    assert (champions["r_score"] >= 4).all()
    assert (champions["f_score"] >= 4).all()
    assert (champions["m_score"] >= 4).all()


def test_hibernating_segment_has_low_recency_and_frequency(rfm):
    seg = build_segments(rfm)
    hib = seg[seg["segment"] == "Hibernating"]
    assert (hib["r_score"] == 1).all()
    assert (hib["f_score"] <= 2).all()


def test_segment_rules_are_mutually_exclusive_and_exhaustive(rfm):
    """Every possible r/f/m score combination (5x5x5=125) must map to
    exactly one segment via the waterfall -- verified by construction
    (apply() always returns a string, checked here for completeness)."""
    from segment import assign_segment
    for r in range(1, 6):
        for f in range(1, 6):
            for m in range(1, 6):
                label = assign_segment({"r_score": r, "f_score": f, "m_score": m})
                assert isinstance(label, str) and len(label) > 0
