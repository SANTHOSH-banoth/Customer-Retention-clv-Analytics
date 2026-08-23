# Phase 2 - Transaction Cleaning / Classification Report

## Objective

Classify every raw transaction line into an explicit, evidence-based category
instead of applying a blind filter (e.g. `df[df.Quantity > 0]`). No rows are
deleted in this phase -- every row keeps its data plus a new
`transaction_type` label. Downstream phases (starting with Phase 3, Revenue
Definition) decide which categories flow into which calculation.

Implementation: `src/clean.py` (classification logic), `src/test_clean.py`
(8 automated checks, all passing).

## Classification Results (measured on all 1,067,371 rows)

| transaction_type | rows | % of rows | unique invoices | unique customers | total qty | naive line value (qty×price) |
|---|---:|---:|---:|---:|---:|---:|
| sale | 1,037,979 | 97.25% | 39,826 | 5,868 | 11,412,806 | 20,452,668.52 |
| cancellation | 18,825 | 1.76% | 7,851 | 2,532 | -487,342 | -1,150,138.14 |
| non_merchandise | 4,379 | 0.41% | 4,204 | 641 | 10,764 | 132,334.30 |
| stock_correction | 3,457 | 0.32% | 3,393 | 0 | -573,085 | 0.00 |
| stock_inbound_no_customer | 2,656 | 0.25% | 1,909 | 0 | 230,599 | 0.00 |
| free_item | 69 | 0.006% | 59 | 49 | 14,744 | 0.00 |
| bad_debt_adjustment | 6 | 0.0006% | 6 | 0 | 6 | -147,614.10 |
| **unclassified** | **0** | **0.00%** | – | – | – | – |

Every row is accounted for; the classification is exhaustive and mutually
exclusive (verified by `test_row_count_reconciles` and
`test_every_row_gets_exactly_one_label`).

## Rules and Evidence (priority order — first match wins)

**1. `bad_debt_adjustment`** — `StockCode == 'B'`
All 5 negative-price rows in the raw data are StockCode `B`, description
"Adjust bad debt", on `A`-prefixed invoices, with no Customer ID. These are
accounting write-offs, not merchandise transactions, and are excluded from
all revenue and customer analytics.

**2. `non_merchandise`** — StockCode in a manually-inspected set: `POST`,
`DOT`, `C2`, `D`, `S`, `BANK CHARGES`, `ADJUST`, `ADJUST2`, `AMAZONFEE`,
`CRUK`, `TEST001`, `TEST002`. Confirmed via their Description fields
(POSTAGE, DOTCOM POSTAGE, CARRIAGE, Discount, SAMPLES, Bank Charges, manual
adjustments, AMAZON FEE, CRUK Commission, test rows). These are operating
costs/fees/test entries, not product sales.

*Important correction from the Phase 1 hypothesis:* `M`/`m` ("Manual") was
initially suspected to be administrative overhead. Investigation showed 709
of 1,426 Manual rows carry a real Customer ID and a real positive price
(e.g. £1,213.02, £803.25) — these are manually keyed-in sales/returns (e.g.
phone orders), not overhead. They are therefore **excluded** from
`non_merchandise` and instead flow through as ordinary `sale` or
`cancellation` rows depending on sign and invoice prefix.

**3. `cancellation`** — `Invoice` starts with `C`
19,493 of 19,494 C-prefixed rows have negative quantity. Spot-checked
example (`C489449`) links directly to a prior positive-quantity sale of the
same StockCode by the same customer — confirming these are genuine
customer-initiated returns/cancellations, not a coincidental naming
convention.

**4. `stock_correction`** — `Quantity < 0` AND not a C-invoice AND `Price == 0`
Verified on the **full population** (not a sample): all 3,457 such rows have
Price exactly 0.00, and none have a Customer ID. Descriptions include "lost",
"damages", "short", "invcd as 84879?" — internal inventory corrections that
cannot be, and should not be, attributed to any customer.

**5. `free_item`** — `Quantity > 0` AND `Price == 0` AND Customer ID present
69 rows: a small number of zero-price positive-quantity rows that do carry a
real Customer ID and a real product description (e.g. "DOOR MAT FAIRY CAKE",
"6 RIBBONS EMPIRE"). Most plausibly promotional/goodwill items given within
a real order. Kept as valid order lines with zero revenue contribution —
they still count toward that invoice's existence but add £0 to Monetary.

**6. `sale`** — `Quantity > 0` AND `Price > 0`
The ordinary case: 97.25% of all rows.

**7. `stock_inbound_no_customer`** — `Quantity > 0` AND `Price == 0` AND no
Customer ID. 2,656 rows, the mirror image of `stock_correction`: 100% have
no Customer ID, 63% have no Description either. Most plausibly goods-received
/ stock-inbound entries into the warehouse system rather than customer
purchases.

**8. `unclassified`** — residual catch-all. **0 rows** fell through all
rules above.

## Open Decision: Duplicate Rows

Phase 1 flagged that 6.30% of all rows are duplicated on the full business
key (Invoice + StockCode + Quantity + Date + Price + Customer ID). This
phase investigated whether that represents genuine repeated order lines or
data errors.

**Evidence:** inspecting a full example invoice (`489517`, 36 line items)
shows several products appearing as separate lines with identical quantity
and price (e.g. StockCode `21491` "SET OF THREE VINTAGE GIFT WRAPS" appears
twice, each `Quantity=1, Price=1.95`; StockCode `21912` "VINTAGE SNAKES &
LADDERS" appears three times). There is no line-item ID in this dataset, so
a customer/warehouse system entering the same product as two separate order
lines is indistinguishable from an accidental duplicate row — but the
pattern (many distinct products in one large order, each appearing 1-3
times) is far more consistent with genuine repeated line entries than with
a systematic export error.

**Quantified impact within `sale` rows specifically:**
- Duplicate rows on the business key: 65,972 (6.36% of sale rows)
- Revenue if all kept: £20,452,668.52
- Revenue if naively deduplicated: £19,984,307.25
- Difference: **£468,361.27 (2.29% of sale revenue)**

**Decision: do NOT deduplicate.** The evidence does not support treating
these as errors, and blind deduplication would remove real revenue and
understate purchase frequency for affected customers. This decision is
labeled **Assumption** — it is the more defensible reading of the evidence,
not a certainty, since the dataset has no way to conclusively distinguish
"same product ordered twice" from "row accidentally exported twice." If a
future phase's validation (e.g. reconciliation in Phase 27) surfaces
evidence against this, it should be revisited.

## What This Means Going Into Phase 3

- `sale`, `cancellation`, and `free_item` are the categories that represent
  real customer transaction behavior and will feed Revenue Definition and
  RFM.
- `bad_debt_adjustment`, `non_merchandise`, `stock_correction`, and
  `stock_inbound_no_customer` (0.98% of rows combined) are operationally
  real but are not customer purchase events — they will be excluded from
  customer-level analytics starting Phase 4, and will only reappear if a
  company-wide (not customer-level) revenue reconciliation is needed.
- No rows have been deleted. Everything is preserved with a label, so any
  downstream phase can audit or revisit this decision.
