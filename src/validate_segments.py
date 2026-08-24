"""
Phase 8 - Segment Validation

Tests whether the 8 RFM segments from Phase 7 are actually statistically
and behaviorally different from each other, not just different by
construction (they're partly tautological on R/F/M since segments are
DEFINED from R/F/M scores -- so the real test here is on metrics NOT used
to build the segments, plus formal confirmation on R/F/M themselves).

WHY KRUSKAL-WALLIS INSTEAD OF ANOVA
------------------------------------
What: Levene's test for homogeneity of variance was run first, across all
      8 segments, for Recency, Frequency, Monetary, and active_months.
      Result: variances are significantly unequal for all four (p < 0.001
      in every case -- see printed output). Combined with the heavy
      right-skew already established in Phase 6 (Monetary skew=27.0,
      Frequency skew=12.5), two of ANOVA's core assumptions (normality,
      homogeneity of variance) are both violated.
Why this matters: running ANOVA anyway would produce a p-value that looks
      authoritative but rests on assumptions this data doesn't meet --
      exactly the "p<0.05, therefore great" trap the project brief warns
      against.
What we use instead: Kruskal-Wallis H-test (non-parametric, rank-based,
      doesn't assume normality or equal variance) as the primary
      significance test, followed by Dunn's post-hoc test with
      Bonferroni correction to identify which SPECIFIC segment pairs
      differ (Kruskal-Wallis alone only tells us "not all groups are
      equal," not which ones).
What could go wrong: Dunn's test with Bonferroni correction across 8
      segments means C(8,2)=28 pairwise comparisons per metric --
      Bonferroni is conservative and could mask real pairwise differences
      (Type II error risk). Noted as a limitation, not silently ignored.
How this is validated: cross-checked against a metric NOT used to build
      the segments (active_months) to confirm the segments aren't just
      trivially different because they were defined from R/F/M.
"""

import pandas as pd
from scipy import stats
import scikit_posthocs as sp
from pathlib import Path

SEG_PKL = Path("data/processed/rfm_segmented.pkl")
CUSTOMERS_PKL = Path("data/processed/customers.pkl")

METRICS = ["recency_days", "frequency", "monetary", "active_months"]


def load_data():
    seg = pd.read_pickle(SEG_PKL)
    customers = pd.read_pickle(CUSTOMERS_PKL)
    seg = seg.merge(customers[["customer_id", "active_months"]], on="customer_id")
    return seg


def levene_tests(seg: pd.DataFrame) -> dict:
    segments = seg["segment"].unique().tolist()
    results = {}
    for metric in METRICS:
        groups = [seg.loc[seg["segment"] == s, metric] for s in segments]
        stat, p = stats.levene(*groups)
        results[metric] = {"statistic": stat, "p_value": p, "equal_variance": p >= 0.05}
    return results


def kruskal_tests(seg: pd.DataFrame) -> dict:
    segments = seg["segment"].unique().tolist()
    results = {}
    for metric in METRICS:
        groups = [seg.loc[seg["segment"] == s, metric] for s in segments]
        stat, p = stats.kruskal(*groups)
        results[metric] = {"statistic": stat, "p_value": p, "significant": p < 0.05}
    return results


def dunn_posthoc(seg: pd.DataFrame, metric: str) -> pd.DataFrame:
    return sp.posthoc_dunn(seg, val_col=metric, group_col="segment", p_adjust="bonferroni")


def count_non_distinguishable_pairs(dunn_result: pd.DataFrame, alpha: float = 0.05) -> list:
    """Return segment pairs that are NOT significantly different after correction."""
    pairs = []
    segs = dunn_result.columns.tolist()
    for i, s1 in enumerate(segs):
        for s2 in segs[i + 1:]:
            p = dunn_result.loc[s1, s2]
            if p >= alpha:
                pairs.append((s1, s2, p))
    return pairs


def main():
    seg = load_data()

    print("=" * 70)
    print("LEVENE'S TEST (variance homogeneity -- ANOVA assumption check)")
    print("=" * 70)
    for metric, res in levene_tests(seg).items():
        flag = "OK for ANOVA" if res["equal_variance"] else "VIOLATED"
        print(f"  {metric}: stat={res['statistic']:.2f}, p={res['p_value']:.2e} -> {flag}")

    print()
    print("=" * 70)
    print("KRUSKAL-WALLIS H-TEST (non-parametric, primary test)")
    print("=" * 70)
    kw_results = kruskal_tests(seg)
    for metric, res in kw_results.items():
        print(f"  {metric}: H={res['statistic']:.2f}, p={res['p_value']:.2e}, significant={res['significant']}")

    print()
    print("=" * 70)
    print("DUNN'S POST-HOC TEST (Bonferroni-corrected pairwise comparisons)")
    print("=" * 70)
    for metric in METRICS:
        dunn = dunn_posthoc(seg, metric)
        non_distinct = count_non_distinguishable_pairs(dunn)
        print(f"\n  {metric}: {len(non_distinct)} of 28 segment pairs are NOT significantly different (alpha=0.05, Bonferroni)")
        for s1, s2, p in non_distinct:
            print(f"    {s1} vs {s2}: p={p:.3f}")

    return seg, kw_results


if __name__ == "__main__":
    main()
