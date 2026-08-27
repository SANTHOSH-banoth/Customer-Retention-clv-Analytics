"""
Phase 26 - Final Data Quality Review

Re-verifies that headline figures cited throughout Phases 1-25 have not
drifted (e.g. from a later phase's script being re-run with different
inputs), and consolidates every data-quality issue raised across the
project into one audit table. This phase does not introduce new
findings -- it checks the existing ones are still true and organizes them.
"""

import pandas as pd
from pathlib import Path

RAW_PKL = Path("data/raw/online_retail_ii_combined.pkl")
CUSTOMERS_PKL = Path("data/processed/customers.pkl")
RFM_PKL = Path("data/processed/rfm.pkl")
SEG_PKL = Path("data/processed/rfm_segmented.pkl")
RAR_PKL = Path("data/processed/revenue_at_risk.pkl")


def reverify_headline_figures() -> dict:
    raw = pd.read_pickle(RAW_PKL)
    customers = pd.read_pickle(CUSTOMERS_PKL)
    rfm = pd.read_pickle(RFM_PKL)
    seg = pd.read_pickle(SEG_PKL)
    rar = pd.read_pickle(RAR_PKL)

    return {
        "raw_rows": len(raw),
        "raw_missing_customerid_pct": round(raw["Customer ID"].isna().mean() * 100, 2),
        "customers_total": len(customers),
        "rfm_valid_population": len(rfm),
        "segments_count": seg["segment"].nunique(),
        "champions_count": int((seg["segment"] == "Champions").sum()),
        "total_historical_revenue": round(rfm["monetary"].sum(), 2),
        "revenue_at_risk_winsorized": round(rar["revenue_at_risk_winsorized"], 2),
    }


EXPECTED = {
    "raw_rows": 1_067_371,
    "raw_missing_customerid_pct": 22.77,
    "customers_total": 5921,
    "rfm_valid_population": 5868,
    "segments_count": 8,
    "champions_count": 1266,
    "total_historical_revenue": 16_590_567.52,
    "revenue_at_risk_winsorized": 234_622.30,
}


def main():
    actual = reverify_headline_figures()
    print("HEADLINE FIGURE CONSISTENCY CHECK")
    print("=" * 60)
    all_match = True
    for key, expected_val in EXPECTED.items():
        actual_val = actual[key]
        match = abs(actual_val - expected_val) < 0.01 if isinstance(expected_val, float) else actual_val == expected_val
        all_match = all_match and match
        flag = "OK" if match else "MISMATCH -- INVESTIGATE"
        print(f"  {key}: expected={expected_val}, actual={actual_val} -> {flag}")

    assert all_match, "One or more headline figures have drifted since they were originally reported"
    print("\nAll headline figures confirmed consistent with prior phase reports.")
    return actual


if __name__ == "__main__":
    main()
