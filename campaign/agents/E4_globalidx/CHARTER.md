# E4_globalidx — global index books (Nikkei downloaded; more if fetchable)

DATA: tools/quant/data/newdata/NIKKEI225.csv (1949+!! full daily history, FRED).
Try also fetching from FRED: DJIA? (DJIA exists? try fredgraph.csv?id=DJIA), SP500 (10y limit),
NASDAQCOM (1971+), DJCA (2016+ only), DCOILWTICO etc. NOTE FRED free-range works for some
indices: NIKKEI225, NASDAQCOM, DJIA all likely full-history. Save under tools/quant/data/newdata/
with README updates.

IDEAS:
1. Nikkei TSMOM (21/63/126/252d, weekly decisions) — a NEW market for the pool; corr to US
   sleeves should be low. Trade the index directly (ETF proxy cost 6bps).
2. Nikkei-SPX lead-lag: Nikkei close leads US open (time zones) — overnight-signal book on SPX.
3. NASDAQCOM vs DJIA relative momentum (growth-vs-value macro proxy) 63d.
4. Cross-index TSMOM basket EW: [NIKKEI, NASDAQ, DJIA, SPX] vol-normalized weekly.
5. Nikkei level z-reversion (check both signs honestly; Japan-specific dynamics).

Gates per GOAL100_AGENT_BRIEF.md; document exactly which FRED ids worked. Log in FINDINGS.md.
Last line: ROUND 1 DONE
