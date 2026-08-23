"""
Phase 2 - Transaction Cleaning / Classification

Assigns every raw row an explicit transaction_type based on rules derived
from Phase 1 profiling evidence (see reports/phase1_data_quality_report.md
and reports/phase2_transaction_cleaning_report.md for the reasoning).

No rows are deleted here. Classification is additive: every row keeps its
original data plus a new `transaction_type` column. Downstream phases
decide which categories to include in which analysis.

Categories (evaluated in this priority order, first match wins):

1. bad_debt_adjustment
   Rule: StockCode == 'B'
   Evidence: all 5 negative-price rows in the raw data are StockCode 'B',
   Description 'Adjust bad debt', on 'A'-prefixed invoices, no Customer ID.
   These are accounting write-offs, not merchandise transactions.

2. non_merchandise
   Rule: StockCode in a manually-inspected set of administrative codes
   (postage, carriage, bank charges, discount, samples, manual adjustments,
   Amazon fees, CRUK commission, test rows).
   Evidence: their Description fields confirm they are not physical
   products (Section 9 of Phase 1 report). NOTE: 'M'/'m' ("Manual") was
   investigated separately and found to represent real manually-entered
   sales/returns (positive price, real Customer IDs in 709 of 1,426 rows)
   -- it is therefore NOT included here and flows through as an ordinary
   sale/cancellation instead.

3. cancellation
   Rule: Invoice starts with 'C'
   Evidence: 19,493 of 19,494 C-prefixed rows have negative quantity;
   spot-checked example (C489449) links directly to a prior positive-
   quantity sale of the same StockCode by the same customer. This is a
   customer-initiated return/cancellation of a previously recorded sale.

4. stock_correction
   Rule: Quantity < 0 AND Invoice does not start with 'C' AND Price == 0
   Evidence: all 3,457 such rows have Price == 0.00 exactly (verified on
   the full population, not a sample) and 99% have no Customer ID.
   Descriptions include 'lost', 'damages', 'short', 'mixed',
   'invcd as 84879?' -- internal inventory adjustments, not customer
   transactions, and structurally cannot be assigned to a customer.

5. free_item
   Rule: Quantity > 0 AND Price == 0 AND Customer ID is present
   Evidence: a small number (71 rows) of zero-price positive-quantity
   rows do carry a real Customer ID and plausible product descriptions
   (e.g. "6 RIBBONS EMPIRE", "DOOR MAT FAIRY CAKE") -- most plausibly
   promotional/goodwill items given to a real customer within a real
   order. Kept as valid order lines with zero revenue contribution.

6. sale
   Rule: Quantity > 0 AND Price > 0 (everything remaining that looks like
   an ordinary completed transaction line)

7. stock_inbound_no_customer
   Rule: Quantity > 0 AND Price == 0 AND Customer ID is missing
   Evidence: 2,656 rows -- the mirror image of stock_correction. 100% have
   no Customer ID (verified on the full population); 63% also have no
   Description. These look like goods-received / stock-inbound entries
   into the warehouse system, not customer purchases, and cannot be
   attributed to a customer even if they were.

8. unclassified
   Rule: anything not captured by the rules above. Should be a very small
   (ideally zero) residual; investigated explicitly and never silently
   dropped.
"""

import pandas as pd
from pathlib import Path

INPUT_PKL = Path("data/raw/online_retail_ii_combined.pkl")
OUTPUT_PKL = Path("data/processed/transactions_classified.pkl")

NON_MERCHANDISE_CODES = {
    "POST", "DOT", "C2", "D", "S", "BANK CHARGES",
    "ADJUST", "ADJUST2", "AMAZONFEE", "CRUK", "TEST001", "TEST002",
}


def classify(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    is_cancellation_invoice = df["Invoice"].str.startswith("C")

    conditions = [
        df["StockCode"] == "B",
        df["StockCode"].isin(NON_MERCHANDISE_CODES),
        is_cancellation_invoice,
        (df["Quantity"] < 0) & (~is_cancellation_invoice) & (df["Price"] == 0),
        (df["Quantity"] > 0) & (df["Price"] == 0) & (df["Customer ID"].notna()),
        (df["Quantity"] > 0) & (df["Price"] > 0),
        (df["Quantity"] > 0) & (df["Price"] == 0) & (df["Customer ID"].isna()),
    ]
    labels = [
        "bad_debt_adjustment",
        "non_merchandise",
        "cancellation",
        "stock_correction",
        "free_item",
        "sale",
        "stock_inbound_no_customer",
    ]

    df["transaction_type"] = "unclassified"
    for cond, label in zip(conditions, labels):
        df.loc[cond & (df["transaction_type"] == "unclassified"), "transaction_type"] = label

    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    summary = (
        df.groupby("transaction_type")
        .agg(
            rows=("Invoice", "size"),
            pct_of_rows=("Invoice", lambda s: len(s) / n * 100),
            unique_invoices=("Invoice", "nunique"),
            unique_customers=("Customer ID", "nunique"),
            total_qty=("Quantity", "sum"),
            naive_line_value=("Price", lambda s: (df.loc[s.index, "Quantity"] * s).sum()),
        )
        .sort_values("rows", ascending=False)
    )
    return summary


def main():
    df = pd.read_pickle(INPUT_PKL)
    df = classify(df)

    assert df["transaction_type"].notna().all(), "Every row must get a classification"

    summary = summarize(df)
    print(summary.to_string())

    unclassified_pct = (df["transaction_type"] == "unclassified").mean() * 100
    print(f"\nUnclassified rows: {unclassified_pct:.4f}% of dataset")

    df.to_pickle(OUTPUT_PKL)
    print(f"\nSaved classified transactions -> {OUTPUT_PKL}")
    return df, summary


if __name__ == "__main__":
    main()
