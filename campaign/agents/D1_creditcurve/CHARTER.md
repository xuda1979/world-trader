# D1_creditcurve — credit term-structure + curve-carry (champion improvement round)

Current champion: 55.5% ann @ -6.9% DD (see campaign/GOAL100_CHAMPION.md). Your job: find
ONE more decorrelated sleeve to push it up. Round-2 rates-fly lesson: edges die at 6bps on
daily turnover — design for LOW turnover (weekly/monthly decisions, holds of >=5 days).

DATA on disk:
- tools/quant/hedge_fund_strats/data_fred_new/: BAMLC0A0CM (IG OAS), BAMLH0A0HYM2 (HY OAS,
  2023+ only — too short), DAAA (A yield 90s+), DBAA (BAA 90s+), DTB3, DFF, DPRIME, DGS*.
  Note: data_fred BAMLC0A0CM.csv (newdata) starts 2023 — if the long IG history is absent,
  use BAA-AAA spread (aaa.csv,baa.csv in data_fred, 1990+) as the IG-credit proxy — LEGAL
  and 35y of history.
- Full US curve: data_fred/DGS{1MO,3MO,6MO,1,2,3,5,7,10,20,30}.csv.

IDEAS (low-turnover designs ONLY, document turnover/day for each):
1. Credit quality-timing: BAA-AAA spread z-score (252d, weekly decision) -> long credit
   (A1credit-style but SPREAD-based not yield-momentum) via BAA-synth; flat otherwise.
   Check corr to A1credit (campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv)
   — must be < 0.5 to it AND < 0.15 to champion blend (COORD_FINAL_daily.csv).
2. 5s30s + 2s10s carry basket: C2's always-on steepener carry (SR 1.33, corr -0.05, in
   campaign/scripts/C2_r3_final.py) FAILED sleeve gates on yearly DD (2011/2014 -15%).
   Test: steepener carry with 126d DD-throttle (cut 50% at -3%) — does throttle fix the
   yearly gate? turnover 0 => costs trivial.
3. Curve-belly carry: long 5y vs DN wings with MONTHLY rebalance (C2 flyC weekly failed;
   monthly kills the reversion but keeps convexity carry? test honestly).
4. IG-vs-rates divergence: (BAA-synth TR) vs (10y-synth TR) spread momentum, 63d, weekly.
5. Real-rate momentum: DFII10 (2003+) 126d trend via TIPS-synth TR — short window, disclose.

All gates in campaign/GOAL100_AGENT_BRIEF.md (SR>=1.0 etc). Log in FINDINGS.md. Last line: ROUND 1 DONE
