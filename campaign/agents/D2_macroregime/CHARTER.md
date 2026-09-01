# D2_macroregime — weekly labor/macro momentum books (NEW domain, never tested)

DATA on disk (tools/quant/data/newdata/ + data_fred):
- ICSA.csv: initial claims weekly 1967+ (SA). CLAIMSx: continuing claims if fetchable (try).
- PAYEMS.csv (nonfarm payrolls monthly), CFNAIMA3.csv (Chicago Fed activity, monthly),
  W875RX1.csv (real income), M2SL.csv (M2 weekly), BOGMBASE.csv (st base weekly),
  TGA.csv (treasury general account daily), WALCL.csv (Fed assets weekly), RRPFONTSM (broken).
- NFCI/STLFSI4 weekly (known: NFCI 4w spike fails plateau — avoid repeating).

IDEAS (weekly-decision books, T+1 on the weekly cycle, 6bps on switches, vt10 trailing):
1. Claims-momentum regime: 4w-average claims YoY change rising = labor deteriorating ->
   defensive book (long 2y-synth via DGS2 TR approx, or inverse-SPX? pick the tradeable
   side with on-disk instruments; a LONG-ONLY 2y book gated by claims is clean).
2. Net liquidity = WALCL - TGA - (RRP unavailable -> use BOGMBASE-TGA as proxy):
   13w change z -> long/short SPX (spx series on disk). This is the famous net-liquidity
   regime trade — test honestly with proper weekly lag (data published 4d later: shift).
3. CFNAI 3m-avg momentum -> credit-on/off gate around A1credit-like book (only if corr
   to A1credit < 0.5).
4. M2 growth regime -> gold (xau) long/flat (monetary-inflation thesis), monthly decision.
5. Composite: best 2 of the above EW (if each passes solo gates at SR>=0.8 half-gates).

CRITICAL: all series are WEEKLY/MONTHLY — enforce publication lag: signal known 4 calendar
days after period end (weekly) / mid-month after (monthly). Document the lag you assume.
Gates as in GOAL100_AGENT_BRIEF.md. Log in FINDINGS.md. Last line: ROUND 1 DONE
