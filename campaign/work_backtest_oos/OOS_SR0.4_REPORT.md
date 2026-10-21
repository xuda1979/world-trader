# OOS BACKTEST — ALL CAMPAIGN STRATEGIES (INDEPENDENT MULTI-AGENT AUDIT)

Generated 2026-09-16 — each strategy audited & backtested by an INDEPENDENT agent process (12 parallel agents), reconciled by coordinator.
Contract: [date,ret] daily NET-return stream; OOS = returns >= 2016-01-01.
Filter: annualized OOS Sharpe > 0.4, on a genuine daily return-stream (agent-adversarially verified; non-stream/constant files rejected).

## SUMMARY
- Independent agents run: 12 (parallel, disjoint slices)
- Strategies audited: 415
- Genuine daily-return streams: 352
- Non-stream files rejected by agents: 63
- **PASSING OOS SR>0.4: 166**
  - OOS SR>5: 16 | 2-5: 37 | 1-2: 30 | 0.4-1: 83

## WARNING — top entries are campaign-discredited artifacts (NOT adoptable)
- **MHX** (2 files, OOS SR to ~6.18): pickle-cache leak / unverifiable model cache (AUDIT1_mhx) — rejected by campaign
- **HT_TAIL** (9 files, OOS SR to ~5.04): half-turn@6.0 cost-undercharge artifact (audit A1 defect) — rejected by campaign

## PASSING BY FAMILY (honest, OOS SR>0.4)
- agents/chief: n=52, OOS SR max=3.58, median=0.68
- agents/loop_team: n=43, OOS SR max=5.04, median=1.06
- team/agents: n=15, OOS SR max=1.22, median=0.56
- results/sleeve_library: n=14, OOS SR max=0.92, median=0.77
- agents/COORD: n=11, OOS SR max=6.18, median=3.19
- agents/E1_20yspan: n=9, OOS SR max=5.56, median=1.74
- agents/A1_trend_cta: n=4, OOS SR max=1.24, median=0.98
- agents/A5_vol_cond: n=3, OOS SR max=1.19, median=1.19
- agents/A6_reversal: n=3, OOS SR max=1.74, median=1.05
- agents/C5_newdata: n=3, OOS SR max=2.55, median=2.53
- agents/A3_xs_quality: n=2, OOS SR max=1.15, median=0.98
- agents/B2_highfreq: n=2, OOS SR max=2.40, median=1.68
- agents/B5_construct: n=2, OOS SR max=5.13, median=4.46
- agents/C4_metaalloc: n=2, OOS SR max=5.81, median=5.60
- agents/A2_fx_carry: n=1, OOS SR max=0.82, median=0.82

