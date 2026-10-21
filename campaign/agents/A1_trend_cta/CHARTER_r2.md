# A1 round 2 — portfolio sleeves + alternative trend targets (your r1 spent on FRED single-asset trend)
Missions:
1. BREADTH CTA: the 10+ FRED macro series (xau, wti, brent, copper_monthly, natgas, dxy, spx, us10y synth TR
   via duration 7.5, us30y synth via dur 15, slv) — long each if 252d trend>0 (63d confirm), vol-target each 10%
   (expanding), average; costs 6bps on switches. This diversifies the 2022 rate-shock problem single-asset trend had.
2. Sector-momentum on the 298 panel: group by GICS-lite (build sectors from correlation clustering or by
   fundamentals revenue prefix), 6m sector momentum, long top 3 sectors (ETF-like book), monthly.
3. Portfolio sleeves allowed: if a mix of your trend sleeve + any 2022-positive library sleeve passes all gates,
   save as mix (document members in .meta).
Append FINDINGS.md; last line ROUND r2 DONE.
