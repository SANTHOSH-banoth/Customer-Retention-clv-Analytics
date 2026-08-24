# Phase 10 - Cohort Definition Report

## Objective

Assign every customer to an acquisition-month cohort and build the
monthly activity table that Phase 11's retention matrix will be built
from — with an explicit, tested definition of "active."

Implementation: `src/cohorts.py`, tested in `src/test_cohorts.py` (7
tests, all passing). Full pipeline: **56/56 tests passing.**

## Definitions

- **Cohort** = calendar month of a customer's first `sale` transaction
  (`customers.first_purchase_date` from Phase 4).
- **Active in month M** = at least one `sale` transaction in month M.
  Cancellations do **not** count as activity, mirroring the Frequency
  definition from Phase 5 — a customer who only returned something in a
  given month, with no new purchase, is not "active" that month.
  Verified directly by `test_cancellation_only_activity_does_not_count_as_active_month`.
- **months_since_first_purchase** = whole calendar months between the
  activity month and the cohort month.

## Population

**5,868 customers** assigned to a cohort — the same population from Phase
5 (RFM-valid). The 53 cancellation-only customers excluded there have no
`first_purchase_date` and structurally cannot belong to a cohort; this is
the same exclusion carried forward, not a new decision.

## Result

**25 monthly cohorts, December 2009 through December 2011** (matching the
dataset's full date range).

```
2009-12    952
2010-01    369
2010-02    374
2010-03    445
2010-04    295
2010-05    255
2010-06    270
2010-07    186
2010-08    163
2010-09    243
2010-10    377
2010-11    325
2010-12     76
2011-01     71
2011-02    125
2011-03    179
2011-04    106
2011-05    111
2011-06    108
2011-07    102
2011-08    107
2011-09    189
2011-10    221
2011-11    191
2011-12     28
```

## Important Finding: The First Cohort Is Not a Real Acquisition Cohort

**December 2009 has 952 customers — roughly 2.9x the size of the average
early-2010 cohort** (369-445 in the following months). This was checked
directly (`test_first_cohort_is_anomalously_large`) rather than assumed.

**What this means:** the dataset's observation window starts on
2009-12-01, but many of these "December 2009" customers almost certainly
made their *actual* first purchase earlier, before the data collection
began. Because we can only see what's in this extract, their first
*visible* purchase gets misclassified as their first purchase overall.
This is a form of **left-censoring** — a known limitation of any
snapshot-window dataset, not a data-quality error to fix.

**Decision: keep the December 2009 cohort in the cohort table, but flag
it explicitly wherever cohort-based conclusions are drawn (Phase 12-13).**
Retention curves computed for this cohort will look different from later
cohorts for a structural reason (it's a mix of genuinely new and
long-tenured pre-existing customers), not necessarily because December
2009 was a materially different acquisition month. This should not be
over-interpreted as a real business finding without that caveat attached.

## Sanity Check

Every one of the 5,868 customers is confirmed active in their own cohort
month (`months_since_first_purchase == 0`), by construction and verified
by test — this is the foundation Phase 11's retention percentages are
computed against, so it needed to be airtight before moving on.

## What This Means Going Into Phase 11

- The cohort assignment and monthly activity table are ready to pivot
  into the retention matrix (rows = cohort month, columns = months since
  acquisition, values = % of the cohort active).
- December 2009 needs a visible caveat in any retention-matrix
  visualization or interpretation.
- Later cohorts (e.g. 2011-11, 2011-12) will have very few observable
  months before the dataset ends — Phase 12 must mark those cells as
  unavailable, not zero, exactly as specified in the project brief.