## TOP 40 HONEST PASSING (excl known discredited)
| OOS SR | Full SR | H1 | H2 | negYr | OOS n | Start | End | Flag | Strategy |
|--------|---------|----|----|-------|-------|-------|-----|------|----------|
| 5.81 | 5.40 | 5.00 | 5.79 | 0.0/19.0 | 2781.0 | 2008-09-01 | 2026-08-28 |  | agents/C4_metaalloc/sleeves/C4_construct_v2.csv |
| 5.56 | 5.12 | 4.78 | 5.45 | 1.0/21.0 | 2781.0 | 2006-10-02 | 2026-08-28 |  | agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_uncostB3.csv |
| 5.40 | 5.09 | 4.95 | 5.23 | 0.0/19.0 | 2937.0 | 2008-09-01 | 2026-08-28 |  | agents/C4_metaalloc/sleeves/C4_construct_v1.csv |
| 5.27 | 4.85 | 4.53 | 5.15 | 1.0/21.0 | 2781.0 | 2006-10-02 | 2026-08-28 |  | agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_costedB3.csv |
| 5.13 | 4.53 | 3.95 | 5.12 | 0.0/19.0 | 2781.0 | 2008-09-01 | 2026-08-28 |  | agents/B5_construct/sleeves/B5_CONSTRUCT_vt75_dd4_13.csv |
| 3.80 | 3.40 | 2.80 | 3.97 | 0.0/19.0 | 2781.0 | 2008-09-01 | 2026-08-28 |  | agents/B5_construct/sleeves/B5_vt8_dd3_ew9.csv |
| 3.58 | 3.53 | 3.72 | 3.34 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_bm_overlay_on_CHAMP.csv |
| 3.57 | 3.53 | 3.72 | 3.33 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_BTCMA50_gate_on_CHAMP.csv |
| 3.21 | 3.19 | 3.33 | 3.07 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt7.csv |
| 3.21 | 3.19 | 3.33 | 3.07 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt7__prefix.csv |
| 3.21 | 3.27 | 3.64 | 2.97 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt_ens.csv |
| 3.21 | 3.27 | 3.72 | 3.00 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_a_overlay_on_CHAMP.csv |
| 3.21 | 3.10 | 3.26 | 2.97 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5__prefix.csv |
| 3.21 | 3.10 | 3.26 | 2.97 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt5.csv |
| 3.20 | 3.32 | 3.72 | 2.86 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_am_overlay_on_CHAMP.csv |
| 3.20 | 3.24 | 3.63 | 3.04 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_MACRO2/sleeves/champ_overlay_T10Y2Yz63m2_x06.csv |
| 3.19 | 3.48 | 3.71 | 3.24 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/COORD/sleeves/brwt5_2000.csv |
| 3.19 | 3.48 | 3.71 | 3.24 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5_2000__prefix.csv |
| 3.18 | 3.26 | 3.80 | 3.02 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_MACRO2/sleeves/champ_overlay_VIXsus21_OR_T10Y2Yz63_x06.csv |
| 3.12 | 3.23 | 3.72 | 2.87 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_b_overlay_on_CHAMP.csv |
| 3.05 | 3.02 | 3.17 | 2.90 | 0.0/19.0 | 2631.0 | 2008-03-31 | 2026-08-28 |  | agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv |
| 3.03 | 3.01 | 3.15 | 2.89 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt7__R3COSTFIX.csv |
| 3.02 | 2.91 | 3.07 | 2.78 | 0.0/19.0 | 2631.0 | 2008-03-31 | 2026-08-28 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv |
| 2.99 | 2.89 | 3.05 | 2.75 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5__R3COSTFIX.csv |
| 2.98 | 3.28 | 3.52 | 3.03 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5_2000__costfix.csv |
| 2.92 | 3.41 | 3.84 | 2.97 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/COORD/sleeves/brwt10_2000.csv |
| 2.92 | 3.41 | 3.84 | 2.97 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__prefix.csv |
| 2.92 | 3.00 | 3.24 | 2.75 | 0.0/19.0 | 2611.0 | 2008-01-02 | 2026-07-31 |  | agents/COORD/sleeves/brent_wti_spread.csv |
| 2.77 | 3.26 | 3.68 | 2.82 | 0.0/27.0 | 2631.0 | 2000-03-30 | 2026-08-28 |  | agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv |
| 2.76 | 3.25 | 3.68 | 2.80 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt10__R3COSTFIX.csv |
| 2.66 | 3.21 | 3.82 | 2.58 | 13.0/38.0 | 126.0 | 1989-02-01 | 2026-06-01 |  | agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv |
| 2.55 | 2.19 | 1.67 | 2.62 | 0.0/19.0 | 2679.0 | 2008-03-28 | 2026-08-24 |  | agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv |
| 2.54 | 2.02 | 1.76 | 2.27 | 1.0/30.0 | 2679.0 | 1997-04-02 | 2026-08-24 |  | agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv |
| 2.53 | 2.05 | 1.32 | 2.61 | 0.0/19.0 | 2679.0 | 2008-03-28 | 2026-08-24 |  | agents/C5_newdata/sleeves/C5_ng_summer_weekday_ddt.csv |
| 2.45 | 2.53 | 2.96 | 2.22 | 1.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt21.csv |
| 2.40 | 2.50 | 2.83 | 2.24 | 0.0/19.0 | 2611.0 | 2008-03-31 | 2026-07-31 |  | agents/B2_highfreq/sleeves/brwt_spread_rev15.csv |
| 2.39 | 2.76 | 3.02 | 2.49 | 0.0/27.0 | 2611.0 | 2000-03-30 | 2026-07-31 |  | agents/chief/coord/CAMP_COST/sleeves/brwt15__prefix.csv |
| 2.28 | 2.65 | 2.92 | 2.37 | 0.0/27.0 | 2611.0 | 2000-03-30 | 2026-07-31 |  | agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv |
| 2.25 | 2.58 | 3.06 | 2.05 | 0.0/19.0 | 2526.0 | 2008-01-02 | 2026-08-24 |  | agents/COORD/sleeves/WTI-Brent_rev.csv |
| 2.21 | 1.92 | 1.56 | 2.26 | 0.0/19.0 | 2665.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L60Z1.0.csv |

## AGENT-BY-AGENT PASSING (independent slices)
- agent_0: 15/35 passing (slice 35)
- agent_1: 15/35 passing (slice 35)
- agent_2: 16/35 passing (slice 35)
- agent_3: 10/35 passing (slice 35)
- agent_4: 12/35 passing (slice 35)
- agent_5: 14/35 passing (slice 35)
- agent_6: 14/35 passing (slice 35)
- agent_7: 12/34 passing (slice 34)
- agent_8: 16/34 passing (slice 34)
- agent_9: 14/34 passing (slice 34)
- agent_10: 13/34 passing (slice 34)
- agent_11: 15/34 passing (slice 34)

