# Phase 16 - CLV Model Report

## Objective

Fit BG/NBD and Gamma-Gamma on a calibration period, carrying forward every
decision flagged in Phase 15, and build a simple baseline for comparison —
all validated against a held-out period in Phase 17, not asserted as
correct here.

Implementation: `src/clv_model.py`, tested in `src/test_clv_model.py` (8
tests, all passing). Full pipeline: **85/85 tests passing.**

## Setup

- **Transactions:** `sale`-type only, consistent with the Frequency
  definition used throughout this project.
- **Excluded population:** the December 2009 cohort (952 of 5,868 RFM-valid
  customers) — per the Phase 15 decision, since their customer "age" is
  unreliable due to left-censoring. Verified by test
  (`test_left_censored_cohort_excluded_from_modeling_population`).
- **Modeling population:** 4,916 customers, 483,002 sale transactions.
- **Calibration period:** start of data → 2011-06-30 (18 months)
- **Holdout period:** 2011-06-30 → 2011-12-09 (162 days / ~5.4 months)

This is a judgment call, not a statistically optimized split — flagged in
`src/clv_model.py`'s docstring as an explicit limitation, not tested for
sensitivity in this project.

## BG/NBD Fitted Parameters

```
            coef   se(coef)   95% CI
r       0.7326     0.0260     [0.682, 0.784]
alpha  92.1890     4.1152     [84.123, 100.255]
a       0.3111     0.0826     [0.149, 0.473]
b       4.4387     1.5443     [1.412, 7.466]
```

All four parameters (r, alpha, a, b) are positive with confidence
intervals well clear of zero, and standard errors are small relative to
the coefficient magnitudes for r and alpha — the model converged to a
stable solution, not a degenerate one. `a` and `b` govern the dropout
(Beta) distribution; `b` being notably larger than `a` (4.44 vs 0.31)
suggests dropout probability is concentrated toward lower values for most
customers — consistent with a customer base where the median customer,
once active, doesn't churn immediately.

## Gamma-Gamma: Fit Only on Repeat Purchasers, as Decided in Phase 15

**2,543 of 4,075 calibration-eligible customers (62.4%) have at least one
repeat purchase** in the calibration period and were used to fit
Gamma-Gamma. The remaining **1,532 (37.6%)** are single-purchase-in-
calibration customers, structurally excluded from Gamma-Gamma per the
Phase 15 decision — they do not get a `predicted_avg_value_ggf` or
`predicted_clv_bgnbd_ggf` value (left as `NaN`), rather than a forced or
fabricated estimate.

```
        coef    se(coef)   95% CI
p     2.6731    0.1673     [2.345, 3.001]
q     3.7755    0.1631     [3.456, 4.095]
v   400.2779   40.1535     [321.577, 478.979]
```

All parameters positive with tight confidence intervals — no convergence
red flags.

## Baseline Model (for comparison in Phase 17)

A simple, non-probabilistic CLV estimate was also built:
`(calibration-period purchase rate per day) × (holdout window length) ×
(calibration-period average order value)`, using only calibration data —
exactly the kind of naive extrapolation a shallow project might present
as "CLV." This is included specifically so Phase 17 can test whether
BG/NBD + Gamma-Gamma actually outperforms it, rather than assuming a
fancier model is automatically better.

## Predicted Values — Descriptive Only (Not Yet Validated)

| Metric | Mean | Median | Max |
|---|---:|---:|---:|
| BG/NBD predicted purchases (162-day window) | — | — | — |
| Predicted CLV (BG/NBD × Gamma-Gamma), n=2,543 | £556.39 | £307.76 | £29,682.04 |
| Baseline CLV, n=2,543 | £744.03 | £355.66 | £43,640.59 |

**These numbers are reported as model output, not as validated
predictions.** The baseline consistently runs higher than the
probabilistic model's estimate at both the mean and median — whether
that means the baseline over-predicts, the probabilistic model
under-predicts, or something in between is exactly the question Phase 17
exists to answer using actual holdout purchase behavior. No claim of
accuracy is made in this phase.

## What This Means Going Into Phase 17

The models are fit and produce parameter estimates that look
statistically stable (positive values, reasonable confidence intervals).
That is a necessary but not sufficient condition for trusting the
predictions — Phase 17 will compare `predicted_purchases_bgnbd` against
`frequency_holdout` (actual observed holdout purchases) and
`predicted_clv_bgnbd_ggf` against actual holdout monetary value, using
temporal (not random) validation as the project brief requires. If that
validation shows poor performance, this project will report it plainly.
