"""
Phase 24 - Dashboard Data Export

Exports the aggregated data the dashboard (dashboard/index.html) is built
from, as a reproducible step separate from the dashboard file itself.
Re-running this script regenerates dashboard/data_export/dashboard_data.json
from the current state of the validated pipeline (Phases 1-23) -- the
dashboard never computes anything itself, it only displays what this
script exports.
"""

import pandas as pd
import json
from pathlib import Path

OUTPUT_JSON = Path("dashboard/data_export/dashboard_data.json")
SEGMENT_ORDER = [
    "Champions", "Loyal Customers", "Potential Loyalists", "New Customers",
    "Need Attention", "At Risk", "About To Sleep", "Hibernating",
]


def export():
    merged = pd.read_pickle("data/processed/rfm_clv_combined.pkl")
    customers = pd.read_pickle("data/processed/customers.pkl")
    pct = pd.read_pickle("data/processed/cohort_retention_pct.pkl")
    rar = pd.read_pickle("data/processed/revenue_at_risk.pkl")
    sim = pd.read_pickle("data/processed/retention_simulation.pkl")
    country = pd.read_pickle("data/processed/country_analysis.pkl")

    overview = {
        "total_customers": int(len(merged)),
        "total_revenue": round(float(merged["monetary"].sum()), 2),
        "total_orders": int(customers["order_count"].sum()),
        "aov": round(float(merged["monetary"].sum() / customers["sale_order_count"].sum()), 2),
        "pct_active_90d": round(float((merged["recency_days"] <= 90).mean() * 100), 1),
    }

    seg_counts = merged["segment"].value_counts().reindex(SEGMENT_ORDER).fillna(0).astype(int)
    seg_revenue = merged.groupby("segment")["monetary"].sum().reindex(SEGMENT_ORDER).fillna(0)
    segments = {
        "labels": SEGMENT_ORDER,
        "counts": seg_counts.tolist(),
        "revenue": [round(float(x), 2) for x in seg_revenue.tolist()],
    }

    milestones = {}
    for m in [1, 3, 6, 12]:
        vals = pct[m].dropna()
        milestones[f"M{m}"] = {"mean": round(float(vals.mean()), 1), "n_cohorts": int(len(vals))}

    country_summary = country.groupby("country_group").agg(
        customers=("customer_id", "size"), revenue=("monetary", "sum"), avg_recency=("recency_days", "mean")
    ).round(1)

    rfm_stats = {
        "recency": merged["recency_days"].describe().round(1).to_dict(),
        "frequency": merged["frequency"].describe().round(1).to_dict(),
        "monetary": merged["monetary"].describe().round(1).to_dict(),
    }

    # Per-segment RFM stats -- powers the Page 3 filter drill-down (Phase 25 fix)
    rfm_stats_by_segment = {}
    for seg in SEGMENT_ORDER:
        sub = merged[merged["segment"] == seg]
        rfm_stats_by_segment[seg] = {
            "recency": sub["recency_days"].describe().round(1).to_dict(),
            "frequency": sub["frequency"].describe().round(1).to_dict(),
            "monetary": sub["monetary"].describe().round(1).to_dict(),
        }

    # Top-10 at-risk customers by predicted CLV -- powers the Page 4
    # drill-down table (Phase 25 fix). Winsorized at the same 99th
    # percentile as Phase 19/20, AND additionally excludes customers with
    # negative historical monetary -- a known data-artifact pattern
    # (Phase 6/18/22, e.g. Customer 12346) that would otherwise put an
    # unreliable prediction at the top of an actionable target list.
    cap = merged.loc[merged["predicted_clv_final"].notna(), "predicted_clv_final"].quantile(0.99)
    merged["clv_winsorized"] = merged["predicted_clv_final"].clip(upper=cap)
    at_risk_segs = ["At Risk", "About To Sleep", "Hibernating", "Need Attention"]
    at_risk_targetable = merged[
        merged["segment"].isin(at_risk_segs) & merged["clv_winsorized"].notna() & (merged["monetary"] > 0)
    ]
    top_targets = at_risk_targetable.nlargest(10, "clv_winsorized")[
        ["customer_id", "segment", "recency_days", "frequency", "monetary", "clv_winsorized"]
    ].round(2)

    output = {
        "overview": overview,
        "segments": segments,
        "cohort_milestones": milestones,
        "country": country_summary.reset_index().to_dict(orient="records"),
        "revenue_at_risk": {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in rar.to_dict().items()},
        "retention_simulation": sim[sim["win_back_rate_label"] == "20%"].reset_index().to_dict(orient="records"),
        "rfm_stats": rfm_stats,
        "rfm_stats_by_segment": rfm_stats_by_segment,
        "top_at_risk_targets": top_targets.to_dict(orient="records"),
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Exported dashboard data -> {OUTPUT_JSON}")
    return output


if __name__ == "__main__":
    export()
