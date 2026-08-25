"""
Phase 16 - Tests for CLV model fitting.

Run with: python3 -m pytest src/test_clv_model.py -v
"""

import pandas as pd
import pytest
from clv_model import (
    get_modeling_population, build_calibration_holdout, fit_bgf, fit_ggf,
    LEFT_CENSORED_COHORT,
)


@pytest.fixture
def txn():
    return pd.read_pickle("data/processed/transactions_with_revenue.pkl")


@pytest.fixture
def cohort():
    return pd.read_pickle("data/processed/cohort_assignment.pkl")


@pytest.fixture
def sales(txn, cohort):
    return get_modeling_population(txn, cohort)


@pytest.fixture
def cal_holdout(sales):
    return build_calibration_holdout(sales)


def test_left_censored_cohort_excluded_from_modeling_population(sales, cohort):
    excluded_ids = set(cohort.loc[cohort["cohort_month"] == LEFT_CENSORED_COHORT, "customer_id"])
    modeled_ids = set(sales["Customer ID"].unique())
    assert len(excluded_ids & modeled_ids) == 0


def test_only_sale_transactions_used(sales):
    """get_modeling_population should never include cancellations or
    non-merchandise rows -- this is checked structurally since the
    source frame is pre-filtered to transaction_type == 'sale'."""
    assert (sales["transaction_type"] == "sale").all()


def test_calibration_recency_never_exceeds_T(cal_holdout):
    assert (cal_holdout["recency_cal"] <= cal_holdout["T_cal"]).all()


def test_bgf_fits_without_error_and_produces_valid_params(cal_holdout):
    bgf = fit_bgf(cal_holdout)
    params = dict(bgf.params_)
    assert all(v > 0 for v in params.values()), "all BG/NBD parameters must be positive"


def test_ggf_only_fit_on_repeat_purchasers(cal_holdout):
    ggf, repeat_customers = fit_ggf(cal_holdout)
    assert (repeat_customers["frequency_cal"] > 0).all()
    assert len(repeat_customers) < len(cal_holdout), (
        "Gamma-Gamma population should be a strict subset (single-purchase customers excluded)"
    )


def test_ggf_params_are_valid(cal_holdout):
    ggf, _ = fit_ggf(cal_holdout)
    params = dict(ggf.params_)
    assert all(v > 0 for v in params.values())


def test_predicted_purchases_non_negative(cal_holdout):
    bgf = fit_bgf(cal_holdout)
    pred = bgf.predict(162, cal_holdout["frequency_cal"], cal_holdout["recency_cal"], cal_holdout["T_cal"])
    assert (pred >= 0).all()


def test_prob_alive_between_zero_and_one(cal_holdout):
    bgf = fit_bgf(cal_holdout)
    prob = bgf.conditional_probability_alive(
        cal_holdout["frequency_cal"], cal_holdout["recency_cal"], cal_holdout["T_cal"]
    )
    assert ((prob >= 0) & (prob <= 1)).all()
