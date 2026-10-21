# A6 r7 — NEW FREE DATA engines (data_fred_new/ + existing)
Focus: build de-correlated high-SR engines. You have the XGB 21d corpus (h21 books) proving ML L/S
works. Missions (SR>=1.0, corr<0.25 to champion):
1. **Bond-momentum (rate-trend)**: DGS10/DGS2 - synth total return (dur 7.5 for 10y), 3/6/12m trend,
   monthly, vol-target 12%. Rates trend is de-correlated from equity L/S (prior bond trend failed on
   2013-2022 whipsaw; now with 1990+ and better carry handle, retest honestly).
2. **Term-structure carry**: T10Y2Y steep/flat carry book, 1990+, DV01-neutral, funded honestly.
3. **Cross-sectional commodity momentum**: momentum ranking across WTI/Brent/gold/copper(XAU xau.csv)
   /natgas - long top 2 short bottom 2, 63d, weekly, vol-tgt. Commodity xs momentum is a classic
   de-correlated engine.
4. **Equity-index residual momentum on extended data**: reuse your resid-mom engine but add the new
   longer FRED VIX/dollar as regime filter.
All gates (seeded scramble, plateau, halves, yearly, corr<0.25). APPEND FINDINGS.md; last line ROUND r7 DONE.
