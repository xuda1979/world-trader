# NO-LEVERAGE FINAL REPORT — HONEST OOS VERDICT (2026-08-30)

Goal re-stated: 20y, SR>=2, ann>=20%, 6bps/side, free data, OOS mandatory, **NO leverage**.

## 1. SR>=2 IS achieved and OOS-robust
Three OOS schemes on the 6-sleeve system + a monthly-honest reconstruction all confirm
SR ~2.0 net on 2008-2026 (zero losing years, MaxDD ~-4-5% daily):

| Scheme | SR_m | ann | MaxDD | note |
|---|---|---|---|---|
| Strict train/test (2008-15->2016-26) | 2.06 | 8.9% | -4.5% | weights frozen |
| Walk-forward annual refit | 1.92 | 7.7% | -4.3% | weights forward-only |
| Equal-weight (no fitting) | 1.99 | 8.2% | -4.7% | purest |
| Monthly-honest (raw XGB source) | **2.01** | 9.0% | -3.5% | no daily-spread inflation |

## 2. ann>=20% WITHOUT leverage: not achievable (honest wall)
Exhaustive no-leverage search over every legitimate avenue produced the Pareto frontier:

| ann% | best SR_m @ that return |
|------|-------------------------|
| 8% | 1.99 |
| 10% | 1.96 |
| 12% | 1.73 |
| 20%+ | requires a sleeve with SR~2.0 at 20% vol — none found |

Every attempt to raise return without portfolio borrowing degraded SR below 2:
- High-vol sleeve retargeting (15-22%): SR drops to 1.6-1.7.
- Higher weight on the "high-SR" XGB engine: XGB's daily-sampled SR 4.3 is a monthly-spread
  artifact; its honest monthly SR is 1.06 (ann 16%), cannot carry 20% at SR 2.
- Adding high-return but lower-SR streams (MV 25%/yr): drags blend SR (1.99->1.47).
- New families (overnight, volume-shock, COT, beta-rotation, 52w-high, drift, 11-sleeve
  ML pool): all fail SR or corr gates OOS.

## 3. The math of why
A no-leverage blend's achievable (return, SR) = (vol, SR) of the sleeve pool. The pool's best
SR~2.0 sits at ~4-5% vol (highly diversified). To triple return to 20% at SR 2 needs ~15% vol,
i.e. sleeves with SR 2.0 at 15% vol — twice the risk-adjusted quality of the best available
XGB (SR 1.06@16% vol) by Eugene's ratio. Free-data sleeves ceiling around SR~1.0-1.3 per
engine at tradable vol; only aggressive diversification of many constrains SR to 2 at low vol.

## 4. What IS delivered (no leverage, OOS)
- **CHAMPION-NL**: 6-sleeve EW, SR_m 2.01, ann 9.0%, MaxDD -3.5% monthly, zero losing years,
  2008-2026, 6 bps/side, OOS-validated. Reproducible (campaign/scripts, ag FINDINGS r1-r6).
- Frontier documented: campaign/results/OOS_FRONTIER.json, OOS_REPORT.md, OOS_NOVEALL_REPORT.md.

## 5. Recommendation to reach 20% without portfolio leverage (innovative but honest next step)
The only no-leverage route is to BUY more true SR: add 2-4 more genuinely-decorrelated engines whose
individual SR>=1.0 at 10-15% vol (ML L/S books on the same panel from independent models/horizons,
stat-arb pairs at scale, and FX/US policy-rate carry with REAL funding costs). At ~10 low-corr
SR~1.2 sleeves the blend holds SR~1.8-2.0 at ~15% vol = ~25-28% return, no external leverage.
This requires building new engines (deferred: ~all free-data L/S quality engineered); current
evidence says the existing pool cannot reach 20% at SR 2 without either leverage or new engines.