## FULL PASSING TABLE (all {n}, OOS SR>0.4)
| OOS SR | Full SR | H1 | H2 | negYr | OOS n | Start | End | Flag | Strategy |
|--------|---------|----|----|-------|-------|-------|-----|------|----------|
| 6.18 | 5.32 | 5.05 | 5.98 | 0.0/19.0 | 2643.0 | 2008-09-02 | 2026-07-14 | MHX-AUDIT1 | agents/COORD/sleeves/MHX_f6.csv |
| 6.02 | 5.20 | 4.95 | 5.81 | 0.0/19.0 | 2769.0 | 2008-09-02 | 2026-08-12 | MHX-AUDIT1 | agents/COORD/sleeves/MHX_multihorizon_xgb.csv |
| 5.81 | 5.40 | 5.00 | 5.79 | 0.0/19.0 | 2781.0 | 2008-09-01 | 2026-08-28 |  | agents/C4_metaalloc/sleeves/C4_construct_v2.csv |
| 5.56 | 5.12 | 4.78 | 5.45 | 1.0/21.0 | 2781.0 | 2006-10-02 | 2026-08-28 |  | agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_uncostB3.csv |
| 5.40 | 5.09 | 4.95 | 5.23 | 0.0/19.0 | 2937.0 | 2008-09-01 | 2026-08-28 |  | agents/C4_metaalloc/sleeves/C4_construct_v1.csv |
| 5.27 | 4.85 | 4.53 | 5.15 | 1.0/21.0 | 2781.0 | 2006-10-02 | 2026-08-28 |  | agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_costedB3.csv |
| 5.13 | 4.53 | 3.95 | 5.12 | 0.0/19.0 | 2781.0 | 2008-09-01 | 2026-08-28 |  | agents/B5_construct/sleeves/B5_CONSTRUCT_vt75_dd4_13.csv |
| 5.04 | 4.71 | 4.44 | 4.98 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_LEV16_BAL_daily.csv |
| 5.04 | 4.71 | 4.44 | 4.98 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_L16C_BAL_daily.csv |
| 5.04 | 4.71 | 4.44 | 4.98 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_HL16_BAL_daily.csv |
| 5.04 | 4.70 | 4.41 | 4.98 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_LEV16_AGGR_daily.csv |
| 5.04 | 4.70 | 4.41 | 4.98 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_L16C_AGGR_daily.csv |
| 5.04 | 4.70 | 4.41 | 4.98 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_HL16_AGGR_daily.csv |
| 5.02 | 4.72 | 4.47 | 4.96 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_L16C_SAFE_daily.csv |
| 5.02 | 4.72 | 4.47 | 4.96 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_LEV16_SAFE_daily.csv |
| 5.02 | 4.71 | 4.46 | 4.96 | 0.0/19.0 | 2592.0 | 2008-03-31 | 2026-07-31 | HT_TAIL-A1 | agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_HL16_SAFE_daily.csv |
| 3.80 | 3.40 | 2.80 | 3.97 | 0.0/19.0 | 2781.0 | 2008-09-01 | 2026-08-28 |  | agents/B5_construct/sleeves/B5_vt8_dd3_ew9.csv |
| 3.58 | 3.53 | 3.72 | 3.34 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_bm_overlay_on_CHAMP.csv |
| 3.57 | 3.53 | 3.72 | 3.33 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_BTCMA50_gate_on_CHAMP.csv |
| 3.21 | 3.19 | 3.33 | 3.07 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt7.csv |
| 3.21 | 3.19 | 3.33 | 3.07 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt7__prefix.csv |
| 3.21 | 3.27 | 3.64 | 2.97 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt_ens.csv |
| 3.21 | 3.27 | 3.72 | 3.00 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_a_overlay_on_CHAMP.csv |
| 3.21 | 3.10 | 3.26 | 2.97 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5__prefix.csv |
| 3.21 | 3.10 | 3.26 | 2.97 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt5.csv |
| 3.20 | 3.32 | 3.72 | 2.86 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_am_overlay_on_CHAMP.csv |
| 3.20 | 3.24 | 3.63 | 3.04 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_MACRO2/sleeves/champ_overlay_T10Y2Yz63m2_x06.csv |
| 3.19 | 3.48 | 3.71 | 3.24 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/COORD/sleeves/brwt5_2000.csv |
| 3.19 | 3.48 | 3.71 | 3.24 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5_2000__prefix.csv |
| 3.18 | 3.26 | 3.80 | 3.02 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_MACRO2/sleeves/champ_overlay_VIXsus21_OR_T10Y2Yz63_x06.csv |
| 3.12 | 3.23 | 3.72 | 2.87 | 0.0/19.0 | 2780.0 | 2008-03-31 | 2026-08-27 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_b_overlay_on_CHAMP.csv |
| 3.05 | 3.02 | 3.17 | 2.90 | 0.0/19.0 | 2631.0 | 2008-03-31 | 2026-08-28 |  | agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv |
| 3.03 | 3.01 | 3.15 | 2.89 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt7__R3COSTFIX.csv |
| 3.02 | 2.91 | 3.07 | 2.78 | 0.0/19.0 | 2631.0 | 2008-03-31 | 2026-08-28 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv |
| 2.99 | 2.89 | 3.05 | 2.75 | 0.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5__R3COSTFIX.csv |
| 2.98 | 3.28 | 3.52 | 3.03 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt5_2000__costfix.csv |
| 2.92 | 3.41 | 3.84 | 2.97 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/COORD/sleeves/brwt10_2000.csv |
| 2.92 | 3.41 | 3.84 | 2.97 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__prefix.csv |
| 2.92 | 3.00 | 3.24 | 2.75 | 0.0/19.0 | 2611.0 | 2008-01-02 | 2026-07-31 |  | agents/COORD/sleeves/brent_wti_spread.csv |
| 2.77 | 3.26 | 3.68 | 2.82 | 0.0/27.0 | 2631.0 | 2000-03-30 | 2026-08-28 |  | agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv |
| 2.76 | 3.25 | 3.68 | 2.80 | 0.0/27.0 | 2617.0 | 2000-03-30 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/brwt10__R3COSTFIX.csv |
| 2.66 | 3.21 | 3.82 | 2.58 | 13.0/38.0 | 126.0 | 1989-02-01 | 2026-06-01 |  | agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv |
| 2.55 | 2.19 | 1.67 | 2.62 | 0.0/19.0 | 2679.0 | 2008-03-28 | 2026-08-24 |  | agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv |
| 2.54 | 2.02 | 1.76 | 2.27 | 1.0/30.0 | 2679.0 | 1997-04-02 | 2026-08-24 |  | agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv |
| 2.53 | 2.05 | 1.32 | 2.61 | 0.0/19.0 | 2679.0 | 2008-03-28 | 2026-08-24 |  | agents/C5_newdata/sleeves/C5_ng_summer_weekday_ddt.csv |
| 2.45 | 2.53 | 2.96 | 2.22 | 1.0/19.0 | 2617.0 | 2008-03-31 | 2026-08-10 |  | agents/COORD/sleeves/brwt21.csv |
| 2.40 | 2.50 | 2.83 | 2.24 | 0.0/19.0 | 2611.0 | 2008-03-31 | 2026-07-31 |  | agents/B2_highfreq/sleeves/brwt_spread_rev15.csv |
| 2.39 | 2.76 | 3.02 | 2.49 | 0.0/27.0 | 2611.0 | 2000-03-30 | 2026-07-31 |  | agents/chief/coord/CAMP_COST/sleeves/brwt15__prefix.csv |
| 2.28 | 2.65 | 2.92 | 2.37 | 0.0/27.0 | 2611.0 | 2000-03-30 | 2026-07-31 |  | agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv |
| 2.25 | 2.58 | 3.06 | 2.05 | 0.0/19.0 | 2526.0 | 2008-01-02 | 2026-08-24 |  | agents/COORD/sleeves/WTI-Brent_rev.csv |
| 2.21 | 1.92 | 1.56 | 2.26 | 0.0/19.0 | 2665.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L60Z1.0.csv |
| 2.18 | 1.92 | 1.59 | 2.24 | 0.0/19.0 | 2665.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L40Z1.0.csv |
| 2.13 | 1.94 | 1.71 | 2.18 | 0.0/19.0 | 2665.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L30Z1.0.csv |
| 1.92 | 1.92 | 2.44 | 1.29 | 2.0/8.0 | 1799.0 | 2019-09-10 | 2026-08-05 |  | agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_carry_raw_daily.csv |
| 1.91 | 1.91 | 2.43 | 1.29 | 2.0/8.0 | 1799.0 | 2019-09-10 | 2026-08-05 |  | agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv |
| 1.87 | 1.87 | 2.45 | 1.10 | 1.0/8.0 | 1749.0 | 2019-11-22 | 2026-08-05 |  | agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv |
| 1.85 | 1.89 | 1.83 | 1.95 | 0.0/16.0 | 2681.0 | 2011-03-30 | 2026-09-01 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L20Z1.0.csv |
| 1.74 | 1.43 | 1.14 | 1.81 | 2.0/20.0 | 2664.0 | 2007-01-02 | 2026-08-27 |  | agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv |
| 1.74 | 2.03 | 2.60 | 1.29 | 4.0/37.0 | 2664.0 | 1990-01-04 | 2026-08-27 |  | agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv |
| 1.63 | 0.93 | 0.02 | 1.83 | 7.0/19.0 | 2664.0 | 2008-01-02 | 2026-08-27 |  | agents/COORD/sleeves/C2_steep_carry.csv |
| 1.50 | 1.74 | 2.18 | 1.55 | 0.0/19.0 | 2679.0 | 2008-03-28 | 2026-08-24 |  | agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv |
| 1.45 | 1.63 | 1.93 | 1.46 | 0.0/30.0 | 2679.0 | 1997-04-02 | 2026-08-24 |  | agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv |
| 1.36 | 1.42 | 1.22 | 1.64 | 0.0/16.0 | 2681.0 | 2011-03-30 | 2026-09-01 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L40Z1.5.csv |
| 1.25 | 1.22 | 1.17 | 1.27 | 1.0/21.0 | 2739.0 | 2006-09-27 | 2026-07-01 |  | agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv |
| 1.24 | 1.15 | 0.94 | 1.32 | 1.0/19.0 | 2739.0 | 2008-01-03 | 2026-07-01 |  | agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv |
| 1.22 | 0.92 | 0.71 | 1.23 | 2.0/22.0 | 2653.0 | 2005-01-25 | 2026-08-12 |  | team/agents/RES_CREDIT/sleeves/RC_t102_d5mr_w21_band50_vt5.csv |
| 1.19 | 1.02 | 0.94 | 1.10 | 1.0/18.0 | 2666.0 | 2009-09-18 | 2026-08-11 |  | agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv |
| 1.19 | 1.02 | 0.94 | 1.10 | 1.0/18.0 | 2666.0 | 2009-09-18 | 2026-08-11 |  | agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv |
| 1.18 | 1.02 | 0.82 | 1.20 | 1.0/21.0 | 2668.0 | 2006-12-13 | 2026-08-12 |  | agents/chief/coord/CAMP_COST/sleeves/QAxasts__prefix.csv |
| 1.17 | 1.01 | 0.80 | 1.19 | 1.0/21.0 | 2668.0 | 2006-12-13 | 2026-08-12 |  | agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv |
| 1.15 | 1.06 | 0.97 | 1.14 | 1.0/19.0 | 2668.0 | 2008-01-09 | 2026-08-12 |  | agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv |
| 1.13 | 1.51 | 1.69 | 1.35 | 2.0/37.0 | 2659.0 | 1990-01-03 | 2026-08-27 |  | agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv |
| 1.12 | 1.01 | 0.93 | 1.12 | 1.0/19.0 | 2648.0 | 2008-03-28 | 2026-08-10 |  | agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv |
| 1.11 | 1.03 | 0.88 | 1.18 | 2.0/19.0 | 2637.0 | 2008-01-02 | 2026-06-30 |  | agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv |
| 1.11 | 1.11 | 1.70 | 0.21 | 4.0/10.0 | 3215.0 | 2017-11-15 | 2026-09-03 |  | agents/loop_team/HUNT_CRYPTO_SAT/sleeves/CRYPTO_TSMOM21LO_net.csv |
| 1.08 | 0.96 | 0.87 | 1.08 | 1.0/19.0 | 2658.0 | 2008-03-28 | 2026-08-24 |  | agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv |
| 1.07 | 0.99 | 0.98 | 1.03 | 0.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L60Z1.5.csv |
| 1.06 | 1.15 | 1.02 | 1.29 | 0.0/16.0 | 2681.0 | 2011-03-30 | 2026-09-01 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_6_L40Z1.5.csv |
| 1.05 | 0.88 | 0.70 | 1.11 | 2.0/19.0 | 2668.0 | 2008-01-04 | 2026-08-12 |  | agents/A6_reversal/sleeves/a6_r2_pair_residmom_msew.csv |
| 1.04 | 1.35 | 2.18 | 0.75 | 0.0/19.0 | 2627.0 | 2008-02-19 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv |
| 1.04 | 0.84 | 0.80 | 0.90 | 2.0/19.0 | 2665.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_dieseljet_L60Z1.5.csv |
| 1.03 | 0.96 | 0.98 | 1.00 | 2.0/19.0 | 2648.0 | 2008-03-28 | 2026-08-10 |  | agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L15Z15_net.csv |
| 1.01 | 0.98 | 0.91 | 1.06 | 3.0/19.0 | 2637.0 | 2008-01-02 | 2026-06-30 |  | agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_raw_daily.csv |
| 0.99 | 0.96 | 1.06 | 0.90 | 1.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_gas_crack_nyh_L30Z1.5.csv |
| 0.99 | 1.04 | 1.08 | 1.01 | 2.0/19.0 | 2667.0 | 2008-01-03 | 2026-08-11 |  | agents/A1_trend_cta/sleeves/A1_mix_breadthCTA_SharpeW_LS13030.csv |
| 0.99 | 1.20 | 1.35 | 1.09 | 1.0/18.0 | 2681.0 | 2009-12-11 | 2026-09-01 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_3_6_L20Z1.5.csv |
| 0.98 | 0.92 | 0.91 | 0.96 | 1.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_gas_crack_nyh_L30Z2.0.csv |
| 0.97 | 0.92 | 0.97 | 0.91 | 1.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_gas_crack_nyh_L40Z1.0.csv |
| 0.96 | 0.82 | 0.57 | 1.01 | 0.0/19.0 | 2762.0 | 2008-01-03 | 2026-08-03 |  | agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv |
| 0.96 | 1.17 | 1.42 | 1.00 | 2.0/19.0 | 2925.0 | 2008-03-24 | 2026-08-13 |  | agents/B2_highfreq/sleeves/crossasset_rev_L8.csv |
| 0.95 | 0.83 | 0.62 | 1.00 | 3.0/21.0 | 2762.0 | 2006-09-27 | 2026-08-03 |  | agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv |
| 0.95 | 1.02 | 1.33 | 0.87 | 1.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack211_nyh_L15Z1.5.csv |
| 0.94 | 0.83 | 0.51 | 1.18 | 1.0/16.0 | 2681.0 | 2011-03-30 | 2026-09-01 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L60Z2.0.csv |
| 0.92 | 0.92 | 0.65 | 1.16 | 0.0/9.0 | 2161.0 | 2018-01-02 | 2026-08-06 |  | results/sleeve_library/ls_n10r14_2018.csv |
| 0.91 | 0.94 | 1.04 | 0.82 | 3.0/19.0 | 2668.0 | 2008-02-01 | 2026-08-12 |  | results/sleeve_library/AP_gold.csv |
| 0.91 | 0.91 | 1.35 | 0.23 | 2.0/10.0 | 3272.0 | 2017-09-19 | 2026-09-03 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_10-30_EW12_audit.csv |
| 0.88 | 0.98 | 1.27 | 0.82 | 1.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L15Z1.5.csv |
| 0.86 | 0.79 | 0.91 | 0.75 | 2.0/19.0 | 2665.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_dieseljet_L60Z1.0.csv |
| 0.86 | 1.44 | 2.05 | 0.91 | 3.0/37.0 | 2781.0 | 1990-03-28 | 2026-08-28 |  | agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv |
| 0.85 | 0.91 | 0.92 | 0.91 | 1.0/20.0 | 2637.0 | 2007-01-03 | 2026-06-30 |  | agents/A6_reversal/sleeves/a6_r2_pair_residmom_fm1926.csv |
| 0.84 | 0.87 | 0.92 | 0.82 | 2.0/19.0 | 2665.0 | 2008-01-03 | 2026-08-10 |  | results/sleeve_library/L_S_Market_Neutral.csv |
| 0.82 | 0.82 | 0.45 | 1.19 | 2.0/9.0 | 2235.0 | 2018-02-01 | 2026-08-27 |  | agents/A2_fx_carry/sleeves/A2_fx_carry_W11_accrual.csv |
| 0.82 | 0.89 | 0.99 | 0.80 | 1.0/20.0 | 2668.0 | 2007-10-08 | 2026-08-12 |  | agents/chief/coord/CAMP_COST/sleeves/dualmom__prefix.csv |
| 0.81 | 0.87 | 0.94 | 0.80 | 2.0/19.0 | 2897.0 | 2008-01-03 | 2026-08-11 |  | results/sleeve_library/Multi_Strategy_SharpeW.csv |
| 0.81 | 0.88 | 0.99 | 0.79 | 1.0/20.0 | 2668.0 | 2007-10-08 | 2026-08-12 |  | agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv |
| 0.80 | 0.88 | 1.11 | 0.76 | 1.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L60Z1.0.csv |
| 0.79 | 0.80 | 0.79 | 0.82 | 4.0/19.0 | 2668.0 | 2008-02-05 | 2026-08-12 |  | results/sleeve_library/L_S_130_30_volmanaged.csv |
| 0.79 | 0.79 | 0.94 | 0.73 | 0.0/19.0 | 2664.0 | 2008-03-28 | 2026-08-31 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack211_nyh_L60Z1.5.csv |
| 0.79 | 0.73 | 0.51 | 0.98 | 0.0/16.0 | 2681.0 | 2011-03-30 | 2026-09-01 |  | agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_6_L60Z2.0.csv |
| 0.79 | 0.81 | 0.87 | 0.77 | 3.0/19.0 | 2667.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/L_S_Dollar_Neutral.csv |
| 0.77 | 0.92 | 1.19 | 0.67 | 1.0/18.0 | 2743.0 | 2009-07-01 | 2026-08-17 |  | agents/loop_team/HUNT_FUNDAMENTAL/sleeves/HF_mom_cheap_liq_daily.csv |
| 0.77 | 0.83 | 0.86 | 0.80 | 1.0/19.0 | 2668.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/L_S_120_20.csv |
| 0.77 | 0.90 | 1.16 | 0.66 | 1.0/18.0 | 2743.0 | 2009-07-01 | 2026-08-17 |  | agents/loop_team/HUNT_FUNDAMENTAL/sleeves/HF_mom_cheap_daily.csv |
| 0.77 | 0.82 | 0.88 | 0.78 | 1.0/19.0 | 2668.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/L_S_130_30.csv |
| 0.76 | 1.08 | 1.90 | 0.54 | 1.0/19.0 | 2627.0 | 2008-02-25 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w63_z15_zo1.csv |
| 0.73 | 0.75 | 0.83 | 0.68 | 5.0/19.0 | 2668.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/Risk_Parity_Bridgewater.csv |
| 0.73 | 1.01 | 1.62 | 0.63 | 0.0/19.0 | 2627.0 | 2008-04-09 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w126_z15_zo1.csv |
| 0.73 | 0.82 | 0.87 | 0.81 | 2.0/14.0 | 2598.0 | 2013-04-02 | 2026-09-14 |  | agents/loop_team/HUNT_CN_FUTURES/sleeves/cnpair_M0_RM0_L60Z1.5.csv |
| 0.70 | 0.95 | 1.46 | 0.64 | 2.0/21.0 | 2630.0 | 2006-06-15 | 2026-08-28 |  | agents/loop_team/HUNT_BASIS2/sleeves/CRACK_ho_br_L21Z2_vt10.csv |
| 0.70 | 0.59 | 0.55 | 0.62 | 3.0/19.0 | 2682.0 | 2008-01-02 | 2026-09-02 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/D_xlu_ief.csv |
| 0.68 | 0.65 | 0.59 | 0.71 | 6.0/19.0 | 2684.0 | 2008-04-04 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT3_Sprd_DBE_DBP_LO_63d.csv |
| 0.68 | 0.70 | 0.61 | 0.78 | 5.0/19.0 | 2749.0 | 2008-01-04 | 2026-08-12 |  | results/sleeve_library/Multi_Strategy_EW.csv |
| 0.68 | 0.68 | 0.55 | 0.96 | 1.0/9.0 | 2047.0 | 2018-06-20 | 2026-08-12 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv |
| 0.68 | 1.10 | 2.00 | 0.47 | 2.0/19.0 | 2627.0 | 2008-02-04 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w40_z15_zo1.csv |
| 0.67 | 0.53 | 0.38 | 0.69 | 2.0/19.0 | 2667.0 | 2008-01-02 | 2026-08-12 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/A_rs_ratio.csv |
| 0.67 | 0.91 | 1.60 | 0.48 | 2.0/19.0 | 2627.0 | 2008-02-04 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w40_z20_zo1.csv |
| 0.67 | 0.58 | 0.46 | 0.70 | 5.0/20.0 | 2684.0 | 2007-06-04 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_h2_LS.csv |
| 0.65 | 0.31 | -0.15 | 0.71 | 3.0/16.0 | 2686.0 | 2011-02-09 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT3_Sprd_USCI_DBC_LO_126d.csv |
| 0.65 | 0.65 | 0.58 | 0.83 | 1.0/9.0 | 2047.0 | 2018-06-20 | 2026-08-12 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_invvol.csv |
| 0.64 | 0.64 | 0.58 | 0.81 | 1.0/9.0 | 2047.0 | 2018-06-20 | 2026-08-12 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_60_40_daily.csv |
| 0.64 | 0.64 | 1.06 | -0.07 | 2.0/10.0 | 3272.0 | 2017-09-19 | 2026-09-03 |  | agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_20-60_EW12.csv |
| 0.62 | 0.61 | 0.74 | 0.55 | 3.0/19.0 | 2682.0 | 2008-01-02 | 2026-09-02 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/B_barbell.csv |
| 0.61 | 0.78 | 1.20 | 0.55 | 2.0/19.0 | 2627.0 | 2008-02-25 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w63_z20_zo1.csv |
| 0.61 | 0.61 | 0.56 | 0.76 | 1.0/9.0 | 2047.0 | 2018-06-20 | 2026-08-12 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_monthly.csv |
| 0.61 | 0.61 | 0.55 | 0.76 | 1.0/9.0 | 2047.0 | 2018-06-20 | 2026-08-12 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_daily.csv |
| 0.61 | 0.52 | 0.36 | 0.83 | 2.0/15.0 | 2743.0 | 2012-03-28 | 2026-08-17 |  | agents/loop_team/HUNT_HF_STATARB/sleeves/al_dollar_neutral_net.csv |
| 0.60 | 0.60 | 0.54 | 0.76 | 1.0/9.0 | 2047.0 | 2018-06-20 | 2026-08-12 |  | agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_never.csv |
| 0.59 | 0.33 | 0.07 | 0.65 | 7.0/19.0 | 2668.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/Merger_Arb_PEAD_2pct.csv |
| 0.59 | 0.87 | 1.07 | 0.61 | 8.0/19.0 | 2658.0 | 2008-01-02 | 2026-08-21 |  | agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv |
| 0.59 | 0.85 | 1.04 | 0.60 | 8.0/19.0 | 2658.0 | 2008-01-02 | 2026-08-21 |  | agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_poolvt_daily.csv |
| 0.58 | 0.71 | 0.78 | 0.63 | 2.0/19.0 | 2684.0 | 2008-04-04 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT3_Sprd_DBE_DBP_LS_63d.csv |
| 0.57 | 0.46 | 0.32 | 0.62 | 5.0/19.0 | 2668.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/Merger_Arb_PEAD.csv |
| 0.56 | 0.51 | 0.69 | 0.41 | 4.0/19.0 | 2659.0 | 2008-04-10 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w126_z15_zo1.csv |
| 0.53 | 0.12 | -0.43 | 0.61 | 9.0/20.0 | 2663.0 | 2007-07-20 | 2026-09-01 |  | agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w126_z1_vt.csv |
| 0.52 | 0.57 | 0.80 | 0.43 | 3.0/19.0 | 2627.0 | 2008-09-15 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w126_z20_zo1.csv |
| 0.51 | 0.40 | 0.28 | 0.56 | 5.0/19.0 | 2668.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/Merger_Arb_PEAD_3pct.csv |
| 0.51 | 0.39 | 0.28 | 0.54 | 6.0/19.0 | 2668.0 | 2008-01-03 | 2026-08-12 |  | results/sleeve_library/Merger_Arb_PEAD_5pct.csv |
| 0.51 | 0.56 | 0.57 | 0.55 | 7.0/19.0 | 2667.0 | 2008-11-04 | 2026-08-12 |  | agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R2_RS252_LS.csv |
| 0.50 | 0.10 | -0.34 | 0.52 | 10.0/20.0 | 2684.0 | 2007-01-31 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_InflRegime_T10YIE_g2.csv |
| 0.50 | 0.74 | 1.18 | 0.32 | 22.0/77.0 | 2605.0 | 1950-12-15 | 2026-08-31 |  | agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_252_LF.csv |
| 0.48 | -0.09 | -0.40 | 0.40 | 14.0/25.0 | 2679.0 | 2002-08-01 | 2026-08-28 |  | agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k52_vt.csv |
| 0.47 | 0.08 | -0.15 | 0.40 | 14.0/25.0 | 2679.0 | 2002-08-01 | 2026-08-28 |  | agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k52_novt.csv |
| 0.47 | 0.43 | 0.55 | 0.37 | 3.0/19.0 | 2659.0 | 2008-05-23 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w126_z20_zo1.csv |
| 0.47 | 0.21 | -0.03 | 0.62 | 6.0/15.0 | 2684.0 | 2012-08-02 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_CotMom_9m_k2_UNGATED_ablation.csv |
| 0.44 | 0.38 | 0.47 | 0.34 | 6.0/19.0 | 2659.0 | 2008-03-05 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w63_z20_zo1.csv |
| 0.44 | 0.26 | -0.18 | 0.46 | 7.0/17.0 | 2778.0 | 2010-06-16 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ng_storage_z.csv |
| 0.44 | 0.17 | -0.04 | 0.54 | 5.0/15.0 | 2684.0 | 2012-08-02 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_XSMom_CORE9MOO_9m_k2_familybest.csv |
| 0.43 | 0.20 | -0.02 | 0.44 | 8.0/20.0 | 2665.0 | 2007-12-04 | 2026-09-01 |  | agents/chief/coord/HUNT_CMDT2/sleeves/prop_seas_12-02_novt.csv |
| 0.43 | 0.24 | -0.05 | 0.74 | 7.0/15.0 | 2684.0 | 2012-01-04 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_CarryBasis_k1_h3_familybest.csv |
| 0.42 | -0.06 | -0.73 | 0.53 | 12.0/20.0 | 2663.0 | 2007-06-05 | 2026-09-01 |  | agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w63_z1_vt.csv |
| 0.42 | 0.17 | -0.02 | 0.43 | 8.0/20.0 | 2665.0 | 2007-12-04 | 2026-09-01 |  | agents/chief/coord/HUNT_CMDT2/sleeves/prop_seas_12-02_vt.csv |
| 0.42 | -0.02 | -0.51 | 0.45 | 13.0/20.0 | 2663.0 | 2007-06-05 | 2026-09-01 |  | agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w63_z2_vt.csv |
| 0.41 | 0.45 | 0.48 | 0.41 | 5.0/20.0 | 2684.0 | 2007-07-03 | 2026-09-04 |  | agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_LS.csv |
| 0.41 | 0.25 | 0.02 | 0.58 | 6.0/19.0 | 2734.0 | 2008-03-31 | 2026-09-07 |  | team/agents/RES_FXSTYLE/sleeves/fx_xsmom189_44h10_net.csv |
| 0.41 | 0.32 | 0.39 | 0.29 | 5.0/19.0 | 2659.0 | 2008-02-21 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w63_z15_zo1.csv |
| 0.40 | 0.33 | 0.48 | 0.24 | 7.0/19.0 | 2659.0 | 2008-02-08 | 2026-08-25 |  | team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w40_z15_zo1.csv |