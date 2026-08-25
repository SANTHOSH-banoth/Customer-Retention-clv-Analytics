"""
Phase 19 - Revenue at Risk

Defines and calculates revenue-at-risk with an explicit, tested separation
between three concepts that are easy to blur together:

  Historical Revenue   = money already earned (Phase 3/5 Net Merchandise
                          Sales, customer-level). A fact, not an estimate.
  Predicted Future Value = BG/NBD + Gamma-Gamma's expected value over the
                          162-day holdout-equivalent window (Phase 16),
                          available for 69.4% of customers only (Phase 18).
                          A MODEL OUTPUT, not a fact -- carries the
                          validated error characteristics from Phase 17.
  Revenue at Risk       = the portion of Predicted Future Value associated
                          with customers whose RFM segment indicates
                          declining engagement (At Risk, About To Sleep,
                          Hibernating, Need Attention). NOT historical
                          revenue, NOT a guarantee of loss -- an estimate
                          of near-term value that could be lost if these
                          customers churn, conditional on the CLV model's
                          accuracy (Phase 17 findings apply here).

AT-RISK POPULATION DEFINITION
--------------------------------
What: RFM segments {At Risk, About To Sleep, Hibernating, Need Attention}
      -- i.e. every segment except Champions, Loyal Customers, Potential
      Loyalists, and New Customers.
Why RFM-segment-based rather than purely prob_alive-based: RFM segment
      covers 100% of the 5,868-customer population; a prob_alive<0.5
      threshold (the more rigorous, model-based definition) only covers
      the 4,075 customers with BG/NBD predictions, and produces a very
      small population (132 customers, 3.2% of covered customers) that
      would badly understate the true at-risk population. RFM segment is
      used as the population definition; predicted CLV (where available)
      supplies the £ magnitude.
What could go wrong: RFM segment recency thresholds were shown to be
      somewhat sensitive to bin-count choice (Phase 9); this population
      definition inherits that sensitivity.

OUTLIER SENSITIVITY -- DIRECTLY ADDRESSING THE PHASE 18 CAUTION
--------------------------------------------------------------------
Phase 18 found that Customer 12346's predicted CLV (£16,799) is an
extreme outlier driven by a single large sale-then-cancelled transaction,
not genuine value. This phase computes Revenue at Risk BOTH with raw
predicted CLV values AND with values winsorized at the 99th percentile,
and reports both, rather than letting one customer's data artifact
silently dominate a business figure.
"""

import pandas as pd
from pathlib import Path

MERGED_PKL = Path("data/processed/rfm_clv_combined.pkl")
OUTPUT_PKL = Path("data/processed/revenue_at_risk.pkl")

AT_RISK_SEGMENTS = ["At Risk", "About To Sleep", "Hibernating", "Need Attention"]
WINSORIZE_PCT = 0.99


def compute_revenue_at_risk(merged: pd.DataFrame) -> dict:
    total_historical = merged["monetary"].sum()

    at_risk_pop = merged[merged["segment"].isin(AT_RISK_SEGMENTS)]
    at_risk_historical = at_risk_pop["monetary"].sum()

    covered = merged[merged["predicted_clv_final"].notna()]
    total_predicted = covered["predicted_clv_final"].sum()

    at_risk_covered = at_risk_pop[at_risk_pop["predicted_clv_final"].notna()]
    at_risk_predicted_raw = at_risk_covered["predicted_clv_final"].sum()

    cap = covered["predicted_clv_final"].quantile(WINSORIZE_PCT)
    at_risk_predicted_winsorized = at_risk_covered["predicted_clv_final"].clip(upper=cap).sum()
    total_predicted_winsorized = covered["predicted_clv_final"].clip(upper=cap).sum()

    return {
        "total_historical_revenue": total_historical,
        "at_risk_population_size": len(at_risk_pop),
        "at_risk_population_pct": len(at_risk_pop) / len(merged) * 100,
        "at_risk_historical_revenue": at_risk_historical,
        "at_risk_historical_pct_of_total": at_risk_historical / total_historical * 100,
        "at_risk_clv_coverage_n": len(at_risk_covered),
        "at_risk_clv_coverage_pct": len(at_risk_covered) / len(at_risk_pop) * 100,
        "total_predicted_future_value": total_predicted,
        "revenue_at_risk_raw": at_risk_predicted_raw,
        "revenue_at_risk_pct_of_predicted_raw": at_risk_predicted_raw / total_predicted * 100,
        "winsorize_cap_99pct": cap,
        "revenue_at_risk_winsorized": at_risk_predicted_winsorized,
        "total_predicted_winsorized": total_predicted_winsorized,
        "revenue_at_risk_pct_of_predicted_winsorized": at_risk_predicted_winsorized / total_predicted_winsorized * 100,
    }


def main():
    merged = pd.read_pickle(MERGED_PKL)
    result = compute_revenue_at_risk(merged)

    print("REVENUE AT RISK -- RESULTS")
    print("=" * 60)
    for k, v in result.items():
        if isinstance(v, float):
            print(f"{k}: {v:,.2f}")
        else:
            print(f"{k}: {v}")

    pd.Series(result).to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")

    return result


if __name__ == "__main__":
    main()
