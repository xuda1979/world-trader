# AGENT 6 — independent OOS audit/backtest
slice size: 35 | PASS_OOS>0.4: 14
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv (oos_sr=1.15) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/B5_construct/sleeves/B5_vt8_dd3_ew9.csv (oos_sr=3.8) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/WTI-Brent_rev.csv (oos_sr=2.25) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_costedB3.csv (oos_sr=5.27) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt5_2000__prefix.csv (oos_sr=3.19) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_RatioCPERGLD_252d.csv (oos_sr=-0.02) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_h2_LS.csv (oos_sr=0.67) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w252_z2_vt.csv (oos_sr=-0.24) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w252_lo_vt.csv (oos_sr=0.38) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w252_compress_vt.csv (oos_sr=-0.65) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w63_mom_vt.csv (oos_sr=-0.92) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k52_i_vt.csv (oos_sr=-0.41) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k52_i_vt.csv (oos_sr=-0.7) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_RV_BTCETH_ratio30.csv (oos_sr=0.13) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_CARRY_EWtop3_12m.csv (oos_sr=-0.55) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_CountryMom_12m_k3.csv (oos_sr=-0.45) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOY_dates.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_63_LF.csv (oos_sr=0.36) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_monthly.csv (oos_sr=0.61) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_PROP_f1_daily.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_10.csv (oos_sr=-0.7) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST3_10_long.csv (oos_sr=-0.27) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_10_anti.csv (oos_sr=-0.41) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_CURV_rev.csv (oos_sr=-0.33) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_BASIS2/sleeves/CRACK_ho_br_L21Z2_vt10.csv (oos_sr=0.7) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack211_nyh_L15Z1.5.csv (oos_sr=0.95) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L60Z1.0.csv (oos_sr=2.21) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv (oos_sr=0.59) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_LEV16_BAL_daily.csv (oos_sr=5.04) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_br_mom_w63_z15_zo1.csv (oos_sr=-0.97) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_cl_mom_w63_z15_zo1.csv (oos_sr=-0.56) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_Futures_15vol.csv (oos_sr=0.36) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/FI_Arb_curve.csv (oos_sr=-3.26) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/Merger_Arb_PEAD_2pct.csv (oos_sr=0.59) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/ls_n10r14_2018.csv (oos_sr=0.92) reason=honest stream status=ok
AGENT 6 DONE