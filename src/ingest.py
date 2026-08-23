"""
Phase 1 - Data Ingestion

Loads the raw Online Retail II workbook (two sheets: 'Year 2009-2010' and
'Year 2010-2011'), combines them into a single frame, normalizes dtypes,
and caches the result for fast reuse in later phases.

This script does NOT clean or filter any rows. It only ingests and
type-normalizes. Cleaning decisions belong in Phase 2 (src/clean.py).
"""

import pandas as pd
from pathlib import Path

RAW_XLSX = Path("data/raw/online_retail_II.xlsx")
CACHE_PKL = Path("data/raw/online_retail_ii_combined.pkl")

EXPECTED_COLUMNS = [
    "Invoice", "StockCode", "Description", "Quantity",
    "InvoiceDate", "Price", "Customer ID", "Country",
]


def load_raw(xlsx_path: Path = RAW_XLSX) -> pd.DataFrame:
    """Load both sheets of the Online Retail II workbook and combine them."""
    sheets = pd.read_excel(xlsx_path, sheet_name=None, engine="openpyxl")

    expected_sheets = {"Year 2009-2010", "Year 2010-2011"}
    if set(sheets.keys()) != expected_sheets:
        raise ValueError(
            f"Unexpected sheet names: {set(sheets.keys())}. "
            f"Expected: {expected_sheets}"
        )

    frames = []
    for sheet_name, sheet_df in sheets.items():
        missing_cols = set(EXPECTED_COLUMNS) - set(sheet_df.columns)
        if missing_cols:
            raise ValueError(f"Sheet '{sheet_name}' is missing columns: {missing_cols}")
        sheet_df = sheet_df.copy()
        sheet_df["source_sheet"] = sheet_name.replace("Year ", "")
        frames.append(sheet_df)

    df = pd.concat(frames, ignore_index=True)

    # Normalize dtypes: some columns arrive as mixed str/object across sheets
    # (e.g. Invoice is read as int in one sheet's numeric-only rows and str
    # in the other where cancellation prefixes like 'C'/'A' appear).
    for col in ["Invoice", "StockCode", "Description", "Country", "source_sheet"]:
        df[col] = df[col].astype(str)
        df.loc[df[col] == "nan", col] = pd.NA

    df["Quantity"] = df["Quantity"].astype("int64")
    df["Price"] = df["Price"].astype("float64")
    df["Customer ID"] = df["Customer ID"].astype("float64")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    return df


def main():
    df = load_raw()
    df.to_pickle(CACHE_PKL)
    print(f"Ingested {len(df):,} rows, {df.shape[1]} columns -> {CACHE_PKL}")
    return df


if __name__ == "__main__":
    main()
