# A4 round 4 — HIGH-RETURN directive (coordinator)
System now: SR_m 2.03 but ret 8.8%. Missing: return. Your mission: a sleeve with
SR>=0.8 AND ann>=12% AND |corr|<=0.3 to the champion (load champion legs via shared harness;
champion list in campaign/results/CHAMPION_FINAL.json).
Ideas (return-tilted):
1. Trend-following WITH reinvested carry on gold + silver + copper (FRED xau, slv, copper_monthly):
   126d trend + vol-target 15% (not 10) — higher vol budget, trend books scale.
2. SPX + VIX-regime momentum: long SPX when VIX<25 (lagged), 2x vol budget (20%), flat above.
   (Simple but high-return; must pass gates at 15-20% vol target.)
3. XGB-1y-style monthly momentum on FF factors (Mkt/SMB/HML/Mom factor timing, 252d lookback,
   monthly, 2x on best factor) — factor timing had SR 0.4 solo but at higher vol budget?
4. crypto BTC 63d trend vol-target 20% (data/binance/BTC.csv 2023+ too short for gates — SKIP unless padded honestly).
5. Rates steepener/flattener z-book on 2y10y (t10y2y FRED 2005+, DV01-neutral synth) — ret moderate, corr ~0.
Gates: standard (full SR>=0.8, halves>=0.4, <=2 neg yr, worst>-6%, scramble<0.05, plateau).
Vol-target UP to 15% is ALLOWED for your sleeve (document it). Append FINDINGS.md; last line ROUND r4 DONE.
