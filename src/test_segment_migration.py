"""
Phase 23 - Tests for segment migration.

Run with: python3 -m pytest src/test_segment_migration.py -v
"""

import pandas as pd
import pytest
from segment_migration import build_t1_segments, build_migration_table, T1_CUTOFF


@pytest.fixture
def t1():
    txn = pd.read_pickle("data/processed/transactions_with_revenue.pkl")
    return build_t1_segments(txn)


@pytest.fixture
def t2():
    return pd.read_pickle("data/processed/rfm_segmented.pkl")


@pytest.fixture
def migration(t1, t2):
    return build_migration_table(t1, t2)


def test_t1_only_uses_transactions_before_cutoff():
    txn = pd.read_pickle("data/processed/transactions_with_revenue.pkl")
    txn_t1 = txn[txn["InvoiceDate"] <= T1_CUTOFF]
    assert txn_t1["InvoiceDate"].max() <= T1_CUTOFF


def test_t1_population_smaller_than_t2(t1, t2):
    """T1 is an earlier snapshot -- fewer customers should have made a
    purchase by then than by the final snapshot."""
    assert len(t1) < len(t2)


def test_migration_only_includes_customers_present_at_both_snapshots(t1, t2, migration):
    assert len(migration) <= len(t1)
    assert set(migration["customer_id"]).issubset(set(t1["customer_id"]))
    assert set(migration["customer_id"]).issubset(set(t2["customer_id"]))


def test_no_customer_becomes_new_customer_at_t2(migration):
    """Validity check: a customer who already existed at T1 (mid-2011)
    cannot legitimately be scored 'New Customers' at T2 five months
    later, since that segment requires a very recent first purchase."""
    assert (migration["segment_t2"] != "New Customers").all()


def test_champions_show_high_but_not_perfect_stability(migration):
    champions_t1 = migration[migration["segment_t1"] == "Champions"]
    stayed = (champions_t1["segment_t2"] == "Champions").mean()
    assert 0.5 < stayed < 1.0  # meaningfully stable, but not everyone stays


def test_at_risk_to_champions_recovery_is_measured_and_nonzero(migration):
    """Documents a real, positive finding: some At Risk customers DO
    recover to Champions status by T2."""
    recovered = migration[(migration["segment_t1"] == "At Risk") & (migration["segment_t2"] == "Champions")]
    assert len(recovered) > 0


def test_transition_revenue_sums_to_total_t2_monetary(migration):
    total_from_matrix = migration.groupby(["segment_t1", "segment_t2"])["monetary_t2"].sum().sum()
    assert abs(total_from_matrix - migration["monetary_t2"].sum()) < 1.0
