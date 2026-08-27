# Phase 25 - Dashboard Design Review Report

## Objective

Review the Phase 24 dashboard as a CRM manager would, page by page,
against 8 fixed questions. Where the review surfaced a real gap, fix it
— not just note it — and re-verify.

Implementation changes: `src/export_dashboard_data.py` (2 new export
functions), `dashboard/index.html` (Page 3 KPI row + filter-reactive
table, Page 4 drill-down table). Tests: `src/test_dashboard_export.py`
now has 9 tests (4 new). Full pipeline: **141/141 tests passing.**

## Page 1: Customer Overview

1. **Who is this for?** CRM/Retention Manager — stated in the page header.
2. **What decision does it support?** Overall book-of-business health
   check — stated.
3. **Most important KPI?** Arguably "Active (90d)%" — the most directly
   retention-relevant number, though it's presented alongside four other
   KPIs of similar visual weight rather than emphasized as primary.
4. **What action follows?** If active% looks low, the natural next step
   is Page 3 (which segments are driving it) — this flow is implicit
   (separate tabs) rather than a literal link.
5. **Can the user drill down?** No cross-page filtering (disclosed as a
   scope limitation in Phase 24). A user must manually switch tabs.
6. **Any unnecessary visual?** No — both panels (segment revenue,
   country table) map to a real business question.
7. **Any ambiguous KPI?** Initially "Total Orders" could have been
   ambiguous (line items? invoices?) but the subtitle already reads
   "Distinct sale invoices" — checked and found adequate, no change
   needed.
8. **Are definitions documented?** Yes — a footnote defines "Active
   (90d)" and how AOV is computed.

**Finding, not fixed (accepted limitation):** the Active(90d)% KPI is a
single snapshot with no trend line or prior-period comparison, so a
viewer can't tell if 49.2% is improving or declining. This is a real
limitation of a one-time analytical snapshot (vs. a live, periodically
refreshed BI report) — documented here and in Phase 33's Limitations
section rather than fixed, since building a proper time series would
require re-deriving the whole pipeline at multiple historical dates
(the same scope issue already addressed explicitly in Phase 23).

## Page 2: Cohort Retention

1-2. Same audience/decision framing as Page 1, retention-specific.
3. **Most important KPI:** M3 (21.6% average, 22 of 25 cohorts
   observable) is the most trustworthy headline number — better coverage
   than M6/M12, more purchase-cycle time than M1.
4. **Action:** if a specific cohort's row looks anomalous, action = dig
   into that acquisition period — supported directly, since the full
   heatmap (not just aggregates) is shown.
5. **Drill down:** the heatmap itself IS the drill-down (all 25 cohorts
   visible) — no further drill-down needed for this page's purpose.
6. **Unnecessary visual:** none — one well-justified heatmap.
7. **Ambiguous KPI:** none found — "(avg)" is explicit in each card label.
8. **Definitions documented:** yes — gray-vs-zero and the December 2009
   left-censoring caveat are both stated directly under the heatmap.

**No changes made to this page** — review did not surface a gap.

## Page 3: RFM Segmentation — Two Real Gaps Found and Fixed

1-2. Audience/decision framing present and correct.
3. **Most important KPI — GAP FOUND:** this page had **zero KPI cards**,
   inconsistent with the other three pages and missing the single most
   quotable number in the whole project (Champions + Loyal Customers =
   85.3% of revenue from 36% of customers). **Fixed:** added a 4-KPI row
   (Segments Defined, Largest Segment, Most Valuable Segment, Champions +
   Loyal Share).
4. **Action:** now directly visible via the new KPI row rather than
   requiring the viewer to compute it from the chart.
5. **Drill down — GAP FOUND:** the segment filter dropdown updated the
   chart but **not** the RFM Distribution Summary table, which kept
   showing aggregate stats regardless of the selected segment — a real
   inconsistency, not a cosmetic one. **Fixed:** the table now re-renders
   per-segment when a segment is selected (e.g. selecting "At Risk" shows
   n=441, mean recency 376.4 days, mean monetary £1,038.80 — verified
   directly against Phase 7/19's published At Risk population figures).
   Required a genuinely new data export (`rfm_stats_by_segment`, tested
   in `test_rfm_stats_by_segment_counts_match_phase7_populations`).
6. **Unnecessary visual:** none.
7. **Ambiguous KPI:** none, post-fix.
8. **Definitions documented:** yes.

## Page 4: CLV & Retention Opportunities — One Real Gap Found, With a Trap Inside the Fix

1-2. Audience/decision framing present and correct — this page already
had the clearest "recommended action" statement of the four.
3. **Most important KPI:** "Revenue at Risk (winsorized)" — correctly
   given the risk-accent color treatment.
4. **Action:** already explicit ("prioritize Strategy C") in the
   footnote from Phase 24.
5. **Drill down — GAP FOUND:** the page told a manager *how many*
   customers to target and the expected ROI, but never *which*
   customers — no actionable list, the single biggest practical gap for
   a CRM tool. **Fixed:** added a "Top 10 At-Risk Customers by Predicted
   Value" table.
6. **Unnecessary visual:** none, post-fix.
7. **Ambiguous KPI:** "Total Predicted Value" could be misread as
   specifically the at-risk population's value (it isn't — it's across
   *all* CLV-covered customers). **Fixed:** relabeled to "Total Predicted
   Value (all covered)" with an updated subtitle.
8. **Definitions documented:** yes, post-fix (see below).

**The trap inside the fix — caught before shipping, not after:**
building the naive version of the "Top 10" table (sort all at-risk
customers by predicted CLV, descending) would have put **Customer
12346 — the confirmed data artifact from Phase 18/22 (a 74,215-unit
order placed then cancelled 16 minutes later, actual holdout revenue
£0) — at the very top of the list**, since the Phase 19 winsorization
caps extreme values but doesn't remove them from ranking, and 12346's
capped value still ties for the highest predicted CLV in the dataset.
Presenting this customer as the #1 recommended retention target would
have been actively wrong and would have undermined every piece of
careful data-quality work from Phases 2, 6, 18, 19, and 22. **Fix:** the
target list additionally excludes any customer with negative historical
Monetary (a defensible, explainable business rule — don't recommend
targeting based on a prediction for a customer whose realized value is
negative), verified directly by test
(`test_top_at_risk_targets_excludes_known_artifact_customer`). Customer
15749 (the genuine high-value At Risk case from Phase 18, £21,536
historical, £2,985 predicted) now correctly sits at #1 instead.

## What This Means Going Into Phase 26

The design review process caught and fixed three real issues (missing
Page 3 KPIs, a filter that silently didn't affect part of the page, and
a drill-down gap on Page 4) plus one near-miss (Customer 12346 almost
becoming the #1 recommended target) — exactly the kind of review this
phase exists for. All fixes were re-verified with a real browser
(Chromium, offline) before being considered complete, not just reviewed
by reading the code. Phase 26 (Final Data Quality Review) can now treat
the dashboard as reflecting the pipeline's validated findings accurately.
