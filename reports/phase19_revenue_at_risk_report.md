# Phase 19 - Revenue at Risk Report

## Objective

Define revenue-at-risk rigorously, with a hard separation between money
already earned, model-predicted future value, and the specific slice of
predicted value tied to declining-engagement customers — and directly
address the Phase 18 caution about outlier-driven CLV distortion rather
than letting it silently affect a headline business number.

Implementation: `src/revenue_at_risk.py`, tested in
`src/test_revenue_at_risk.py` (6 tests, all passing). Full pipeline:
**105/105 tests passing.**

## Three Distinct Concepts — Not Interchangeable

| Concept | Definition | Basis |
|---|---|---|
| **Historical Revenue** | Money already earned | Fact (Phase 3/5 Net Merchandise Sales) |
| **Predicted Future Value** | Expected value, 162-day window | Model output (Phase 16), validated with real error characteristics (Phase 17) |
| **Revenue at Risk** | Predicted future value tied to customers showing declining-engagement signals | Model output × RFM segment population — an estimate, not a guarantee |

## At-Risk Population Definition

RFM segments **At Risk, About To Sleep, Hibernating, Need Attention**
(everything except Champions, Loyal Customers, Potential Loyalists, and
New Customers). This covers **100% of the customer base** (unlike a pure
`prob_alive < 0.5` model-based cutoff, which was tested and found to
cover only 132 customers — 3.2% of the CLV-covered population — far too
narrow to represent "at risk" for business purposes).

## Measured Results

```
Total historical revenue (all 5,868 customers):     £16,590,567.52

At-risk population:                                  2,802 customers (47.8%)
At-risk historical revenue:                          £1,677,818.48 (10.1% of total historical)
At-risk customers with a CLV prediction:              2,287 of 2,802 (81.6%)

Total predicted future value (all CLV-covered):       £1,414,891.40
Revenue at risk (raw):                                £255,295.44  (18.0% of predicted total)
Revenue at risk (winsorized at 99th percentile):      £234,622.30  (18.3% of predicted total)
```

## Directly Addressing the Phase 18 Outlier Caution

Phase 18 flagged that Customer 12346's predicted CLV (£16,799, driven by
a sold-then-cancelled 74,215-unit order) was an extreme, data-artifact-
driven outlier. This phase tested its effect on Revenue at Risk directly
rather than assuming it away:

- **In absolute £ terms, the outlier's effect is real and non-trivial:**
  winsorizing at the 99th percentile reduces the raw figure by
  **£20,673** (£255,295 → £234,622) — verified by test
  (`test_outlier_customer_meaningfully_affects_raw_but_not_ratio`), most
  of which is directly attributable to this one customer.
- **The overall AT-RISK SHARE of total predicted value is comparatively
  stable** (18.0% raw vs. 18.3% winsorized — under 1 percentage point of
  difference), because winsorizing affects both the at-risk subgroup and
  the overall total similarly.

**This means: don't quote the raw £255,295 figure to a stakeholder
without disclosing that ~£20,673 of it (8%) comes from a single flagged
data artifact.** The winsorized figure, **£234,622**, is the more
defensible number to present as the headline "revenue at risk" estimate,
with the raw figure available as a sensitivity check.

## Important Caveats — Stated Explicitly, Not Buried

1. **This is not guaranteed lost revenue.** It is an estimate of near-term
   predicted value associated with customers whose engagement signals
   suggest elevated churn risk — conditional on the CLV model's accuracy,
   which Phase 17 found to be moderate (ranking correlation ~0.6, mixed
   error-metric performance vs. a simple baseline).
2. **18.4% of the at-risk population (515 of 2,802 customers) has no CLV
   prediction at all** and therefore contributes £0 to the £255,295/
   £234,622 figures above — not because they have no future value, but
   because this project genuinely has not measured it (Phase 15/16
   exclusions: left-censored cohort, post-calibration-cutoff customers).
   **The true revenue-at-risk figure, if full CLV coverage existed, would
   almost certainly be higher than what's reported here** — this is a
   documented lower bound, not a complete estimate.
3. **The two time bases are not directly comparable.** Historical revenue
   accumulates over ~2 years; predicted future value is a 162-day window.
   Any comparison between them (e.g. "at-risk revenue is X% of historical
   revenue") is for scale reference only, not an apples-to-apples ratio.

## What This Means Going Into Phase 20

Phase 20's retention strategy simulation should use the **winsorized
£234,622 figure** (or the underlying customer-level winsorized predicted
CLV) as the basis for estimating potential recovered value under
different targeting strategies, with the coverage caveat above carried
forward explicitly — the simulation's addressable population is at most
the 2,287 at-risk customers with a CLV prediction, not the full 2,802.
