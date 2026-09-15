# Customer Retention & CLV Analytics Pipeline

An end-to-end analytics pipeline that turns raw e-commerce transaction data into customer retention insights, lifetime value predictions, and revenue-at-risk estimates — built on the [Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) dataset.

## What it does

The pipeline runs in 28 sequential phases, taking raw transactional data all the way to business-ready outputs:

1. **Data engineering** — ingest, clean, and compute revenue from raw transaction records
2. **Customer analytics** — RFM (Recency, Frequency, Monetary) segmentation, cohort analysis, retention matrices
3. **Predictive modeling** — Customer Lifetime Value (CLV) modeling with validation against a naive baseline
4. **Business insights** — revenue-at-risk estimation, retention simulation, country-level breakdowns, segment migration analysis
5. **Delivery** — a fully self-contained, offline-capable interactive HTML dashboard

## Highlights

- **149 passing tests** across 21 test files, validating the pipeline end-to-end
- **28 phase reports** (Markdown + figures) documenting each analytical step
- Interactive dashboard with KPI views, segment filters, and drill-down analysis — no external dependencies

## Tech stack

Python · Pandas · NumPy · scikit-learn · pytest · HTML/CSS/JS (dashboard)

## Project structure

```
src/        28 phase scripts + 21 test files
data/       raw and processed datasets (raw source data excluded from repo — see below)
reports/    per-phase Markdown reports and figures
dashboard/  self-contained interactive HTML dashboard
```

## Running it locally

1. Download the [Online Retail II dataset](https://archive.ics.uci.edu/dataset/502/online+retail+ii) and place it in `data/raw/`
2. Run the phase scripts in order (see `PACKAGE_NOTES.md` for the full list):
   ```
   python3 src/ingest.py
   python3 src/clean.py
   ...
   python3 src/export_dashboard_data.py
   ```
3. Verify with:
   ```
   python3 -m pytest src/ -q
   ```
4. Open `dashboard/index.html` in a browser to view the dashboard

## Dashboard

Open `dashboard/index.html` directly in a browser, or [view it live](#) *(add a GitHub Pages link here once enabled)*.
