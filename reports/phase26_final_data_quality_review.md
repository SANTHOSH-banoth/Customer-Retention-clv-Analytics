# Phase 26 - Final Data Quality Review

## Objective

A final, consolidated audit across every data-quality category flagged
throughout Phases 1-25, with headline figures re-verified against the
current pipeline state to confirm nothing has drifted.

Implementation: `src/final_audit.py`, tested in `src/test_final_audit.py`
(1 test, passing). Full pipeline: **142/142 tests passing.**

## Consistency Check

8 headline figures cited across earlier phase reports were recomputed
directly from the current pipeline state and compared byte-for-byte
against their originally reported values:

```
raw_rows: expected=1,067,371, actual=1,067,371 -> OK
raw_missing_customerid_pct: expected=22.77, actual=22.77 -> OK
customers_total: expected=5,921, actual=5,921 -> OK
rfm_valid_population: expected=5,868, actual=5,868 -> OK
segments_count: expected=8, actual=8 -> OK
champions_count: expected=1,266, actual=1,266 -> OK
total_historical_revenue: expected=£16,590,567.52, actual=£16,590,567.52 -> OK
revenue_at_risk_winsorized: expected=£234,622.30, actual=£234,622.30 -> OK
```

**All 8 confirmed consistent.** This matters because this project spans
26 phases and dozens of scripts sharing intermediate pickle files — a
silent drift (e.g. a later phase accidentally overwriting an earlier
phase's output with different parameters) would be easy to miss without
this kind of explicit cross-check.

## Consolidated Audit Table

| # | Issue | Finding | Treatment | Residual Risk |
|---|---|---|---|---|
| 1 | Missing Customer ID | 22.77% of raw rows | Excluded from all customer-level analysis (Phase 4) | None — by design |
| 2 | Duplicate rows | 6.30% duplicated on business key | Investigated (Phase 2), found consistent with genuine repeated order lines, not errors — kept | **Unresolved by nature**: cannot be proven either way with this dataset; flagged as an assumption |
| 3 | Returns/cancellations | 19,494 rows, 1.76% | Classified and netted against prior sales (Phase 2-3) | Cancellation-to-sale 1:1 matching not verified at the individual-pair level (Phase 3 caveat) |
| 4 | Negative quantity (non-cancellation) | 3,457 rows, internal stock corrections | Classified separately, excluded from revenue/customer analytics (Phase 2) | None — by design |
| 5 | Zero-price rows | 2,725 rows (69 free_item, 2,656 stock_inbound) | Split by Customer ID presence; free_item kept at £0, stock_inbound excluded (Phase 2) | None — by design |
| 6 | Bookkeeping-correction outliers | Manual-code sale/cancel/re-sale/cancel sequences (17 of 22 negative-monetary customers) | Investigated, quantified (-0.20% of net revenue), documented, NOT deleted (Phase 6) | **Present in aggregates** unless specifically winsorized — Phase 19/20 winsorize for CLV-derived figures; Phase 22's naive comparison deliberately does NOT, to demonstrate the impact |
| 7 | Snapshot date choice | Day after max transaction date | Tested for sensitivity (Phase 6/9): 0% segment change at up to +30 days | None — confirmed robust |
| 8 | Incomplete cohorts | Later cohorts lack full M6/M12 history | Marked NaN, never zero-filled (Phase 11), verified by test | None — by design |
| 9 | Left-censored cohort | December 2009, 2.9x oversized (Phase 10) | Kept in cohort/retention tables (with caveat) but excluded from CLV modeling and "typical cohort" trend claims (Phase 13-16) | Requires the reader to carry the caveat forward — mitigated by repeating it in every relevant report and the dashboard |
| 10 | Small country populations | 37 of 41 countries have <30 customers | Grouped into "Other," never reported individually (Phase 21) | None — by design |
| 11 | Segment cutoff sensitivity | Quintile vs. quartile causes 24.6% segment-membership churn | Root-caused to scale-dependent score thresholds (Phase 9); aggregate revenue-concentration finding confirmed robust despite this | **Unresolved**: segment *rules* still use absolute thresholds, not percentile-relative ones — documented improvement opportunity for Phase 33 |
| 12 | CLV model assumptions | Left-censoring violates BG/NBD's full-history assumption; Gamma-Gamma independence mildly violated (ρ=0.19); 27.7% single-purchase population unusable by Gamma-Gamma | Left-censored cohort excluded from fitting; single-purchase customers get a labeled approximation, not a Gamma-Gamma output (Phase 15-16) | **CLV coverage is genuinely partial**: 30.6% of customers have no prediction at all, and the New Customers segment has 0% coverage (Phase 18) — a real, disclosed limitation, not fixed |
| 13 | Temporal validation | CLV predictions validated on a real 162-day holdout, ground truth recomputed independently of the modeling library | Mixed, honestly reported result: BG/NBD+GG wins MAE/ranking, simple baseline wins RMSE/bias (Phase 17) | None — this is the correct, disclosed state of the evidence, not a gap |

## What Changed Since the Issue Was First Flagged?

Nothing has been silently "cleaned up" between when an issue was found
and this final review — every treatment above was already decided and
implemented in the phase where it was found (Phases 2-22), and this
review confirms those decisions are still in effect and the resulting
figures are stable.

## Genuinely Unresolved Items (Not Fixed, By Choice, and Said So)

Three items above are explicitly **not** resolved, and this project does
not claim otherwise:

1. **Duplicate-row treatment** (#2) — cannot be definitively proven
   correct or incorrect with the data available.
2. **Segment cutoff sensitivity** (#11) — the underlying rule design
   (absolute score thresholds) is a known, fixable limitation not fixed
   in this project's timeframe.
3. **CLV coverage gaps** (#12) — 30.6% of customers, and 100% of the New
   Customers segment, have no CLV prediction under the current
   calibration-cutoff design.

Each of these is carried into Phase 33's Limitations section rather than
overstated as solved.

## What This Means Going Into Phase 27

The data pipeline's outputs are confirmed internally consistent across
26 phases of development. Phase 27 (Final Analytical Reconciliation)
performs the complementary check: not "do the same numbers stay the
same" but "do numbers that are SUPPOSED to reconcile across different
tables (e.g. customer-level revenue vs. transaction-level revenue vs.
dashboard figures) actually tie out" — a different, equally important
form of validation.
