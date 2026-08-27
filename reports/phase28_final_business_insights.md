# Phase 28 - Final Business Insights

## Objective

Produce 3-5 major findings, each following Finding → Evidence →
Interpretation → Business Implication → Recommended Action →
Measurement. Every number below is drawn directly from the validated,
reconciled pipeline (Phases 1-27) — nothing here is invented or
extrapolated beyond what was measured.

---

## Finding 1: Revenue Is Extremely Concentrated in a Small Customer Group

**Finding:** Champions and Loyal Customers together are 36.0% of the
customer base but generate 85.3% of all historical revenue.

**Evidence:** Phase 7 — Champions (1,266 customers, 21.6%) contribute
£11,530,710 (69.5% of revenue); Loyal Customers (847 customers, 14.4%)
contribute £2,614,980 (15.8%). Stress-tested in Phase 9 against a more
disruptive segmentation scheme (4-bin instead of 5-bin scoring): the
combined share only moved from 85.3% to 84.9% — confirmed robust, not an
artifact of one specific cutoff choice.

**Interpretation:** This is a far sharper concentration than the common
"80/20" rule of thumb. A relatively small number of repeat, high-spend
customers carry the overwhelming majority of the business's value.

**Business Implication:** Losing even a small number of Champions has an
outsized revenue impact compared to losing an equivalent number of
lower-tier customers. Retention effort and account-care investment should
scale with this concentration, not be spread evenly across the customer
base.

**Recommended Action:** Establish a proactive touchpoint cadence for the
Champions segment specifically (not folded into general marketing), and
monitor Champion → Loyal/At Risk migration monthly as an early-warning
signal (Phase 23 showed 26.9% of Champions moved down a tier over 5.4
months).

**Measurement:** Track the % of total revenue held by Champions + Loyal
Customers quarter over quarter; a material decline would indicate this
core group is eroding faster than it's being replenished.

---

## Finding 2: Retention Drops Sharply After First Purchase, Then Plateaus — It Does Not Continue Declining

**Finding:** Retention falls from 100% (M0) to a mean of 20.4% by M1, but
shows **no statistically significant further decline** through M12.

**Evidence:** Phase 13 — paired Wilcoxon signed-rank test on the 12
cohorts with both M1 and M12 observable: mean M1 = 18.8%, mean M12 =
16.6%, p = 0.110 (not significant). A naive average across all available
cohorts at each milestone (which naturally shrinks the sample at later
milestones) misleadingly looks like continued decline; the fair,
matched-cohort comparison does not support that.

**Interpretation:** The business's retention challenge is concentrated in
the first purchase cycle, not a slow ongoing leak. Once a customer
survives past month 1, their probability of remaining engaged does not
appear to keep eroding at a detectable rate through the first year.

**Business Implication:** Retention investment has the best evidence-based
case for concentrating on the M0→M1 transition (e.g. a second-purchase
incentive shortly after the first order) rather than spreading effort
evenly across a customer's first 12 months.

**Recommended Action:** Pilot a post-first-purchase engagement campaign
(e.g. a time-limited second-order incentive) targeted specifically at
customers within 30-45 days of their first purchase, and measure its
effect on M1 retention specifically.

**Measurement:** M1 retention rate for cohorts that received the pilot
campaign vs. a holdout cohort that didn't — this project's simulation
work (Phase 20) demonstrates the ROI-comparison methodology that would
apply here.

---

## Finding 3: Concentrated Retention Targeting Substantially Outperforms Broad Targeting

**Finding:** Targeting the top 25% of at-risk customers by predicted CLV
(572 customers) produces a higher expected net value (£33,414) than
targeting the entire at-risk population (2,802 customers, £32,914) or the
entire customer base (5,868 customers, £17,584) — at roughly 10-20% of
the cost.

**Evidence:** Phase 20 — ROI of 11.68x (Strategy C) vs. 2.35x (Strategy
B) vs. 0.60x (Strategy A) at a 20% assumed win-back rate. This ordering
(C best, A worst) held at every win-back rate tested (10%, 20%, 30%) —
Strategy A actually loses money at 10%. This directly reflects Phase 17's
finding that the top predicted-value decile captures ~49% of actual
future revenue, reaching ~82% of the theoretical best-case concentration.

**Interpretation:** A small, well-identified subset of at-risk customers
accounts for most of the recoverable value — the CLV model's ranking
ability (even with imperfect absolute £ precision, per Phase 17) is
strong enough to make this concentration usable for targeting decisions.

