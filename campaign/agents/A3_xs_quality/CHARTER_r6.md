# A3 r6 — NEW-FAMILY directive (joint goal: SR_m>=2.0, ann>=20%, MaxDD<5%)
Fresh families only (vol-budget scaling closed):
1. **Daily seasonal momentum**: names' average same-weekday excess return (e.g., every Monday)
   over trailing 2y — long names with strong weekday profile, weekly rebalance, 6bps.
2. **Beta-rotation on the panel**: monthly long the bottom-beta-quintile EW (pure construction,
   no anomaly claim) gated by FF-mkt MA200 — different from your dualmom (no momentum term).
3. **Volume-shock reversal**: daily long the 10% biggest volume-shock losers (down >3% on >3x volume),
   hold 5d, vol-target 10%. Event book, corr should be low.
4. **Dispersion regime**: cross-sectional dispersion of panel returns (21d trailing) as a risk switch
   on QA_dualmom — high dispersion = carry momentum, low = flat. This RE-TIMES your sleeve; the
   retimed-sleeve may pass as new if corr to your old one <0.7 and SR improves >=0.1.
Gates: SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%, scramble<0.05 (circular shift), plateau, corr<0.35 to champion.
Append FINDINGS.md; last line ROUND r6 DONE.
