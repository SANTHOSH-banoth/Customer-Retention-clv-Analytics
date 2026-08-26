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

    output = {
        "overview": overview,
        "segments": segments,
        "cohort_milestones": milestones,
        "country": country_summary.reset_index().to_dict(orient="records"),
        "revenue_at_risk": {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in rar.to_dict().items()},
        "retention_simulation": sim[sim["win_back_rate_label"] == "20%"].reset_index().to_dict(orient="records"),
        "rfm_stats": rfm_stats,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Exported dashboard data -> {OUTPUT_JSON}")
    return output


if __name__ == "__main__":
    export()
