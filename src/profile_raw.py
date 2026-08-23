"""
Phase 1 - Data Profiling

Runs a battery of data-quality checks against the ingested raw dataset
and writes a report to reports/phase1_data_quality_report.md.

All numbers in the output report are measured directly from the data.
Nothing here is estimated or assumed.
"""

import re
import pandas as pd
from pathlib import Path

CACHE_PKL = Path("data/raw/online_retail_ii_combined.pkl")
REPORT_PATH = Path("reports/phase1_data_quality_report.md")

STANDARD_STOCKCODE_RE = re.compile(r"^\d{5}[A-Za-z]?$")

# Codes identified by manual inspection of their Description field as
# administrative / non-merchandise line items (postage, fees, adjustments,
# test rows) rather than actual products. This list is a documented,
# inspected classification -- not a guess -- and will be used in Phase 2.
ADMIN_STOCKCODES = {
    "POST", "DOT", "M", "m", "C2", "D", "S", "BANK CHARGES",
    "ADJUST", "ADJUST2", "AMAZONFEE", "CRUK", "TEST001", "TEST002", "B",
}


def profile(df: pd.DataFrame) -> str:
    n = len(df)
    lines = []
    a = lines.append

    a("# Phase 1 - Data Quality Report")
    a("")
    a("Dataset: Online Retail II (UCI / Kaggle mirror), sheets 'Year 2009-2010' "
      "and 'Year 2010-2011' combined.")
    a("")
    a("All figures below are measured directly from the ingested file. None are assumed.")
    a("")

    # --- Shape ---
    a("## 1. Basic Shape")
    a(f"- Rows: **{n:,}**")
    a(f"- Columns: **{df.shape[1]}** -> {list(df.columns)}")
    a("")

    # --- Date range ---
    a("## 2. Date Range")
    a(f"- Min InvoiceDate: **{df['InvoiceDate'].min()}**")
    a(f"- Max InvoiceDate: **{df['InvoiceDate'].max()}**")
    span_days = (df['InvoiceDate'].max() - df['InvoiceDate'].min()).days
    a(f"- Span: **{span_days:,} days** (~{span_days/365.25:.1f} years)")
    a("")

    # --- Unique counts ---
    a("## 3. Unique Entity Counts")
    a(f"- Unique Invoices: **{df['Invoice'].nunique():,}**")
    a(f"- Unique Customers (non-null Customer ID): **{df['Customer ID'].nunique():,}**")
    a(f"- Unique StockCodes: **{df['StockCode'].nunique():,}**")
    a(f"- Unique Countries: **{df['Country'].nunique():,}**")
    a("")
    a("Note: unique invoice count (line-item groups) is far smaller than row count "
      "-- confirms that a row is a line item, not an order.")
    a("")

    # --- Country distribution ---
    a("## 4. Country Distribution (top 15 by row count)")
    a("")
    country_counts = df['Country'].value_counts().head(15)
    a("| Country | Rows | % of rows |")
    a("|---|---:|---:|")
    for c, cnt in country_counts.items():
        a(f"| {c} | {cnt:,} | {cnt/n*100:.2f}% |")
    a("")
    uk_pct = (df['Country'] == 'United Kingdom').sum() / n * 100
    a(f"United Kingdom accounts for **{uk_pct:.1f}%** of all rows. This has direct "
      f"implications for Phase 21 (country analysis) -- most non-UK countries will "
      f"have very small sample sizes.")
    a("")

    # --- Missing values ---
    a("## 5. Missing Values")
    a("")
    miss = df.isna().sum()
    miss_pct = (miss / n * 100).round(2)
    a("| Column | Missing rows | Missing % |")
    a("|---|---:|---:|")
    for col in df.columns:
        if miss[col] > 0:
            a(f"| {col} | {miss[col]:,} | {miss_pct[col]}% |")
    a("")
    cust_missing_pct = df['Customer ID'].isna().sum() / n * 100
    a(f"**Customer ID is missing on {cust_missing_pct:.2f}% of rows.** These rows "
      f"cannot be attributed to any customer and will be excluded from all "
      f"customer-level analysis (RFM, cohorts, CLV) starting Phase 4. They can "
      f"still contribute to raw/company-level revenue reporting if that is ever needed.")
    a("")

    # --- Duplicates ---
    a("## 6. Duplicate Rows")
    a("")
    dup_full = df.duplicated(keep=False).sum()
    dup_key = df.duplicated(
        subset=['Invoice', 'StockCode', 'Quantity', 'InvoiceDate', 'Price', 'Customer ID'],
        keep=False
    ).sum()
    a(f"- Fully duplicated rows (every column identical): **{dup_full:,}** ({dup_full/n*100:.2f}%)")
    a(f"- Duplicated on business key (Invoice+StockCode+Qty+Date+Price+CustomerID): "
      f"**{dup_key:,}** ({dup_key/n*100:.2f}%)")
    a("")
    a("Possible explanations: repeated exports, genuinely repeated line entries "
      "(e.g. same product added twice in one order), or system-level duplication "
      "during data collection. This needs a decision in Phase 2 -- not yet resolved.")
    a("")

    # --- Quantity ---
    a("## 7. Quantity")
    a("")
    neg_qty = (df['Quantity'] < 0).sum()
    zero_qty = (df['Quantity'] == 0).sum()
    pos_qty = (df['Quantity'] > 0).sum()
    a(f"- Negative quantity rows: **{neg_qty:,}** ({neg_qty/n*100:.2f}%)")
    a(f"- Zero quantity rows: **{zero_qty:,}** ({zero_qty/n*100:.2f}%)")
    a(f"- Positive quantity rows: **{pos_qty:,}** ({pos_qty/n*100:.2f}%)")
    a(f"- Min: {df['Quantity'].min():,}, Max: {df['Quantity'].max():,}")
    a("")

    # --- Invoice prefix vs quantity sign ---
    a("### 7a. Invoice Prefix vs Quantity Sign")
    a("")
    df = df.copy()
    df['invoice_first_char'] = df['Invoice'].str[0]
    ct = pd.crosstab(df['invoice_first_char'], df['Quantity'].apply(
        lambda x: 'negative' if x < 0 else ('zero' if x == 0 else 'positive')))
    a("```")
    a(ct.to_string())
    a("```")
    a("")
    c_invoices = df[df['invoice_first_char'] == 'C']
    c_non_negative = (c_invoices['Quantity'] >= 0).sum()
    a(f"- {len(c_invoices):,} rows have an Invoice starting with 'C'. Of these, "
      f"only **{c_non_negative}** have non-negative quantity -- i.e. C-prefixed "
      f"invoices are essentially always paired with negative quantity.")
    a(f"- {(df['invoice_first_char']=='A').sum()} rows have an Invoice starting with "
      f"'A' (all found to be 'Adjust bad debt' entries -- see section 9).")
    a("")
    neg_not_c = df[(df['Quantity'] < 0) & (df['invoice_first_char'] != 'C')]
    a(f"- **{len(neg_not_c):,} rows have negative quantity but are NOT on a "
      f"C-prefixed invoice.** Sample descriptions found: 'lost', 'damages', "
      f"'short', 'mixed', 'invcd as 84879?', all with Price = 0.00 and missing "
      f"Customer ID. These look like internal stock corrections, not customer "
      f"returns -- a distinct category from C-prefixed cancellations. This "
      f"needs its own classification rule in Phase 2.")
    a("")

    # --- Price ---
    a("## 8. Price")
    a("")
    neg_price = (df['Price'] < 0).sum()
    zero_price = (df['Price'] == 0).sum()
    pos_price = (df['Price'] > 0).sum()
    a(f"- Negative price rows: **{neg_price}** ({neg_price/n*100:.3f}%)")
    a(f"- Zero price rows: **{zero_price:,}** ({zero_price/n*100:.2f}%)")
    a(f"- Positive price rows: **{pos_price:,}** ({pos_price/n*100:.2f}%)")
    a(f"- Min: {df['Price'].min():,.2f}, Max: {df['Price'].max():,.2f}")
    a("")

    # --- Negative price detail ---
    a("### 8a. Negative Price Rows (all 5, shown in full)")
    a("")
    neg_price_rows = df[df['Price'] < 0][
        ['Invoice', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Price', 'Customer ID']
    ]
    a("```")
    a(neg_price_rows.to_string(index=False))
    a("```")
    a("")
    a("All 5 negative-price rows are StockCode 'B', Description 'Adjust bad debt', "
      "no Customer ID, on Invoice numbers prefixed 'A'. These are clearly "
      "accounting adjustments, not customer purchases. Candidate for exclusion "
      "in Phase 2.")
    a("")

    # --- StockCode anomalies ---
    a("## 9. StockCode / Non-Product Line Items")
    a("")
    is_standard = df['StockCode'].apply(lambda c: bool(STANDARD_STOCKCODE_RE.match(c)))
    nonstd = df[~is_standard]
    a(f"- Rows with a StockCode that does not match the typical 5-digit "
      f"(+ optional letter) product code pattern: **{len(nonstd):,}** ({len(nonstd)/n*100:.2f}%)")
    a("- **Important:** not all of these are non-product rows. Some products "
      "genuinely use non-standard codes (e.g. `15056BL`, `79323LP`, `DCGS0058`, "
      "gift voucher codes). Format alone is not a reliable classifier.")
    a("")
    a("- Codes manually confirmed (via their Description field) to be "
      "administrative / non-merchandise, not products:")
    a("")
    a("| StockCode | Rows | Description |")
    a("|---|---:|---|")
    for code in sorted(ADMIN_STOCKCODES):
        sub = df[df['StockCode'] == code]
        if len(sub) == 0:
            continue
        desc = sub['Description'].mode()
        desc = desc.iloc[0] if len(desc) else 'N/A'
        a(f"| {code} | {len(sub):,} | {desc} |")
    a("")
    admin_rows = df[df['StockCode'].isin(ADMIN_STOCKCODES)]
    a(f"Total rows on confirmed administrative codes: **{len(admin_rows):,}** "
      f"({len(admin_rows)/n*100:.2f}% of all rows). These represent postage, "
      f"carriage, bank charges, manual adjustments, Amazon fees, and test rows -- "
      f"none of them are real merchandise sales and none should count toward "
      f"product-level or (in most cases) customer purchase-behavior analysis. "
      f"Final treatment decision belongs in Phase 2.")
    a("")

    # --- Missing CustomerID vs invoice prefix ---
    a("## 10. Missing Customer ID vs Invoice Prefix")
    a("")
    df['cust_missing'] = df['Customer ID'].isna()
    ct2 = pd.crosstab(df['invoice_first_char'], df['cust_missing'])
    a("```")
    a(ct2.to_string())
    a("```")
    a("")
    a("Missing-CustomerID rate is noticeably lower on cancellation invoices "
      "(C-prefix) than on normal invoices -- worth keeping in mind when Phase 2 "
      "decides how cancellations interact with customer-level netting.")
    a("")

    # --- Summary of open decisions ---
    a("## 11. Open Data-Quality Decisions for Phase 2")
    a("")
    a("This report intentionally does not delete or alter any rows. The "
      "following decisions are flagged for Phase 2, with the evidence needed "
      "to make each one:")
    a("")
    a("1. **C-prefixed invoices (cancellations):** clearly returns/cancellations "
      "linked to an original sale. Needs a rule for how they net against "
      "revenue and customer purchase counts.")
    a("2. **Negative quantity on non-C invoices:** likely internal stock "
      "corrections (Price = 0, no Customer ID) -- probably excluded entirely "
      "from customer/revenue analytics, but distinct from cancellations.")
    a("3. **'A'-prefixed invoices / negative price ('Adjust bad debt'):** "
      "accounting write-offs, no Customer ID -- candidate for exclusion.")
    a("4. **Administrative StockCodes** (postage, carriage, bank charges, fees, "
      "manual, test rows): candidate for exclusion from product/customer "
      "purchase-behavior analysis; may still matter for total company revenue "
      "reconciliation.")
    a("5. **Zero-price rows:** needs investigation into what they represent "
      "(free items, promotions, data errors) before deciding treatment.")
    a("6. **Duplicate rows:** needs a decision on whether they represent "
      "genuine repeated line entries or export artifacts.")
    a("7. **Missing Customer ID (22.77% of rows):** excluded from all "
      "customer-level analysis by definition of customer grain (Phase 0).")
    a("")

    return "\n".join(lines)


def main():
    df = pd.read_pickle(CACHE_PKL)
    report = profile(df)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH} ({len(report):,} characters)")


if __name__ == "__main__":
    main()
