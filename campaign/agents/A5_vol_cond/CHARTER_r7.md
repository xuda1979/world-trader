# A5 r7 — NEW FREE VIX + rates data (data_fred_new/)
New: VIXCLS (1990+ vs prior 2000+), DGS10 (1990+), T10Y2Y (1990+), TEDRATE (1990-2022), DAAA/DBAA.
Missions (SR>=1.0, corr<0.25):
1. **VIX term-structure 1990-style**: VIXCLS 21d z-score vs its 252d (proxies contango w/o vix3m);
   long SPX when calm, flat when stressed, T+1, 10% vol-tgt. Your contango sleeve was 2009+ (vix3m);
   this uses 1990+ and a different construction -> longer OOS, lower corr.
2. **Rate-shock defensive tilts** using DGS10 1990+ (long rates defensive when 10y rising).
3. **Credit spread 1990+**: DAAA-DBAA wide -> long IG, tight -> flat (value book, 10y history better than 2008).
4. **Vol-terror regime**: TEDRATE high + VIX high -> defensive (cash), else risky - event switch.
All gates; save sleeves; APPEND FINDINGS.md; last line ROUND r7 DONE.
