"""
Phase 18 - RFM x CLV

Builds the combined customer-value view (Segment x Historical Revenue x
Predicted CLV) and investigates where RFM segment and predicted CLV
disagree.

CLV COVERAGE -- STATED EXPLICITLY, NOT HIDDEN
------------------------------------------------
Of the 5,868 RFM-valid customers, only a SUBSET has a CLV prediction, for
reasons already established in Phases 15-17:

  - 1,793 customers (30.6%) have NO CLV prediction at all: 952 from the
    excluded left-censored December 2009 cohort (Phase 15/16), plus 841
    customers acquired after the calibration cutoff (2011-06-30) who have
    no calibration-period history for BG/NBD to fit on. Labeled
    "Not yet measured" wherever they'd otherwise appear -- never
    silently imputed or defaulted to zero.
  - 1,532 customers (26.1%) have a BG/NBD purchase-count prediction but
    NO Gamma-Gamma monetary prediction (they made only one purchase in
    the calibration period, so Gamma-Gamma structurally cannot estimate
    their typical spend -- Phase 15/16 decision). A labeled APPROXIMATION
    is used for these: predicted purchases x their own single observed
    order value. This is explicitly flagged as an approximation, not a
    Gamma-Gamma output, everywhere it's used.
  - 2,543 customers (43.3%) have the full BG/NBD + Gamma-Gamma CLV
    prediction from Phase 16, validated in Phase 17.
"""

import pandas as pd
from pathlib import Path

SEG_PKL = Path("data/processed/rfm_segmented.pkl")
CLV_PKL = Path("data/processed/clv_validation.pkl")
OUTPUT_PKL = Path("data/processed/rfm_clv_combined.pkl")

HOLDOUT_DAYS = 162  # matches Phase 16/17's holdout window length


def build_combined_view() -> pd.DataFrame:
    seg = pd.read_pickle(SEG_PKL)
    clv = pd.read_pickle(CLV_PKL)

    merged = seg.merge(
        clv[["predicted_purchases_bgnbd", "predicted_clv_bgnbd_ggf", "monetary_value_cal", "prob_alive"]],
        left_on="customer_id", right_index=True, how="left",
    )

    merged["clv_coverage"] = "no_prediction"
    merged.loc[merged["predicted_purchases_bgnbd"].notna(), "clv_coverage"] = "approximated_single_purchase"
    merged.loc[merged["predicted_clv_bgnbd_ggf"].notna(), "clv_coverage"] = "full_bgnbd_gammagamma"

    # Approximated CLV for BG/NBD-only (no Gamma-Gamma) customers:
    # predicted purchases x their single observed calibration order value.
    approx_mask = merged["clv_coverage"] == "approximated_single_purchase"
    merged["predicted_clv_final"] = merged["predicted_clv_bgnbd_ggf"]
    merged.loc[approx_mask, "predicted_clv_final"] = (
        merged.loc[approx_mask, "predicted_purchases_bgnbd"] * merged.loc[approx_mask, "monetary_value_cal"]
    )
    # monetary_value_cal is 0/NaN for true single-purchase customers in
    # lifetimes' convention (it only records value for REPEAT purchases);
    # fall back further to their overall historical average order value.
    still_missing = approx_mask & merged["predicted_clv_final"].isna()
    if still_missing.any():
        merged.loc[still_missing, "predicted_clv_final"] = (
            merged.loc[still_missing, "predicted_purchases_bgnbd"]
            * (merged.loc[still_missing, "monetary"] / 1)  # single order -> monetary IS the order value
        )

    return merged


def segment_summary(merged: pd.DataFrame) -> pd.DataFrame:
    summary = merged.groupby("segment").agg(
        customers=("customer_id", "size"),
        historical_revenue=("monetary", "sum"),
        clv_coverage_n=("predicted_clv_final", lambda s: s.notna().sum()),
        avg_clv_measured=("predicted_clv_final", "mean"),
        total_clv_measured=("predicted_clv_final", "sum"),
    )
    summary["clv_coverage_pct"] = summary["clv_coverage_n"] / summary["customers"] * 100
    return summary.sort_values("historical_revenue", ascending=False)


def find_mismatches(merged: pd.DataFrame) -> dict:
    """Identify interesting historical-vs-predicted-value disagreements,
    restricted to customers with a real (non-approximated) CLV figure."""
    full = merged[merged["clv_coverage"] == "full_bgnbd_gammagamma"].copy()

    # High historical value + declining recency (At Risk / Need Attention with high monetary)
    high_hist_declining = full[(full["monetary"] > full["monetary"].quantile(0.75)) & (full["r_score"] <= 2)]

    # Low historical value + high predicted future value
    low_hist_high_pred = full[
        (full["monetary"] < full["monetary"].quantile(0.5))
        & (full["predicted_clv_final"] > full["predicted_clv_final"].quantile(0.75))
    ]

    # High RFM score + low predicted CLV
    high_rfm_low_clv = full[
        (full["rfm_score_sum"] >= 12) & (full["predicted_clv_final"] < full["predicted_clv_final"].quantile(0.25))
    ]

    # Low RFM score + unexpectedly high predicted CLV
    low_rfm_high_clv = full[
        (full["rfm_score_sum"] <= 6) & (full["predicted_clv_final"] > full["predicted_clv_final"].quantile(0.75))
    ]

    return {
        "high_historical_declining_recency": high_hist_declining,
        "low_historical_high_predicted": low_hist_high_pred,
        "high_rfm_low_clv": high_rfm_low_clv,
        "low_rfm_high_clv": low_rfm_high_clv,
    }


def main():
    merged = build_combined_view()

    print("CLV coverage breakdown:")
    print(merged["clv_coverage"].value_counts())
    print((merged["clv_coverage"].value_counts(normalize=True) * 100).round(1))

    summary = segment_summary(merged)
    print("\nSegment summary:")
    print(summary.round(1))

    mismatches = find_mismatches(merged)
    print("\nMismatch group sizes:")
    for name, group in mismatches.items():
        print(f"  {name}: {len(group)} customers")

    merged.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")

    return merged, summary, mismatches


if __name__ == "__main__":
    main()
