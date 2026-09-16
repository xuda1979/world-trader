# AGENT 0 — independent OOS audit/backtest
slice size: 35 | PASS_OOS>0.4: 15
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv (oos_sr=0.96) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/A6_reversal/sleeves/a6_r2_pair_residmom_fm1926.csv (oos_sr=0.85) reason=honest stream status=ok
- [REJECT] agents/CHAMP_HUNT_FUND/sleeves/PIT_quality_ls_daily.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [PASS_OOS>0.4] agents/COORD/sleeves/brwt5_2000.csv (oos_sr=3.19) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/QAxasts__prefix.csv (oos_sr=1.18) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt7__prefix.csv (oos_sr=3.21) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT3_Sprd_USCI_DBC_LO_126d.csv (oos_sr=0.65) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/prop_seas_12-02_vt.csv (oos_sr=0.42) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w126_ls_vt.csv (oos_sr=0.03) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w63_ls_vt.csv (oos_sr=-0.31) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w63_stress_vt.csv (oos_sr=-0.87) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k13_vt.csv (oos_sr=0.21) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k13_vt.csv (oos_sr=-0.04) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_r3_carry_HYG_IEF_k252.csv (oos_sr=-0.78) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_am_overlay_on_CHAMP.csv (oos_sr=3.2) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_TREND_mom63_LF.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOM_dates.csv (oos_sr=-0.03) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_126_LF.csv (oos_sr=0.3) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_MACRO2/sleeves/macro_liquidity_qqq.csv (oos_sr=0.36) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_DIR_EW6_daily.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT2_mom1030_k126_NEG.csv (oos_sr=-0.08) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_30.csv (oos_sr=-0.35) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_2_long.csv (oos_sr=-0.11) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_30_long.csv (oos_sr=-0.53) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_curve2s10s_k21_NEG.csv (oos_sr=-1.62) reason=honest stream status=ok
- [below_threshold] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_3_6_L60Z2.0.csv (oos_sr=0.29) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_gas_crack_nyh_L30Z2.0.csv (oos_sr=0.98) reason=honest stream status=ok
- [REJECT] agents/loop_team/HUNT_CRYPTO_SAT/sleeves/CRYPTO_TSMOM21LO_weights.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_HL16_BAL_daily.csv (oos_sr=5.04) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w63_z15_zo1.csv (oos_sr=0.76) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w63_z15_zo1.csv (oos_sr=0.41) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_FXSTYLE/sleeves/fx_xsmom189_44h10_net.csv (oos_sr=0.41) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Credit_spread_z_reversion.csv (oos_sr=-1.07) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/L_S_120_20.csv (oos_sr=0.77) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/Risk_Parity_Bridgewater.csv (oos_sr=0.73) reason=honest stream status=ok
AGENT 0 DONE