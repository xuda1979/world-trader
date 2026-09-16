# AGENT 7 — independent OOS audit/backtest
slice size: 34 | PASS_OOS>0.4: 12
## per-candidate verdicts
- [REJECT] agents/A3_xs_quality/sleeves/QUAL_PIT_ls_monthly.csv (oos_sr=None) reason=not an honest daily-return stream status=suspect_ffilled
- [PASS_OOS>0.4] agents/C4_metaalloc/sleeves/C4_construct_v1.csv (oos_sr=5.4) reason=honest stream status=ok
- [below_threshold] agents/COORD/sleeves/bab.csv (oos_sr=-0.71) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_uncostB3.csv (oos_sr=5.56) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt5__R3COSTFIX.csv (oos_sr=2.99) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_SpreadWTIBrent_63d.csv (oos_sr=0.23) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_XSMom_12m_k3_h3.csv (oos_sr=-0.06) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w63_z1_vt.csv (oos_sr=0.42) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w252_ls_novt.csv (oos_sr=0.16) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w252_stress_novt.csv (oos_sr=-0.91) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w63_rv_novt.csv (oos_sr=-1.62) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k52_novt.csv (oos_sr=0.2) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k52_novt.csv (oos_sr=0.47) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_RV_baseVSalt_30.csv (oos_sr=-0.14) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R5_CARRY_EWtop4_12m.csv (oos_sr=-0.66) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_EMDM_LS_12m.csv (oos_sr=-0.77) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOY_dates_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_63_LF_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_never.csv (oos_sr=0.6) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_PROP_f1_signal.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_10_anti.csv (oos_sr=-0.07) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST3_10_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_10_anti_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT7_ECB_CURV_rev_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L15Z15_net.csv (oos_sr=1.03) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack211_nyh_L60Z1.5.csv (oos_sr=0.79) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CN_FUTURES/sleeves/cnpair_M0_RM0_L60Z1.5.csv (oos_sr=0.73) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv (oos_sr=1.87) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_LEV16_SAFE_daily.csv (oos_sr=5.02) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_br_mom_w63_z20_zo1.csv (oos_sr=-0.73) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_cl_mom_w63_z20_zo1.csv (oos_sr=-0.54) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_Futures_macro_21d.csv (oos_sr=0.28) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/FactorMom_1926.csv (oos_sr=0.21) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/Merger_Arb_PEAD_3pct.csv (oos_sr=0.51) reason=honest stream status=ok
AGENT 7 DONE