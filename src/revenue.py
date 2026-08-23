"""
Phase 3 - Revenue Definition

Defines transaction-level and aggregate revenue measures explicitly, built
on top of the Phase 2 transaction_type classification. Nothing here is
called "revenue" without a qualifier -- every number is one of the
explicitly defined tiers below, and the reconciliation makes clear what
each tier includes and excludes.

DEFINITIONS
-----------

Naive Raw Total
    sum(Quantity x Price) across every row in the raw dataset, with no
    cleaning applied at all. This is what a shallow analysis would report
    if it never looked past `df['Quantity'] * df['Price']`. Included only
    as a reconciliation anchor -- never used for actual business reporting.

Gross Merchandise Sales
    sum(Quantity x Price) for transaction_type == 'sale' only.
    This is genuine product revenue from completed customer purchases,
    before any returns are netted out. free_item rows are included in
    this population by definition but contribute exactly £0 (£0 price).

Returns
    sum(Quantity x Price) for transaction_type == 'cancellation', reported
    as a positive value (the sign is flipped for readability -- the
    underlying values are negative because Quantity is negative on
    cancellation rows).

Net Merchandise Sales
    Gross Merchandise Sales - Returns
    This is the primary revenue measure used for customer-level Monetary
    (RFM), CLV, and all core business reporting in this project, because it
    reflects money actually retained by the business net of the returns we
    can directly observe and attribute to a prior sale.

Non-Merchandise Charges (excluded from Net Merchandise Sales)
    sum(Quantity x Price) for transaction_type == 'non_merchandise'
    (postage, carriage, bank charges, discounts, Amazon fees, CRUK
    commission, test rows). This IS real money that changed hands in some
    cases (e.g. postage the customer paid), but it is not merchandise
    revenue and mixing it into product-level or customer-purchase-behavior
    analysis would distort what a "purchase" represents. Tracked
    separately for transparency, not silently discarded.

Excluded, Non-Revenue Categories
    bad_debt_adjustment, stock_correction, stock_inbound_no_customer.
    These do not represent money exchanged with a customer at all (write-
    offs and internal inventory movements) and are excluded from every
    revenue tier above.

IMPORTANT ANALYTICAL DECISION
------------------------------
What: Net Merchandise Sales (not the naive raw total, and not a figure that
      includes postage/fees) is the revenue measure used going forward for
      customer-level Monetary, CLV, and RFM.
Why: The stakeholder (CRM/Retention Manager) cares about product purchase
     behavior. Postage/fees do not reflect purchase intent or product
     value, and unclassified adjustment rows do not reflect customer
     transactions at all.
Assumption: A cancellation fully and correctly offsets the specific prior
     sale it is returning (i.e., simple netting by summation is valid).
     This project has NOT verified a 1:1 match between every cancellation
     row and a specific prior sale row -- only a spot check (see Phase 2
     report) confirmed the general pattern for one example. This is
     flagged as an unverified assumption, not a proven fact.
What could go wrong: If a cancellation's Price differs from the original
     sale's Price (e.g. due to a promotional discount applied only at
     purchase time, or a price change between purchase and return), simple
     summation still nets out correctly in £ terms as long as the values
     recorded on the cancellation row are accurate -- but if the return
     Price was recorded incorrectly, net revenue would be biased. Not yet
     validated.
How we would validate: A future check (not implemented in this phase)
     could attempt to match cancellation rows to a specific prior sale by
     Customer ID + StockCode + Quantity magnitude, and confirm the price
     matches. Flagged as a possible extension, not built here to avoid
     scope creep on Phase 3.
"""

import pandas as pd
from pathlib import Path

INPUT_PKL = Path("data/processed/transactions_classified.pkl")
OUTPUT_PKL = Path("data/processed/transactions_with_revenue.pkl")

REVENUE_CATEGORY = "sale"
RETURN_CATEGORY = "cancellation"
NON_MERCH_CATEGORY = "non_merchandise"
EXCLUDED_CATEGORIES = {"bad_debt_adjustment", "stock_correction", "stock_inbound_no_customer"}


def add_line_value(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["line_value"] = df["Quantity"] * df["Price"]
    return df


def reconcile(df: pd.DataFrame) -> dict:
    naive_raw_total = df["line_value"].sum()

    gross_merch_sales = df.loc[df["transaction_type"] == REVENUE_CATEGORY, "line_value"].sum()
    returns = -df.loc[df["transaction_type"] == RETURN_CATEGORY, "line_value"].sum()  # flip sign
    net_merch_sales = gross_merch_sales - returns

    non_merch_charges = df.loc[df["transaction_type"] == NON_MERCH_CATEGORY, "line_value"].sum()
    excluded_total = df.loc[df["transaction_type"].isin(EXCLUDED_CATEGORIES), "line_value"].sum()

    # Reconciliation: naive raw total must equal the sum of every tier,
    # using SIGNED values (cancellations are negative in the raw data).
    cancellation_signed = df.loc[df["transaction_type"] == RETURN_CATEGORY, "line_value"].sum()
    reconciled_total = gross_merch_sales + cancellation_signed + non_merch_charges + excluded_total

    return {
        "naive_raw_total": naive_raw_total,
        "gross_merchandise_sales": gross_merch_sales,
        "returns": returns,
        "net_merchandise_sales": net_merch_sales,
        "non_merchandise_charges": non_merch_charges,
        "excluded_non_revenue_total": excluded_total,
        "reconciled_total": reconciled_total,
        "reconciliation_diff": naive_raw_total - reconciled_total,
    }


def main():
    df = pd.read_pickle(INPUT_PKL)
    df = add_line_value(df)

    stats = reconcile(df)

    print("REVENUE RECONCILIATION")
    print("-" * 60)
    for k, v in stats.items():
        print(f"{k:30s} £{v:>16,.2f}")

    assert abs(stats["reconciliation_diff"]) < 0.01, "Reconciliation must tie out to the penny"

    df.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")
    return df, stats


if __name__ == "__main__":
    main()
