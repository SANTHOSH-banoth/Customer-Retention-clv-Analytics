"""
Phase 6 - RFM Validation

Investigates the RFM distributions computed in Phase 5 before any
segmentation cutoffs are chosen. Produces the numbers behind
reports/phase6_rfm_validation_report.md. No outliers are removed here --
every extreme value is investigated and classified (data error /
legitimate / unusual behavior) rather than dropped automatically.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

RFM_PKL = Path("data/processed/rfm.pkl")
CUSTOMERS_PKL = Path("data/processed/customers.pkl")
TXN_PKL = Path("data/processed/transactions_with_revenue.pkl")


def skewness_report(rfm: pd.DataFrame) -> dict:
    return {
        col: {"skew": stats.skew(rfm[col]), "kurtosis": stats.kurtosis(rfm[col])}
        for col in ["recency_days", "frequency", "monetary"]
    }


def investigate_negative_monetary(rfm: pd.DataFrame, txn: pd.DataFrame) -> dict:
    neg_custs = rfm.loc[rfm["monetary"] < 0, "customer_id"].tolist()
    manual_driven = 0
    for cid in neg_custs:
        sub = txn[txn["Customer ID"] == cid]
        manual_neg = -sub.loc[
            (sub["StockCode"] == "M") & (sub["transaction_type"] == "cancellation"), "line_value"
        ].sum()
        total_neg = -sub.loc[sub["transaction_type"] == "cancellation", "line_value"].sum()
        if total_neg > 0 and manual_neg / total_neg > 0.5:
            manual_driven += 1

    total_neg_monetary = rfm.loc[rfm["monetary"] < 0, "monetary"].sum()
    return {
        "n_negative": len(neg_custs),
        "n_manual_driven": manual_driven,
        "pct_manual_driven": manual_driven / len(neg_custs) * 100 if neg_custs else 0,
        "total_negative_monetary": total_neg_monetary,
        "pct_of_total_net_revenue": total_neg_monetary / rfm["monetary"].sum() * 100,
    }


def snapshot_sensitivity(rfm: pd.DataFrame) -> dict:
    offsets = {"no_offset": 0, "plus_7d": 7, "plus_30d": 30}
    base = pd.Timestamp("2011-12-10")
    base_recency = rfm["recency_days"]
    base_q = pd.qcut(base_recency, 5, labels=False, duplicates="drop")

    results = {}
    for name, offset in offsets.items():
        alt_snapshot = base + pd.Timedelta(days=offset - 1)  # -1 undoes the main +1
        alt_recency = (alt_snapshot - rfm["last_purchase_date"].dt.normalize()).dt.days
        alt_q = pd.qcut(alt_recency, 5, labels=False, duplicates="drop")
        pct_same = (base_q == alt_q).mean() * 100
        corr = base_recency.corr(alt_recency, method="spearman")
        results[name] = {"pct_same_quintile": pct_same, "spearman_corr": corr}
    return results


def returns_customer_comparison(rfm: pd.DataFrame, customers: pd.DataFrame) -> dict:
    merged = rfm.merge(customers[["customer_id", "cancellation_order_count"]], on="customer_id")
    merged["has_returns"] = merged["cancellation_order_count"] > 0

    u_freq, p_freq = stats.mannwhitneyu(
        merged.loc[merged["has_returns"], "frequency"],
        merged.loc[~merged["has_returns"], "frequency"],
    )
    u_mon, p_mon = stats.mannwhitneyu(
        merged.loc[merged["has_returns"], "monetary"],
        merged.loc[~merged["has_returns"], "monetary"],
    )
    return {
        "pct_with_returns": merged["has_returns"].mean() * 100,
        "median_by_group": merged.groupby("has_returns")[["recency_days", "frequency", "monetary"]]
        .median()
        .to_dict(),
        "mannwhitney_p_frequency": p_freq,
        "mannwhitney_p_monetary": p_mon,
    }


def single_purchase_profile(rfm: pd.DataFrame) -> dict:
    single = rfm[rfm["frequency"] == 1]
    multi = rfm[rfm["frequency"] > 1]
    return {
        "n_single": len(single),
        "pct_single": len(single) / len(rfm) * 100,
        "median_recency_single": single["recency_days"].median(),
        "median_recency_multi": multi["recency_days"].median(),
        "median_monetary_single": single["monetary"].median(),
        "median_monetary_multi": multi["monetary"].median(),
    }


def main():
    rfm = pd.read_pickle(RFM_PKL)
    customers = pd.read_pickle(CUSTOMERS_PKL)
    txn = pd.read_pickle(TXN_PKL)

    print("SKEWNESS / KURTOSIS")
    for col, stats_d in skewness_report(rfm).items():
        print(f"  {col}: skew={stats_d['skew']:.2f}, kurtosis={stats_d['kurtosis']:.2f}")

    print("\nNEGATIVE MONETARY INVESTIGATION")
    for k, v in investigate_negative_monetary(rfm, txn).items():
        print(f"  {k}: {v}")

    print("\nSNAPSHOT DATE SENSITIVITY")
    for k, v in snapshot_sensitivity(rfm).items():
        print(f"  {k}: {v}")

    print("\nRETURNS-CUSTOMER COMPARISON")
    for k, v in returns_customer_comparison(rfm, customers).items():
        print(f"  {k}: {v}")

    print("\nSINGLE-PURCHASE PROFILE")
    for k, v in single_purchase_profile(rfm).items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
