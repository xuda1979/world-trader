# AGENT 4 — independent OOS audit/backtest
slice size: 35 | PASS_OOS>0.4: 12
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A2_fx_carry/sleeves/A2_fx_carry_W11_accrual.csv (oos_sr=0.82) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/B2_highfreq/sleeves/crossasset_rev_L8.csv (oos_sr=0.96) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/MHX_f6.csv (oos_sr=6.18) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv (oos_sr=2.54) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt15__prefix.csv (oos_sr=2.39) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_CotGatedMom_9m_k2_thr0.2.csv (oos_sr=0.38) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_InflRegime_T10YIE_g2.csv (oos_sr=0.5) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w21_z2_vt.csv (oos_sr=-0.13) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w21_ls_vt.csv (oos_sr=0.01) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w21_stress_vt.csv (oos_sr=-1.32) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w252_rv_vt.csv (oos_sr=-1.05) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k26_vt.csv (oos_sr=0.01) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k26_vt.csv (oos_sr=0.2) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_r3_spread_JNK_IEF_k63.csv (oos_sr=-0.7) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R3_ddstop10_carry_EW.csv (oos_sr=0.13) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_Carry10y_6ccy_lag2m.csv (oos_sr=0.24) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOM_rank3.csv (oos_sr=-0.09) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_252_LS.csv (oos_sr=0.09) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/B_barbell.csv (oos_sr=0.62) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_NKY_f5_daily.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND3_10.csv (oos_sr=-0.7) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST10_10_long.csv (oos_sr=-0.27) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_5_long.csv (oos_sr=0.29) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_CURV_mom.csv (oos_sr=0.3) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_VOL2/sleeves/vol2_round2_scan.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_6_L40Z1.5.csv (oos_sr=1.06) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L30Z1.0.csv (oos_sr=2.13) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_FUNDAMENTAL/sleeves/HF_mom_cheap_liq_daily.csv (oos_sr=0.77) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_L16C_SAFE_daily.csv (oos_sr=5.02) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_br_mom_w40_z15_zo1.csv (oos_sr=-0.94) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_cl_mom_w40_z15_zo1.csv (oos_sr=-0.62) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_CTA_15vol_10d.csv (oos_sr=-0.21) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Credit_z250_2008.csv (oos_sr=-0.49) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/L_S_Market_Neutral.csv (oos_sr=0.84) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/StatArb_80pairs_z15.csv (oos_sr=-0.45) reason=honest stream status=ok
AGENT 4 DONE