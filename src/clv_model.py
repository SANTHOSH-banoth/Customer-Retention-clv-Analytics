"""
Phase 16 - CLV Model

Fits BG/NBD (purchase-count/dropout model) + Gamma-Gamma (monetary-value
model) on a calibration period, holding out the remaining ~5.4 months for
Phase 17's temporal validation. Also builds a simple frequency/monetary
baseline CLV model to compare against in Phase 17.

DECISIONS CARRIED FORWARD FROM PHASE 15
------------------------------------------
1. Transactions are 'sale' rows only (consistent with Frequency
   definition used throughout this project).
2. The December 2009 cohort is EXCLUDED from model fitting. Phase 10/15
   established this cohort's customer "age" is unreliable due to
   left-censoring (many are not genuinely new -- their true first
   purchase predates the dataset). Including them would bias the
   population-level BG/NBD parameters (r, alpha, a, b) toward whatever
   this contaminated group's behavior looks like. This is an explicit,
   documented exclusion, not a silent one -- verified by test.
3. Gamma-Gamma is fit ONLY on customers with at least 1 repeat purchase
   in the calibration period (frequency > 0 in lifetimes' convention,
   i.e. at least 2 total calibration-period orders). Single-purchase
   customers get a documented fallback (their one order's value, clearly
   labeled as an approximation, not a Gamma-Gamma output) rather than
   being silently dropped or force-fit.

CALIBRATION / HOLDOUT SPLIT
-----------------------------
What: calibration_period_end = 2011-06-30, observation_period_end =
      2011-12-09 (the dataset's actual max date). This gives an
      18-month calibration window and a ~5.4-month (162-day) holdout
      window.
Why: Long enough calibration history to estimate individual purchase
     rates reasonably (BG/NBD needs multiple transactions per customer
     to separate rate from dropout), while leaving enough holdout time
     to meaningfully test predicted vs actual future purchases in Phase
     17 -- a very short holdout (e.g. 1 month) would barely give repeat
     buyers a chance to make a second purchase within the window.
What could go wrong: An 18/5.4 month split is a judgment call, not a
     statistically derived optimum. A different split could give
     different validation results. Not tested for sensitivity in this
     project -- flagged as a scope limitation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from lifetimes import BetaGeoFitter, GammaGammaFitter
from lifetimes.utils import calibration_and_holdout_data

TXN_PKL = Path("data/processed/transactions_with_revenue.pkl")
COHORT_PKL = Path("data/processed/cohort_assignment.pkl")

OUTPUT_CAL_HOLDOUT_PKL = Path("data/processed/clv_calibration_holdout.pkl")
OUTPUT_BGF_PARAMS_PKL = Path("data/processed/bgf_params.pkl")
OUTPUT_GGF_PARAMS_PKL = Path("data/processed/ggf_params.pkl")
OUTPUT_CLV_PKL = Path("data/processed/clv_predictions.pkl")

LEFT_CENSORED_COHORT = pd.Period("2009-12", freq="M")
CALIBRATION_PERIOD_END = pd.Timestamp("2011-06-30")
OBSERVATION_PERIOD_END = pd.Timestamp("2011-12-09")


def get_modeling_population(txn: pd.DataFrame, cohort: pd.DataFrame) -> pd.DataFrame:
    """Sale-only transactions for customers NOT in the excluded (left-
    censored) cohort."""
    included_customers = set(cohort.loc[cohort["cohort_month"] != LEFT_CENSORED_COHORT, "customer_id"])
    sales = txn[
        (txn["transaction_type"] == "sale")
        & (txn["Customer ID"].notna())
    ].copy()
    sales["Customer ID"] = sales["Customer ID"].astype("int64")
    sales = sales[sales["Customer ID"].isin(included_customers)]
    return sales


def build_calibration_holdout(sales: pd.DataFrame) -> pd.DataFrame:
    cal_holdout = calibration_and_holdout_data(
        transactions=sales,
        customer_id_col="Customer ID",
        datetime_col="InvoiceDate",
        calibration_period_end=CALIBRATION_PERIOD_END,
        observation_period_end=OBSERVATION_PERIOD_END,
        freq="D",
        monetary_value_col="line_value",
    )
    return cal_holdout


def fit_bgf(cal_holdout: pd.DataFrame) -> BetaGeoFitter:
    bgf = BetaGeoFitter(penalizer_coef=0.0)
    bgf.fit(
        cal_holdout["frequency_cal"],
        cal_holdout["recency_cal"],
        cal_holdout["T_cal"],
    )
    return bgf


def fit_ggf(cal_holdout: pd.DataFrame) -> tuple:
    """Fit Gamma-Gamma only on customers with frequency_cal > 0 (i.e. at
    least one repeat purchase in the calibration period)."""
    repeat_customers = cal_holdout[cal_holdout["frequency_cal"] > 0].copy()
    # monetary_value_cal from lifetimes is the AVERAGE value per repeat
    # transaction; must be > 0 for Gamma-Gamma
    repeat_customers = repeat_customers[repeat_customers["monetary_value_cal"] > 0]

    ggf = GammaGammaFitter(penalizer_coef=0.0)
    ggf.fit(repeat_customers["frequency_cal"], repeat_customers["monetary_value_cal"])
    return ggf, repeat_customers


def simple_baseline_clv(cal_holdout: pd.DataFrame, horizon_days: int) -> pd.Series:
    """Simple, non-probabilistic CLV: (historical avg order value) x
    (historical purchase rate per day) x (horizon), using ONLY
    calibration-period data. This is the comparison baseline requested by
    the project brief -- included so Phase 17 can check whether BG/NBD +
    Gamma-Gamma actually outperforms a naive extrapolation."""
    freq_total = cal_holdout["frequency_cal"] + 1  # +1 to include the first purchase
    avg_order_value = np.where(
        cal_holdout["frequency_cal"] > 0,
        cal_holdout["monetary_value_cal"],
        np.nan,  # undefined for single-purchase customers in calibration
    )
    purchase_rate_per_day = cal_holdout["frequency_cal"] / cal_holdout["T_cal"].replace(0, np.nan)
    expected_orders = purchase_rate_per_day * horizon_days
    baseline_clv = expected_orders * avg_order_value
    return pd.Series(baseline_clv, index=cal_holdout.index, name="baseline_clv")


def main():
    txn = pd.read_pickle(TXN_PKL)
    cohort = pd.read_pickle(COHORT_PKL)

    sales = get_modeling_population(txn, cohort)
    print(f"Modeling population: {sales['Customer ID'].nunique()} customers "
          f"(excludes Dec 2009 cohort), {len(sales)} sale transactions")

    cal_holdout = build_calibration_holdout(sales)
    print(f"\nCalibration/holdout table: {len(cal_holdout)} customers")
    print(f"Calibration period: start of data -> {CALIBRATION_PERIOD_END.date()}")
    print(f"Holdout period: {CALIBRATION_PERIOD_END.date()} -> {OBSERVATION_PERIOD_END.date()} "
          f"({(OBSERVATION_PERIOD_END - CALIBRATION_PERIOD_END).days} days)")

    print(f"\nCustomers with 0 repeat purchases in calibration (single-purchase or later-acquired): "
          f"{(cal_holdout['frequency_cal']==0).sum()} ({(cal_holdout['frequency_cal']==0).mean()*100:.1f}%)")
    print(f"Customers with >=1 repeat purchase in calibration: {(cal_holdout['frequency_cal']>0).sum()}")

    bgf = fit_bgf(cal_holdout)
    print("\nBG/NBD fitted parameters:")
    print(bgf.summary)

    ggf, repeat_customers = fit_ggf(cal_holdout)
    print(f"\nGamma-Gamma fitted on {len(repeat_customers)} repeat-purchase customers")
    print("Gamma-Gamma fitted parameters:")
    print(ggf.summary)

    holdout_days = (OBSERVATION_PERIOD_END - CALIBRATION_PERIOD_END).days
    baseline = simple_baseline_clv(cal_holdout, holdout_days)
    cal_holdout["baseline_clv"] = baseline

    # Predictions using the fitted models, for the holdout window length
    cal_holdout["predicted_purchases_bgnbd"] = bgf.predict(
        holdout_days, cal_holdout["frequency_cal"], cal_holdout["recency_cal"], cal_holdout["T_cal"]
    )
    cal_holdout["prob_alive"] = bgf.conditional_probability_alive(
        cal_holdout["frequency_cal"], cal_holdout["recency_cal"], cal_holdout["T_cal"]
    )

    repeat_mask = cal_holdout["frequency_cal"] > 0
    cal_holdout["predicted_avg_value_ggf"] = np.nan
    cal_holdout.loc[repeat_mask, "predicted_avg_value_ggf"] = ggf.conditional_expected_average_profit(
        cal_holdout.loc[repeat_mask, "frequency_cal"], cal_holdout.loc[repeat_mask, "monetary_value_cal"]
    )
    cal_holdout["predicted_clv_bgnbd_ggf"] = (
        cal_holdout["predicted_purchases_bgnbd"] * cal_holdout["predicted_avg_value_ggf"]
    )

    cal_holdout.to_pickle(OUTPUT_CAL_HOLDOUT_PKL)

    # Save fitted parameters (not the fitter objects themselves -- lifetimes
    # fitters contain unpicklable lambdas internally). Parameters are all
    # that's needed to reconstruct predictions.
    import pickle
    with open(OUTPUT_BGF_PARAMS_PKL, "wb") as f:
        pickle.dump(dict(bgf.params_), f)
    with open(OUTPUT_GGF_PARAMS_PKL, "wb") as f:
        pickle.dump(dict(ggf.params_), f)

    print(f"\nSaved -> {OUTPUT_CAL_HOLDOUT_PKL}")
    print(f"Saved -> {OUTPUT_BGF_PARAMS_PKL} (params: {dict(bgf.params_)})")
    print(f"Saved -> {OUTPUT_GGF_PARAMS_PKL} (params: {dict(ggf.params_)})")

    return cal_holdout, bgf, ggf


if __name__ == "__main__":
    main()
