"""
Phase 5 - RFM Foundations

Implements Recency, Frequency, Monetary from first principles on top of
the Phase 4 customer table. No black-box RFM library is used.

SNAPSHOT DATE
-------------
What: snapshot_date = one day after the last observed transaction date in
      the full (not just customer-level) dataset: max(InvoiceDate) + 1 day.
      Measured max(InvoiceDate) = 2011-12-09 12:50:00 -> snapshot_date =
      2011-12-10 (date only, time dropped since recency is measured in
      whole days).
Why: Using "day after max date" instead of the max date itself means the
     most recently active customer gets Recency = 1, not 0. Recency = 0
     is reserved conceptually for "later than any data we have," which
     would be a modeling artifact, not a real value.
Assumption: The dataset's max date is representative of "today" for
     business reporting purposes -- i.e. we're treating this as a snapshot
     taken the day after data collection ended, not simulating a specific
     real calendar "today."
What could go wrong: If this dataset were refreshed daily, the snapshot
     date would need to move with it. Hard-coded here because we have a
     static historical extract, not a live feed.
How we validate it: Recompute recency for a few known customers manually
     against their last_purchase_date and confirm arithmetic.
Bug caught during implementation: an initial version subtracted
     last_purchase_date (which retains a time-of-day component, e.g.
     2011-12-09 12:50:00) from the normalized snapshot_date without also
     normalizing last_purchase_date, which let the single most-recent
     customer's recency compute to 0 days instead of 1. Fixed by
     normalizing both sides to whole calendar days before subtracting.
     Caught by an assertion (recency_days.min() >= 1) that failed loudly
     rather than silently shipping a wrong value.

FREQUENCY
---------
Frequency = sale_order_count from Phase 4 (distinct invoices of type
'sale' -- i.e. actual completed purchase orders, NOT line items, NOT
cancellations). This directly follows the Phase 0 grain decision: an
invoice with 10 products is one purchase occasion, not ten.

MONETARY
--------
Monetary = net_revenue from Phase 4 (Gross Merchandise Sales minus
Returns per customer, i.e. the Phase 3 "Net Merchandise Sales" definition
applied at customer grain). This was chosen over gross_revenue because it
reflects money actually retained by the business, which is what a
CRM/Retention Manager cares about when deciding who is valuable.

IMPORTANT: Monetary CAN be negative or zero. This is not clipped or
floored. A customer who returned more (within the observed window) than
they show as having purchased is a real, if unusual, pattern worth seeing,
not an error to be hidden by clamping to zero. Measured: 40 customers
have sale_order_count > 0 but net_revenue <= 0.

HANDLING OF THE 53 CANCELLATION-ONLY CUSTOMERS (from Phase 4)
---------------------------------------------------------------
These 53 customers have sale_order_count == 0 and no last_purchase_date,
so Recency cannot be computed under the "days since last sale" definition
-- there is no sale to measure from.

Decision: EXCLUDE these 53 customers from the primary RFM population
(rfm_valid), but retain them in a separate rfm_excluded table with the
reason recorded, rather than silently dropping them or assigning a
fabricated recency value.

What could go wrong: This slightly understates total customer count in
all RFM-based segmentation and reporting from here forward (5,868 vs
5,921, a 0.9% difference). Flagged explicitly so it's never mistaken for
the full customer base.
"""

import pandas as pd
from pathlib import Path

INPUT_PKL = Path("data/processed/customers.pkl")
OUTPUT_VALID_PKL = Path("data/processed/rfm.pkl")
OUTPUT_EXCLUDED_PKL = Path("data/processed/rfm_excluded.pkl")

RAW_TXN_PKL = Path("data/processed/transactions_with_revenue.pkl")


def get_snapshot_date() -> pd.Timestamp:
    df = pd.read_pickle(RAW_TXN_PKL)
    max_date = df["InvoiceDate"].max()
    snapshot = (max_date + pd.Timedelta(days=1)).normalize()
    return snapshot


def build_rfm(customers: pd.DataFrame, snapshot_date: pd.Timestamp):
    customers = customers.copy()

    excluded_mask = customers["sale_order_count"] == 0
    rfm_excluded = customers[excluded_mask].copy()
    rfm_excluded["exclusion_reason"] = "no_sale_orders_cancellation_only"

    valid = customers[~excluded_mask].copy()

    valid["recency_days"] = (snapshot_date - valid["last_purchase_date"].dt.normalize()).dt.days
    valid["frequency"] = valid["sale_order_count"]
    valid["monetary"] = valid["net_revenue"]

    rfm = valid[[
        "customer_id", "country", "first_purchase_date", "last_purchase_date",
        "recency_days", "frequency", "monetary",
    ]].reset_index(drop=True)

    return rfm, rfm_excluded


def main():
    customers = pd.read_pickle(INPUT_PKL)
    snapshot_date = get_snapshot_date()
    print(f"Snapshot date: {snapshot_date.date()}")

    rfm, rfm_excluded = build_rfm(customers, snapshot_date)

    print(f"\nRFM-valid customers: {len(rfm)}")
    print(f"Excluded (cancellation-only) customers: {len(rfm_excluded)}")
    print(f"Total accounted for: {len(rfm) + len(rfm_excluded)} (customer table had {len(customers)})")

    print("\nRFM summary statistics:")
    print(rfm[["recency_days", "frequency", "monetary"]].describe().round(2))

    assert rfm["recency_days"].min() >= 1, "Recency should never be < 1 given the snapshot date rule"
    assert (rfm["frequency"] > 0).all(), "Every RFM-valid customer must have at least 1 sale order"

    rfm.to_pickle(OUTPUT_VALID_PKL)
    rfm_excluded.to_pickle(OUTPUT_EXCLUDED_PKL)
    print(f"\nSaved -> {OUTPUT_VALID_PKL}")
    print(f"Saved -> {OUTPUT_EXCLUDED_PKL}")

    return rfm, rfm_excluded


if __name__ == "__main__":
    main()
