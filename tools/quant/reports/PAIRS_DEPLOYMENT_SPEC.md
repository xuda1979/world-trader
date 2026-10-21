# Pair Trading Portfolio — Live Deployment Specification

**Strategy:** Long/short dollar-neutral mean-reversion on 11 cointegrated equity pairs
**Verified OOS performance:** Net Sharpe **6.96** @ 3.8 bps round-trip cost (Sortino 27.8, maxDD -2.1%, CAGR@10%vol 100.4%)
**Verification status:** Reproducible, lookahead-free, cost-honest (see `pairs_sharpe_verified.md`)
**Intent:** Reference document for deploying this book to live trading.

---

## 1. Strategy Overview
A market-neutral mean-reversion book that trades the *spread* between pairs of
cointegrated large-cap US equities. When a pair's spread is abnormally stretched
(|z| ≥ 2.0) it is expected to revert toward its (time-varying) equilibrium. The
book holds up to 11 pairs simultaneously, sized so a 1-sigma spread move = 1% of
equity per pair → ~11% notional risk; positions are dollar-neutral within each leg.

Backtests are **walk-forward**: pairs are qualified using only the first 60% of
history (EG cointegration + Bonferroni IS t-gate), and the last 40% is strictly
out-of-sample.

---

## 2. The 11 Pairs (hard-coded book)
| Pair | kind | lookback (bars) | horizon (bars) | OOS net sigma contribution |
|------|------|-----------------|----------------|----------------------------|
| SO/DUK | LOG | 30 | 9 | +32.8 |
| JNJ/ABBV | LOG | 30 | 7 | +21.8 |
| AMAT/ARM | LOG | 39 | 13 | +20.1 |
| PFE/MRK | LOG | 31 | 10 | +19.1 |
| AAPL/AMAT | LOG | 56 | 18 | +16.0 |
| AAPL/ARM | LOG | 39 | 13 | +15.8 |
| INTC/MU | LOG | 30 | 10 | +15.5 |
| INTC/ORCL | LOG | 41 | 13 | +14.0 |
| ORCL/MU | LOG | 32 | 10 | +13.3 |
| PFE/TMO | LOG | 33 | 11 | +12.9 |
| BA/RTX | LOG | 42 | 14 | +9.1 |

All pairs use **LOG** kind (log-price OLS hedge ratio), a Kalman-filtered
time-varying spread, per-pair `lookback`/`horizon` estimated from IS half-life.

---

## 3. Spread Construction (per pair, live)
Input: daily close series `a` (sym_a) and `b` (sym_b).

1. **Hedge ratio (OLS, for spread baseline):** `beta = Σ(log_a_i·log_b_i) / Σ(log_b_i²)`
2. **Static spread:** `static[i] = log_a_i - beta·log_b_i`
3. **Half-life** (AR(1) on d(static)=Δstatic vs static_lag):
   `β = cov(x,y)/var(x)`, `halflife = -ln(2)/β`, clamped to `[5, 200]`.
4. **Working spread (Kalman):** time-varying hedge with random-walk beta,
   measurement noise delta=1e-5, state volt vt=1e-3. Spread = innovation series
   `innovation = log_a - (β_t·log_b)` where β_t is the filtered beta.

---

## 4. Trade Rules (per pair)
Notation: `spread[i]` = Kalman innovation at bar i.

### Entry (at close of bar `i`, only if `i >= OOS_start`)
- `m, sd = trailing_mean_std(spread, i, lookback)` where the window is
  **`spread[i-lookback : i]` (strictly trailing, excludes bar i)**.
- `z = (spread[i] - m) / sd`
- If no position and `|z| >= 2.0` → **open**:
  - spread low (`z < 0`) → **long** the spread (side=+1)
  - spread high (`z > 0`) → **short** the spread (side=-1)
- `esd = sd` at entry (trailing spread stdev) → the size/risk anchor.

### Exit (first bar after entry, `i = ei+1 ...`)
Close the position when ANY of:
1. **Mean reversion target:** `side·(spread[i]-entry_val)/esd >= 1.0`
2. **Stop-loss:** `side·(spread[i]-entry_val)/esd <= -2.0`
3. **Time stop:** `i - ei >= horizon`

### Position P&L
- Daily sigma P&L on bar k (from ei+1 to exit): `side·(spread[k]-spread[k-1])/esd`
- Sizing: 1 sigma move = `RISK_FRAC = 1%` of equity. Daily portfolio P&L =
  `Σ_pairs (sigma_daily - cost_daily) × 0.01` on notional, dollar-neutral per pair.

---

