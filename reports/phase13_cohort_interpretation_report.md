# Phase 13 - Cohort Interpretation Report

## Objective

Turn the retention charts into tested findings using
**Observation → Evidence → Possible Explanation → Business Implication**,
without asserting causality the data can't support. The December 2009
cohort is excluded from every analysis in this phase, consistent with the
Phase 10 left-censoring finding.

Implementation: `src/interpret_cohorts.py`, tested in
`src/test_interpret_cohorts.py` (5 tests, all passing). Full pipeline:
**71/71 tests passing.**

---

## Finding 1: A Large, Consistent Early Retention Drop

**Observation:** Retention collapses from 100% at M0 to a mean of 20.4%
at M1 — an average drop of **79.6 percentage points** in a single month,
across every non-left-censored cohort (range 9.2%-31.7%).

**Evidence:** Measured directly from the Phase 11 matrix, excluding
2009-12. No cohort in the dataset avoids this pattern.

**Possible explanation:** This is a structural feature of non-subscription
retail, not a business failure specific to this company. Most customers
in a giftware retailer buy once for a specific occasion (a gift, a
one-time need) and don't have a natural reason to return the following
month. This is consistent with Phase 6's finding that 27.7% of all
customers are single-purchase, and Phase 7's finding that "New Customers"
and "About To Sleep/Hibernating" together make up a large share of the
customer base.

**Business implication:** A CRM manager should not be alarmed by a large
M0→M1 drop on its own — it appears to be the baseline behavior of this
business model, not evidence of a specific retention problem. The more
useful question is what happens *after* the first month (Finding 2), and
which specific customers are worth targeting (Phase 7/20), not the size
of the initial drop itself.

---

## Finding 2: No Statistically Significant Long-Term Decay Beyond the Initial Drop

**Observation:** Naively averaging M1 (20.4%), M3 (20.7%), M6 (16.8%), M9
(14.0%), M12 (16.6%) looks like a gradual decline.

**Evidence — and why the naive average is misleading:** Each of those
averages is computed over a *different, shrinking set of cohorts* (23,
21, 18, 15, 12 respectively), because later cohorts haven't reached later
milestones yet. Comparing M1's average (across 23 cohorts) to M12's
average (across only 12 *earlier* cohorts) confounds "change over
lifecycle" with "which cohorts happen to be old enough to measure."

**A fair test:** Restricting to the 12 cohorts that have **both** M1 and
M12 observable, and running a paired Wilcoxon signed-rank test on the
same cohorts: mean M1 = 18.8%, mean M12 = 16.6%, **p = 0.110 — not
statistically significant** at α=0.05.

**Possible explanation:** There may be a small real decline (the point
estimate does drop ~2 points), but with only 12 paired cohorts, this
project does not have enough statistical power to distinguish a genuine
gradual decay from random cohort-to-cohort noise.

**Business implication:** **Do not claim retention continues declining
significantly after the first month** — the evidence doesn't support
that. The story is better characterized as "sharp initial drop, then a
plateau around 15-21% that doesn't show a statistically confirmed further
decline through month 12." This is a meaningfully different, more
optimistic message for a CRM manager than "retention keeps eroding."

---

## Finding 3: No Evidence That Later Cohorts Retain Worse (or Better)

**Observation:** A visual read of the Phase 12 heatmap might suggest
cohort behavior looks a little "spottier" for later cohorts, tempting a
narrative like "recent cohorts are lower quality."

**Evidence:** Spearman correlation between acquisition order (time) and
early retention:
- M1 retention vs. cohort order: ρ = 0.283, **p = 0.191 — not significant**
- M3 retention vs. cohort order: ρ = -0.214, **p = 0.351 — not significant**

The two correlations don't even agree in direction (M1 trends slightly
positive, M3 slightly negative), which is itself evidence against a real
underlying trend rather than for one.

**Possible explanation:** With only 21-23 cohorts and retention
percentages that are themselves noisy (based on cohort sizes as small as
28-378 customers), there simply isn't enough statistical power to detect
a modest trend even if one existed. This is a **limitation of the data
size**, not proof that no trend exists — absence of significance is not
evidence of absence, and this project treats it accordingly.

**Business implication:** **This project makes no claim that acquisition
quality changed over time.** If a stakeholder wants to test this
hypothesis with confidence, more data (a longer observation window, or a
larger customer base) would be needed. Any marketing/channel narrative
built on "cohorts got worse" would currently be unsupported speculation.

---

## Finding 4: Acquisition Volume Has Seasonality — Retention Behavior Does Not

**Observation:** Cohort *size* varies substantially by acquisition month:
October averages 299 new customers, versus 135-144 in July/August — a
plausible signature of a gift retailer's pre-holiday shopping ramp-up.

**Evidence — cohort size by calendar month (mean, 2009-12 excluded):**
```
Jan 220   Apr 200   Jul 144   Oct 299
Feb 250   May 183   Aug 135   Nov 258
Mar 312   Jun 189   Sep 216   Dec  52
```
(December's low average of 52 partly reflects the truncated final month —
only 2010-12 and 2011-12 exist in the data, and 2011-12 has just 28
customers from a 9-day partial month, per Phase 11's caveat.)

Testing whether *retention behavior* (not just acquisition volume)
differs for holiday-acquired cohorts (Oct/Nov/Dec) vs. others: mean M1
retention 19.7% (holiday) vs. 20.6% (other), Mann-Whitney U test
**p = 0.691 — not significant**.

**Possible explanation:** More people buy gifts in the pre-holiday
season, which plausibly explains the acquisition volume pattern. But
those holiday-acquired customers don't appear to behave differently
afterward — they return (or don't) at roughly the same rate as customers
acquired at other times of year.

**Business implication:** A hypothesis like "holiday shoppers are
low-quality, one-off customers we shouldn't bother retaining" is **not
supported by this data**. Seasonal acquisition campaigns don't appear to
bring in a systematically worse cohort in terms of early retention — the
volume swing is real, but it isn't evidence of a quality trade-off.

---

## Summary Table

| Finding | Statistically confirmed? |
|---|---|
| Large M0→M1 drop (~80 points) | Yes — directly measured, consistent across cohorts |
| Long-term decay beyond M1 | **No** — p=0.110, not significant |
| Later cohorts retain worse | **No** — p=0.191 / p=0.351, not significant |
| Holiday cohorts retain differently | **No** — p=0.691, not significant |
| Acquisition volume has seasonality | Yes — directly observed pattern by month |

## What This Means Going Into Phase 14

Three of five investigated patterns turned out to be **not statistically
supported**, despite looking plausible from a visual read of the charts.
This is intentional and useful — Phase 14 (Segment × Cohort) and later
business recommendation phases should lean on the two confirmed findings
(large early drop, seasonal acquisition volume) and avoid building
recommendations on the three unconfirmed narratives, however tempting
they might look on a chart.
