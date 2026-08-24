# Phase 8 - Segment Validation Report

## Objective

Test whether the 8 RFM segments from Phase 7 are actually meaningfully
different from each other — not just "p < 0.05, therefore great," but a
real answer to: *are these segments different enough to justify different
business actions?*

Implementation: `src/validate_segments.py`, tested in
`src/test_validate_segments.py` (6 tests, all passing). Full pipeline:
**44/44 tests passing.**

## Step 1: Checking ANOVA's Assumptions Before Using It

Levene's test for homogeneity of variance was run across all 8 segments
for four metrics: Recency, Frequency, Monetary, and active_months (this
last one deliberately **not** used to build the segments — see Step 3).

```
recency_days:   p = 0.00e+00  -> variance homogeneity VIOLATED
frequency:      p = 1.14e-136 -> variance homogeneity VIOLATED
monetary:       p = 1.88e-40  -> variance homogeneity VIOLATED
active_months:  p = 0.00e+00  -> variance homogeneity VIOLATED
```

Combined with the heavy right-skew already established in Phase 6
(Monetary skew=27.0, Frequency skew=12.5), two of ANOVA's core assumptions
are both violated. **Decision: use Kruskal-Wallis (non-parametric,
rank-based) instead of ANOVA.** This is exactly the check the project
brief asked for — not blindly running ANOVA and reporting a p-value that
looks authoritative but rests on assumptions this data doesn't meet.

## Step 2: Kruskal-Wallis H-Test (primary significance test)

```
recency_days:   H=4875.04, p=0.00e+00, significant=True
frequency:      H=5258.00, p=0.00e+00, significant=True
monetary:       H=4042.62, p=0.00e+00, significant=True
active_months:  H=5031.85, p=0.00e+00, significant=True
```

All four metrics differ significantly across the 8 segments as a whole.
With n=5,868, this alone is not surprising or especially informative —
large samples make almost any real difference statistically significant.
The more useful question is **which specific segment pairs differ**,
answered next.

## Step 3: Dunn's Post-Hoc Test (Bonferroni-corrected pairwise comparisons)

28 pairwise comparisons per metric (C(8,2)). Segment pairs that are **NOT**
significantly different after Bonferroni correction (α=0.05):

| Metric | Non-distinguishable pairs (of 28) |
|---|---|
| Recency | Loyal Customers vs Need Attention; New Customers vs Potential Loyalists |
| Frequency | About To Sleep vs Hibernating; At Risk vs Need Attention; Hibernating vs New Customers |
| Monetary | At Risk vs Need Attention; At Risk vs Potential Loyalists; Hibernating vs New Customers; Need Attention vs Potential Loyalists |
| active_months | About To Sleep vs Hibernating; At Risk vs Need Attention; At Risk vs Potential Loyalists; Hibernating vs New Customers |

**Important limitation, stated plainly:** Bonferroni correction across 28
comparisons is conservative and can mask real pairwise differences (higher
Type II error risk than an uncorrected test). Some of these "not
significant" results might reflect the correction's conservatism rather
than true equivalence. Not treated as definitive — flagged as a limitation.

## Step 4: Interpreting the Overlaps — Is This a Problem?

The recurring pattern is that segment pairs sharing an overlap almost
always differ on the **one metric that's supposed to distinguish them**,
even when they don't differ on others. This is the expected, healthy
pattern for a segmentation built on combined R+F+M rules, not evidence
that segments are redundant:

- **New Customers vs Potential Loyalists** — statistically indistinguishable
  on Recency (both require R≥4) but built to differ on Frequency. Expected.
- **About To Sleep vs Hibernating / Hibernating vs New Customers** — overlap
  on Frequency and active_months (both groups skew toward low order
  counts), but this is a Frequency-scoring artifact from the large
  single-purchase population (Phase 6/7), not a segmentation failure.

**One overlap deserves closer scrutiny: At Risk vs Need Attention.**
These two are statistically indistinguishable on Frequency, Monetary,
*and* active_months — three of four metrics. Directly checking their
medians:

```
                recency_days  frequency  monetary  active_months
At Risk                377.0        3.0    842.18            3.0
Need Attention          100.5        3.0    918.15            3.0
```

They are behaviorally near-identical **except for Recency** (377 vs 100.5
days — a huge, business-relevant gap). This is confirmed statistically:
Dunn's test shows Recency differs significantly between them (p < 0.05)
while Frequency does not (p ≥ 0.05) — verified directly in
`test_at_risk_and_need_attention_differ_on_recency_not_other_metrics`.

**Conclusion: this is a real, useful distinction, not redundancy.** A
customer who buys moderately (F=3, ~£850-900 monetary) but hasn't
purchased in over a year (At Risk) needs different handling than one
buying at the same rate who purchased within the last few months (Need
Attention) — recency is precisely the urgency signal a CRM manager cares
about. Keeping them separate is the right call, though this pairing is
flagged as one to re-examine in Phase 9 (Segment Stability) if cutoffs
shift.

## Directional Sanity Checks

Beyond "a statistical difference exists," two direct sanity checks confirm
the differences point the expected direction:
- Champions have significantly *lower* (better) median Recency than
  Hibernating — verified.
- Champions have significantly *higher* median Monetary than New
  Customers — verified.

## What This Means Going Into Phase 9

The segmentation passes validation: it is statistically justified
(Kruskal-Wallis significant on all four metrics, including one not used
to construct the segments), and the handful of pairwise overlaps found
have sensible business explanations rather than indicating redundant
labels. The one pairing worth re-examining under different cutoff choices
is **At Risk vs Need Attention**, since their separation currently rests
almost entirely on the Recency cutoff at R≤2 — Phase 9 will test how
stable that boundary is.
