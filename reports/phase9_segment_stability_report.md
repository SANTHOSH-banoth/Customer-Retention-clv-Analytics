# Phase 9 - Segment Stability Report

## Objective

Test whether the Phase 7 segmentation is robust to reasonable alternative
choices — not "is this the only possible segmentation" but "would a
slightly different, equally defensible choice tell a different business
story?"

Implementation: `src/stability.py`, tested in `src/test_stability.py` (5
tests, all passing). Full pipeline: **49/49 tests passing.**

## Five Sensitivity Tests, Compared to the Phase 7 Baseline

| Variation | Customers changing segment | % changed |
|---|---:|---:|
| 4-bin (quartile) instead of 5-bin (quintile) for Recency/Monetary | 1,445 / 5,868 | **24.6%** |
| Gross revenue instead of net revenue for Monetary | 17 / 5,868 | 0.3% |
| Snapshot date +7 days | 0 / 5,868 | 0.0% |
| Snapshot date +30 days | 0 / 5,868 | 0.0% |
| Monetary winsorized at 99th percentile | 0 / 5,868 | 0.0% |

## Finding 1: Snapshot date and extreme-value handling are non-issues

Consistent with Phase 6's recency-rank finding, shifting the snapshot date
by up to 30 days produces **zero** segment changes — expected, since a
constant shift doesn't change relative rank and segmentation is entirely
rank/quantile-based. Winsorizing Monetary at the 99th percentile before
scoring also produces zero changes, because capping a handful of extreme
values doesn't move anyone across a quantile boundary when those extreme
values were already comfortably inside the top bin.

## Finding 2: The returns-netting decision (Phase 3) barely matters here

Only 17 customers (0.3%) change segment when Monetary is computed from
gross revenue instead of net revenue. This is a useful cross-check on
Phase 3's choice: **using net vs. gross revenue matters a great deal for
accurate financial reporting (£19.30M vs £20.45M, Phase 3), but has almost
no effect on which segment a customer lands in**, because segmentation is
rank-based and returns are relatively rare/small per customer relative to
the gaps between quantile boundaries.

## Finding 3: Quintile vs quartile is genuinely the sensitive dimension — and here's exactly why

24.6% of customers change segment when Recency/Monetary are scored on a
4-point instead of 5-point scale. This is the only material instability
found, and it deserved a real explanation rather than just being reported
as a scary percentage.

**Root cause, confirmed directly:** the segment rules (Phase 7) use fixed
absolute score thresholds like `r_score >= 4`. On a 5-point scale,
`r_score >= 4` means "top 40% most recent." On a 4-point scale, `r_score
>= 4` means "top 25% most recent" — a stricter bar. Directly checking the
1,266 baseline Champions: **30.5% of them have `r_score = 4` on the
5-scale (i.e. they were in the "top 40%, not quite top 20%" band)**, and
when rescored on a 4-point scale, that same recency percentile no longer
clears the `>= 4` bar, demoting them out of Champions even though nothing
about their actual purchase behavior changed.

**This means the observed 24.6% instability is substantially a rule-design
artifact — reusing scale-dependent absolute thresholds — rather than
evidence that customers' underlying RFM values are unstable.** A fairer
comparison would redefine segment rules in terms of percentile bands
("top 20%" for Champions) rather than raw score values, so the rule means
the same thing regardless of bin count. This is flagged as a specific,
fixable limitation of the current rule design, not papered over.

## Finding 4: Does the headline business conclusion survive?

Phase 7's central finding was that Champions + Loyal Customers = ~36% of
customers but **85.3%** of historical value. Recomputing this under the
quartile variant (the most disruptive scenario tested):

```
Champions + Loyal Customers (quartile variant): 84.9% of value
```

**This is essentially unchanged (85.3% → 84.9%).** Even though individual
customers move between segment labels under the quartile scheme, the
*aggregate* business conclusion — a small, high-value customer base
concentrates the overwhelming majority of revenue — is highly robust. The
label a specific customer gets ("Champion" vs "Loyal Customer") is more
sensitive to bin-count choice than the overall shape of the value
concentration is.

## What This Means Going Into Phase 10

1. Snapshot date, extreme-value handling, and the net-vs-gross revenue
   choice are all confirmed safe — no further caution needed there.
2. The 5-bin (quintile) scheme from Phase 7 is retained as-is. Switching
   to 4 bins would require rewriting the segment rules in percentile
   terms to be a fair comparison, which is out of scope for this project
   but explicitly documented as a known improvement opportunity (belongs
   in Phase 33's Limitations section).
3. The aggregate revenue-concentration story (small % of customers, ~85%
   of value) is the most defensible number to carry into business
   recommendations (Phase 28-29) — it survives the largest stress test
   applied in this phase, unlike individual segment membership.
4. The At Risk vs Need Attention overlap flagged in Phase 8 is a separate
   concern from bin-count sensitivity — it exists even at the baseline
   5-bin scheme and reflects a genuine (if narrow) Recency-only
   distinction, not an artifact of this phase's tests.
