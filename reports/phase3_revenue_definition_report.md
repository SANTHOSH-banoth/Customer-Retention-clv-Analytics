# Phase 3 - Revenue Definition Report

## Objective

Define transaction-level revenue explicitly rather than casually calling
`Quantity × Price` "revenue," and reconcile every defined tier back to the
raw dataset so nothing is silently lost or double-counted.

Implementation: `src/revenue.py`, tested in `src/test_revenue.py` (5 tests,
all passing).

## Definitions

| Tier | Formula | What it represents |
|---|---|---|
| Naive Raw Total | `sum(Qty × Price)` over ALL rows, no cleaning | What a shallow analysis would report. Reconciliation anchor only — never used for business reporting. |
| Gross Merchandise Sales | `sum(Qty × Price)` where `transaction_type == 'sale'` | Real product revenue from completed purchases, before returns are netted out |
| Returns | `sum(Qty × Price)` where `transaction_type == 'cancellation'`, sign flipped to positive | Value of goods returned/cancelled by customers |
| **Net Merchandise Sales** | Gross Merchandise Sales − Returns | **Primary revenue measure used going forward** (Monetary in RFM, CLV, core reporting) |
| Non-Merchandise Charges | `sum(Qty × Price)` where `transaction_type == 'non_merchandise'` | Postage, carriage, bank charges, discounts, fees — real money in some cases, but not product revenue. Tracked separately, not discarded. |
| Excluded Non-Revenue | `sum` of `bad_debt_adjustment`, `stock_correction`, `stock_inbound_no_customer` | Not money exchanged with a customer at all |

## Measured Reconciliation

```
naive_raw_total                £   19,287,250.57
gross_merchandise_sales        £   20,452,668.52
returns                        £    1,150,138.15
net_merchandise_sales          £   19,302,530.37
non_merchandise_charges        £      132,334.28
excluded_non_revenue_total     £     -147,614.08
reconciled_total               £   19,287,250.57
reconciliation_diff            £            0.00
```

The reconciled total (gross sales + signed cancellations + non-merchandise
charges + excluded categories) ties out to the naive raw total **exactly**,
to the penny. This confirms the classification from Phase 2 is exhaustive
and non-overlapping — every pound in the raw data is accounted for in
exactly one tier.

## Interpretation

- **Net Merchandise Sales (£19,302,530.37)** is close to, but not identical
  to, the naive raw total (£19,287,250.57) — a difference of about
  £15,280 (0.08%). This is coincidental, not by design: it happens because
  Non-Merchandise Charges (+£132k) and Excluded Non-Revenue (−£148k) partly
  offset each other. **This closeness should not be read as "cleaning
  barely matters."** It very much does — Gross Merchandise Sales is
  £20.45M and Returns are £1.15M, both of which are meaningfully different
  from a number nobody would see if they only computed the naive total.
- Returns represent **5.6% of Gross Merchandise Sales** — a material
  share, not a rounding error.
- Non-Merchandise Charges (£132k, largely postage) is real revenue the
  business collected but is being deliberately excluded from Net
  Merchandise Sales because it doesn't reflect product purchase behavior.
  If a future stakeholder needed total cash collected rather than product
  revenue, this figure would need to be added back — the code keeps it
  separately labeled specifically so that's possible.

## Important Analytical Decision (per the 5-question framework)

**What:** Net Merchandise Sales, not the naive total and not a
postage-inclusive total, is the revenue measure used for customer-level
Monetary, CLV, and core business reporting from here forward.

**Why:** The stakeholder (CRM/Retention Manager) needs a measure of actual
product purchase behavior. Postage/fees don't reflect purchase intent or
product value; write-offs and stock corrections aren't customer
transactions at all.

**Assumption:** Simple summation — Gross Sales minus Returns — correctly
nets out each customer's true spend. This assumes cancellation rows
accurately reverse the specific prior sale they relate to.

**What could go wrong:** This has **not** been verified at the individual
transaction-pair level (e.g. matching a specific cancellation to the exact
sale it reverses by Customer ID + StockCode + Quantity + Price). Only one
example (Phase 2 report) was spot-checked. If cancellation prices were
recorded inconsistently with the original sale price, net revenue could be
subtly biased even though the reconciliation still ties out arithmetically.

**How we'd validate it:** A future extension could attempt 1:1 matching
between cancellation rows and prior sales by the same customer/product, and
confirm price consistency. Not built in this phase, to avoid scope creep —
flagged explicitly here rather than silently assumed to be fine.

## What This Means Going Into Phase 4

Phase 4 (Customer-Level Analytical Table) will aggregate `sale`,
`cancellation`, and `free_item` rows to the customer grain, using Net
Merchandise Sales logic per customer. `non_merchandise`,
`stock_correction`, `stock_inbound_no_customer`, and `bad_debt_adjustment`
rows will be excluded from that aggregation, consistent with the customer
grain established in Phase 0.