**Business Implication:** Broad "contact everyone who looks inactive"
retention campaigns are a measurably worse use of budget than a
tightly-scoped, CLV-ranked campaign — this is true across a range of
plausible win-back-rate assumptions, not just a single favorable
scenario.

**Recommended Action:** Redirect retention campaign budget toward the
CLV-ranked top-quartile at-risk list (Phase 25's dashboard drill-down
provides this list directly), rather than blanket "at risk" segment
campaigns.

**Measurement:** Compare actual recovered revenue (customers in the
targeted list who make a subsequent purchase within the campaign window)
against the assumed win-back rate used in this simulation, and update the
assumption with real data once a campaign has run.

---

## Finding 4: Naive Data Treatment Would Have Produced a Materially Wrong Picture of the Business

**Finding:** A shallow analysis that filters `Quantity > 0` without
classifying transaction types overstates total revenue by 6.9% and can
misrank an individual customer by over 5,800 positions.

**Evidence:** Phase 22 — naive total (£17,742,651) vs. correct Net
Merchandise Sales (£16,590,568). Customer 12346 ranks #19 (top 0.3%,
"Loyal Customers") under naive treatment but #5,852 of 5,868 ("At Risk",
negative net revenue) under correct treatment — because a £77,184
wholesale-scale order was fully cancelled 16 minutes after being placed,
and naive treatment never nets that out.

**Interpretation:** This is not a hypothetical risk — this dataset
contains real, concrete cases where uncleaned data would drive a wrong
business decision (e.g. flagging a customer with negative realized value
as a top-20 VIP target).

**Business Implication:** Any customer analytics built directly on raw
transaction exports, without explicit classification of returns,
cancellations, and non-merchandise charges, cannot be trusted for
individual-customer targeting decisions, even if aggregate totals look
approximately reasonable.

**Recommended Action:** If this analysis is operationalized into a
recurring reporting process (see Phase 32's production-analytics
discussion), the transaction classification logic built in this project
(Phase 2) must be a mandatory step before any customer-level output is
generated — not an optional cleanup pass.

**Measurement:** Periodic spot-audits comparing a sample of "naive"
top-customer rankings against the classified/netted rankings, to confirm
the classification pipeline continues catching cases like Customer 12346
as new data arrives.

---

## Finding 5: CLV Coverage Has a Real Gap Exactly Where It Would Be Most Useful

**Finding:** The New Customers segment (239 customers, 4.1% of the
customer base) has **0% CLV coverage** — no predicted future value is
available for any customer in the segment a business would most want an
early value estimate for.

**Evidence:** Phase 18 — mechanically caused by the calibration cutoff
(2011-06-30) predating nearly every customer who qualifies as "New" as of
the final snapshot (2011-12-10), since BG/NBD requires calibration-period
purchase history to fit on.

**Interpretation:** This is a structural limitation of the current
single-snapshot CLV design, not a data-quality problem — it would recur
in any live deployment unless the calibration cutoff is set to track a
rolling window close to "now."

**Business Implication:** Decisions about how much to invest in newly
acquired customers currently cannot be informed by this project's CLV
model at all — a real gap in an otherwise-validated system.

**Recommended Action:** For a production version of this system, use a
rolling (not fixed) calibration cutoff that stays close to the current
date, accepting a shorter calibration window in exchange for coverage of
recent acquisitions — a trade-off to test explicitly, not assume.

**Measurement:** Track CLV coverage % by segment on every refresh; New
Customers coverage should not remain at 0% in a properly designed
production pipeline.

---

## Summary Table

| # | Finding | Strength of Evidence |
|---|---|---|
| 1 | Revenue concentration (85.3% in 36% of customers) | Strong — stress-tested, robust |
| 2 | Retention plateaus, no proven long-term decay | Strong — formally tested, non-significant result reported honestly |
| 3 | Concentrated targeting beats broad targeting | Strong — robust across win-back-rate sensitivity |
| 4 | Naive data treatment materially misleads | Strong — concrete, reproducible example |
| 5 | CLV coverage gap for New Customers | Confirmed, structural limitation — not yet solved |

## What This Means Going Into Phase 29

These five findings, each grounded in specific measured evidence and
already stress-tested where appropriate, form the basis for Phase 29's
formal business recommendations — each recommendation traces directly
back to one of these findings, not to a new, unsupported claim.
