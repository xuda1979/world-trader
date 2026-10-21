# V1_volterm — Volatility Term-Structure Slope as Regime Gate

## VERDICT: REJECT
**Best slope-gate sleeve SR = 0.76 (TS_bin) vs unconditional SPY buy-and-hold SR = 0.78 on the same window. The term-structure slope gate adds ZERO timing alpha on SPY — every gated variant is dominated by simply holding SPY. Fails the SR>=1.5 sleeve gate by a wide margin (0.76 << 1.5). No sleeve written (V1_sleeve.csv withheld per gate).**

Champion context (same window 2009-10-01..2026-08-28, n=4412): SR=5.12, ann=60.8%.

## Data spans (verified from file heads/tails)
| Series | Span | Note |
|---|---|---|
| VIX | 1990-01-02..2026-09-02 | |
| VIX3M | 2009-09-18..2026-09-02 | window driver: main test = 2009-10-01.. |
| VIX6M | 2008-01-02..2026-09-02 | |
| VIX9D | 2011-01-04..2026-09-02 | |
| VXV | 2007-12-04..2026-09-01 | corr(VXV,VIX3M)=1.0000 on overlap (n=4264) — VXV IS VIX3M post-rename; not a separate tenor |
| OVX | 2009-09-18..2026-09-02 | single tenor — no true term structure exists |
| GVZ | 2009-09-18..2026-09-02 | single tenor, same limitation |
| SPY | 2004-01-02..2026-09-09 | tools/quant/data/cboe_hist/SPY.csv |
| XLE | 1998-12-22..2026-09-04 | more_etf |
| Champion | 2008-09-01..2026-08-28 | GOAL100_CHAMPION_daily.csv col `ret` |

## Method (causal, no lookahead)
- Signal computed from closes at day t; weight held over close t -> close t+1 (`w.shift(1)` applied to day-t+1 return). Strict T+1.
- Costs per campaign rule: 6bps per FULL one-side |dW| turnover charged daily; 4.5%/yr margin on (gross-1) for any leveraged variant; 0.5%/yr borrow on short notional for L/S variants.
- Math: ann=(1+r).prod()**(252/n)-1; SR=r.mean()/r.std()*sqrt(252); MaxDD=(1+r).cumprod() drawdown (negative).
- main window n=4255 days (2009-10-01..2026-08-28), slope=VIX3M/VIX ffilled, 0 NaN in window.
- **Data caveat (disclosed): SPY/XLE sources are price-only (no adjusted close available offline). Dividends (~1.8%/yr) are missing from ALL variants equally; sensitivity below shows conclusions unchanged with divs added.**

## Results A — slope gates on SPY (n=4255, 2009-10..2026-08)
| Variant | ann | SR | MaxDD | turn/yr | corr champ |
|---|---|---|---|---|---|
| BH_SPY (benchmark) | 12.6% | **0.780** | -34.1% | 0 | 0.263 |
| TS_bin (w=1 if slope>1) | 9.8% | 0.757 | -30.5% | 12.6 | 0.288 |
| TS_bin_hyst (1.02/0.98) | 9.0% | 0.694 | -24.7% | 6.3 | 0.299 |
| TS_z continuous | 11.1% | 0.742 | -34.1% | 19.3 | 0.238 |
| TS_lin clip((s-1)*10) | 6.7% | 0.650 | -26.0% | 20.1 | 0.289 |
| TS_LS (+1/-1) | 5.8% | 0.416 | -38.1% | 25.1 | 0.193 |
| TS_bin + VIX>32 standdown | 8.3% | 0.670 | -30.3% | 14.2 | 0.288 |
| TS69_bin (VIX6M/VIX9D, n=3937) | 7.3% | 0.611 | -32.2% | 15.4 | 0.293 |
| 69_BH_SPY (matched benchmark) | 12.2% | 0.757 | -34.1% | 0 | 0.260 |

## Results B — inverse / short-hedge / risk-budget variants
| Variant | ann | SR | MaxDD | corr champ |
|---|---|---|---|---|
| BH_SPY | 12.6% | **0.780** | -34.1% | 0.263 |
| INV_bin (long only in backwardation) | 1.2% | 0.165 | -30.9% | 0.057 |
| SHORT_backw (short SPY when slope<1) | -3.7% | -0.312 | -50.0% | -0.057 |
| VT15_slope (slope gate x 15% vol target, lev<=2) | 7.2% | 0.537 | -25.6% | 0.316 |
| VT15_BH (vol-target, NO signal — benchmark) | 9.5% | 0.640 | -22.3% | 0.336 |
| Steep_lev25 (slope>1.05, lev<=2.5) | 4.4% | 0.377 | -27.8% | 0.295 |
| Slope_vs_MA100 | 3.3% | 0.408 | -21.0% | 0.190 |
| Hyst + VIX<15 OR-gate | 7.1% | 0.592 | -30.3% | 0.288 |

## Results C — OVX gating XLE (single-tenor proxies, no true slope; n=4187, 2010+)
| Variant | ann | SR | MaxDD | corr champ |
|---|---|---|---|---|
| BH_XLE | 4.9% | 0.312 | -77.4% | 0.128 |
| OVX < 63d-median | -1.8% | -0.024 | -56.6% | 0.104 |
| OVX 5d-momentum < 0 | 0.2% | 0.102 | -56.4% | 0.100 |
| OVX < 40 | -4.9% | -0.223 | -75.4% | 0.185 |

## Kill evidence
1. **No edge vs benchmark:** best gate (TS_bin 0.757) < matched BH (0.757/0.780). The gate cuts vol (13.5% vs 17.1%) but cuts return MORE (9.8% vs 12.6%) — the days it sits out are net-positive SPY days.
2. **Scramble test FAILS to separate:** TS_bin_hyst actual SR=0.694; circular-shift(+252d) weights scramble SR=0.650. Edge indistinguishable from noise/long-bias.
3. **Dividend sensitivity:** adding 1.8%/yr to long days: BH SR 0.886 vs TS_bin 0.879 — gate still dominated.
4. **OVX "slope" does not exist** (single tenor) and both level/trend proxies LOSE money vs BH_XLE (SR -0.02 and +0.10 vs 0.31).
5. Consistent with A5_vol_cond FINDINGS (r7): "VIX/rate timing have no post-2000 alpha." The champion's A5 contango sleeve monetizes the term structure as CARRY (short VIX futures in contango), a different mechanism from gating equity beta; the slope as an equity gate is just a slow, churning trend filter.
6. Corr-to-champion passed (max 0.32 < 0.5) but is moot — SR gate fails 0.78 << 1.5.

## FAIL-CLOSED log
- No check was incomputable; all gates computed. REJECT logged with numbers above.
- Dead-ideas #62-63 (IV/PCA bond) NOT rebuilt, per brief.
- Grid + return series on disk: grid1.csv, series.pkl; scripts run_v1.py (+ inline round B).
- V1_sleeve.csv NOT written — condition SR>=1.5 not met (best 0.757).

DONE V1_volterm
