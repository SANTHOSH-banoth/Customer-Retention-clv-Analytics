# Phase 15 - CLV Theory Report

## Objective

Understand BG/NBD and Gamma-Gamma — their inputs, assumptions, outputs,
and limitations — and check those assumptions against what this project
already knows about the dataset, **before** fitting anything in Phase 16.
No implementation in this phase.

## BG/NBD (Beta-Geometric / Negative Binomial Distribution)

**What it models:** repeat purchasing behavior in a **non-contractual**
setting — i.e. a business (like this giftware retailer) where a customer
never formally "cancels," they simply stop buying, and their departure is
never directly observed.

**Core assumptions:**
1. While a customer is "alive" (still an active buyer), their purchases
   follow a Poisson process with individual transaction rate λ.
2. λ varies across customers according to a Gamma distribution
   (population-level heterogeneity in purchase rate).
3. After any transaction, a customer becomes permanently inactive
   ("dies") with probability *p* — an unobserved dropout process.
4. *p* varies across customers according to a Beta distribution.
5. λ and *p* are independent across customers (a customer's underlying
   purchase rate doesn't predict their dropout probability).

**Inputs required per customer:** `frequency` (number of *repeat*
transactions — total transactions minus 1), `recency` (time between first
and last transaction), and `T` (time between first transaction and the
end of the observation/calibration period). Monetary value is **not**
used by BG/NBD at all.

**Outputs:** probability a customer is still "alive" as of today, and
expected number of future transactions in a given time window.

**Key limitation:** BG/NBD assumes we observe each customer's **entire**
history since their true first-ever purchase. If a customer's real first
purchase happened before our observation window starts, their measured
"age" (T) is wrong, which biases the fitted rate.

## Gamma-Gamma

**What it models:** the **monetary value** of each transaction, to be
combined with BG/NBD's transaction-count estimate into a full CLV figure.

**Core assumptions:**
1. Each transaction's monetary value is Gamma-distributed for a given
   customer.
2. A customer's average transaction value doesn't change systematically
   with their purchase frequency — i.e. **frequency and average order
   value are assumed independent** across the customer population.
3. Requires customers to have made at least one repeat purchase (i.e.
   frequency ≥ 1 in BG/NBD's convention, meaning at least 2 total orders)
   — a single order gives no information about a customer's *typical*
   spend, only one observation of it.

## Checking These Assumptions Against What This Project Already Knows

This project has direct, measured evidence bearing on three of these
assumptions, gathered in earlier phases:

### 1. The left-censoring problem (Phase 10) directly threatens BG/NBD's core requirement

Phase 10 found the December 2009 cohort is **2.9x** the size of a typical
early cohort — strong evidence that many "December 2009" customers'
*true* first purchase predates the dataset. BG/NBD requires the observed
first transaction to be the *actual* first transaction. **This is a real,
already-quantified assumption violation, not a hypothetical one.**
Implication for Phase 16: the December 2009 cohort's `T` (customer age)
values will systematically understate true tenure, likely biasing their
estimated purchase rate and alive-probability. This needs to be either
excluded or explicitly caveated when fitting, not ignored.

### 2. The 27.7% single-purchase population (Phase 5-7) limits what BG/NBD/Gamma-Gamma can learn from a large share of customers

1,624 of 5,868 RFM-valid customers (27.7%) have made exactly one
purchase. BG/NBD can technically still model these customers (a
zero-repeat-transaction customer still contributes to the likelihood,
via a declining alive-probability over time since their single
purchase), but they carry very little information about the *purchase
rate* parameter — only about the *dropout* parameter, indirectly. **More
importantly, Gamma-Gamma cannot use this population at all** (they have
no second transaction to establish a "typical" spend pattern) — Phase 16
will need to exclude them from monetary-value estimation and, if a CLV
figure is still wanted for them, use a simpler fallback (e.g. their single
transaction's value, clearly labeled as a rough approximation, not a
Gamma-Gamma output).

### 3. Gamma-Gamma's independence assumption is measurably, if mildly, violated

Directly tested: among the 4,244 repeat-purchase customers, Spearman
correlation between Frequency and average order value:

```
rho = 0.188, p = 3.30e-35
```

This is **statistically significant** (unsurprising given n=4,244) but
**practically small** (rho=0.19 is a weak correlation, not a strong one).
**Decision going into Phase 16: proceed with Gamma-Gamma, but disclose
this violation explicitly rather than pretending the assumption holds
perfectly.** A small positive correlation means more frequent buyers tend
to also spend slightly more per order — Gamma-Gamma will likely very
mildly underestimate monetary value for high-frequency customers and
overestimate it for low-frequency ones, but the effect size measured here
does not suggest a severe distortion.

### 4. Skew shape is broadly consistent with the Gamma-heterogeneity assumption

Phase 6 found Frequency skew = 12.5 and Monetary skew = 27.0 — both
heavily right-skewed. A Gamma distribution is capable of producing this
shape (unlike a Normal distribution), so this is at least not evidence
*against* the Gamma-heterogeneity assumption in BG/NBD/Gamma-Gamma, even
though it doesn't prove the assumption holds either — skew shape alone is
weak evidence, not confirmation.

### 5. Transaction definition must stay consistent with the rest of this project

BG/NBD's "transaction" will be defined as a `sale`-type invoice (Phase
2-5's definition), excluding cancellations and non-merchandise rows —
matching the Frequency definition already used throughout this project,
so CLV estimates remain comparable to the RFM/cohort work already done.

## Overall Assessment: Is This Dataset Appropriate for BG/NBD + Gamma-Gamma?

**Conditionally yes, with explicit caveats, not a clean fit.**

| Consideration | Verdict |
|---|---|
| Non-contractual repeat-purchase setting | ✅ Matches BG/NBD's design use case |
| Enough repeat purchasers to fit on | ✅ 4,244 customers (72.3%) have repeat purchases |
| Full observation of true customer history | ⚠️ **Violated** for the Dec 2009 cohort (left-censoring) |
| Frequency/monetary independence (Gamma-Gamma) | ⚠️ **Mildly violated** (rho=0.19, statistically significant) |
| Single-purchase customers | ⚠️ Large population (27.7%) that Gamma-Gamma structurally can't use |
| Short observation window (~2 years) for a possibly long/seasonal purchase cycle (gifts) | ⚠️ Flagged as a risk, not yet tested — Phase 16/17 fitting and holdout validation will show whether this is a practical problem |

**Decision: proceed to Phase 16 with BG/NBD + Gamma-Gamma**, since the
core setting fits and the violations found are real but not severe enough
to rule the model out — but every one of these caveats will be carried
forward explicitly into the fitting and validation phases, and if Phase
17's holdout validation shows poor predictive performance, this project
will report that plainly rather than keep tuning until the numbers look
acceptable, per the project's stated ground rules.

## What This Means Going Into Phase 16

1. Fit on `sale`-type transactions only, consistent with the rest of the
   project.
2. Consider excluding or flagging the December 2009 cohort given the
   left-censoring finding — decide explicitly in Phase 16, don't default
   silently either way.
3. Fit BG/NBD on the full RFM-valid population (including single-purchase
   customers, since BG/NBD can technically use them), but restrict
   Gamma-Gamma to the 4,244 repeat-purchase customers, with a clearly
   labeled fallback for the rest.
4. Temporal (not random) holdout validation is mandatory per the project
   brief and directly relevant here — Phase 17 will test whether these
   theoretical concerns translate into real predictive problems.
