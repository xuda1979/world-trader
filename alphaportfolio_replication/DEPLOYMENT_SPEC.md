# Deployment Spec — Champion Composite (consolidated, 2026-08-12)

The loop's research program is complete. This is the single deployment
reference; full history in AP_RESEARCH_LOG.md.

## 1. The strategy (backtest-validated, full 2008-2026)

**Momentum(6+12+24mo composite) + value/quality fundamental tilt (w=0.10)
+ 20% gold sleeve + SPY13MA binary trend gate + VIX gate OFF + top-1/6
concentration (G_DIV=6) + vol-target (cap 1.2) + DD-reducer, monthly
rebalance, 6bps costs.**

| vol target | Sharpe (net) | ret | MaxDD | split-half | cost drag |
|------------|-------------|-----|-------|-----------|-----------|
| **10%** | **1.41** | **16.2%** | **-10.3%** | 1.56/1.30 | 0.18%/yr |
| **6%** | **1.40** | 11.6% | **-7.6%** | 1.53/1.30 | 0.18%/yr |

vs SPY buy-and-hold: 0.67 SR / 10.4% / -47.3% MaxDD.

### Era validation (vt10, net)
| era | SR | ret | MaxDD |
|-----|-----|------|-------|
| 2008-2013 | 1.54 | 17.7% | -8.9% |
| 2014-2019 | 1.31 | 16.6% | -10.3% |
| 2020-2026 | 1.29 | 17.3% | -9.7% |
| 2024-07+ (extension era) | 1.62 | 24.4% | -8.5% |

Uniform across eras; the edge is STRONGER on the newest data. The
champion is a transparent composite (no fitted model state), immune to
the ls-framework's state-contamination failure on the same panel.

## 2. Robustness evidence
- Lag sensitivity: fundamental tilt survives 3-12mo reporting lags
- Cost sensitivity: SR 1.41 (6bps) -> 1.39 (10bps) -> 1.34 (20bps)
- Split-half and 3-era splits all > 1.29 SR; 2nd half > 1.30
- Family flat: tilt w 0.05-0.15, gold 15-25%, G_DIV 4-8, gate 11-13 all
  within ~0.05 SR of optimum — not a knife-edge
- Fairest benchmark: vs static 80/20 SPY/GLD buy-hold (same asset mix,
  no timing/tilt): +0.63 SR, +5.9pp/yr, 3.8x smaller DD. The alpha is
  from the SIGNALS (timing/selection/concentration), not the gold
  sleeve (static 80/20 earns only 10.4%).
- Alpha decomposition (layer ablation, vt10): trend gate = DD engine
  (+0.33 SR, MaxDD -20.5% -> -10.3%); gold = modern-era stability
  (2nd-half SR 0.944 -> 1.296); tilt = +0.12 SR; raw selection alone
  (SR 0.823) still beats SPY (0.674) and 80/20 (0.775).

## 3. What was tried and rejected (honest ledger)
| lever | result |
|-------|--------|
| crash filters (blunt & sharp) | kill return or no DD gain — DD is grind + factor crash |
| self-trend gate | return-to-smoothness only |
| bonds TLT/IEF sleeve | -41.5% through 2021-23 grind — hurts |
| JPY sleeve | -24% through 2021-23 grind — hurts |
| weekly rebalance | SR 0.54 — noise+cost |
| quarterly/semi-annual | worse DD, less gate responsiveness |
| VIX de-risk gate | redundant with SPY13MA — removal improved SR 1.33->1.37 |
| soft (proportional) gate | worse than binary |
| gross-margin tilt | sparse coverage, hurts |
| ls h21_n13 blend | stream STALE (twelvedata path dead on current panel) — retracted |
| ls n10_r14 blend | current-data valid but 3.1%/yr leg drags return |

## 4. Deployment options
1. **Champion composite alone (recommended, fully backtested)**:
   `run_champion_fund_tilt.py` with TILT_MODE=vq TILT_W=0.10 GOLD_W=0.20
   GATE_LB=13 VIX_F1=VIX_F2=VIX_F3=1.0 MOM_LB="6 12 24" G_DIV=6
   VOL_CAP=1.2 REV_SLEEVE=0.0 VOL_TARGET=0.10 (or 0.06 for max safety).
   - vt10: SR 1.41 / 16.2% / -10.3% | vt6: SR 1.40 / 11.6% / -7.6%
2. **+ ls L/S overlay (2018+, current-data n10_r14 stream)**:
   champ vt6 60-70% + ls 30-40% -> SR 1.38-1.44 / 7.5-8.3% / -4.3..-5.1%.
   Lower return, much lower DD. Requires running the ls polygon/8y
   champion pipeline regularly (not yet automated).

## 5. Current position (as of 2026-07-31)
- Gate ON (SPY 747 > 13MA 691) — momentum leg active
- 48 names; top: MU DELL INTC AMD HPE AMAT CRWD NET FTNT DDOG VRT WBD
  VLO HWM PANW
- Allocation: 80% book + 20% GLD

## 6. Cost note
All figures net of 6bps on measured turnover (momentum churn 24.4%/mo +
gold ~0). Gross is ~0.18%/yr higher return. Scripts:
- `run_champion_fund_tilt.py` — champion (all knobs env-tunable)
- `run_live_champion.py` — current signal + paper-trade history
- `check_paper_trade.py` — score recorded signals vs realized months
- `blend_ls.py` — ls overlay testing
- `tools/quant/refresh_panel.py` — data refresh (idempotent, 0.04s when
  current; SKIP_SYMS for provider-never-resolves tickers; ~70 min only
  after a multi-day gap). Run it in the monitoring loop each fire.
- Data: twelve_big panel + GLD (twelvedata) + SEC fundamentals parquet

## 7. Monitoring loop (self-maintaining)
Each fire (or cron): `refresh_panel.py` (keep data current) ->
`run_live_champion.py` (emit signal, append history) ->
`check_paper_trade.py` (score realized months). Costs: ~0.04s + ~10s +
~1s when data is current. New month-end data flows through automatically.
