# Phase 5 - RFM Foundations Report

## Objective

Implement Recency, Frequency, Monetary from first principles — no black-box
RFM library — with explicit, documented choices for snapshot date, purchase
definition, and monetary basis.

Implementation: `src/rfm.py`, tested in `src/test_rfm.py` (8 tests, all
passing). Full pipeline test suite: **28/28 passing**.

## Definitions Used

| Component | Definition | Source |
|---|---|---|
| Snapshot date | `max(InvoiceDate) + 1 day`, normalized to calendar date | Measured: 2011-12-10 |
| Recency | `snapshot_date − last_purchase_date` (days, both normalized to calendar date) | Phase 4 `last_purchase_date` (from `sale` rows only) |
| Frequency | Count of distinct `sale`-type invoices | Phase 4 `sale_order_count` |
| Monetary | Net Merchandise Sales per customer (Gross Sales − Returns) | Phase 4 `net_revenue` |

## Snapshot Date

**Measured max InvoiceDate:** 2011-12-09 12:50:00 → **snapshot_date =
2011-12-10**.

*What:* One day after the last observed transaction, not the max date
itself.
*Why:* So the most recently active customer gets Recency = 1, not 0 —
Recency = 0 is reserved as a modeling artifact for "later than any data we
have," not a value a real customer should carry.
*Assumption:* This static historical extract is treated as if "today" is
the day after data collection ended.
*What could go wrong:* If this pipeline were rerun against a live daily
feed, the snapshot date would need to move dynamically — not an issue for
this project's static dataset, but worth stating for the Phase 33 README.

## Bug Caught During Implementation

The first version of the recency calculation subtracted `last_purchase_date`
(which retains a time-of-day component, e.g. `2011-12-09 12:50:00`) from
the *normalized* snapshot date without also normalizing `last_purchase_date`.
This caused the single most-recently-active customer to get **Recency = 0**
instead of 1 — a direct violation of the design intent above.

Caught by an assertion (`recency_days.min() >= 1`) that failed loudly the
first time the script ran, rather than silently shipping a wrong value.
Fixed by normalizing both sides to whole calendar days before subtracting.
This is exactly the kind of subtle off-by-one that a "just calculate RFM
and move on" approach would miss — worth keeping in the record as evidence
this project validates its own arithmetic, not just its business logic.

## Handling the 53 Cancellation-Only Customers (flagged in Phase 4)

**Decision: excluded from the primary RFM population, not silently
dropped.** They're written to a separate `rfm_excluded.pkl` with an
explicit `exclusion_reason` column, and a dedicated test
(`test_cancellation_only_customers_excluded_not_dropped`) locks this in.

*What:* 53 of 5,921 customers (0.9%) have zero `sale` orders — their only
recorded activity is a return whose original purchase isn't visible in
this dataset — so Recency is undefined under the "days since last sale"
definition.
*Why excluded rather than assigned a value:* Any recency value we could
assign (e.g. based on the cancellation date) would represent "days since
last return," a different and misleading concept, not comparable to every
other customer's "days since last purchase."
*What could go wrong:* Every RFM-based segmentation and report from here
forward will describe 5,868 customers, not the full 5,921-customer base.
This is stated explicitly wherever RFM population size is reported.

## Measured RFM Distributions

```
                recency_days   frequency     monetary
count                5868.0       5868.0       5868.0
mean                  201.2          6.3       2827.30
std                   208.7         12.9      14024.00
min                     1.0          1.0     -10953.50
25%                    26.0          1.0        331.77
50%                    96.0          3.0        852.98
75%                   380.0          7.0       2207.01
max                   739.0        392.0     599443.64
```

- **Frequency:** 27.7% of customers (1,624) have Frequency = 1 — a single
  purchase order across the ~2-year window. This is a large one-time-buyer
  population that Phase 7 segmentation needs to handle deliberately, not
  average away.
- **Monetary:** confirmed heavily right-skewed (mean £2,827 vs. median
  £853 — mean is >3x median). 40 customers have Monetary ≤ £0, of which
  22 are strictly negative. These are real, kept as-is, not floored to
  zero, per the Phase 4/5 decision.
- **Recency:** near-uniform-looking spread from 1 to 739 days (the full
  observable range), median 96 days.

## What This Means Going Into Phase 6

None of these distributions look close to normal or symmetric. This is
the direct evidence Phase 6 (RFM Validation) needs before deciding whether
naive quintile cutoffs are appropriate, and it's exactly why Phase 0 called
for investigating 3/4/5-bin structures rather than assuming quintiles.
The large single-purchase population (27.7% at Frequency = 1) in particular
will make Frequency quintiles behave oddly — several quantile boundaries
will likely collapse onto the same value.
