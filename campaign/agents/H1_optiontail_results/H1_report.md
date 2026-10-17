# H1_optiontail — Cross-Sectional Tail-Pricing State Estimation

**VERDICT: PASS (as a STATE-ESTIMATION deliverable). NOT A BACKTEST — there is no trading
rule, no P&L, and therefore no PASS/REJECT vs the champion (GOAL100 SR 3.7845/ann 23.86%/MDD -3.30%, canonical per CHAMPION_CARD.md) is
claimed or possible. Explicit fail-open: only ONE options snapshot date exists
(2026-09-08); any backtest would require historical IV-by-expiry, which the repo does not
have. Champion cost rules (6bps/full |dW| + 4.5%/yr margin + 0.5%/yr borrow) are recorded
as REQUIREMENTS for the future sleeve, not applied here (zero turnover today).**

Data: `tools/quant/data/cboe_options/latest/{AAPL,GLD,IWM,MSFT,NVDA,QQQ,SPY,TLT,TSLA}.csv`
— single snapshot generated 2026-09-08 (spot, exp, typ, strike, bid, ask, iv, oi, volume,
delta, …, moneyness). 19–29 usable expiries per symbol out to ~Dec-2026.

## 1. Deliverables
| file | content |
|---|---|
| `H1_tailfactor.csv` | symbol, p20_30d, var95, var99, skew, kurt (9 rows, 9/9 emitted, 0 REJECT) |
| `H1_diagnostics.csv` | per-symbol fit diagnostics (norm_Z, atm_iv_30d, iv_80pct, digital cross-check, wing mass) |
| `H1_build_tailfactor.py` | reproducible build (offline, single file) |

## 2. Causality (T+1, no lookahead)
All inputs are from the 2026-09-08 close snapshot. The factor vector for symbol *i* is a
function of the 2026-09-08 chain only: F_i = g(chain_i(2026-09-08)). A decision formed on
F at T=2026-09-08 is executable at T+1=2026-09-09. No historical series is touched, so no
lookahead is possible **by construction**. This is state estimation for a future data
collection harness, not a backtest.

## 3. Derivation and formulas
Notation: S₀ = spot; expiry dates τ_e (ACT/365); k = ln(K/F) log-moneyness; mid prices
m = (bid+ask)/2.

**(a) Forward and discount from the data (no external rates).** Per expiry, put-call
parity on common strikes, C−P = S₀e^{−qτ} − K e^{−rτ}, is regressed across strikes:
slope b = −e^{−rτ} ⇒ r = −ln(−b)/τ, intercept a = S₀e^{−qτ} ⇒ q = −ln(a/S₀)/τ.
Sanity gate |r|<20%, −10%<q<30%; fallback (r,q)=(4.5%,1.3%) if the regression fails
(parity fails on 0–5 of ~20 expiries per symbol; see n_parity_ok). Forward F = S₀e^{(r−q)τ}.

**(b) Smile interpolation (the "delta+iv interpolation").** For each expiry, OTM+ATM
quotes (puts K≤F, calls K≥F; filters: ask>0, 0.01<iv<3.0, oi≥10 or volume≥10) give points
(k, iv). Since Black–Scholes delta is *strictly monotone in k at fixed τ*, interpolating
iv against delta is the same interpolation up to reparametrisation; we work in k.
Per expiry we fit the **SVI total-variance slice**
  w(k) = a + b·(ρ(k−m) + √((k−m)²+σ²)),  w = iv²τ,
by robust least squares (soft-L1; SVI guarantees a smooth, arbitrage-plausible wing; a
constrained quadratic w = c₀+c₁k+c₂k², c₂≥0, is the fallback for thin slices).

**(c) Term structure (multiple expiries available).** Total variance is linearly
interpolated across expiries at fixed k to the 30-calendar-day target τ*=30/365
(flat extrapolation in τ beyond the last listing; the 30d point is bracketed by
2026-10-02 and 2026-10-09 expiries, so extrapolation is negligible):
  w(k,τ*) = lin-interp_τ[ w(k,τ) ],  iv(k,τ*) = √(w(k,τ*)/τ*).

