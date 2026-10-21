# A5 r6 — NEW-FAMILY directive (joint goal SR_m>=2.0, ann>=20%, MaxDD<5%)
1. **Term-premium timing**: long 10y synth TR (dur 7.5) only when t10y2y slope > 0 AND us10y < its
   252d mean (yield attractive vs own history), monthly — carry+value on rates, 2000+ window.
2. **VIX-level term premium**: your contango signal but on the VIX FRED series alone (2000+):
   vix vs its 252d mean as slow gate on SPX (independent computation from vix3m version — decorrelation check needed).
3. **Overnight premium in SPX**: SPX open-to-close vs close-to-open split using FRED spx (2016+ only, short —
   use only if you can extend via tools/quant/data/polygon/SPY.csv 2024+ or twelvedata SPY if present;
   otherwise SKIP and log).
4. **Credit carry**: BAA-Aaa spread slope carry (long credit when spread wide vs 252d, short when tight,
   DV01-neutral, funded honestly) — your A1 found 0.53; push with better entry bands.
Gates: SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%, scramble<0.05, plateau, corr<0.35.
Append FINDINGS.md; last line ROUND r6 DONE.
