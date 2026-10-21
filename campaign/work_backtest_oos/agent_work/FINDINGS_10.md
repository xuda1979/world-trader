# AGENT 10 — independent OOS audit/backtest
slice size: 34 | PASS_OOS>0.4: 13
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv (oos_sr=1.19) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/C5_newdata/sleeves/C5_ng_summer_weekday_ddt.csv (oos_sr=2.53) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/brwt21.csv (oos_sr=2.45) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv (oos_sr=2.28) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt7__R3COSTFIX.csv (oos_sr=3.03) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT3_Sprd_DBE_DBP_LO_63d.csv (oos_sr=0.68) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_seas_11-03_vt.csv (oos_sr=0.07) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w126_lo_vt.csv (oos_sr=0.3) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w63_lo_vt.csv (oos_sr=0.05) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w63_compress_vt.csv (oos_sr=-1.32) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k13_i_vt.csv (oos_sr=-0.5) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k13_i_vt.csv (oos_sr=-0.25) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_curve2s10s_k21.csv (oos_sr=-0.36) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_20-60_EW12.csv (oos_sr=0.64) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_TREND_mom252_LF.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_SELLMAY.csv (oos_sr=0.39) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOY_rank5.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [below_threshold] agents/chief/coord/HUNT_MACRO2/sleeves/macro_activity_nowcast_dbc.csv (oos_sr=0.16) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_SECTOR2/sleeves/C_xle_crud.csv (oos_sr=0.02) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT2_kink_eq_k126_NEG.csv (oos_sr=-0.36) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_2.csv (oos_sr=-1.17) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_10_long.csv (oos_sr=-0.27) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_2_long.csv (oos_sr=-0.39) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_SLOPE_rev.csv (oos_sr=-0.29) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv (oos_sr=1.91) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L60Z1.5.csv (oos_sr=1.07) reason=honest stream status=ok
- [REJECT] agents/loop_team/HUNT_CRYPTO_SAT/sleeves/CRYPTO_TSMOM21LO_ledger_full.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/loop_team/HUNT_SECTOR_FULL/sleeves/SECTOR_FULL_trio_lb21_cap10_ledger.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w40_z15_zo1.csv (oos_sr=0.68) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w40_z15_zo1.csv (oos_sr=0.4) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_CREDIT/sleeves/RC_t102_d5mr_w21_band50_vt5.csv (oos_sr=1.22) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_Futures_tsmom_10d.csv (oos_sr=0.27) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Factor_Momentum_FF.csv (oos_sr=0.02) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/Multi_Strategy_EW.csv (oos_sr=0.68) reason=honest stream status=ok
AGENT 10 DONE