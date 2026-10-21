# Deployment Spec — validated strategy portfolio (2026-08-12)

The research program has converged. This documents the deployable portfolio:
two validated books and their blend, with operational requirements.

## The two books

### 1. Polygon LS champion (market-neutral alpha)
- **Config**: `tools/quant/ls/results/champion_n10_r14/config.json`
  (n=10/10, train_window=160, refit_freq=20, rebalance_freq=14, h=10,
  gbrt depth 4, mean_var weighting, 6bps one-side, VIX>=32/0.3 gate,
  call-rate short financing). DEPLOYMENT VARIANT: gross_leverage=3.0
  (SR 1.686, ret 14.1%, DD -6.3% net of proportional costs - the alpha is
  under-deployed at gross 0.13, SR RISES with leverage).
- **Data**: polygon panel (`tools/quant/data/polygon`, 84-85 names) —
  MUST use polygon prices; the edge is price-source-specific (cross-data
  test: same config on twelvedata prices -> SR -0.83)
- **Validation**: SR 1.613 (lev 1) / 1.686 (lev 3) on fresh data
  (2024-07..2026-08-11), scramble PASS (p=0.000), regime: bull 2.69 /
  sideways 0.62 / bear -0.78 (48d)
- **Profile (lev 3)**: ret ~14%, vol ~8.3%, MaxDD -6.3%, gross 0.39,
  beta 0.07, cost drag ~0.8%/yr
- **Run**: `python -m tools.quant.ls.runner` with the config, or
  `regime_gbrt_v12.py` for the research sweep; refresh panel via
  `python -m tools.quant.ls.extend_polygon_panel` (free tier, ~18 min)

### 2. AP gold composite (long-biased momentum/reversal + gold)
- **Config**: gold 0.2 static, vol-target 12%, reversal sleeve 0.3
  (`alphaportfolio_replication/run_champion_gold_sleeve.py` with
  `GOLD_W=0.2 MODE=static VOL_TARGET=0.12 REV_SLEEVE=0.3`)
- **Data**: twelve_big panel (291 names) + GLD + SPY + VIX (twelvedata)
- **Validation**: SR 1.086, ret 14.1%, MaxDD -14.2% (2008-2026, 224 mo);
  split-half: improves every metric in BOTH halves
- **Profile**: ret ~14%, vol ~13%, MaxDD -14%, monthly rebalance

### 3. DRL AlphaPortfolio ensemble (S&P 500 cross-section) — OPTIONAL SLEEVE
- **Source**: 16-seed ensemble net-of-6bps monthly returns
  (`alphaportfolio_replication/data/ap_net6bps_returns.csv`)
- **Validation**: SR 1.663 at 0.57% vol (19 OOS mo 2025-01..2026-07)
- **IMPORTANT — vol-targeting NOT achievable**: full-sample vol scaling
  (SR 1.66 at any vt) is arithmetic, not implementable. An honest
  trailing 3-month vol-target collapses SR to 0.43 (monthly-frequency
  scaling lags the vol regime). At its RAW size the sleeve adds ~0.92%/yr
  with near-zero vol: small SR contribution in the blend, dilutes return
  at meaningful weights.
- **Universe**: full S&P 500 + SEC EDGAR fundamentals — a genuinely
  different cross-section from the other two legs (corr +0.09..+0.30)

## The blend (recommended)

`alphaportfolio_replication/run_blend_champions.py` — raw monthly streams:

| w_ap | w_ls(3x) | SR (full, daily) | SR (active*, daily) | ret (active) | MaxDD (daily) |
|------|------|------|------|------|-------|
| .40 | .60 | **1.726** | **2.262** | 22.7% | **-5.7%** ← DEPLOYMENT DEFAULT |
| .50 | .50 | 1.627 | 2.124 | 21.8% | -6.7% |

DAILY-FREQUENCY AUDIT (2026-08-13): the monthly-sampled numbers understate
the investor's true intra-month drawdown. The honest daily figures: blend
40/60 SR 1.73 full / 2.26 active, ret 13.8%/22.7%, MaxDD -5.7% (still
meets both targets); AP leg SR 0.94 / MaxDD -17.5% (not -14.2%). Monthly
figures remain valid as monthly-sampled statistics. *Active = 2025-08+,
after the LS walk-forward warm-up.

*Active = 2025-08..2026-08, after the LS warm-up (first ~13 months are
flat by construction: the walk-forward needs ~180 days before the first
prediction). The full-window SR includes the flat ramp-up; the active SR
is the true deployed experience. Caveat: 13 months is short and the
window was a favorable market stretch.

(The DRL sleeve is optional at raw size — see section 3; vol-targeted DRL
versions are NOT achievable and are excluded from this table.)

Caveats: 26-month overlap (polygon panel history is API-capped at ~2y),
cross-book costs not fully reconciled, LS leg runs at 3x gross leverage
(financing included via call-rate config; gross 1.17x total — feasible).
The Sharpe >2 approaches the paper's headline but on a short sample vs
the paper's 30y WRDS data. Split-half: positive in both halves (SR 0.85 /
3.24) but concentrated in the second half — the SR is uneven across
time. The DRL vol-target claims were RETRACTED (arithmetic scaling, not
implementable — see research log).

## Live-ops notes

1. **DO NOT run the old live config** (`validation_test/tw320d4_deep_full`)
   on the extended twelvedata panel as-is — it produces a broken model
   (SR -0.19 on 20y, +0.03 on 8y; the twelvedata factor edge is dead on
   the current panel; see RESEARCH_LOG.md 2026-08-12 entries).
2. **Live signal migration decision (user)**: either point
   `run_live_signal.py` at the polygon champion config, or re-derive a
   twelvedata factor set. The polygon champion must use polygon data.
3. **Determinism**: run pipeline jobs one at a time (concurrent runs race
   on the macro/VIX cache; solo runs reproduce exactly, SR 1.4224 x3).
4. **Data freshness**: polygon panel refresh is manual
   (`extend_polygon_panel.py`, ~18 min); twelvedata refreshes nightly via
   the scanner.
5. **Screen-stability guard** already added to `run_live_signal.py`
   (kept_factors + screen_status in live_signal.json).
