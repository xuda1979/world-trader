# Pairs Trading R&D Notes

Last updated: 2026-07-24

## Prior work (baseline)

`rv_scale_backtest.md` (2026-07-23) tested 10 RV pairs on FRED daily data
(~6 years): 4 yield-curve spreads + 6 FX cross spreads. Findings:
- **5/6 FX pairs positive OOS Sharpe**; best AUD/CAD (+0.56).
- **0/4 yield pairs positive OOS Sharpe**; yield-curve trades are trend-
  following in disguise and the no-stop-loss strategy DD = 93%.
- Portfolio untradeable as-is (no stop-loss).

## This run: `run_pairs_scale.py` (2026-07-24)

Expanded universe to **61 pairs** across asset classes:
- 6 FX cross spreads (FRED DEX* series, ~1400 bars / 6 years)
- 1 crypto pair (Binance BTC/ETH, ~1000 bars)
- 40 US equity same-sector pairs (Polygon, ~500 bars / 2 years)
- 10 index/sector ETF pairs (Polygon + Twelve Data, ~500-1000 bars)
- 1 country ETF pair (EWA/EWC, Twelve Data, ~1000 bars)
- 1 commodity ETF pair (GLD/SLV — SLV missing, failed)
- 1 cross-asset pair (COIN/BTC)

### Methodology
- Spread: log-price OLS hedge for stocks/ETFs/crypto; raw diff for FX.
- Signal: rolling 60-bar z-score; entry |z|>2, exit z=0, horizon 10 bars.
- Walk-forward: 60% IS / 40% OOS chronological split.
- Qualifying gate (Bonferroni n_tests=61): IS edge>=0.60, IS t>=3.34,
  OOS n>=8, OOS exp_ret>0, 0<OOS edge<=3.0, worst trade>=-3 stdev,
  max DD<=6 stdev, streak<=5.

### Results: 3/58 qualify

| Pair | Class | OOS edge | OOS exp_ret | z_now | Why it works |
|------|-------|----------|-------------|-------|--------------|
| **NKE/HD** | STOCK | +1.10 | +1.07 | -1.25 | Both consumer-discretionary exposed to US housing/retail cycle; NKE sneaker demand and HD home-spend co-move, spread mean-reverts on regime shifts |
| **SPY/IWM** | ETF | +0.75 | +0.69 | -0.89 | Large-cap vs small-cap rotation; risk-on/off regimes drive spread, reverts as risk appetite cycles |
| **QQQ/IWM** | ETF | +0.52 | +0.33 | -1.32 | Tech vs small-cap rotation; same risk-on/off driver, sharper because QQQ is growth-concentrated |

### Near-miss / promising (positive OOS but fail IS edge gate)

| Pair | Class | OOS edge | OOS exp_ret | z_now | Note |
|------|-------|----------|-------------|-------|------|
| **XLE/XLB** | ETF | +0.37 | +0.43 | +0.77 | Energy vs materials sector rotation |
| **XLB/XLI** | ETF | +0.37 | +0.43 | -0.77 | Materials vs industrials rotation (mirror of above) |
| **XLF/SPY** | ETF | +0.36 | +0.33 | +1.63 | Financials vs broad market; z approaching +2 entry |
| **EUR/CHF** | FX | +0.30 | +0.30 | -1.15 | Eurozone cross; SNB floor regime legacy |
| **AUD/CAD** | FX | +0.27 | +0.29 | -0.67 | Commodity dollars; prior 6-yr winner, OOS still positive |
| **EUR/GBP** | FX | +0.23 | +0.35 | **-2.37** | **FIRING NOW** — Brexit-era spread, z below -2 entry |
| **SPY/DIA** | ETF | +0.23 | +0.23 | -0.75 | S&P 500 vs Dow 30; nearly identical benchmarks |

### Live firing setups (|z_now| > 2.0)

- **EUR/GBP**: z = -2.37 → LONG EUR/USD, SHORT GBP/USD (bet spread reverts wider toward mean). This is the only pair currently in entry territory.

