# AGENT 3 — independent OOS audit/backtest
slice size: 35 | PASS_OOS>0.4: 10
## per-candidate verdicts
- [PASS_OOS>0.4] agents/A1_trend_cta/sleeves/A1_mix_breadthCTA_SharpeW_LS13030.csv (oos_sr=0.99) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/B2_highfreq/sleeves/brwt_spread_rev15.csv (oos_sr=2.4) reason=honest stream status=ok
- [below_threshold] agents/COORD/sleeves/H21_fixed.csv (oos_sr=0.39) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv (oos_sr=1.25) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/chief/coord/CAMP_COST/sleeves/brwt10__R3COSTFIX.csv (oos_sr=2.76) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_CPERtrend_252d.csv (oos_sr=0.2) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_CarryBasis_k2_h3.csv (oos_sr=0.33) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_spreadmr_w21_z1_vt.csv (oos_sr=0.02) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CMDT2/sleeves/prop_trend_w21_ls_novt.csv (oos_sr=-0.01) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_cpois_w21_stress_novt.csv (oos_sr=-1.32) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_mortgap_w252_rv_novt.csv (oos_sr=-0.99) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_credit_k26_novt.csv (oos_sr=0.03) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CRED5_nfci_risk_k26_novt.csv (oos_sr=0.21) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_CREDIT2/sleeves/CREDIT2_r3_spread_HYG_LQD_k63.csv (oos_sr=-1.04) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R2_carry_nominal_EW.csv (oos_sr=0.27) reason=honest stream status=ok
- [below_threshold] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_Carry10y_6ccy.csv (oos_sr=0.26) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_CAL_TOM_k3k3_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_252_LF_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [PASS_OOS>0.4] agents/chief/coord/HUNT_SECTOR2/sleeves/A_rs_ratio.csv (oos_sr=0.67) reason=honest stream status=ok
- [REJECT] agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_NKY_f1_signal.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND10_10_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_COND5_5_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_POST5_30_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [REJECT] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT5_PRE5_5_long_positions.csv (oos_sr=None) reason=not an honest daily-return stream status=no_ret_col
- [below_threshold] agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_tipsrev_N252_t10_NEG.csv (oos_sr=-0.17) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L60Z2.0.csv (oos_sr=0.94) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_dieseljet_L60Z1.5.csv (oos_sr=1.04) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_FUNDAMENTAL/sleeves/HF_mom_cheap_daily.csv (oos_sr=0.77) reason=honest stream status=ok
- [PASS_OOS>0.4] agents/loop_team/HUNT_TAIL/sleeves/HT_TAIL_L16C_BAL_daily.csv (oos_sr=5.04) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_br_mom_w126_z20_zo1.csv (oos_sr=-0.6) reason=honest stream status=ok
- [below_threshold] team/agents/RES_BASIS/sleeves/RB_ho_cl_mom_w126_z20_zo1.csv (oos_sr=-0.53) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/CTA_CTA_10vol_21d.csv (oos_sr=-0.12) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/Credit_z250_1986.csv (oos_sr=-0.49) reason=honest stream status=ok
- [PASS_OOS>0.4] results/sleeve_library/L_S_Dollar_Neutral.csv (oos_sr=0.79) reason=honest stream status=ok
- [below_threshold] results/sleeve_library/StatArb_40pairs_z15.csv (oos_sr=-0.66) reason=honest stream status=ok
AGENT 3 DONE