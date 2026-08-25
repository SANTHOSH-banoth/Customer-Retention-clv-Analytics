"""
Phase 20 - Retention Strategy Simulation

Compares three retention-campaign targeting strategies. This is a
SCENARIO SIMULATION, not a causal experiment -- every number downstream
of an assumed win-back rate is a modeled projection under that
assumption, never a claim about what a campaign would actually cause.

OBSERVED DATA vs MODEL OUTPUT vs BUSINESS ASSUMPTION -- kept explicit throughout:
  OBSERVED:   customer counts, historical revenue, segment membership
  MODEL OUTPUT: predicted CLV (BG/NBD + Gamma-Gamma, Phase 16-19, with
                its own validated error characteristics from Phase 17)
  ASSUMPTION: cost per contact, win-back probability -- NOT derived from
              this dataset, since it contains no actual campaign history
              to estimate these from. Clearly labeled as assumptions.

STRATEGIES
----------
A. Target Everyone (5,868 customers) -- the naive "contact the whole
   list" approach.
B. Target All At Risk (2,802 customers) -- the Phase 19 at-risk
   population (segments: At Risk, About To Sleep, Hibernating, Need
   Attention).
C. Target High-Value At Risk (572 customers) -- the top 25% of the
   CLV-covered at-risk population (2,287 customers) by winsorized
   predicted CLV (Phase 19's outlier-corrected figure).

KEY MODELING ASSUMPTION -- STATED EXPLICITLY
------------------------------------------------
Expected recovered value is computed ONLY for at-risk customers with a
measured predicted CLV. Contacting an already-engaged customer
(Champions, Loyal Customers, Potential Loyalists, New Customers) is
assumed to produce ZERO incremental recovered value in this model --
they were not going to churn, so there is nothing to "win back," even
though contacting them still costs money. This is what makes Strategy A
look wasteful in the simulation: it pays to contact 3,066 customers
(5,868 - 2,802) whose assumed recovered value is zero.
This is a modeling simplification, not a claim that contacting engaged
customers has no value at all (e.g. it could have goodwill or upsell
value) -- it is simply outside what a "win-back" framing can justify
with the data available here.
"""

import pandas as pd
from pathlib import Path

MERGED_PKL = Path("data/processed/rfm_clv_combined.pkl")
OUTPUT_PKL = Path("data/processed/retention_simulation.pkl")

AT_RISK_SEGMENTS = ["At Risk", "About To Sleep", "Hibernating", "Need Attention"]
WINSORIZE_PCT = 0.99
HIGH_VALUE_PCT = 0.75  # top 25% by predicted value

# Business assumptions -- explicitly labeled, not derived from data
COST_PER_CONTACT = 5.0  # GBP, assumed cost of a retention email/direct-mail touch
WIN_BACK_RATES_TO_TEST = [0.10, 0.20, 0.30]  # sensitivity range
BASE_WIN_BACK_RATE = 0.20


def prepare_population(merged: pd.DataFrame) -> pd.DataFrame:
    df = merged.copy()
    cap = df.loc[df["predicted_clv_final"].notna(), "predicted_clv_final"].quantile(WINSORIZE_PCT)
    df["clv_winsorized"] = df["predicted_clv_final"].clip(upper=cap)
    df["is_at_risk"] = df["segment"].isin(AT_RISK_SEGMENTS)
    return df


def define_strategies(df: pd.DataFrame) -> dict:
    everyone = df
    at_risk = df[df["is_at_risk"]]
    at_risk_covered = at_risk[at_risk["clv_winsorized"].notna()]

    threshold = at_risk_covered["clv_winsorized"].quantile(HIGH_VALUE_PCT)
    high_value_at_risk = at_risk_covered[at_risk_covered["clv_winsorized"] >= threshold]

    return {
        "A_target_everyone": everyone,
        "B_target_all_at_risk": at_risk,
        "C_target_high_value_at_risk": high_value_at_risk,
    }


def simulate(strategies: dict, win_back_rate: float, cost_per_contact: float = COST_PER_CONTACT) -> pd.DataFrame:
    rows = []
    for name, pop in strategies.items():
        n_targeted = len(pop)
        cost = n_targeted * cost_per_contact
        # Recoverable value = sum of predicted CLV for at-risk, CLV-covered
        # members of this population ONLY (see module docstring assumption)
        recoverable_pop = pop[pop["is_at_risk"] & pop["clv_winsorized"].notna()]
        total_recoverable_value = recoverable_pop["clv_winsorized"].sum()
        expected_recovered_value = total_recoverable_value * win_back_rate
        net_value = expected_recovered_value - cost
        roi = net_value / cost if cost > 0 else float("nan")

        rows.append({
            "strategy": name,
            "customers_targeted": n_targeted,
            "campaign_cost_gbp": cost,
            "assumed_win_back_rate": win_back_rate,
            "expected_recovered_value_gbp": expected_recovered_value,
            "expected_net_value_gbp": net_value,
            "roi": roi,
        })
    return pd.DataFrame(rows).set_index("strategy")


def main():
    merged = pd.read_pickle(MERGED_PKL)
    df = prepare_population(merged)
    strategies = define_strategies(df)

    print("Strategy population sizes:")
    for name, pop in strategies.items():
        print(f"  {name}: {len(pop)} customers")

    print(f"\nBase case simulation (win-back rate = {BASE_WIN_BACK_RATE:.0%}, cost/contact = £{COST_PER_CONTACT}):")
    base_result = simulate(strategies, BASE_WIN_BACK_RATE)
    print(base_result.round(2))

    print("\nSensitivity across win-back rate assumptions:")
    all_results = []
    for rate in WIN_BACK_RATES_TO_TEST:
        res = simulate(strategies, rate)
        res["win_back_rate_label"] = f"{rate:.0%}"
        all_results.append(res)
        print(f"\n  Win-back rate = {rate:.0%}:")
        print(res[["customers_targeted", "campaign_cost_gbp", "expected_recovered_value_gbp", "expected_net_value_gbp", "roi"]].round(2))

    combined = pd.concat(all_results)
    combined.to_pickle(OUTPUT_PKL)
    print(f"\nSaved -> {OUTPUT_PKL}")

    return combined


if __name__ == "__main__":
    main()
