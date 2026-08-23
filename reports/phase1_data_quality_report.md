# Phase 1 - Data Quality Report

Dataset: Online Retail II (UCI / Kaggle mirror), sheets 'Year 2009-2010' and 'Year 2010-2011' combined.

All figures below are measured directly from the ingested file. None are assumed.

## 1. Basic Shape
- Rows: **1,067,371**
- Columns: **9** -> ['Invoice', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Price', 'Customer ID', 'Country', 'source_sheet']

## 2. Date Range
- Min InvoiceDate: **2009-12-01 07:45:00**
- Max InvoiceDate: **2011-12-09 12:50:00**
- Span: **738 days** (~2.0 years)

## 3. Unique Entity Counts
- Unique Invoices: **53,628**
- Unique Customers (non-null Customer ID): **5,942**
- Unique StockCodes: **5,305**
- Unique Countries: **43**

Note: unique invoice count (line-item groups) is far smaller than row count -- confirms that a row is a line item, not an order.

## 4. Country Distribution (top 15 by row count)

| Country | Rows | % of rows |
|---|---:|---:|
| United Kingdom | 981,330 | 91.94% |
| EIRE | 17,866 | 1.67% |
| Germany | 17,624 | 1.65% |
| France | 14,330 | 1.34% |
| Netherlands | 5,140 | 0.48% |
| Spain | 3,811 | 0.36% |
| Switzerland | 3,189 | 0.30% |
| Belgium | 3,123 | 0.29% |
| Portugal | 2,620 | 0.25% |
| Australia | 1,913 | 0.18% |
| Channel Islands | 1,664 | 0.16% |
| Italy | 1,534 | 0.14% |
| Norway | 1,455 | 0.14% |
| Sweden | 1,364 | 0.13% |
| Cyprus | 1,176 | 0.11% |

United Kingdom accounts for **91.9%** of all rows. This has direct implications for Phase 21 (country analysis) -- most non-UK countries will have very small sample sizes.

## 5. Missing Values

| Column | Missing rows | Missing % |
|---|---:|---:|
| Description | 4,382 | 0.41% |
| Customer ID | 243,007 | 22.77% |

**Customer ID is missing on 22.77% of rows.** These rows cannot be attributed to any customer and will be excluded from all customer-level analysis (RFM, cohorts, CLV) starting Phase 4. They can still contribute to raw/company-level revenue reporting if that is ever needed.

## 6. Duplicate Rows

- Fully duplicated rows (every column identical): **23,430** (2.20%)
- Duplicated on business key (Invoice+StockCode+Qty+Date+Price+CustomerID): **67,246** (6.30%)

Possible explanations: repeated exports, genuinely repeated line entries (e.g. same product added twice in one order), or system-level duplication during data collection. This needs a decision in Phase 2 -- not yet resolved.

## 7. Quantity

- Negative quantity rows: **22,950** (2.15%)
- Zero quantity rows: **0** (0.00%)
- Positive quantity rows: **1,044,421** (97.85%)
- Min: -80,995, Max: 80,995

### 7a. Invoice Prefix vs Quantity Sign

```
Quantity            negative  positive
invoice_first_char                    
4                        729    107760
5                       2728    936654
A                          0         6
C                      19493         1
```

- 19,494 rows have an Invoice starting with 'C'. Of these, only **1** have non-negative quantity -- i.e. C-prefixed invoices are essentially always paired with negative quantity.
- 6 rows have an Invoice starting with 'A' (all found to be 'Adjust bad debt' entries -- see section 9).

- **3,457 rows have negative quantity but are NOT on a C-prefixed invoice.** Sample descriptions found: 'lost', 'damages', 'short', 'mixed', 'invcd as 84879?', all with Price = 0.00 and missing Customer ID. These look like internal stock corrections, not customer returns -- a distinct category from C-prefixed cancellations. This needs its own classification rule in Phase 2.

## 8. Price

- Negative price rows: **5** (0.000%)
- Zero price rows: **6,202** (0.58%)
- Positive price rows: **1,061,164** (99.42%)
- Min: -53,594.36, Max: 38,970.00

### 8a. Negative Price Rows (all 5, shown in full)

```
Invoice StockCode     Description  Quantity         InvoiceDate     Price  Customer ID
A506401         B Adjust bad debt         1 2010-04-29 13:36:00 -53594.36          NaN
A516228         B Adjust bad debt         1 2010-07-19 11:24:00 -44031.79          NaN
A528059         B Adjust bad debt         1 2010-10-20 12:04:00 -38925.87          NaN
A563186         B Adjust bad debt         1 2011-08-12 14:51:00 -11062.06          NaN
A563187         B Adjust bad debt         1 2011-08-12 14:52:00 -11062.06          NaN
```

All 5 negative-price rows are StockCode 'B', Description 'Adjust bad debt', no Customer ID, on Invoice numbers prefixed 'A'. These are clearly accounting adjustments, not customer purchases. Candidate for exclusion in Phase 2.

## 9. StockCode / Non-Product Line Items

- Rows with a StockCode that does not match the typical 5-digit (+ optional letter) product code pattern: **7,466** (0.70%)
- **Important:** not all of these are non-product rows. Some products genuinely use non-standard codes (e.g. `15056BL`, `79323LP`, `DCGS0058`, gift voucher codes). Format alone is not a reliable classifier.

- Codes manually confirmed (via their Description field) to be administrative / non-merchandise, not products:

| StockCode | Rows | Description |
|---|---:|---|
| ADJUST | 67 | Adjustment by john on 26/01/2010 16 |
| ADJUST2 | 3 | Adjustment by Peter on Jun 25 2010  |
| AMAZONFEE | 43 | AMAZON FEE |
| B | 6 | Adjust bad debt |
| BANK CHARGES | 102 | Bank Charges |
| C2 | 282 | CARRIAGE |
| CRUK | 16 | CRUK Commission |
| D | 177 | Discount |
| DOT | 1,446 | DOTCOM POSTAGE |
| M | 1,421 | Manual |
| POST | 2,122 | POSTAGE |
| S | 104 | SAMPLES |
| TEST001 | 15 | This is a test product. |
| TEST002 | 2 | This is a test product. |
| m | 5 | Manual |

Total rows on confirmed administrative codes: **5,811** (0.54% of all rows). These represent postage, carriage, bank charges, manual adjustments, Amazon fees, and test rows -- none of them are real merchandise sales and none should count toward product-level or (in most cases) customer purchase-behavior analysis. Final treatment decision belongs in Phase 2.

## 10. Missing Customer ID vs Invoice Prefix

```
cust_missing         False   True 
invoice_first_char                
4                    79540   28949
5                   726080  213302
A                        0       6
C                    18744     750
```

Missing-CustomerID rate is noticeably lower on cancellation invoices (C-prefix) than on normal invoices -- worth keeping in mind when Phase 2 decides how cancellations interact with customer-level netting.

## 11. Open Data-Quality Decisions for Phase 2

This report intentionally does not delete or alter any rows. The following decisions are flagged for Phase 2, with the evidence needed to make each one:

1. **C-prefixed invoices (cancellations):** clearly returns/cancellations linked to an original sale. Needs a rule for how they net against revenue and customer purchase counts.
2. **Negative quantity on non-C invoices:** likely internal stock corrections (Price = 0, no Customer ID) -- probably excluded entirely from customer/revenue analytics, but distinct from cancellations.
3. **'A'-prefixed invoices / negative price ('Adjust bad debt'):** accounting write-offs, no Customer ID -- candidate for exclusion.
4. **Administrative StockCodes** (postage, carriage, bank charges, fees, manual, test rows): candidate for exclusion from product/customer purchase-behavior analysis; may still matter for total company revenue reconciliation.
5. **Zero-price rows:** needs investigation into what they represent (free items, promotions, data errors) before deciding treatment.
6. **Duplicate rows:** needs a decision on whether they represent genuine repeated line entries or export artifacts.
7. **Missing Customer ID (22.77% of rows):** excluded from all customer-level analysis by definition of customer grain (Phase 0).
