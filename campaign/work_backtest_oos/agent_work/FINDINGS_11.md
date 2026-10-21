# AGENT 11 — independent OOS audit/backtest
slice size: 34 | PASS_OOS>0.4: 15
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv (oos_sr=1.13) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv (oos_sr=1.5) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/brwt5.csv (oos_sr=3.21) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv (oos_sr=0.95) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv (oos_sr=3.05) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT3_Sprd_DBE_DBP_LS_63d.csv (oos_sr=0.58) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/prop_seas_12-02_novt.csv (oos_sr=0.43) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w126_ls_novt.csv (oos_sr=0.03) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w63_ls_novt.csv (oos_sr=-0.33) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w63_stress_novt.csv (oos_sr=-0.87) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k13_novt.csv (oos_sr=0.21) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k13_novt.csv (oos_sr=-0.02) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_lqdltt_k126.csv (oos_sr=-0.38) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_a_overlay_on_CHAMP.csv (oos_sr=3.21) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_TREND_mom252_LS.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_SELLMAY_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOY_rank5_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_MACRO2/sleeves/macro_credit_composite_qqq.csv (oos_sr=0.19) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/D_xlu_ief.csv (oos_sr=0.7) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT2_lvl10_k126_reg_NEG.csv (oos_sr=-0.21) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_2_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_10_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_2_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_SLOPE_rev_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_3_6_L20Z1.5.csv (oos_sr=0.99) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_gas_crack_nyh_L30Z1.5.csv (oos_sr=0.99) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CRYPTO_SAT/sleeves/CRYPTO_TSMOM21LO_net.csv (oos_sr=1.11) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_HL16_AGGR_daily.csv (oos_sr=5.04) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w40_z20_zo1.csv (oos_sr=0.67) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w40_z20_zo1.csv (oos_sr=0.31) reason=honest stream status=ok
- [below_threshold] team/agents/RES_FXSTYLE/sleeves/CFX4_long1999_dtf2163_net.csv (oos_sr=-0.94) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_Futures_tsmom_21d.csv (oos_sr=0.24) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Global_Macro.csv (oos_sr=0.2) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/Multi_Strategy_SharpeW.csv (oos_sr=0.81) reason=honest stream status=ok
AGENT 11 DONE