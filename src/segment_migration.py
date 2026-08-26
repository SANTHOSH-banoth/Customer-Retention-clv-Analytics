"""
Phase 23 - Segment Migration

SCOPE DECISION -- STATED UP FRONT, PER THE PROJECT BRIEF'S OWN INSTRUCTION
------------------------------------------------------------------------------
The brief asks for MONTHLY segment migration (a transition matrix computed
for every consecutive month pair across the ~24-month dataset). Building
that properly requires recomputing Recency/Frequency/Monetary AND
re-deriving quantile/custom-bin score boundaries AT EACH of ~24 monthly
snapshots (quantile cutoffs are population-dependent and must be
recalculated fresh at every snapshot, not reused from the final Phase 7
scoring) -- effectively rebuilding Phases 4-7 as a 24-point time series.

Per the brief's own instruction ("If this becomes disproportionately
time-consuming, document it as an optional extension rather than
sacrificing the core analysis"), this phase implements a SCOPED-DOWN,
still-genuine two-snapshot version instead:

  Snapshot T1: 2011-06-30 (reuses the Phase 16 CLV calibration cutoff --
               a meaningful, already-established date, not arbitrary)
  Snapshot T2: 2011-12-10 (the project's final snapshot date, Phase 5)

This demonstrates real, measured segment migration over a ~5.4-month gap,
with the same rigor (fresh quantile scoring at T1, not reused from T2) a
full monthly version would need at every step. A full monthly-cadence
version is documented here as a scoped extension, not built, to avoid
sacrificing time needed for the remaining core phases (24-33).
"""

import pandas as pd
from pathlib import Path

from customer_table import build_customer_table
from segment import score_recency, score_frequency, score_monetary, assign_segment

TXN_PKL = Path("data/processed/transactions_with_revenue.pkl")
FINAL_SEG_PKL = Path("data/processed/rfm_segmented.pkl")
OUTPUT_PKL = Path("data/processed/segment_migration.pkl")

T1_CUTOFF = pd.Timestamp("2011-06-30")
T1_SNAPSHOT_DATE = pd.Timestamp("2011-07-01")


def build_t1_segments(txn: pd.DataFrame) -> pd.DataFrame:
    txn_t1 = txn[txn["InvoiceDate"] <= T1_CUTOFF].copy()
    customers_t1 = build_customer_table(txn_t1)

    valid_t1 = customers_t1[customers_t1["sale_order_count"] > 0].copy()
    valid_t1["recency_days"] = (T1_SNAPSHOT_DATE - valid_t1["last_purchase_date"].dt.normalize()).dt.days
    valid_t1["frequency"] = valid_t1["sale_order_count"]
    valid_t1["monetary"] = valid_t1["net_revenue"]

    valid_t1["r_score"] = score_recency(valid_t1)
    valid_t1["f_score"] = score_frequency(valid_t1)
    valid_t1["m_score"] = score_monetary(valid_t1)
    valid_t1["segment_t1"] = valid_t1.apply(assign_segment, axis=1)

    return valid_t1[["customer_id", "recency_days", "frequency", "monetary", "segment_t1"]]


def build_migration_table(t1: pd.DataFrame, t2: pd.DataFrame) -> pd.DataFrame:
    merged = t1.merge(
        t2[["customer_id", "segment", "monetary"]].rename(
            columns={"segment": "segment_t2", "monetary": "monetary_t2"}
        ),
        on="customer_id", how="inner",  # only customers present at BOTH snapshots can "migrate"
    )
    merged = merged.rename(columns={"monetary": "monetary_t1"})
    return merged


def transition_matrix(migration: pd.DataFrame) -> pd.DataFrame:
    return pd.crosstab(migration["segment_t1"], migration["segment_t2"])


def transition_revenue(migration: pd.DataFrame) -> pd.DataFrame:
    return migration.groupby(["segment_t1", "segment_t2"])["monetary_t2"].sum().unstack(fill_value=0)


def main():
    txn = pd.read_pickle(TXN_PKL)
    t2 = pd.read_pickle(FINAL_SEG_PKL)

    t1 = build_t1_segments(txn)
    print(f"T1 (2011-07-01 snapshot) population: {len(t1)} customers")
    print(f"T2 (2011-12-10 snapshot) population: {len(t2)} customers")

    migration = build_migration_table(t1, t2)
    print(f"Customers present at BOTH snapshots (can be tracked): {len(migration)}")

    matrix = transition_matrix(migration)
    print("\nTransition matrix (counts), T1 rows -> T2 columns:")
    print(matrix)

    same_segment = (migration["segment_t1"] == migration["segment_t2"]).mean() * 100
    print(f"\n% staying in the same segment: {same_segment:.1f}%")

    # Highlight specific business-relevant transitions
    for from_seg, to_seg in [
        ("Champions", "At Risk"), ("Loyal Customers", "At Risk"),
        ("At Risk", "Champions"), ("At Risk", "Hibernating"),
        ("Hibernating", "Champions"),
    ]:
        n = len(migration[(migration["segment_t1"] == from_seg) & (migration["segment_t2"] == to_seg)])
        print(f"  {from_seg} -> {to_seg}: {n} customers")

    migration.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")

    return migration, matrix


if __name__ == "__main__":
    main()
