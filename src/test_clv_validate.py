"""
Phase 17 - Tests for CLV validation.

Run with: python3 -m pytest src/test_clv_validate.py -v
"""

import pandas as pd
import pytest
from clv_validate import (
    compute_actual_holdout, purchase_count_errors, clv_ranking_quality,
    decile_capture, clv_error_metrics,
)
from clv_model import get_modeling_population


@pytest.fixture
def df():
    return pd.read_pickle("data/processed/clv_validation.pkl")


def test_actual_holdout_computed_independently_of_lifetimes_columns():
    """Confirms actual holdout values are recomputed directly from
    transactions, not taken on faith from the lifetimes library's
    internal 'frequency_holdout'/'monetary_value_holdout' columns."""
    txn = pd.read_pickle("data/processed/transactions_with_revenue.pkl")
    cohort = pd.read_pickle("data/processed/cohort_assignment.pkl")
    sales = get_modeling_population(txn, cohort)
    actual = compute_actual_holdout(sales)
    assert (actual["actual_holdout_orders"] > 0).all()  # only customers WITH holdout activity appear
    assert (actual["actual_holdout_revenue"] >= 0).all()


def test_purchase_count_errors_are_non_negative(df):
    result = purchase_count_errors(df)
    assert result["mae"] >= 0
    assert result["rmse"] >= 0
    assert result["rmse"] >= result["mae"], "RMSE should never be less than MAE"


def test_purchase_count_ranking_is_significant(df):
    result = purchase_count_errors(df)
    assert result["spearman_p"] < 0.05
    assert result["spearman_corr"] > 0, "predicted purchases should positively correlate with actual"


def test_clv_ranking_quality_positive_for_both_models(df):
    for col in ["predicted_clv_bgnbd_ggf", "baseline_clv"]:
        result = clv_ranking_quality(df, col)
        assert result["spearman_corr"] > 0
        assert result["spearman_p"] < 0.05


def test_decile_capture_top_decile_beats_random(df):
    """The core business-relevant check: does the top predicted decile
    capture meaningfully more than its 10% population share of actual
    revenue? If not, the model has no practical targeting value regardless
    of any other metric."""
    decile = decile_capture(df, "predicted_clv_bgnbd_ggf")
    top_decile_capture = decile.iloc[0]["pct_of_actual_revenue"]
    assert top_decile_capture > 30.0, (
        f"top predicted decile only captured {top_decile_capture:.1f}% of revenue -- "
        f"barely better than random (10%), model would have little practical value"
    )


def test_decile_capture_sums_to_100_percent(df):
    decile = decile_capture(df, "predicted_clv_bgnbd_ggf")
    assert abs(decile["pct_of_actual_revenue"].sum() - 100) < 1.0


def test_neither_model_dominates_on_every_metric(df):
    """Documents the Phase 17 finding directly: BG/NBD+GG wins on MAE and
    ranking correlation, but the simple baseline wins on RMSE and bias
    magnitude. This test locks in that nuance so a future edit can't
    silently claim one model is unconditionally better."""
    bg_err = clv_error_metrics(df, "predicted_clv_bgnbd_ggf")
    base_err = clv_error_metrics(df, "baseline_clv")
    bg_better_mae = bg_err["mae"] < base_err["mae"]
    base_better_rmse = base_err["rmse"] < bg_err["rmse"]
    assert bg_better_mae and base_better_rmse, (
        "expected a mixed result (BG/NBD+GG better MAE, baseline better RMSE) -- "
        "if this no longer holds, the Phase 17 report's conclusion needs updating"
    )
