"""
Phase 20 - Tests for retention strategy simulation.

Run with: python3 -m pytest src/test_retention_simulation.py -v
"""

import pandas as pd
import pytest
from retention_simulation import prepare_population, define_strategies, simulate


@pytest.fixture
def df():
    merged = pd.read_pickle("data/processed/rfm_clv_combined.pkl")
    return prepare_population(merged)


@pytest.fixture
def strategies(df):
    return define_strategies(df)


def test_strategy_population_sizes(strategies):
    assert len(strategies["A_target_everyone"]) == 5868
    assert len(strategies["B_target_all_at_risk"]) == 2802
    assert len(strategies["C_target_high_value_at_risk"]) == 572


def test_strategy_c_is_subset_of_strategy_b(strategies):
    b_ids = set(strategies["B_target_all_at_risk"]["customer_id"])
    c_ids = set(strategies["C_target_high_value_at_risk"]["customer_id"])
    assert c_ids.issubset(b_ids)


def test_strategy_b_is_subset_of_strategy_a(strategies):
    a_ids = set(strategies["A_target_everyone"]["customer_id"])
    b_ids = set(strategies["B_target_all_at_risk"]["customer_id"])
    assert b_ids.issubset(a_ids)


def test_strategy_a_and_b_have_identical_recoverable_value(strategies):
    """Core assumption check: since only at-risk customers contribute
    recoverable value, targeting 'everyone' recovers exactly as much as
    targeting 'all at risk' -- just at higher cost. This is the specific
    mechanism that makes Strategy A look wasteful in the simulation."""
    result = simulate(strategies, win_back_rate=0.20)
    assert abs(
        result.loc["A_target_everyone", "expected_recovered_value_gbp"]
        - result.loc["B_target_all_at_risk", "expected_recovered_value_gbp"]
    ) < 0.01


def test_strategy_c_has_best_roi_at_every_tested_rate(strategies):
    for rate in [0.10, 0.20, 0.30]:
        result = simulate(strategies, rate)
        assert result.loc["C_target_high_value_at_risk", "roi"] == result["roi"].max()


def test_strategy_a_has_worst_roi_at_every_tested_rate(strategies):
    for rate in [0.10, 0.20, 0.30]:
        result = simulate(strategies, rate)
        assert result.loc["A_target_everyone", "roi"] == result["roi"].min()


def test_higher_win_back_rate_increases_net_value_for_all_strategies(strategies):
    low = simulate(strategies, 0.10)
    high = simulate(strategies, 0.30)
    for strategy in low.index:
        assert high.loc[strategy, "expected_net_value_gbp"] > low.loc[strategy, "expected_net_value_gbp"]


def test_cost_scales_linearly_with_population(strategies):
    result = simulate(strategies, 0.20)
    for strategy_name, pop in strategies.items():
        expected_cost = len(pop) * 5.0
        assert abs(result.loc[strategy_name, "campaign_cost_gbp"] - expected_cost) < 0.01