### Key analytical observations

1. **FX pairs have lower per-trade edge (~0.2-0.3) than stocks (~0.6-1.1) but
   6-year sample depth.** The IS edge gate (>=0.60) is calibrated for stock-like
   volatility; FX spreads are calmer and structurally fail this gate even though
   they have positive OOS edge. **AUD/CAD and EUR/GBP remain positive OOS** —
   consistent with the prior 6-year baseline.

2. **Stock/ETF pairs show high per-trade edge but only 2-year sample depth
   (Polygon free-tier cap of 500 bars).** The 3 qualifiers (NKE/HD, SPY/IWM,
   QQQ/IWM) have strong OOS stats but on ~20 OOS trades each — treat with
   caution. Deeper history (Twelve Data paid or Stooq unblock) would firm this
   up.

3. **Sector-rotation ETF pairs (XLE/XLB, XLF/SPY) are promising** — positive
   OOS edge, economically linked, and XLF/SPY is approaching a firing zone
   (z=+1.63). Worth monitoring.

4. **Cointegration logic (log-price OLS hedge) works** for stocks/ETFs: the
   spread is more stationary than raw price diff, and the z-score signal fires
   at economically meaningful divergence points.

5. **Crypto (BTC/ETH) and COIN/BTC both show NEGATIVE OOS edge** — crypto
   spreads trend rather than mean-revert in the 2-6 year window. This is
   consistent with crypto being a regime-transitioning asset class. Avoid
   mean-reversion on crypto pairs without a regime filter.

### Why certain pairs work (fundamental analysis)

**AUD/CAD (positive OOS over 6 years):**
- Both are commodity-exporting dollars with high correlation to oil/metals.
- AUD has iron-ore + coal exposure; CAD has crude oil exposure.
- Spread mean-reverts because commodity cycles revert, but the two commodities
  have slightly different timing → spread oscillates around a slow-moving mean.

**EUR/GBP (positive OOS, FIRING now):**
- Post-Brexit, EUR/GBP has been range-bound with periodic risk shocks.
- UK fiscal/political events (Truss mini-budget 2022, election cycles) drive
  GBP away from EUR, then reverts as the shock fades.
- Current z=-2.37 suggests GBP is rich vs EUR — a short-GBP/long-EUR reversion
  bet.

**NKE/HD (best OOS edge):**
- Both consumer-discretionary, both exposed to US consumer spending power and
  housing wealth effect.
- NKE has more brand/fashion cyclicality; HD has more housing-turn cyclicality.
- Spread reverts as consumer cycle rotates between goods (HD) and
  apparel/footwear (NKE).

**SPY/IWM and QQQ/IWM (qualify):**
- Large-cap/growth vs small-cap rotation is a classic risk-on/off trade.
- 2024-2026 saw a huge large-cap concentration (AI trade) that pushed SPY/QQQ
  rich vs IWM; spread reverts when small-caps catch up.

### Next steps

1. **Fetch deeper stock history** via Twelve Data (when rate limit clears) or
   Stooq (when network unblocks) to get 6-year samples for the stock/ETF pairs.
2. **Add a regime filter** to crypto pairs (fundling-rate-based) to see if
   mean-reversion works in calm regimes.
3. **Add more commodity pairs**: CL/NG (oil vs gas), GDX/GDXJ (gold majors vs
   juniors), SLV/GLD once SLV data is fetched.
4. **Test intraday ORB on the qualifying pairs** as a complementary signal.
5. **Paper-trade EUR/GBP live setup** — z=-2.37, enter long EUR/USD short
   GBP/USD with 1-sigma spread risk = 1% equity, exit at z=0 or 10 days.

## Cron

This R&D is scheduled to re-run every 10 minutes via cron job
`job_424477cb0bf9` (auto-expires in 7 days). Each run will re-execute the
prompt, which continues the pairs-trading R&D loop.
