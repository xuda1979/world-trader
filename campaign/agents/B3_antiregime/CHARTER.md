# B3_antiregime — MISSION: Profitable during the exact regimes that cause the drawdowns

## OVERRIDING GOAL
20y, SR>=2, ann>=50%, MaxDD<=8%, 6bps/side, free data, no leverage, OOS. The binding
constraint is MaxDD<=8% at 50% return. The system's worst drawdowns cluster in specific
stress regimes (2008, 2011, 2015, 2018Q4, 2020COVID, and especially the 2021-22 rate-shock
sustained bleed). Your mission: build engines that EARN in precisely those regimes,
decorrelating the tail and shrinking blend MaxDD.

## Data (free, on disk)
- Equities: tools/quant/data/twelve_big + twelve_extend (loaders in campaign/harness/data.py).
- FRED 1990+ macro: tools/quant/hedge_fund_strats/data_fred_new (VIXCLS, DGS10, DGS2, T10Y2Y,
  DAAA, DBAA, TEDRATE, CPFF, T5Y...), plus data_fred (vix, dxy, us10y, us2y, t10y2y, hy_oas,
  xau, wti, brent, spx, tbill3m, aaa, baa, copper_monthly, natgas, slv, dow).
- FX: tools/quant/data/fx (8 pairs). FF factors+mom 1926+.

## Ideas (rate-shock / crisis profiting)
1. **Rate-shock profiting book**: long/short on DGS10/DGS2 direction, carry-aware. Prior
   A5/A6 work: bond trend timings are dead post-2000 (secular bull ended); but a NEUTRAL
   convex instrument (e.g., DV01-hedged spread carry, or straddle-like on yield direction)
   may still work. Don't repeat A5's dead bond-timing: be creative.
2. **Credit-dispersion / HY-beat-pain book**: profit when credit widens (short HY OAS /
   long IG), using DAAA-DBAA, HY OAS, CPFF (commercial paper, 2008 stress proxy).
3. **Inflation-surge profiter**: commodity/BREAKEVEN books that pay when inflation surprises
   (2021-22 driver). FRED has CPIAUCSL (CPI), and commodity futures (wti, brent, copper,
   natgas). A short-bond/long-commodity inflation-beta sleeve.
4. **Flight-to-quality carry**: long gold + treasury when VIX/credit blows out, short when
   calm; tight spread-visualization. T+1 honest.
5. **Equity-factor crisis profiter**: low-beta/short-beta families NATURALLY earn in equity
   crashes. CAUTION: COORD found BAB/low-vol INVERT on this survivorship static panel —
   test with suspicion node: verify halves and scramble on the CRISIS sub-segments (2008,
   2011, 2020, 2022) specifically.

## HONESTY CONTRACT
T+1. 6bps/side. Gates: FULL SR>=0.6, halves>=0.3, <=2 negYr each>-5%, scramble 200x,
trailing vt10, plateau, economic rationale. shift(1) ALL macro/publishing signals
(publication-lag: EIA/credit indices print next day). Same-day conditioning = reject.
CRITICAL test for you: does your engine EARN in 2022 (the -12% blend drawdown)? If it is
flat in 2022 it adds little. Report each idea's stress-year P&L (2008, 2011, 2015, 2018,
2020, 2022) in FINDINGS.md.

## DELIVERABLE
Sleeves that pass gates AND earn in the stress regimes (esp. 2022), corr<0.2 to library.
A sleeve that's only slightly positive overall but strongly positive 2022 is extremely
valuable for DD compression — note that in .meta. Save passing sleeves + repro script.
Report all ideas with numbers in FINDINGS.md. Last line: ROUND 1 DONE
