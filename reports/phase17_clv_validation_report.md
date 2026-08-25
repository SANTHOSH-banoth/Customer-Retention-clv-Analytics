# Phase 17 - CLV Validation Report

## Objective

Test predicted vs actual holdout behavior — not just calculate CLV and
declare it correct. Temporal holdout (not random split), reported plainly
whether the model performs well or poorly.

Implementation: `src/clv_validate.py`, tested in `src/test_clv_validate.py`
(7 tests, all passing). Full pipeline: **92/92 tests passing.**

**Ground truth methodology:** actual holdout purchase counts and revenue
are recomputed **directly from the transaction data** for the 162-day
holdout window (2011-06-30 → 2011-12-09), not read from `lifetimes`'
internal holdout columns — so validation doesn't depend on trusting the
library's internal conventions.

## 1. Purchase Count Validation (BG/NBD, all 4,075 calibration customers)

```
MAE:            0.966 orders
RMSE:           1.664 orders
Mean bias:     -0.227 orders  (slight under-prediction)
Spearman rank correlation: 0.557, p < 0.0001
```

The model's purchase-count predictions correlate moderately-strongly with
actual holdout order counts (ρ=0.557) — a real, statistically robust
signal, not noise. The MAE of ~1 order and a small negative bias (model
tends to slightly under-predict) are reasonable for a 162-day window given
this customer base's purchase rates (median calibration Frequency = 1).

## 2. CLV Ranking Quality — Both Models Rank Reasonably Well

Restricted to the 2,543 repeat-purchase customers (the only population
with a CLV prediction from Gamma-Gamma):

| Model | Spearman correlation (predicted CLV vs actual holdout revenue) |
|---|---:|
| BG/NBD + Gamma-Gamma | 0.596 (p < 0.0001) |
| Simple baseline | 0.566 (p < 0.0001) |

Both models produce a statistically significant, moderately strong
ranking of future value. **BG/NBD + Gamma-Gamma ranks slightly better**
(0.596 vs 0.566), though the gap is not large.

## 3. CLV Error Metrics — A Genuinely Mixed Result, Reported Honestly

```
                        MAE (£)    RMSE (£)    Mean bias (£)
BG/NBD + Gamma-Gamma    543.63     2,428.48    -189.14
Simple baseline         577.71     2,254.54       -1.49
```

**Neither model wins cleanly on every metric — this is directly tested**
(`test_neither_model_dominates_on_every_metric`) so this nuance can't be
accidentally overwritten by a future edit:

- **BG/NBD + Gamma-Gamma has lower MAE** (£543.63 vs £577.71) — on a
  typical customer, its prediction error is smaller.
- **The simple baseline has lower RMSE** (£2,254.54 vs £2,428.48) — RMSE
  penalizes large errors more heavily, so BG/NBD+GG is making some larger
  individual mistakes that the baseline avoids.
- **The simple baseline is nearly unbiased on average** (-£1.49) while
  BG/NBD+GG systematically under-predicts by about £189 per customer on
  average. This is worth being direct about: the more sophisticated model
  is not simply "better" here — it has a measurable, real systematic bias
  the simpler model doesn't share.

**This does not mean BG/NBD + Gamma-Gamma should be discarded** — it
still wins on MAE and ranking quality, both practically relevant for a
"who should we prioritize" business use case. But it means this project
does **not** claim the probabilistic model is unconditionally superior,
which would be a stronger claim than the evidence supports.

## 4. Decile Capture — The Most Business-Relevant Result

For the top 10% of customers by predicted CLV, what share of actual
holdout revenue did they generate?

| Decile (by predicted CLV, BG/NBD+GG) | % of customers | % of actual holdout revenue |
|---|---:|---:|
| Top 10% | 10.0% | **49.3%** |
| 2nd decile | 10.0% | 14.5% |
| 3rd decile | 10.0% | 10.6% |
| ... | ... | ... |
| Bottom 10% | 10.0% | 1.5% |

The simple baseline achieves a nearly identical **48.8%** top-decile
capture.

**Context for interpreting 49%:** a random selection of 10% of customers
would capture ~10% of revenue by definition. A theoretically perfect
model (ranking customers by their *actual* realized holdout revenue,
which is of course unknowable in advance) would capture **59.9%** in the
top decile, given how concentrated the actual revenue distribution turned
out to be. **Both models capture roughly 82% of the achievable lift over
random (49% of the 59.9% ceiling).** This is a genuinely strong, honest
result for a targeting use case — even without a perfectly calibrated £
prediction, the model reliably identifies *which* customers will be most
valuable.

## An Important Related Number, Found During Validation

**40.7% of the 2,543 repeat-purchase (Gamma-Gamma-eligible) customers had
£0 actual revenue in the holdout window** — meaning a large share of
customers who had already shown repeat-purchase behavior in calibration
still churned within the 5.4-month holdout. This is a striking, real
number for the business narrative: even "engaged" customers churn at a
substantial rate over roughly half a year, reinforcing why retention
strategy (Phase 20) matters regardless of how good the CLV model's
targeting is.

## Summary: Did the Model Perform Well or Poorly?

**Reasonably well for ranking/targeting purposes, mixed for precise £
prediction — reported exactly as measured, not adjusted to look better:**

- ✅ Statistically significant, moderate-to-strong ranking ability for
  both purchase counts (ρ=0.557) and CLV (ρ=0.596)
- ✅ Strong practical targeting value: top-decile capture (49.3%) reaches
  ~82% of the theoretical ceiling
- ⚠️ BG/NBD + Gamma-Gamma has a real, measurable negative bias (-£189
  average) that the simpler baseline doesn't share
- ⚠️ Neither model dominates the other on every error metric — a fair,
  disclosed result rather than a curated one

## What This Means Going Into Phase 18

CLV predictions (from BG/NBD + Gamma-Gamma) are usable for **relative
ranking and prioritization** (Phase 18's RFM × CLV comparison, Phase 20's
retention targeting), with the explicit caveat that absolute £ figures
carry a documented downward bias and should be treated as directionally
useful, not precise. The 37.6% of customers with no Gamma-Gamma-eligible
CLV prediction (single-purchase-in-calibration customers) will need a
clearly labeled fallback treatment in Phase 18, consistent with the Phase
15/16 decisions already made.
