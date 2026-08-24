# Phase 11 - Cohort Retention Table Report

## Objective

Pivot the Phase 10 monthly activity table into the cohort retention
matrix (rows = cohort month, columns = months since acquisition, values =
% of cohort active), validate the calculation manually, and correctly mark
unavailable future periods instead of filling them with zero.

Implementation: `src/retention_matrix.py`, tested in
`src/test_retention_matrix.py` (7 tests, all passing). Full pipeline:
**63/63 tests passing.**

## Manual Validation

Before trusting the pivot/groupby machinery, one cohort (2011-06, chosen
because it's mid-sized and mid-dataset) was recomputed directly from the
raw activity table, bypassing the pivot entirely:

```
Cohort 2011-06, size = 108
Manual M0 = 108   (matches pivot: 108)
Manual M1 = 25    (matches pivot: 25)
Manual M2 = 23    (matches pivot: 23)
```

Exact match, asserted in code (`test_manual_validation_matches_pivot`),
not just eyeballed.

## The Unavailable-vs-Zero Rule, Verified

This was the single most important rule for this phase, and it was tested
directly rather than trusted by inspection:

- **M0 = 100% for every cohort**, by definition (confirmed for all 25
  cohorts).
- **December 2011 cohort:** only M0 is observable (100%); every column
  from M1 onward is `NaN`, not `0` — there simply isn't a December 2012
  in this dataset to measure M12 against, and there isn't even a January
  2012 to measure M1 against.
- **November 2011 cohort:** exactly M0 and M1 are observable; M2 onward
  is `NaN`.
- **December 2009 cohort:** the *only* cohort with zero unavailable
  cells — it has existed for the entire 25-month observation window, so
  every offset up to M24 has a real, computed value (never NaN).

## Retention Summary (available cohorts only)

| Milestone | Cohorts with data | Mean retention | Median retention |
|---|---:|---:|---:|
| M1 | 24 of 25 | 21.0% | 20.4% |
| M3 | 22 of 25 | 21.6% | 20.0% |
| M6 | 19 of 25 | 17.9% | 16.0% |
| M12 | 13 of 25 | 18.2% | 15.3% |

**Important caveat on these averages:** they are computed only over
cohorts that actually have a value at that milestone — later cohorts
without enough elapsed time are correctly excluded, not zero-filled. This
means, for example, the M12 average is based on only the 13 *earliest*
cohorts (Dec 2009 through Dec 2010), which is a real selection effect: if
retention behavior changed over time (Phase 13 will investigate this),
the M12 average is systematically biased toward whatever early cohorts
did, not a representative cross-section of "the business."

## Two Data-Quality Caveats Carried Forward From Phase 10 — Restated Here Because They Directly Affect This Table

1. **December 2009 (M0) column is inflated by left-censoring** (Phase 10)
   — its retention curve should not be read as representative of a
   genuine acquisition month.
2. **The last calendar month, December 2011, contains only 9 days of
   data** (max date 2011-12-09, per Phase 1). Any retention percentage
   that uses December 2011 as the *activity* month (not just as a cohort)
   is measured against a shorter purchase opportunity window than every
   other month. This affects the last diagonal of the matrix broadly, not
   just the December 2011 cohort's own row — e.g. a customer from an
   earlier cohort who would otherwise have purchased in December 2011 has
   less time to do so than in any prior month, which could slightly
   understate the very last column's retention across all rows. Flagged
   here for transparency; not corrected, since there's no principled way
   to extrapolate the missing 21 days without fabricating data.

## What This Means Going Into Phase 12

The retention matrix is validated and ready for visualization (heatmap,
retention curves, M1/M3/M6/M12 comparisons). Phase 12's visualizations
must continue to respect the NaN-vs-zero distinction established here —
any heatmap or chart that silently renders NaN as 0 would misrepresent
"we don't have this data yet" as "this cohort completely churned," which
would be a serious, avoidable misstatement.
