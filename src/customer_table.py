"""
Phase 4 - Customer-Level Analytical Table

Aggregates cleaned, classified transactions up to the customer grain.

GRAIN RULE (the most important thing in this file):
An "order" is a distinct Invoice number where transaction_type is 'sale',
'cancellation', or 'free_item' (i.e. the invoice contains at least one line
that represents real customer purchase/return behavior). order_count is
built from `Invoice.nunique()`, never from row counts. Invoices consisting
only of non_merchandise / stock_correction / stock_inbound_no_customer /
bad_debt_adjustment rows (5,947 invoices, verified in Phase 4 investigation)
contribute ZERO orders, because they represent no actual merchandise
transaction -- e.g. a postage-only or bank-charge-only line with no product.

CUSTOMER-LEVEL FIELDS
----------------------
customer_id            Customer ID (float in raw data, cast to int here)
country                 Customer's most frequently associated country (mode).
                         Assumption: a customer operates from one country;
                         handles the rare case of multiple observed countries.
first_purchase_date     Earliest InvoiceDate among this customer's 'sale' rows
                         (NOT cancellations -- a return can't be a first purchase)
last_purchase_date      Latest InvoiceDate among this customer's 'sale' rows
order_count              Distinct invoices of type 'sale'/'cancellation'/'free_item'
sale_order_count         Distinct invoices of type 'sale' only (positive purchases)
cancellation_order_count Distinct invoices of type 'cancellation' only
item_count               Sum of Quantity across 'sale' + 'free_item' rows
                         (i.e. units actually kept, not units returned)
gross_revenue            Sum of line_value for 'sale' rows (Phase 3 definition)
return_value              Sum of line_value for 'cancellation' rows, positive
net_revenue               gross_revenue - return_value (Phase 3 Net Merchandise Sales,
                          computed per customer)
active_months             Count of distinct (year, month) with at least one 'sale' row
average_order_value       net_revenue / sale_order_count (undefined / NaN if 0 sale orders)

Customers with ALL activity being cancellations and no sale order
(sale_order_count == 0) ARE still included in the table (their net_revenue
will be negative or zero) -- excluding them would hide real returned-value
information from the business. This is flagged explicitly rather than
silently dropped.
"""

import pandas as pd
from pathlib import Path

INPUT_PKL = Path("data/processed/transactions_with_revenue.pkl")
OUTPUT_PKL = Path("data/processed/customers.pkl")

VALID_CUSTOMER_TXN_TYPES = {"sale", "cancellation", "free_item"}


def build_customer_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["Customer ID"].notna()].copy()
    df["Customer ID"] = df["Customer ID"].astype("int64")
    df["year_month"] = df["InvoiceDate"].dt.to_period("M")

    # Restrict to rows that represent real customer purchase/return behavior
    valid = df[df["transaction_type"].isin(VALID_CUSTOMER_TXN_TYPES)].copy()

    sales = valid[valid["transaction_type"] == "sale"]
    cancellations = valid[valid["transaction_type"] == "cancellation"]
    free_items = valid[valid["transaction_type"] == "free_item"]

    g = valid.groupby("Customer ID")

    customers = pd.DataFrame(index=g.size().index)
    customers.index.name = "customer_id"

    # Country: mode (most frequent observed country per customer)
    customers["country"] = df.groupby("Customer ID")["Country"].agg(
        lambda s: s.mode().iloc[0] if len(s.mode()) else pd.NA
    )

    # Dates: from sale rows only
    sale_dates = sales.groupby("Customer ID")["InvoiceDate"]
    customers["first_purchase_date"] = sale_dates.min()
    customers["last_purchase_date"] = sale_dates.max()

    # Orders: distinct invoice counts, NEVER row counts
    customers["order_count"] = valid.groupby("Customer ID")["Invoice"].nunique()
    customers["sale_order_count"] = sales.groupby("Customer ID")["Invoice"].nunique()
    customers["cancellation_order_count"] = cancellations.groupby("Customer ID")["Invoice"].nunique()

    for col in ["sale_order_count", "cancellation_order_count"]:
        customers[col] = customers[col].fillna(0).astype("int64")
    customers["order_count"] = customers["order_count"].fillna(0).astype("int64")

    # Items: units actually kept (sale + free_item), not units returned
    kept = pd.concat([sales, free_items])
    customers["item_count"] = kept.groupby("Customer ID")["Quantity"].sum()
    customers["item_count"] = customers["item_count"].fillna(0).astype("int64")

    # Revenue
    customers["gross_revenue"] = sales.groupby("Customer ID")["line_value"].sum()
    customers["gross_revenue"] = customers["gross_revenue"].fillna(0.0)
    customers["return_value"] = -cancellations.groupby("Customer ID")["line_value"].sum()
    customers["return_value"] = customers["return_value"].fillna(0.0)
    customers["net_revenue"] = customers["gross_revenue"] - customers["return_value"]

    # Active months: distinct months with at least one sale row
    customers["active_months"] = sales.groupby("Customer ID")["year_month"].nunique()
    customers["active_months"] = customers["active_months"].fillna(0).astype("int64")

    # Average order value: undefined for customers with 0 sale orders
    customers["average_order_value"] = customers.apply(
        lambda r: r["net_revenue"] / r["sale_order_count"] if r["sale_order_count"] > 0 else pd.NA,
        axis=1,
    )

    customers = customers.reset_index()
    return customers


def main():
    df = pd.read_pickle(INPUT_PKL)
    customers = build_customer_table(df)

    print(f"Customer table shape: {customers.shape}")
    print(customers.describe(include="all").T)

    customers.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")
    return customers


if __name__ == "__main__":
    main()
