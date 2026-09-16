# AGENT 8 — independent OOS audit/backtest
slice size: 34 | PASS_OOS>0.4: 16
## per-candidate verdicts
- [REJECT] agents/A3_xs_quality/sleeves/QUAL_ls_quality_PITstyle_monthly.csv (oos_sr=None) reason=not an honest daily-return stream status=short
- [PASS_OOS>0.4] agents/C4_metaalloc/sleeves/C4_construct_v2.csv (oos_sr=5.81) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/brent_wti_spread.csv (oos_sr=2.92) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv (oos_sr=1.17) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv (oos_sr=3.02) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_UNGseasonal_volscaled.csv (oos_sr=-0.39) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_XSMom_CORE9MOO_9m_k2_familybest.csv (oos_sr=0.44) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w63_z2_vt.csv (oos_sr=0.42) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w252_ls_vt.csv (oos_sr=0.17) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w252_stress_vt.csv (oos_sr=-0.91) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w63_rv_vt.csv (oos_sr=-1.64) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k52_vt.csv (oos_sr=0.18) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k52_vt.csv (oos_sr=0.48) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_Rev3_liq_k3.csv (oos_sr=-0.21) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_TREND_mom126_LF.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_EMDM_LongOnly_12m.csv (oos_sr=0.22) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOY_k5.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [PASS_OOS>0.4] agents/chief/coord/HUNT_MACRO2/sleeves/champ_overlay_T10Y2Yz63m2_x06.csv (oos_sr=3.2) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_60_40_daily.csv (oos_sr=0.64) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_PROP_f5_daily.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_10_anti_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_10_anti.csv (oos_sr=-0.5) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_10_long.csv (oos_sr=-0.28) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_SLOPE_mom.csv (oos_sr=0.26) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv (oos_sr=1.08) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L15Z1.5.csv (oos_sr=0.88) reason=honest stream status=ok
- [below_threshold] agents/loop_team/HUNT_CROSSASSET2/sleeves/SEC3_sector_trio_zrev_daily.csv (oos_sr=0.15) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_HF_STATARB/sleeves/al_dollar_neutral_net.csv (oos_sr=0.61) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_br_meanrev_w126_z15_zo1.csv (oos_sr=0.73) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_ho_cl_meanrev_w126_z15_zo1.csv (oos_sr=0.56) reason=honest stream status=ok
- [PASS_OOS>0.4] team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv (oos_sr=1.04) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_Futures_multi_10d.csv (oos_sr=0.15) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/FactorMom_1963.csv (oos_sr=0.36) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/Merger_Arb_PEAD_5pct.csv (oos_sr=0.51) reason=honest stream status=ok
AGENT 8 DONE