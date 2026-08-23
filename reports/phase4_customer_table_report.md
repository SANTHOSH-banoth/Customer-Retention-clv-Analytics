# Phase 4 - Customer-Level Analytical Table Report

## Objective

Aggregate cleaned, classified transactions (Phases 2-3) up to the customer
grain, with explicit protection against the project's most-warned-about
mistake: counting line items as orders.

Implementation: `src/customer_table.py`, tested in
`src/test_customer_table.py` (7 tests, all passing). Full pipeline test
suite: **20/20 passing** (Phases 2-4 combined).

## Grain Rule

An **order** is a distinct `Invoice` number that contains at least one
`sale`, `cancellation`, or `free_item` line. `order_count` is built from
`Invoice.nunique()` — never from `len(rows)`. This was directly tested:
`test_order_count_equals_distinct_invoices_manually` recomputes order count
independently for 20 random customers and asserts an exact match against
the table.

Invoices consisting **only** of `non_merchandise` / `stock_correction` /
`stock_inbound_no_customer` / `bad_debt_adjustment` rows (5,947 invoices,
found during Phase 4 investigation — e.g. a postage-only or bank-charge-only
line with no actual product) contribute **zero** orders, since no real
merchandise transaction occurred on them.

## Result

| Metric | Value |
|---|---:|
| Customers in final table | 5,921 |
| Unique Customer IDs in raw data | 5,942 |
| Customers dropped (see below) | 21 |

### Customer-level summary statistics (measured)

| Metric | Mean | Median | Max |
|---|---:|---:|---:|
| order_count | 7.49 | 4 | 502 |
| sale_order_count | 6.21 | 3 | 392 |
| net_revenue | £2,791.69 | £842.40 | £599,443.64 |
| active_months | 4.31 | 3 | 25 |

The distributions are heavily right-skewed (mean well above median on
every revenue/order metric) — expected for retail customer data, and a
direct signal that RFM/segmentation in Phase 5-7 must not assume normality.

## Two Edge Cases Found and Explicitly Handled

**1. 21 customers dropped entirely.**
Their *only* recorded activity is `non_merchandise` rows (e.g. a
postage-only or bank-charge-only line with no product ever purchased or
returned). Example: Customer 12555's only row across the whole dataset is
a `non_merchandise` charge. These customers have no real purchase
behavior to analyze and are correctly absent from the customer table.
This is a deliberate exclusion, not an oversight — flagged here so it's
auditable.

**2. 53 customers with cancellation activity but no sale rows at all.**
Their only recorded transactions are `cancellation` rows — meaning they
returned something whose original sale is not present in this dataset
(most likely purchased before the data's start date, or their original
sale row was itself later reclassified). These customers:
- have `first_purchase_date` / `last_purchase_date` = null (there's no
  sale to date)
- have negative `net_revenue` (pure returns, no offsetting sale)
- are **retained** in the table, not dropped, because dropping them would
  hide real returned value from the business — this is directly tested
  (`test_customers_with_only_cancellations_are_retained`)
- **Flag for Phase 5:** these 53 customers cannot get a Recency value
  under the "days since last sale" definition, since there is no sale
  date. This needs an explicit decision in Phase 5, not a silent NaN.

Additionally, **74 customers have negative net_revenue** overall (returned
more value than they currently show as purchased — e.g. bought earlier,
outside full visibility, then returned within the observed window) and
**19 customers have net_revenue exactly £0** (e.g. Customer 13256, whose
only row is a single `free_item`, quantity 12, price £0).

## Validation Performed

1. `test_order_count_is_not_row_count` — for a real multi-line invoice,
   confirms the resulting `order_count` isn't inflated toward the line
   count.
2. `test_order_count_equals_distinct_invoices_manually` — independently
   recomputes `order_count` for 20 random customers via `nunique()` and
   requires an exact match.
3. `test_no_duplicate_customers` — one row per customer.
4. `test_net_revenue_matches_phase3_total` — **the sum of every
   customer's `net_revenue` must equal Phase 3's Net Merchandise Sales
   total.** This is the reconciliation test that proves customer-level
   aggregation didn't silently lose or double-count any revenue relative
   to the transaction-level definition. Passing, within £1 float
   tolerance.
5. `test_first_purchase_not_after_last_purchase` — basic date sanity.
6. `test_item_count_never_negative` — item_count only counts kept units
   (sale + free_item), so it can never go negative by construction;
   tested to catch regressions.
7. `test_customers_with_only_cancellations_are_retained` — protects the
   Phase 4 decision documented above from being silently reversed by a
   future edit.

## What This Means Going Into Phase 5

The customer table is ready to serve as the foundation for RFM. Two
specific carry-forward decisions for Phase 5:

- **Recency** cannot be computed the same way for the 53 cancellation-only
  customers as for everyone else (no `last_purchase_date`). Phase 5 must
  decide explicitly whether to exclude them from RFM, assign them an
  extreme/flag value, or use a different date field — not silently
  produce NaN recency scores.
- The right-skewed distributions confirmed here (order_count, net_revenue)
  reinforce that Phase 6 (RFM Validation) needs real distributional
  investigation before committing to quantile cutoffs.
