# COORD findings
- BAB (betting-against-beta, monthly, 252d beta): **FAIL** — full SR -0.51. Beta quintiles
  MONOTONICALLY INCREASE 13.7%->33.6%/yr on this panel: positive beta premium 2008-26
  (survivorship: current large caps that survived). Not saved. Lesson: classic
  defensive factors invert on this static panel — treat panel xs "quality/low-risk"
  priors with suspicion.
- B/M value (monthly, PIT Jul-1): **FAIL** — full SR -0.30. Same panel-bias lesson as BAB:
  static-characteristic xs factors INVERT on this survivorship-biased static panel.
  Campaign rule: xs sleeves must be relative + short-horizon (momentum/reversal/vol families)
  which are robust to panel bias; static characteristics (value, beta, low-vol) are dead here.
- Bond dual-trend (synth 10Y/30Y TR from FRED yields): **FAIL** — best full SR 0.44
  (252d), H2 0.27; H2-negative for most variants (2022 rate shock). Not saved.
- Lesson: H2 (2017-26) is hostile to rates books; equity-vol and credit books better.
- Contango SPX carry (A5 recipe repro): solo SR_m 0.70 but 2022 -20.8% -> fails gates;
  as blend component REDUCES core4 blend SR (1.66 -> 1.53). Not saved. Honest verdict:
  real signal, but long-equity-beta books don't add to this blend.

## GOAL100 coordinator honest log (2026-09-01)
- Spread sweep (19 pairs, exact brwt recipe): only brent/wti passes (corr 0.76 to brwt = same trade). natgas/wti 0.65, others <0.7 or negative. No new engine.
- WTI-Brent SPOT reversion: SR 2.58 but corr 0.764 to brwt — same trade, not additive. Saved for reference only.
- Crack spreads (HO-WTI, Jet-WTI, HO-Brent, Jet-HO): reversion real but MaxDD -14..-20%, SR <= 1.14; FAIL DD/worst-yr gates.
- Level z-reversion (xau, slv, copx, dxy, spx, EM-FX): all fail (SR <= 0.57). Dead family on daily cash data.
- 2s10s hold-until-exit / breakeven reversion / 2s10s30s curvature w/ exit: sign-flip artifacts; family weak. (C2's fly construction remains the only rates winner.)
- NFCI 4w -> SPX inv: SR 1.07 but isolated spike (lb13 0.48, lb26 0.50) — param-plateau FAIL. Not saved.
- KF OP/INV spread momentum: WITHOUT T+1 shift SR 2.3-2.8 (!); WITH proper shift(1): SR 0.14-1.68, H2<=0.38, negy 9-19. LOOKAHEAD ARTIFACT — the quick test's `sig*spread` uses day-t info in day-t position. Not saved. (Vol-target via expanding net std also would have been contaminated.) Lesson repeated: always shift(1) or use shift(-1) returns.
- Day-of-year/month calibrars (TOM, month-of-year, storage Thursday) on NG/WTI/Brent/SPX/XAU/SLV/COPX: all fail. Weekday effect remains natgas-only (Fri t=-4.2, Mon t=+4.7; calendar-scramble p=0.016 on the honest rebuild).
- RRP: FRED series unavailable (HTML error page); WALCL weekly since 2003 — thin. Skipped honestly.
- Pre-FOMC drift book (SPX, 119 meetings parsed from federalreserve.gov, 2008-2026): raw 2-day
  FOMC-window return 0.29%/meeting (~2.3%/yr ann-equivalent, t=2.48 vs non-FOMC t=1.17);
  book SR 0.67, -28% DD, 3 neg yrs — FAIL. The Lucca-Moench effect has regime-decayed post-2011.
- FOMC dates saved to tools/quant/data/newdata/fomc_dates.csv (2008-2027, some recent gaps noted).

## GOAL100-D round (champion improvement) — coordinator log 2026-09-01
- Canonical builder committed (champion_build.py, byte-identical --verify) + leakage-audit
  appendix + FINANCED variants (BALANCED financed: 48.9% @ -7.5%, T-bill+25bps on gross>1x).
- Pool ablations: dropping A5r2 duplicate raises ann +1.9pp but DD -8.0% (rejected,
  risk-adjusted worse); C5ngsum->ddt swap hurts (55.1% @ -7.4%); base 16-pool stays.
- Net liquidity (WALCL-WTREGEN 13-52w -> SPX, 5d pub lag + T+1): SR -0.05..-0.29, FAIL.
  The famous regime trade is dead on 2008-26 free data at 6bps.
- D-series launched: D1 credit/curve carry (low-turnover mandate), D2 weekly macro regimes,
  D3 FX factors weekly, D4 cash microstructure II, D5 construction meta (beat-BALANCED mandate).
