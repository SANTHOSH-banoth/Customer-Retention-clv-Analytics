"""
Phase 7 - RFM Segmentation

Builds interpretable 1-5 scores for Recency, Frequency, and Monetary, then
maps score combinations to business-labeled segments -- only where those
labels are backed by explicit, measurable rules and adequate population.

RECENCY AND MONETARY SCORING: standard quantiles
--------------------------------------------------
Phase 6 confirmed Recency and Monetary are near-continuous (592 and 5,768
distinct values respectively out of 5,868 customers), so pd.qcut produces
5 clean, evenly populated bins (~1,170-1,215 customers each, i.e. ~20%
each) for both. Recency labels are reversed (5 = most recent = best) since
lower day-counts are better; Monetary labels run naturally (5 = highest
spend = best).

FREQUENCY SCORING: custom business-driven bins, NOT quantiles
-----------------------------------------------------------------
What: pd.qcut on Frequency was tested first, per the project's instruction
      to start with quantile-based scoring. It FAILS here: requesting 5
      quantile bins collapses to only 4 effective bins (edges
      [1, 2, 4, 8, 392]), and requesting 4 or 3 bins collapses to only 3
      effective bins. This happens because 87 distinct Frequency values
      carry 5,868 customers, and 69.4% of customers have Frequency <= 5 --
      the tie mass at low values breaks quantile boundaries.
Why not just use rank-based tie-breaking to force 5 equal bins instead:
      That was considered and rejected. Rank-based quantiles would force
      customers who ALL bought exactly once (1,624 of them, 27.7% of the
      population) to be split arbitrarily across two or more score buckets
      based on tie-breaking order (e.g. row order or customer ID) that has
      no business meaning. That manufactures a distinction the data does
      not actually support.
What we use instead: fixed, business-interpretable breakpoints:
      F=1: exactly 1 order (single-purchase customers, flagged in Phase 6
           as a large, distinct population -- 27.7%)
      F=2: exactly 2 orders
      F=3: 3-4 orders
      F=4: 5-9 orders
      F=5: 10+ orders
      Measured populations: 1,624 / 941 / 1,151 / 1,186 / 966 -- i.e.
      16.0% to 27.7% per bin, all well-populated, no bin under 15%.
Assumption: these breakpoints are a defensible business reading of "how
      many times has this customer purchased," not a statistically
      derived optimum. Phase 8/9 will test whether they produce
      meaningfully different customer behavior and how sensitive segment
      membership is to moving these cutoffs.

SEGMENT LABELS
--------------
Assigned via an explicit, ordered rule waterfall (first matching rule
wins) over the R/F/M score combinations. Every customer gets exactly one
label; nothing is left unassigned. Population sizes for every resulting
segment are reported and must be non-trivial before this scheme is
accepted -- see reports/phase7_rfm_segmentation_report.md for the
population check. Statistical validation that these segments actually
behave differently is deferred to Phase 8, not asserted here.
"""

import pandas as pd
import numpy as np
from pathlib import Path

RFM_PKL = Path("data/processed/rfm.pkl")
OUTPUT_PKL = Path("data/processed/rfm_segmented.pkl")

FREQUENCY_BINS = [0, 1, 2, 4, 9, 10_000]
FREQUENCY_LABELS = [1, 2, 3, 4, 5]


def score_recency(rfm: pd.DataFrame) -> pd.Series:
    # Lower recency_days = more recent = better = higher score.
    # qcut assigns ascending bin order to ascending values, so we reverse labels.
    return pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1]).astype(int)


def score_frequency(rfm: pd.DataFrame) -> pd.Series:
    return pd.cut(rfm["frequency"], bins=FREQUENCY_BINS, labels=FREQUENCY_LABELS).astype(int)


def score_monetary(rfm: pd.DataFrame) -> pd.Series:
    return pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)


def assign_segment(row) -> str:
    r, f, m = row["r_score"], row["f_score"], row["m_score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if f >= 4 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f in (2, 3):
        return "Potential Loyalists"
    if r >= 4 and f == 1:
        return "New Customers"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r in (2, 3) and f <= 2:
        return "About To Sleep"
    if r == 1 and f <= 2:
        return "Hibernating"
    return "Need Attention"  # explicit catch-all, not a silent default


def build_segments(rfm: pd.DataFrame) -> pd.DataFrame:
    rfm = rfm.copy()
    rfm["r_score"] = score_recency(rfm)
    rfm["f_score"] = score_frequency(rfm)
    rfm["m_score"] = score_monetary(rfm)
    rfm["rfm_score_sum"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    rfm["rfm_score_code"] = (
        rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)
    )
    rfm["segment"] = rfm.apply(assign_segment, axis=1)
    return rfm


def main():
    rfm = pd.read_pickle(RFM_PKL)
    seg = build_segments(rfm)

    print("Segment population:")
    pop = seg["segment"].value_counts()
    pop_pct = (seg["segment"].value_counts(normalize=True) * 100).round(1)
    print(pd.DataFrame({"count": pop, "pct": pop_pct}))

    assert seg["segment"].isna().sum() == 0, "Every customer must get a segment label"
    assert seg["segment"].value_counts().min() >= 10, "No segment should be near-empty"

    seg.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")
    return seg


if __name__ == "__main__":
    main()
