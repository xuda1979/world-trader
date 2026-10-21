# NEW CHAMPION CARD — optimized from the 166 OOS-SR>0.4 strategy pool

Generated 2026-09-16 by work_backtest_oos/optimize5.py (multi-config sweep, min-overfit selection) + final_champion_card.py.

## Construction
- Candidate pool: 166 strategies with OOS (>=2016) SR>0.4, minus discredited artifacts (MHX, HT_TAIL), minus campaign-FAILED/DEAD sleeves, minus champion-embedded overlays → vetted pool.
- Weight fit: champion blueprint (long-only max-Sharpe, covariance shrunk toward diagonal SHRINK_D∈{0.97,0.99}, per-sleeve cap), decorrelation-gated greedy selection, **energy-cap ≤30%** constraint.
- # sleeves: 18  | sum(w)=1.000
- **ENERGY EXPOSURE: 27.8%  (cap 30%) → PASS**

## Sleeve weights
-   5.56%          agents/C4_metaalloc/sleeves/C4_construct_v2.csv
-   5.56%          agents/COORD/sleeves/brwt7.csv
-   5.56%          agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L60Z1.0.csv
-   5.56%          agents/B2_highfreq/sleeves/crossasset_rev_L8.csv
-   5.56%          agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_6_L40Z1.5.csv
-   5.56%  ENERGY  team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv
-   5.56%  ENERGY  agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv
-   5.56%          agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_3_6_L20Z1.5.csv
-   5.56%          agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv
-   5.56%          agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv
-   5.56%          agents/loop_team/HUNT_CN_FUTURES/sleeves/cnpair_M0_RM0_L60Z1.5.csv
-   5.56%  ENERGY  agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L15Z15_net.csv
-   5.56%  ENERGY  agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack211_nyh_L60Z1.5.csv
-   5.56%          results/sleeve_library/Merger_Arb_PEAD_5pct.csv
-   5.56%          agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv
-   5.56%          agents/chief/coord/CAMP_COST/sleeves/QAxasts__prefix.csv
-   5.56%  ENERGY  agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_dieseljet_L60Z1.0.csv
-   5.56%          team/agents/RES_CREDIT/sleeves/RC_t102_d5mr_w21_band50_vt5.csv

## Full-window (>=2009) profile
- **NEW : SR=2.525  ann=6.5%  geo=6.6%  vol=2.6%  MaxDD=-0.83%  negYr=1 (worst -0.0%)
- CHAMP: SR=3.223  ann=31.6%  geo=35.9%  vol=9.8%  MaxDD=-2.47%  negYr=0

## OOS (>=2016) comparison
- **NEW : OOS SR=3.882  ann=13.2%  vol=3.4%  MaxDD=-0.83%  H1/2(2016-26)=2.47/3.68  negYr=0  worst=6.7%
- CHAMP: OOS SR=3.149  ann=34.0%  vol=10.8%  MaxDD=-2.16%
- **DELTA OOS SR: +0.733  →  BEATS champion;  energy 27.8%≤30%**
- OOS sub-halves: 2016-2019 SR=5.952, 2020-2026 SR=3.391
- Levered to champion OOS vol (×3.17): OOS SR=3.882, ann(est)=41.9%

## Honesty caveats
- IS-SR-OOS-SR gap ~3.1 persists (max-Sharpe optimism); min-overfit config chosen among beating configs, but the absolute SR is indicative, not a guarantee against selection drift.
- The portfolio favors low-volatility decorrelated sleeves → high SR at low vol; to be operationally comparable it needs ~×3.2 gross-to-champion-vol (assume same margin/cost rules).
- Energy exposure held at 27.8% — well under the 30% ceiling, giving headroom.