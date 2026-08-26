# Phase 24 - BI Dashboard Report

## Objective

Build the four-page dashboard specified in the project brief, sourced
from the validated analytics in Phases 1-23.

## Tooling Decision — Stated Explicitly

**What:** the dashboard is built as a single self-contained HTML file
(`dashboard/index.html`) rather than a native Power BI or Tableau file.
**Why:** this project runs in a sandboxed Linux environment with no
Windows desktop and no Power BI Desktop / Tableau installation available
— those are proprietary desktop applications that cannot be installed
here. **Assumption:** an interactive, real-data HTML dashboard is an
acceptable and honest substitute for demonstrating the same BI/dashboard
skill set (KPIs, filtering, multi-page navigation, chart design) that
Power BI or Tableau would showcase, given the environment constraint.
**What could go wrong:** a hiring manager expecting a literal `.pbix` file
won't find one — this is disclosed clearly, not presented as if it were a
Power BI export. **How this is validated:** the dashboard reads from the
same `dashboard_data.json` export the pipeline produces (`src/
export_dashboard_data.py`), tested against the validated pipeline figures
(`src/test_dashboard_export.py`, 5 tests passing) — so the numbers shown
are provably the same numbers computed and validated in Phases 1-23, not
recalculated or re-entered by hand.

## Engineering Choice: Fully Self-Contained, Not CDN-Dependent

The first version linked Chart.js and Google Fonts from public CDNs. This
was deliberately changed: **Chart.js (204KB) is inlined directly into the
HTML file**, and Google Fonts were replaced with a system-font fallback
stack (`Fraunces → Palatino/Georgia`, `Inter → system-ui`, `IBM Plex Mono
→ Consolas/Menlo`). Verified by test
(`test_dashboard_html_file_exists_and_is_self_contained`) and confirmed
directly with a real browser (Chromium via Playwright) with **all network
requests blocked** — the dashboard renders completely correctly offline,
with zero failed requests. This matters for a portfolio deliverable: it
should open and work correctly regardless of the reviewer's network
environment, corporate firewall, or whether they're offline.

**A real bug was found and fixed during this verification, not
theoretical:** the first working version had `Chart.defaults.color = ...`
running at the top level of the script, unguarded. If Chart.js ever
failed to load for any reason, this single line threw an error that
silently halted the *entire* script — meaning none of the KPI cards or
data tables would populate either, even though they don't depend on
Chart.js at all. Fixed by guarding all `Chart` references, tested
directly in Node.js with `Chart` undefined to confirm the script now
completes successfully and every KPI/table still renders even if the
charting library is unavailable.

## Design Direction

Subject: a UK-based online giftware retailer's customer book, viewed by a
CRM/Retention Manager. Visual identity: a deep-navy "ledger" aesthetic —
vertical filing-tab navigation (the signature element, distinct from a
generic top-nav SaaS dashboard), a Fraunces-style serif for headers
(ledger/catalog feel), monospace for all numeric data (reinforces an
analytical, audited-figures tone), muted teal as the primary data color
and ochre/brick as risk/opportunity accents.

## Page 1: Customer Overview

KPIs: total customers (5,868), Net Merchandise Sales (£16,590,568), total
orders (44,370), average order value (£451), % active in last 90 days
(49.2%). Panels: revenue-by-segment bar chart (makes the Champions
concentration immediately visible) and the country breakdown table from
Phase 21 (with the small-sample threshold preserved).

## Page 2: Cohort Retention

KPIs: M1/M3/M6/M12 average retention with the **number of cohorts each
average is based on shown directly on the card** (e.g. "13 cohorts
observable" for M12) — so a viewer can't mistake a partial-coverage
average for a complete one. Main panel: the actual Phase 12 heatmap
image, embedded, with the gray-vs-zero distinction and the December 2009
left-censoring caveat both carried through into the dashboard caption.

## Page 3: RFM Segmentation

Interactive segment filter (a real `<select>` control that highlights the
chosen segment's bars in the chart — genuine client-side interactivity,
not a static image) alongside a combined bar+line chart showing % of
customers vs. % of revenue per segment side by side, plus the full RFM
summary statistics table from Phase 5-6.

## Page 4: CLV & Retention Opportunities

Answers "who should we act on first": at-risk population size and %,
revenue at risk (winsorized figure from Phase 19, with the raw figure
also shown in the supporting table for transparency), total predicted
future value, CLV coverage %, and the full Phase 20 retention-simulation
table with Strategy C's best-ROI result flagged with a visible pill.

## Design Review (Self-Administered, Per Phase 25's Upcoming Checklist)

Applying the questions Phase 25 will ask formally, informally here first:
who is each page for (stated directly in each page's header note), what
decision does it support (also stated), and is anything decorative rather
than functional — the four pages avoid extra charts that don't map to a
specific business question, consistent with the "every visualization must
answer a business question" instruction. A full critique against all 8
of Phase 25's questions is deferred to that phase, as intended.

## Scope Note: Filtering

Only the RFM Segmentation page has live interactive filtering (segment
highlight). Full cross-page filtering (date range, country, segment
propagating across all four pages simultaneously, as a real Power BI
report would support) was not built — the dashboard reads from a single
pre-aggregated JSON export rather than a live queryable data model, which
is a reasonable trade-off for a static HTML deliverable but a real
difference from a production BI tool. Documented here rather than implied
to be more interactive than it is.

## What This Means Going Into Phase 25

The dashboard is built and functionally verified (real browser, offline,
interactive filter tested). Phase 25 will formally review it page by page
against the 8-question checklist from the project brief, likely surfacing
refinements (e.g. whether the country table on Page 1 is the best use of
that space, or whether a KPI is redundant with another page).
