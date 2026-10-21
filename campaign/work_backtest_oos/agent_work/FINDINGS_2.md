# AGENT 2 — independent OOS audit/backtest
slice size: 35 | PASS_OOS>0.4: 16
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv (oos_sr=1.24) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv (oos_sr=1.74) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/C2_steep_carry.csv (oos_sr=1.63) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/brwt_ens.csv (oos_sr=3.21) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__prefix.csv (oos_sr=2.92) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/dualmom__prefix.csv (oos_sr=0.82) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_CarryBasis_k1_h3_familybest.csv (oos_sr=0.43) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w126_z2_vt.csv (oos_sr=0.15) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w21_lo_vt.csv (oos_sr=0.27) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w21_compress_vt.csv (oos_sr=-1.74) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w252_mom_vt.csv (oos_sr=-0.5) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k26_i_vt.csv (oos_sr=-0.23) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k26_i_vt.csv (oos_sr=-0.44) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_r3_meanrev_JNK_k20_z1.csv (oos_sr=-0.14) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_bm_overlay_on_CHAMP.csv (oos_sr=3.58) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R7_overnight_carry_GBP_EUR.csv (oos_sr=0.16) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOM_k3k3.csv (oos_sr=-0.09) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_252_LF.csv (oos_sr=0.5) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv (oos_sr=0.68) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_NKY_f1_daily.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND10_10.csv (oos_sr=-0.7) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_5.csv (oos_sr=-1.42) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_30_long.csv (oos_sr=0.3) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_5_long.csv (oos_sr=-0.57) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv (oos_sr=2.66) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L40Z1.5.csv (oos_sr=1.36) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_dieseljet_L60Z1.0.csv (oos_sr=0.86) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_raw_daily.csv (oos_sr=1.01) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_L16C_AGGR_daily.csv (oos_sr=5.04) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_br_mom_w126_z15_zo1.csv (oos_sr=-0.88) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_cl_mom_w126_z15_zo1.csv (oos_sr=-0.66) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_15vol.csv (oos_sr=-0.18) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Credit_z120_2008.csv (oos_sr=-0.59) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/L_S_130_30_volmanaged.csv (oos_sr=0.79) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/StatArb_40pairs_z10.csv (oos_sr=-0.51) reason=honest stream status=ok
AGENT 2 DONE