**(d) Model-free risk-neutral density (Breeden–Litzenberger).** With
C(K) = e^{−rτ*}[F·Φ(d₁) − K·Φ(d₂)] evaluated on the interpolated surface,
  f(K) = e^{rτ*} ∂²C/∂K²,  computed by ∂²/∂K² on a 4000-point log-spaced grid
(0.25–3.0×S₀), non-uniform-grid gradients (the naive constant-step ∂² is WRONG on a log
grid — caught in build, Z inflated to 14–19, rejected), clipped at 0 and normalised: Z=∫f dK.

**(e) Factor definitions.** With R = S_T/S₀ − 1 (simple return) and X = ln(S_T/S₀):
- `p20_30d` = P^Q(S_T < 0.8·S₀) = ∫_{K<0.8S₀} f(K)dK  — "spot drops >20% in 30d".
- `var95` = 5th percentile of R;  `var99` = 1st percentile of R (reported negative).
- `skew` = μ₃/σ³ of X;  `kurt` = μ₄/σ⁴ − 3 (EXCESS kurtosis), moments from the pdf:
  μ_j = ∫ x^j f(ln(S₀e^x))dx. These are the skew-kurtosis moment estimates of the
  risk-neutral 30d distribution (Breeden–Litzenberger moment form; Bakshi–Kapadia–Madan
  equivalent).

## 4. Results (2026-09-08 snapshot, risk-neutral/Q measure)
| symbol | p20_30d | var95 | var99 | skew | kurt (excess) | ATM iv30d | iv@0.8S |
|---|---|---|---|---|---|---|---|
| SPY  | 0.34% | −6.4%  | −11.6% | −3.61 | 39.4 | 12.4% | 34.0% |
| QQQ  | 0.57% | −8.4%  | −15.9% | −2.68 | 22.7 | 17.6% | 37.0% |
| IWM  | 0.59% | −8.7%  | −16.4% | −2.20 | 15.3 | 16.5% | 35.1% |
| AAPL | 0.55% | −11.0% | −17.3% | −1.13 | 13.6 | 25.0% | 35.9% |
| MSFT | 0.44% | −10.6% | −16.5% | −0.96 | 10.1 | 24.2% | 35.1% |
| NVDA | 1.61% | −14.9% | −22.1% | −0.99 | 10.5 | 35.6% | 42.5% |
| TSLA | 1.82% | −15.7% | −22.5% | −0.20 | 6.3  | 40.9% | 43.2% |
| GLD  | 0.37% | −10.9% | −16.6% | +0.41 | 4.1  | 23.8% | 30.5% |
| TLT  | 0.005%| −4.9%  | −8.4%  | +0.12 | 6.2  | 9.6%  | 20.9% |

Cross-sectional read: equity tail risk ranks TSLA > NVDA > {IWM≈QQQ>AAPL≈MSFT} > SPY;
GLD/TLT carry positive (or flat) skew — index-equity skew (−3.6 for SPY) is the dominant
pricing state. These are **Q (pricing) probabilities**: they embed the variance/skew risk
premium and systematically OVERSTATE physical P(S_T<0.8S₀) (typical Q/P ratio for 1m
equity tails ≈ 2–4×). Use as relative cross-sectional state, not as physical frequency.

## 5. Validation (all checks computed; none skipped)
- **Normalisation gate**: ∫f dK ∈ [0.90,1.10] required; emitted 0.9998–1.0000 for all 9.
- **Independent model-free cross-check**: digital from the put curve,
  P^Q(S_T<0.8S₀) = e^{rτ*}·∂P/∂K|_{0.8S₀} (no pdf, no second derivative). Agreement with
  the Breeden–Litzenberger p20: max abs diff 0.0002 (SPY 0.003441 vs 0.0034; TSLA 0.018213
  vs 0.0184; NVDA 0.016127 vs 0.0163). Gate: |diff| ≤ max(0.003, 0.35·p20) — 9/9 pass.
