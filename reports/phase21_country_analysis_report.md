# Phase 21 - Country Analysis Report

## Objective

Break down customer behavior, revenue, and CLV by country, with an
explicit minimum sample threshold so the many tiny country populations
don't get overinterpreted as reliable business signals.

Implementation: `src/country_analysis.py`, tested in
`src/test_country_analysis.py` (7 tests, all passing). Full pipeline:
**120/120 tests passing.**

## Minimum Sample Threshold

**Countries with fewer than 30 RFM-valid customers are grouped into
"Other (small sample)"**, not dropped and not reported individually. Of
41 countries in the dataset, only **4 qualify**: United Kingdom (5,348),
Germany (106), France (94), Spain (35) — together 95.1% of the customer
base. The remaining 285 customers span 37 countries, several with single-
digit customer counts (e.g. Japan: 10, USA: 8) — far too few to support
any per-country conclusion.

## Country Summary

| Country | Customers | Total Revenue (£) | AOV (£) | Avg Recency (days) | Avg Frequency | % Recently Active | CLV Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| United Kingdom | 5,348 | 13,870,824 | 345.60 | 203.5 | 6.26 | 48.8% | 69.2% |
| Other (small sample) | 285 | 1,956,938 | 871.69 | 214.5 | 6.35 | 43.9% | 75.4% |
| Germany | 106 | 379,213 | 360.47 | 131.7 | 7.18 | 65.1% | 68.9% |
| France | 94 | 301,809 | 423.30 | 121.6 | 6.37 | 64.9% | 62.8% |
| Spain | 35 | 81,783 | 486.81 | 164.4 | 3.97 | 57.1% | 71.4% |

## Finding: Germany and France Customers Are More Consistently Engaged Than UK Customers

**Observation:** Germany and France both show notably lower average
Recency (131.7 and 121.6 days vs. UK's 203.5) and higher % recently
active (65.1% and 64.9% vs. UK's 48.8%).

**This was tested, not just eyeballed:** Kruskal-Wallis across the 4
qualifying countries on Recency: **H=28.74, p=2.54e-06** — highly
significant. Pairwise Mann-Whitney confirms both individual comparisons:
UK vs. Germany p=0.0004, UK vs. France p=0.0001. Monetary also differs
significantly across the 4 countries (H=18.07, p=4.26e-04).

**Possible explanation (not proven causally):** cross-border purchases
from a UK-based retailer likely involve higher shipping costs and more
deliberate purchase intent than a domestic UK order — a customer in
Germany or France choosing to buy from this retailer at all may be
self-selecting toward higher engagement than the average UK customer,
who could include more casual, low-commitment buyers. This is a
plausible story consistent with the data, not something this dataset can
directly confirm (no data on marketing channel, customer acquisition
source, or purchase motivation).

**Business implication:** international customers, while a small
population, appear to convert into more consistently active buyers once
acquired. This doesn't mean the business should suddenly prioritize
international expansion based on this alone (sample sizes are modest —
Spain's n=35 is right at the threshold), but it's a legitimate,
statistically supported signal worth further investigation with better
data (e.g. acquisition channel), not a definitive strategic conclusion.

## Caution Directly Illustrated: Why the Threshold Matters

The "Other (small sample)" group shows an average order value of
**£871.69** and average Monetary of **£6,866.45** — both far higher than
any qualifying country. Investigating this is exactly why the threshold
exists: this aggregate is highly sensitive to a small number of large
international orders among a group with n=285 spread across 37 countries
(many with single-digit counts). Reporting, say, "Japan's average order
value is £X" from 10 customers would be presenting noise as a business
insight. The grouped "Other" figure is disclosed for completeness but
should not be read as characterizing any specific country's typical
customer.

## What This Means Going Into Phase 22

Country is confirmed to be a real, statistically meaningful axis of
customer behavior for the UK/Germany/France/Spain population, but the
overwhelming UK concentration (91.1% of customers) means country-level
segmentation should remain a secondary lens, not a primary one, in the
business recommendations phases (28-29). Phase 22 returns to a different
axis — quantifying the impact of proper return/cancellation treatment,
building directly on the Phase 2-3 cleaning decisions.
