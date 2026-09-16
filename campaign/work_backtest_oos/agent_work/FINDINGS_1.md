# AGENT 1 — independent OOS audit/backtest
slice size: 35 | PASS_OOS>0.4: 15
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv (oos_sr=0.86) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/A6_reversal/sleeves/a6_r2_pair_residmom_msew.csv (oos_sr=1.05) reason=honest stream status=ok
- [REJECT] agents/CHAMP_HUNT_FUND/sleeves/PIT_quality_ls_monthly.csv (oos_sr=None) reason=not an honest daily-return stream status=short
- [PASS_OOS>0.4] agents/COORD/sleeves/brwt7.csv (oos_sr=3.21) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv (oos_sr=2.77) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv (oos_sr=1.12) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT3_Sprd_USCI_DBC_LS_21d.csv (oos_sr=-1.09) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w126_z1_vt.csv (oos_sr=0.53) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w21_lo_novt.csv (oos_sr=0.25) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w21_compress_novt.csv (oos_sr=-1.75) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w252_mom_novt.csv (oos_sr=-0.55) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k26_i_novt.csv (oos_sr=-0.25) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k26_i_novt.csv (oos_sr=-0.45) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_r3_meanrev_HYG_k20_z1.csv (oos_sr=-0.11) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CRYPTO2/sleeves/R2_CRYPTO_b_overlay_on_CHAMP.csv (oos_sr=3.12) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_TREND_mom63_LS.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOM_dates_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_126_LF_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_MACRO2/sleeves/macro_policy_realrate_ief.csv (oos_sr=-0.39) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_MAG_OVL_daily.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT2_mom10_k126_NEG.csv (oos_sr=-0.01) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_30_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_2_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_30_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_fly_N504_t10_NEG.csv (oos_sr=-1.09) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L20Z1.0.csv (oos_sr=1.85) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_gas_crack_nyh_L40Z1.0.csv (oos_sr=0.97) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv (oos_sr=1.11) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_HL16_SAFE_daily.csv (oos_sr=5.02) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w63_z20_zo1.csv (oos_sr=0.61) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w63_z20_zo1.csv (oos_sr=0.44) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/AP_gold.csv (oos_sr=0.91) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Credit_z120_1986.csv (oos_sr=-0.59) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/L_S_130_30.csv (oos_sr=0.77) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/StatArb_40pairs.csv (oos_sr=-0.2) reason=honest stream status=ok
AGENT 1 DONE