- **Ordering gate**: var99 ≤ var95 < 0 and 0 ≤ p20 < 1 — 9/9 pass.
- **Wing-extrapolation exposure**: pdf mass below the lowest observed ~30d strike
  ≤ 0.01% for all symbols; 0.8·S₀ lies INSIDE the observed strike range for 9/9
  (in_data_p20=True), so the headline p20 is quoted from data, not extrapolation.
- **Build-integrity rejections logged en route (fixed, not shipped)**: constant-step
  ∂²C/∂K² on a log grid (norm_Z 14–19 → REJECT, replaced by non-uniform gradients);
  PCHIP-with-flat-wings smile (norm_Z up to 1.58 for GLD/MSFT/QQQ → REJECT, replaced by
  SVI); digital sign error. Fail-closed: no number enters the deliverable without its gate.

## 6. Known limitations (honest)
1. **Single snapshot**: this is today's pricing state. It cannot and does not speak to
   forward returns. It becomes a *signal* only once a time series of the same quantity
   exists (Section 7).
2. **Q ≠ P**: p20_30d is a risk-neutral (insurance-price-implied) probability.
3. **kurt is extrapolation-sensitive**: the 4th moment weights the SVI wing far below the
   last listed strike; treat SPY/QQQ kurt (>20) as an upper-bound indicator. skew and
   var95/var99 are computed well inside the observed strike range.
4. Parity-implied r,q unavailable on 0–5 short expiries per symbol (weekly dispersion);
   fallback (4.5%, 1.3%) used there — immaterial for the 30d point, which interpolates
   expiries with successful parity fits.
5. Synthetic-era caution: iv@0.8S ≈ 34% for SPY is an unusually steep smile vs recent
   history; the pipeline reports what the chain says.

## 7. To make this a tradable sleeve (requirements + collection schedule)
This factor becomes testable only with a **time series of IV-by-expiry**. Requirements:
- **Backfill (licenced)**: ≥5y daily EOD chains for the 9 symbols (2020-03 and 2024-08
  tails must be in-sample; 3y minimum, 5y+ preferred for 1%-quantile stability). Sources
  to evaluate offline of this task: CBOE DataShop, ORATS, ivolatility.com, Polygon.
- **Collection schedule (forward harness)**:
  - Daily EOD snapshot, one file per symbol per date, SAME schema as
    `cboe_options/latest/` (spot, exp, typ, strike, bid, ask, iv, oi, volume, delta,
    moneyness), captured at a fixed clock time after the close (e.g. 16:15 ET) —
    timestamp must be recorded to keep T+1 causality auditable.
  - Retain ALL expiries ≥7 DTE (never just the front month — the term structure in §3(c)
    needs the 10-02/10-09-type brackets); keep full strike range incl. deep OTM (the
    0.8S strikes carried the p20 signal).
  - Persist immutable raw snapshots (parquet, partitioned by date; ~9×4k rows/day) AND
    the recomputed factor file per date (`H1_tailfactor_YYYYMMDD.csv`), so the factor is
    versioned independently of pipeline changes.
  - Weekly integrity job: re-derive r,q from parity and compare to a rates feed; flag
    symbols where fit gates (§5) fail — those days are excluded, fail-closed.
- **Sleeve construction (once ≥3y of factors exist)**: cross-sectional long/short on the
  tail-pricing state (e.g. under/over-priced p20 vs subsequent realised tail), T+1
  execution, and — per campaign rules — costs charged as 6bps per FULL |dW| turnover,
  4.5%/yr margin on (gross−1) where leveraged, 0.5%/yr borrow on short notional; ann/SR/
  MaxDD exactly per the campaign formulas. Note a short-tail variant (harvesting the Q−P
  premium) carries negative skew and must be sized against the champion's overlay, not
  standalone.

Champion benchmark (GOAL100, SR 3.7845/ann 23.86%/MDD -3.30% @1x, canonical per CHAMPION_CARD.md): **N/A here — no returns series exists
for this deliverable.** No PASS/REJECT of any trading rule is claimed.

DONE H1_optiontail
