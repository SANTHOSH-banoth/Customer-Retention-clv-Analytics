# Phase 20 - Retention Strategy Simulation Report

## Objective

Compare three campaign targeting strategies under explicit, labeled
assumptions. **This is a scenario simulation, not a causal experiment.**
No claim of the form "targeting this group will cause £X revenue" is made
anywhere in this phase — every downstream number is conditional on an
assumed win-back rate this project has no campaign history to estimate.

Implementation: `src/retention_simulation.py`, tested in
`src/test_retention_simulation.py` (8 tests, all passing). Full pipeline:
**113/113 tests passing.**

## Observed vs. Model Output vs. Assumption

| | Type | Source |
|---|---|---|
| Customer counts, segment membership, historical revenue | **Observed** | Phases 2-9 |
| Predicted CLV (winsorized) | **Model output** | Phases 16-19, with Phase 17's validated error characteristics |
| Cost per contact (£5), win-back rate (10/20/30%) | **Business assumption** | Not derived from this dataset — labeled explicitly, tested for sensitivity |

## The Three Strategies

| Strategy | Population | Definition |
|---|---:|---|
| A: Target Everyone | 5,868 | All RFM-valid customers |
| B: Target All At Risk | 2,802 | Phase 19's at-risk segments |
| C: Target High-Value At Risk | 572 | Top 25% of the 2,287 CLV-covered at-risk customers by winsorized predicted CLV |

Verified by test: C ⊂ B ⊂ A (`test_strategy_c_is_subset_of_strategy_b`,
`test_strategy_b_is_subset_of_strategy_a`).

## Key Modeling Assumption — Stated Directly

**Expected recovered value is computed only from at-risk, CLV-covered
customers.** Contacting an already-engaged customer (Champions, Loyal
Customers, Potential Loyalists, New Customers) is assumed to produce
**zero incremental recovered value** in this model — they weren't going
to churn, so there's nothing to "win back," even though contacting them
still costs money. This is a modeling simplification (contacting engaged
customers could plausibly have goodwill/upsell value not captured here),
not a claim that it's pointless in general — but it is the mechanism that
makes Strategy A look expensive relative to B and C in this simulation.
Directly verified: Strategy A and B have **identical** total recoverable
value (£46,924.46) despite A costing more than twice as much to run
(`test_strategy_a_and_b_have_identical_recoverable_value`).

## Base Case Results (win-back rate = 20%, £5/contact)

| Strategy | Customers | Cost | Expected Recovered Value | Expected Net Value | ROI |
|---|---:|---:|---:|---:|---:|
| A: Everyone | 5,868 | £29,340 | £46,924 | £17,584 | 0.60 |
| B: All At Risk | 2,802 | £14,010 | £46,924 | £32,914 | 2.35 |
| C: High-Value At Risk | 572 | £2,860 | £36,274 | **£33,414** | **11.68** |

**Strategy C wins on both dimensions that matter** — it has the highest
ROI (11.68 vs. 2.35 vs. 0.60) *and* the highest absolute expected net
value (£33,414), despite spending 95% less than Strategy B and 90% less
than Strategy A. This directly echoes the Phase 17 decile-capture finding
(top-decile customers captured ~49% of actual holdout revenue) — a small,
well-chosen slice of the at-risk population accounts for most of its
recoverable value (77.3% of at-risk predicted value sits in the top 25%
by CLV).

## Sensitivity: Does the Conclusion Hold Across Win-Back Rate Assumptions?

| Win-back rate | Strategy A ROI | Strategy B ROI | Strategy C ROI |
|---|---:|---:|---:|
| 10% | -0.20 | 0.67 | 5.34 |
| 20% | 0.60 | 2.35 | 11.68 |
| 30% | 1.40 | 4.02 | 18.02 |

**Strategy C has the best ROI and Strategy A the worst at every tested
rate** — verified by test
(`test_strategy_c_has_best_roi_at_every_tested_rate`,
`test_strategy_a_has_worst_roi_at_every_tested_rate`). **At a 10% win-back
rate, Strategy A actually loses money (ROI = -0.20)** — spending more on
contacts than the expected recovered value, purely because most of its
targets have zero assumed recoverable value. This ordering is robust to
the win-back-rate assumption; it is not a knife-edge result that depends
on picking a favorable rate.

## What This Simulation Does NOT Claim

- It does **not** claim that contacting an At Risk customer will cause a
  20% chance of recovery — 20% is a stated assumption, not a measured
  probability, because this dataset contains no actual campaign history.
- It does **not** claim Strategy A produces zero value from the
  3,066 non-at-risk customers it also contacts — it claims zero
  *win-back* value under this specific modeling frame, which is different
  from claiming those contacts are worthless for other reasons (loyalty,
  referrals, upsell) this project has no data to measure.
- It does **not** account for the 18.4% of the at-risk population without
  a CLV prediction (515 customers) contributing any recovered value —
  consistent with Phase 19's "documented lower bound" framing, the true
  addressable opportunity for Strategy B specifically is understated here.

## What This Means Going Into Phase 21

The clear, robust simulation result — concentrate retention budget on a
narrow, high-value at-risk segment rather than broad targeting — is a
defensible input to Phase 28-29's business recommendations, precisely
because it was stress-tested across win-back-rate assumptions rather than
asserted from a single scenario.
