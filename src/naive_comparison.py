"""
Phase 22 - Return / Cancellation Impact Analysis

Builds a NAIVE customer-level RFM table using the exact anti-pattern the
project brief warns against -- `df[df.Quantity > 0]` with no transaction
classification -- and compares it directly to the CORRECT pipeline
(Phases 2-5) to quantify what proper cleaning actually changes.

NAIVE PIPELINE DEFINITION
----------------------------
1. Drop rows with missing Customer ID (a common, defensible first step
   even in a naive analysis).
2. Keep only Quantity > 0 rows -- no distinction between genuine sales,
   free items, non-merchandise (postage/fees), or anything else. This is
   the single-line "cleaning" step the brief explicitly calls out as
   something NOT to do without understanding what's being removed.
3. Monetary = sum(Quantity x Price) over these kept rows (includes
   postage/fees/non-merchandise mixed in with real sales, since a naive
   pass never separated them).
4. Frequency = distinct invoice count among kept rows (this project keeps
   the invoice-vs-line-item distinction from Phase 4 correct in BOTH
   pipelines, to cleanly isolate the returns/cancellation treatment as
   the one variable under test here, rather than re-litigating Phase 4).
5. Recency = snapshot_date - last kept-row transaction date, same
   snapshot date as the correct pipeline for a fair comparison.

Everything else (snapshot date, RFM scoring bins, segment rules) reuses
the exact logic from Phases 5 and 7, applied to the naive Monetary/
Frequency/Recency values, so the comparison isolates the effect of
returns/cancellation treatment specifically.
"""

import pandas as pd
from pathlib import Path

from rfm import get_snapshot_date
from segment import score_recency, score_frequency, score_monetary, assign_segment

RAW_PKL = Path("data/raw/online_retail_ii_combined.pkl")
CORRECT_RFM_PKL = Path("data/processed/rfm_segmented.pkl")
OUTPUT_PKL = Path("data/processed/naive_vs_correct.pkl")


def build_naive_rfm(raw: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    naive_txn = raw[(raw["Customer ID"].notna()) & (raw["Quantity"] > 0)].copy()
    naive_txn["Customer ID"] = naive_txn["Customer ID"].astype("int64")
    naive_txn["line_value"] = naive_txn["Quantity"] * naive_txn["Price"]

    g = naive_txn.groupby("Customer ID")
    naive = pd.DataFrame({
        "naive_monetary": g["line_value"].sum(),
        "naive_frequency": g["Invoice"].nunique(),
        "naive_last_purchase_date": g["InvoiceDate"].max(),
    }).reset_index().rename(columns={"Customer ID": "customer_id"})

    naive["naive_recency_days"] = (snapshot_date - naive["naive_last_purchase_date"].dt.normalize()).dt.days

    naive["r_score"] = score_recency(naive.rename(columns={"naive_recency_days": "recency_days"}))
    naive["f_score"] = score_frequency(naive.rename(columns={"naive_frequency": "frequency"}))
    naive["m_score"] = score_monetary(naive.rename(columns={"naive_monetary": "monetary"}))
    naive["naive_segment"] = naive.apply(assign_segment, axis=1)

    return naive


def compare(naive: pd.DataFrame, correct: pd.DataFrame) -> dict:
    merged = correct.merge(naive, on="customer_id", how="left")

    revenue_diff = merged["naive_monetary"].sum() - merged["monetary"].sum()
    monetary_pct_diff = (merged["naive_monetary"] - merged["monetary"]) / merged["monetary"].replace(0, pd.NA) * 100

    segment_changed = merged["segment"] != merged["naive_segment"]
    r_changed = merged["r_score_x"] != merged["r_score_y"] if "r_score_x" in merged else None

    return {
        "total_naive_monetary": merged["naive_monetary"].sum(),
        "total_correct_monetary": merged["monetary"].sum(),
        "total_revenue_diff": revenue_diff,
        "total_revenue_diff_pct": revenue_diff / merged["monetary"].sum() * 100,
        "median_pct_diff_per_customer": monetary_pct_diff.median(),
        "n_customers_compared": len(merged),
        "pct_segment_changed": segment_changed.mean() * 100,
        "n_segment_changed": segment_changed.sum(),
    }


def main():
    raw = pd.read_pickle(RAW_PKL)
    correct = pd.read_pickle(CORRECT_RFM_PKL)
    snapshot_date = get_snapshot_date()

    naive = build_naive_rfm(raw, snapshot_date)

    result = compare(naive, correct)
    print("NAIVE vs CORRECT COMPARISON")
    print("=" * 60)
    for k, v in result.items():
        print(f"  {k}: {v}")

    merged = correct.merge(naive, on="customer_id", how="left", suffixes=("_correct", "_naive"))
    merged.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")

    return merged, result


if __name__ == "__main__":
    main()