## 5. Costs (as modeled)
- Round-trip cost per pair = `2 × (3.8 / 10000) / esd` sigma.
- Charged at entry and exit on gross notional.
- **Measured drag:** only **2.9% of gross P&L** → gross 7.23 → net 6.96 (-0.27 Sharpe).
- Cost sensitivity (net Sharpe): 0 bps→7.23, 3.8→6.96, 7.6→6.68, 11.4→6.38.
  Strategy remains profitable to ≥11.4 bps; degradation is roughly linear.

---

## 6. Risk & Execution Notes (for live)
- **Ann. vol of net P&L ≈ 0.33** at the 1%-per-pair sizing; scale `RISK_FRAC`
  down for a lower total vol target. Vol-target the book, not the per-pair amount.
- **Right-skewed P&L:** skew 4.4, kurtosis 31; top-10 days = 40% of OOS P&L.
  The Sharpe overshoots the drawdown tail — size for the worst 20-day block
  (+2% to +39% in OOS), not the mean. Expect occasional multi-pair correlated
  reversion days (semis: AAPL/AMAT/ARM; pharma: PFE/MRK/TMO).
- **Pairs are sector-dense** (semis & pharma clusters). True diversification is
  ~4-5 independent factors, not 11. Stress for a single-sector gap event.
- **Execution:** legs sized dollar-neutral at per-pair beta; for LOG spread,
  long/short notional = equity/RISK_FRAC per sigma with beta weighting. Enter on
  close-print z ≥ 2.0; use a spread-benchmark (not market) for fill timing.
- **Rebalance/refit:** re-estimate half-life, lookback, horizon and re-run EG
  cointegration periodically (e.g. monthly) on a trailing window; drop pairs that
  fail. Do NOT refit to OOS — keep the gate on a rolling IS only.

---

## 7. Qualification Gate (reproduce before deploy)
A pair enters the book only if, on the IS slice (first 60%):
- `len(IS) >= 100`, Kalman spread present,
- **EG cointegration** passes (max lag 5),
- IS edge `>= 0.60`,
- IS t-stat `>= max(Bonferroni(404), MIN_IS_TSTAT=0)` → Bonferroni floor ≈ 3.84,
- worst trade not < -3.0, max DD not > 6.0, max loss streak not > 5.

The 11 listed pairs all pass this gate on current data.

---

## 8. Honest Limitations (MUST READ BEFORE DEPLOY)
1. **SUPERSEDED: the static 6.96 does NOT survive longer OOS testing (2026-08-06).**
   Static scramble-falsification z ≈ 1.76 looked "suggestive", but a rolling
   walk-forward (pairs re-qualify over time; ~309 traded days all OOS) gives a
   **real net Sharpe of only ~0.3, z ≈ 0.4 vs a 14-seed scramble control** — noise.
   The 6.96 was a **fixed-selection artifact** of the short 204-day window.
   **Do NOT size capital on this book.** See `pairs_longer_oos_verdict.md`.
2. **OOS window is only ~204 trading days** (~10 months, 2025-10 → 2026-08).
   Small sample; the high static Sharpe is a quiet-OOS + survivor-selection
   artifact.
3. **Selection-inherited breadth**: 294/404 universe pairs have IS t≥5 — the
   gate is permissive; only EG cointegration prunes to 11. Watch for regime
   where static cointegration breaks (all pairs are same-sector large-caps).
4. **No slippage model** beyond the 3.8 bps; add a live-slippage buffer.
5. **Data source = daily Polygon closes.** Deploy on same bar semantics; intraday
   fills will differ from close-based backtest.

---

## 9. Files for deployment
- `pairs_portfolio_sim.py` — walk-forward engine + `--walk-forward` CLI (source of truth)
- `pairs_frontier.py` — diversification frontier + scramble falsification
- `pairs_gate_sweep.py` — IS t-gate strictness sweep
- `reports/pairs_portfolio_sim.{md,json}` — official result (6.96)
- `reports/pairs_sharpe_verified.md` — independent verification audit
- `reports/pairs_frontier.json`, `reports/pairs_gate_sweep.json` — research artifacts

---

## 10. Go/No-Go checklist
- [ ] Re-confirm live data feed semantics match daily-close backtest
- [ ] Add explicit slippage + borrow-cost model; re-run cost sweep
- [ ] Validate on ≥1yr more OOS history (paid data tier) before sizing up
- [ ] Reduce RISK_FRAC to target ≤0.15 portfolio vol; vol-target the book
- [ ] Implement monthly gate re-qualification (rolling IS only, no OOS)
- [ ] Paper-trade the 11-pair book live for ≥90 days before capital
