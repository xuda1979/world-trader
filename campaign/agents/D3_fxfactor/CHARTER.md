# D3_fxfactor — FX factor books with the DEX panel (revisit with correct units)

Prior failures: FX momentum/reversal on 8 pairs (A2), EM-FX on DEX (C5) — all daily.
UNTESTED: weekly/monthly FX FACTOR structure on the full DEX panel.

DATA: tools/quant/data/newdata/DEX*.csv (INR,BRL,ZAR,MXN,KRW,SGD,SEK,NOK,JPY,CHF,GBP,EUR,CAD,AL)
+ tools/quant/data/fx/*.csv (8 pairs 2007+ daily) + DTWEXBGS.csv (broad dollar 2006+).
All DEX = USD per local currency (higher = local weaker).

IDEAS (weekly decisions, T+1, 6bps on switches, vt10 trailing):
1. FX CARRY PROXY: interest-rate differential unavailable per-EM — use 10y diffs:
   (us10y - jp10y) momentum -> long USDJPY proxy (jpy.csv)... test us-jp, us-ez rate-diff
   momentum books on the FX series, weekly, 26d/52d.
2. EM basket vs DM basket RELATIVE trend (63d): long EM basket / short DM basket when
   EM outperforms (carry-seeking regime) — weekly.
3. Dollar-smile asymmetry: DTWEXBGS vs VIX interaction — long EM basket only when VIX<20,
   short when VIX>30 (weekly). Gated, so turnover low.
4. Mean-reversion of USD/EM at monthly horizon after extreme monthly moves (>2sigma z).
5. Cross-sectional: rank EM currencies by 63d momentum, long top2/short bottom2 weekly.

Document publication lag for FRED noon rates (next-day). Gates per GOAL100_AGENT_BRIEF.md.
Log in FINDINGS.md. Last line: ROUND 1 DONE
