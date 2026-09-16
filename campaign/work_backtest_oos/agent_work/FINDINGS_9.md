# AGENT 9 — independent OOS audit/backtest
slice size: 34 | PASS_OOS>0.4: 14
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv (oos_sr=1.19) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv (oos_sr=2.55) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/brwt10_2000.csv (oos_sr=2.92) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv (oos_sr=1.74) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt5__prefix.csv (oos_sr=3.21) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_UNGshortdecay_volscaled.csv (oos_sr=-0.02) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_seas_11-03_novt.csv (oos_sr=0.09) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w126_lo_novt.csv (oos_sr=0.27) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w63_lo_novt.csv (oos_sr=0.03) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w63_compress_novt.csv (oos_sr=-1.33) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k13_i_novt.csv (oos_sr=-0.49) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k13_i_novt.csv (oos_sr=-0.27) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_be_tlttip_k63.csv (oos_sr=-0.42) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_10-30_EW12_audit.csv (oos_sr=0.91) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_TREND_mom126_LS.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [PASS_OOS>0.4] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R2_RS252_LS.csv (oos_sr=0.51) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOY_k5_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/chief/coord/HUNT_MACRO2/sleeves/champ_overlay_VIXsus21_OR_T10Y2Yz63_x06.csv (oos_sr=3.18) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_invvol.csv (oos_sr=0.65) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_PROP_f5_signal.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_10_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_10_anti_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_10_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_SLOPE_mom_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_carry_raw_daily.csv (oos_sr=1.92) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L60Z1.0.csv (oos_sr=0.8) reason=honest stream status=ok
- [REJECT] agents/loop_team/HUNT_CRYPTO_SAT/sleeves/CRYPTO_TSMOM21LO_ledger.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/loop_team/HUNT_SECTOR_FULL/sleeves/SECTOR_FULL_trio_lb21_cap10_honest_daily.csv (oos_sr=-0.42) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w126_z20_zo1.csv (oos_sr=0.52) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w126_z20_zo1.csv (oos_sr=0.47) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ng_storage_z.csv (oos_sr=0.44) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_Futures_multi_21d.csv (oos_sr=0.34) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/FactorMom_2008.csv (oos_sr=0.04) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Merger_Arb_Sector_Pair.csv (oos_sr=-0.2) reason=honest stream status=ok
AGENT 9 DONE