"""
Phase 17 - CLV Validation

Compares predicted vs actual holdout behavior using the calibration/
holdout split from Phase 16. Never uses random train/test splitting for
this time-dependent behavior -- the temporal calibration/holdout split
built in Phase 16 is used throughout.

Actual holdout purchase counts and revenue are recomputed DIRECTLY from
the transaction data (not read from lifetimes' internal holdout columns),
so the ground truth used for validation is transparent and independently
verifiable, not dependent on trusting a library's internal convention.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

from clv_model import (
    get_modeling_population, CALIBRATION_PERIOD_END, OBSERVATION_PERIOD_END,
)

TXN_PKL = Path("data/processed/transactions_with_revenue.pkl")
COHORT_PKL = Path("data/processed/cohort_assignment.pkl")
CAL_HOLDOUT_PKL = Path("data/processed/clv_calibration_holdout.pkl")
OUTPUT_VALIDATION_PKL = Path("data/processed/clv_validation.pkl")


def compute_actual_holdout(sales: pd.DataFrame) -> pd.DataFrame:
    """Recompute actual holdout order count and revenue directly from
    transactions, independent of lifetimes' internal column semantics."""
    holdout_txn = sales[
        (sales["InvoiceDate"] > CALIBRATION_PERIOD_END) & (sales["InvoiceDate"] <= OBSERVATION_PERIOD_END)
    ]
    actual = holdout_txn.groupby("Customer ID").agg(
        actual_holdout_orders=("Invoice", "nunique"),
        actual_holdout_revenue=("line_value", "sum"),
    )
    return actual


def purchase_count_errors(df: pd.DataFrame) -> dict:
    """MAE/RMSE for predicted vs actual holdout purchase counts, across
    ALL calibration customers (BG/NBD makes a prediction for everyone,
    including single-purchase-in-calibration customers)."""
    err = df["predicted_purchases_bgnbd"] - df["actual_holdout_orders"]
    mae = err.abs().mean()
    rmse = np.sqrt((err ** 2).mean())
    bias = err.mean()
    corr, p = stats.spearmanr(df["predicted_purchases_bgnbd"], df["actual_holdout_orders"])
    return {"mae": mae, "rmse": rmse, "mean_bias": bias, "spearman_corr": corr, "spearman_p": p, "n": len(df)}


def clv_ranking_quality(df: pd.DataFrame, pred_col: str) -> dict:
    """Restricted to repeat-purchase (Gamma-Gamma-eligible) customers,
    since only they have a CLV prediction. Spearman rank correlation
    between predicted CLV and actual holdout revenue."""
    sub = df.dropna(subset=[pred_col, "actual_holdout_revenue"])
    corr, p = stats.spearmanr(sub[pred_col], sub["actual_holdout_revenue"])
    return {"n": len(sub), "spearman_corr": corr, "spearman_p": p}


def decile_capture(df: pd.DataFrame, pred_col: str, actual_col: str = "actual_holdout_revenue") -> pd.DataFrame:
    """For the top N% of customers by predicted CLV, what % of total
    actual holdout revenue do they capture? Compared to what a random
    selection of the same size would capture (i.e. their population share)."""
    sub = df.dropna(subset=[pred_col, actual_col]).copy()
    sub["decile"] = pd.qcut(sub[pred_col], 10, labels=False, duplicates="drop")
    total_actual = sub[actual_col].sum()

    result = sub.groupby("decile").agg(
        n_customers=(actual_col, "size"),
        actual_revenue=(actual_col, "sum"),
    )
    result["pct_of_customers"] = result["n_customers"] / result["n_customers"].sum() * 100
    result["pct_of_actual_revenue"] = result["actual_revenue"] / total_actual * 100
    result = result.sort_index(ascending=False)  # decile 9 (highest predicted) first
    return result


def clv_error_metrics(df: pd.DataFrame, pred_col: str) -> dict:
    sub = df.dropna(subset=[pred_col, "actual_holdout_revenue"])
    err = sub[pred_col] - sub["actual_holdout_revenue"]
    mae = err.abs().mean()
    rmse = np.sqrt((err ** 2).mean())
    bias = err.mean()
    return {"n": len(sub), "mae": mae, "rmse": rmse, "mean_bias": bias}


def main():
    txn = pd.read_pickle(TXN_PKL)
    cohort = pd.read_pickle(COHORT_PKL)
    cal_holdout = pd.read_pickle(CAL_HOLDOUT_PKL)

    sales = get_modeling_population(txn, cohort)
    actual = compute_actual_holdout(sales)

    df = cal_holdout.join(actual, how="left")
    df["actual_holdout_orders"] = df["actual_holdout_orders"].fillna(0)
    df["actual_holdout_revenue"] = df["actual_holdout_revenue"].fillna(0.0)

    print("=" * 70)
    print("1. PURCHASE COUNT VALIDATION (BG/NBD, all calibration customers)")
    print("=" * 70)
    pc_errors = purchase_count_errors(df)
    for k, v in pc_errors.items():
        print(f"  {k}: {v}")

    print()
    print("=" * 70)
    print("2. CLV RANKING QUALITY (repeat-purchase customers only)")
    print("=" * 70)
    for pred_col, label in [("predicted_clv_bgnbd_ggf", "BG/NBD + Gamma-Gamma"), ("baseline_clv", "Simple baseline")]:
        rank_res = clv_ranking_quality(df, pred_col)
        print(f"  {label}: n={rank_res['n']}, spearman_corr={rank_res['spearman_corr']:.3f}, p={rank_res['spearman_p']:.2e}")

    print()
    print("=" * 70)
    print("3. CLV ERROR METRICS (£, repeat-purchase customers only)")
    print("=" * 70)
    for pred_col, label in [("predicted_clv_bgnbd_ggf", "BG/NBD + Gamma-Gamma"), ("baseline_clv", "Simple baseline")]:
        err_res = clv_error_metrics(df, pred_col)
        print(f"  {label}: {err_res}")

    print()
    print("=" * 70)
    print("4. DECILE CAPTURE (BG/NBD + Gamma-Gamma)")
    print("=" * 70)
    decile_bgggf = decile_capture(df, "predicted_clv_bgnbd_ggf")
    print(decile_bgggf.round(1))

    print()
    print("=" * 70)
    print("5. DECILE CAPTURE (Simple baseline)")
    print("=" * 70)
    decile_baseline = decile_capture(df, "baseline_clv")
    print(decile_baseline.round(1))

    df.to_pickle(OUTPUT_VALIDATION_PKL)
    print(f"\nSaved -> {OUTPUT_VALIDATION_PKL}")

    return df, pc_errors, decile_bgggf, decile_baseline


if __name__ == "__main__":
    main()
