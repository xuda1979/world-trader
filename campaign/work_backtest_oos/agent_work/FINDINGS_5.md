# AGENT 5 — independent OOS audit/backtest
slice size: 35 | PASS_OOS>0.4: 14
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv (oos_sr=0.81) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/B5_construct/sleeves/B5_CONSTRUCT_vt75_dd4_13.csv (oos_sr=5.13) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/COORD/sleeves/MHX_multihorizon_xgb.csv (oos_sr=6.02) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv (oos_sr=1.45) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt5_2000__costfix.csv (oos_sr=2.98) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_CotMom_9m_k2_UNGATED_ablation.csv (oos_sr=0.47) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_LS.csv (oos_sr=0.41) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w252_z1_vt.csv (oos_sr=-0.02) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w252_lo_novt.csv (oos_sr=0.36) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w252_compress_novt.csv (oos_sr=-0.67) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w63_mom_novt.csv (oos_sr=-0.95) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k52_i_novt.csv (oos_sr=-0.43) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k52_i_novt.csv (oos_sr=-0.7) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_BTCMA50_gate_on_CHAMP.csv (oos_sr=3.57) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_CARRY_EWtop2_12m.csv (oos_sr=-0.35) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_CountryMom_12-1m_k3.csv (oos_sr=-0.38) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOM_rank3_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_252_LS_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_daily.csv (oos_sr=0.61) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_NKY_f5_signal.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND3_10_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST10_10_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_5_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_CURV_mom_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/ITER18_STORAGE/sleeves/NG_storage_surprise_daily.csv (oos_sr=0.07) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_6_L60Z2.0.csv (oos_sr=0.79) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L40Z1.0.csv (oos_sr=2.18) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_poolvt_daily.csv (oos_sr=0.59) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_LEV16_AGGR_daily.csv (oos_sr=5.04) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_br_mom_w40_z20_zo1.csv (oos_sr=-0.85) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_cl_mom_w40_z20_zo1.csv (oos_sr=-0.44) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_CTA_15vol_21d.csv (oos_sr=-0.17) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/EMN.csv (oos_sr=-0.31) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/Merger_Arb_PEAD.csv (oos_sr=0.57) reason=honest stream status=ok
- [REJECT] results/sleeve_library/XGB1y_deploy.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
AGENT 5 DONE