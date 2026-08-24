"""
Phase 9 - Segment Stability

Tests whether the Phase 7 segmentation scheme is robust to reasonable
alternative choices, or whether it's fragile and would tell a different
business story under a slightly different (but equally defensible) set of
decisions.

Four sensitivity dimensions tested, each compared back to the Phase 7
baseline segmentation:

1. Quintile vs quartile cutoffs for Recency/Monetary (5-bin vs 4-bin)
2. Snapshot date (+7 days, +30 days -- reusing Phase 6's finding that
   Recency RANK is invariant, but here testing whether SEGMENT LABELS,
   which also depend on the Frequency bins and rule waterfall, are
   invariant too)
3. Returns treatment: Monetary based on gross_revenue instead of
   net_revenue (i.e., what if we had NOT netted out returns)
4. Extreme-value handling: Monetary winsorized at the 99th percentile
   before scoring, instead of using raw values
"""

import pandas as pd
import numpy as np
from pathlib import Path

from segment import score_recency, score_monetary, FREQUENCY_BINS, FREQUENCY_LABELS, assign_segment

RFM_PKL = Path("data/processed/rfm.pkl")
CUSTOMERS_PKL = Path("data/processed/customers.pkl")
BASELINE_SEG_PKL = Path("data/processed/rfm_segmented.pkl")


def score_frequency_custom(freq: pd.Series) -> pd.Series:
    return pd.cut(freq, bins=FREQUENCY_BINS, labels=FREQUENCY_LABELS).astype(int)


def build_variant_segments(rfm: pd.DataFrame, r_col: str, f_col: str, m_col: str,
                             n_bins_rm: int = 5) -> pd.Series:
    """Rebuild segments given specified recency/frequency/monetary source
    columns and number of bins for Recency/Monetary."""
    df = rfm.copy()
    r_labels = list(range(n_bins_rm, 0, -1))
    m_labels = list(range(1, n_bins_rm + 1))

    r_score = pd.qcut(df[r_col], n_bins_rm, labels=r_labels, duplicates="drop").astype(int)
    m_score = pd.qcut(df[m_col], n_bins_rm, labels=m_labels, duplicates="drop").astype(int)
    f_score = score_frequency_custom(df[f_col])

    tmp = pd.DataFrame({"r_score": r_score, "f_score": f_score, "m_score": m_score})
    return tmp.apply(assign_segment, axis=1)


def compare_to_baseline(baseline: pd.Series, variant: pd.Series, customer_ids: pd.Series) -> dict:
    changed = (baseline.values != variant.values)
    pct_changed = changed.mean() * 100

    # Which segments are most affected (highest churn rate out of that segment)?
    df = pd.DataFrame({"customer_id": customer_ids, "baseline": baseline, "variant": variant, "changed": changed})
    churn_by_segment = df.groupby("baseline")["changed"].mean().sort_values(ascending=False) * 100

    return {
        "pct_customers_changed": pct_changed,
        "n_customers_changed": int(changed.sum()),
        "churn_rate_by_baseline_segment": churn_by_segment,
    }


def variant_quartiles(rfm: pd.DataFrame) -> pd.Series:
    return build_variant_segments(rfm, "recency_days", "frequency", "monetary", n_bins_rm=4)


def variant_gross_revenue(rfm: pd.DataFrame, customers: pd.DataFrame) -> pd.Series:
    df = rfm.merge(customers[["customer_id", "gross_revenue"]], on="customer_id")
    return build_variant_segments(df, "recency_days", "frequency", "gross_revenue", n_bins_rm=5)


def variant_snapshot_shift(rfm: pd.DataFrame, days_offset: int) -> pd.Series:
    df = rfm.copy()
    base_snapshot = pd.Timestamp("2011-12-10")
    alt_snapshot = base_snapshot + pd.Timedelta(days=days_offset)
    df["recency_days_alt"] = (alt_snapshot - df["last_purchase_date"].dt.normalize()).dt.days
    return build_variant_segments(df, "recency_days_alt", "frequency", "monetary", n_bins_rm=5)


def variant_winsorized_monetary(rfm: pd.DataFrame) -> pd.Series:
    df = rfm.copy()
    cap = df["monetary"].quantile(0.99)
    df["monetary_winsorized"] = df["monetary"].clip(upper=cap)
    return build_variant_segments(df, "recency_days", "frequency", "monetary_winsorized", n_bins_rm=5)


def main():
    rfm = pd.read_pickle(RFM_PKL)
    customers = pd.read_pickle(CUSTOMERS_PKL)
    baseline = pd.read_pickle(BASELINE_SEG_PKL)

    rfm = rfm.sort_values("customer_id").reset_index(drop=True)
    baseline = baseline.sort_values("customer_id").reset_index(drop=True)
    assert (rfm["customer_id"].values == baseline["customer_id"].values).all()

    baseline_seg = baseline["segment"]

    variants = {
        "quartiles_instead_of_quintiles": variant_quartiles(rfm),
        "gross_revenue_instead_of_net": variant_gross_revenue(rfm, customers),
        "snapshot_plus_7d": variant_snapshot_shift(rfm, 7),
        "snapshot_plus_30d": variant_snapshot_shift(rfm, 30),
        "monetary_winsorized_99pct": variant_winsorized_monetary(rfm),
    }

    print("SEGMENT STABILITY RESULTS")
    print("=" * 70)
    results = {}
    for name, variant_seg in variants.items():
        res = compare_to_baseline(baseline_seg, variant_seg, rfm["customer_id"])
        results[name] = res
        print(f"\n--- {name} ---")
        print(f"  {res['n_customers_changed']} / {len(rfm)} customers changed segment ({res['pct_customers_changed']:.1f}%)")
        print(f"  Highest-churn baseline segments:")
        print(res["churn_rate_by_baseline_segment"].head(3).round(1).to_string())

    return results


if __name__ == "__main__":
    main()
