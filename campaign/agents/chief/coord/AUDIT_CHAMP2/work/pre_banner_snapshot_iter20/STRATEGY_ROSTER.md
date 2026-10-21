# STRATEGY ROSTER — organized map of all requested strategy families (2026-09-15)

Honest contract everywhere (T+1, full 6.4bps, borrow, vol-target, no leak, no flatten, proper
position-rotation scramble). "PASS" = clears every gate (SR>=0.6, H1/H2>=0.3, <=2 neg-yrs>-5%,
scramble p<0.05, |corr|<0.15 to champion, ac1<0.5, uniqR>=0.08).

## VERDICT TABLE
| Strategy | Free data (source) | SR | Result |
|---|---|---|---|
| **Inter-commodity NYH-Gulf basis** (跨品种) | EIA daily spots | 1.94 | ✅ PASS (16 sleeves in HUNT_CLASSIC_SPREADS) |
| **Crack spread** 裂解 (3:2:1/2:1:1/gas) | EIA daily spots | 0.79-1.02 | ✅ PASS (8 sleeves) |
| **Calendar/term-spread** 跨期 | CBOE VIX term (VIX9D/3M/6M) | 0.83-1.89 | ✅ PASS (5 sleeves) |
| **Inter-commodity China M0-RM0** | akshare futures | 0.82 | ✅ PASS (cnpair_M0_RM0) |
| 海龟 Turtle | akshare 25 CN futures | 0.67 | ❌ REJECT (3 neg-yrs) |
| 商品截面多因子 | akshare futures | 0.25-0.39 | ❌ REJECT (needs per-contract carry) |
| 外汇套息 FX Carry | FRED G10 3M + fx_hist | 0.03 | ❌ REJECT (regime-dependent) |
| Pair trading (equity) | twelve_big panel | 0.31 | ❌ REJECT |
| Trend/CTA (spot proxy) | spot/ETF/FX | -0.5..-1.0 | ❌ REJECT (no roll-yield) |
| Vol-arb (VIX-index proxy) | more_vol | -0.16 | ❌ REJECT (needs VIX futures) |
| **Avellaneda-Lee stat-arb** (HF-credible) | twelve_big+twelve_extend 599 names | **0.52** | 🟡 **NET SR 0.52 PASS-direction**: dollar-neutral 599-name residual/OU monthly, real +3.9% ann 2neg-yrs, but below paper 1.44 (large-cap panel+decay). sleeve saved |
| VRP / put-selling | VIX^2 vs SPX realized | 13.9(ac1 .97) | ❌ REJECT — standing-premium artifact, needs option-chain delta/gamma |
| Merger arb | — (SEC 403) | — | ⛔ NOT buildable free on box |

## BUILDABLE WITH FREE DATA AVAILABLE NOW (akshare verified) — next build queue
| Strategy | Data | Note |
|---|---|---|
| ETF 折溢价套利 (#8) | fund_etf_spot_em (1611 ETFs: 价/IOPV/折价率) | buildable; need daily premium history |
| 可转债双低轮动 (#12) | bond_zh_hs_cov_spot/daily | buildable; multi-step historical premium fetch |
| 国债期货-国债ETF套利 (#11) | bond ETFs + CFFEX T/TF (akshare) | buildable |
| 商品跨期正反套 (per-month) | futures_zh_daily_sina per-month (RB2310 vs RB2401) | buildable, next step |
| 中国跨品种补全 (Y/P, RB/I, SC/FU) | akshare | done for M0-RM0; others rejected |

## DOCUMENTED DATA-CONSTRAINED (honest; partial/instructional-depth free data)
| Strategy | Blocker |
|---|---|
| 期权VSI 逐档偏斜 (true per-strike) | needs per-strike OTM/ITM IV chain; **CBOE VIX-term proxy already PASSes** (term-slope) |
| 期权日历价差 (option calendar) | needs near+far month option chains (price+greeks), heavy |
| 国债期货期现 IRR | needs CFFEX T/TF + CTD cash + DR007, institutional depth |
| ETF期权多空 / 夏凯期权腿 | needs option chains with IV/delta by strike |

## ADOPTION GATE (capital-real dAnn>0, fixed 1.6x gross) — HONEST
Every PASSING sleeve was adoption-tested against the champion; NONE raises full-window ann at
fixed 1.6x gross (gasreg -0.97pp, vixterm -1.28pp) though several raise SR (3.27-3.30) and lower
MDD. Champion stays at the honest frontier **ann 39.50% | SR 3.2176 | MDD -6.52% | 0/19 neg-yrs**.
Energy-family weight does NOT drop (brwt block 51% stays 43-47%). Reproduce:
campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch/adoption_test.py.

## REPO MAP
  campaign/STRATEGY_ROSTER.md                      <- this file
  campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/  -> 20 PASS sleeve CSVs + FINDINGS + adoption_test
  campaign/agents/loop_team/HUNT_CN_FUTURES/       -> China futures: data/ fetch, turtle/xsection/
                                                      carry/cnpairs honest results + FINDINGS
  campaign/agents/loop_team/HUNT_CN_INSTITUTIONAL/  -> the 6 high-Sharpe institutional strategies:
                                                      organized doc + FREE-DATA recipes + results
  campaign/agents/loop_team/HUNT_HF_STATARB/        -> hedge-fund-credible strategies (Avellaneda-Lee
                                                      honest reproduction, VRP caution, pairs/turtle):
                                                      HF_STRATEGIES.md + honest gate results
