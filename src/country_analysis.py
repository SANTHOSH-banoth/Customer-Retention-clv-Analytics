"""
Phase 21 - Country Analysis

Breaks down customer behavior, revenue, and CLV by country, with an
explicit minimum sample threshold so tiny country populations aren't
overinterpreted as if they were statistically reliable.

MINIMUM SAMPLE THRESHOLD
--------------------------
What: countries with fewer than 30 RFM-valid customers are excluded from
      comparative analysis and grouped into "Other (small sample)".
Why: Phase 1 already established the UK is 91.1% of the customer base
     (5,348 of 5,868). Of the other 40 countries, most have single or
     low-double-digit customer counts (e.g. Japan: 10, USA: 8) -- far too
     few to draw any reliable conclusion about "how customers from this
     country behave." A threshold of 30 is a conventional rule-of-thumb
     minimum for even roughly stable summary statistics, not a
     statistically derived optimum -- stated as a judgment call.
What this means concretely: only 4 countries qualify for individual
     reporting -- United Kingdom (5,348), Germany (106), France (94),
     Spain (35) -- covering 5,583 of 5,868 customers (95.1%). The
     remaining 285 customers across 37 countries are grouped, not
     dropped, and reported in aggregate only.
"""

import pandas as pd
from pathlib import Path

MERGED_PKL = Path("data/processed/rfm_clv_combined.pkl")
CUSTOMERS_PKL = Path("data/processed/customers.pkl")
OUTPUT_PKL = Path("data/processed/country_analysis.pkl")

MIN_SAMPLE_SIZE = 30
OTHER_LABEL = "Other (small sample, <30 customers)"


def build_country_table(merged: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    df = merged.merge(customers[["customer_id", "order_count"]], on="customer_id")

    counts = df["country"].value_counts()
    qualifying = set(counts[counts >= MIN_SAMPLE_SIZE].index)
    df["country_group"] = df["country"].where(df["country"].isin(qualifying), OTHER_LABEL)

    # "Active" proxy for a simple, consistent retention-like measure across
    # countries: recency_days <= 90 (purchased within the last 3 months of
    # the observation window)
    df["is_recently_active"] = df["recency_days"] <= 90

    return df


def country_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("country_group").agg(
        customers=("customer_id", "size"),
        total_orders=("order_count", "sum"),
        total_revenue=("monetary", "sum"),
        avg_order_value=("monetary", lambda s: s.sum() / df.loc[s.index, "order_count"].sum()),
        avg_recency_days=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        pct_recently_active=("is_recently_active", "mean"),
        clv_coverage_pct=("predicted_clv_final", lambda s: s.notna().mean()),
        avg_clv_measured=("predicted_clv_final", "mean"),
    )
    summary["pct_recently_active"] *= 100
    summary["clv_coverage_pct"] *= 100
    return summary.sort_values("total_revenue", ascending=False)


def main():
    merged = pd.read_pickle(MERGED_PKL)
    customers = pd.read_pickle(CUSTOMERS_PKL)

    df = build_country_table(merged, customers)
    summary = country_summary(df)

    print(f"Qualifying countries (n>={MIN_SAMPLE_SIZE}): {sorted(set(df['country_group']) - {OTHER_LABEL})}")
    print(f"\nCountry summary:")
    print(summary.round(2))

    df.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")

    return df, summary


if __name__ == "__main__":
    main()
