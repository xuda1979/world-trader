# GOAL100 ITER7 — FREE DATA ACQUISITION + FRAMEWORK + VERIFICATION (2026-09-03, live)

## TRACK A — Reusable testable framework (DONE v1, 26 TDD tests)
campaign/bt/ : engine.py | metrics.py | gates.py | reconcile.py | backtest.py (+ README).
Honesty invariants tested: T+1 lag, no-lookahead vol-target (perturbation test), day-level
leverage cap, margin on (gross-1)+, half-turn costs, borrow, flattening gate (uniq/ac1).

## TRACK B — Best results double-checked (INDEPENDENT, via campaign/bt)
- V3_BAL champion: ann_geo 43.61%, SR_d 3.924, SR_m 4.016, MaxDD -4.92%, 0/19 neg (n=4713) — REAL.
- RAW-EW13@1.6x candidate: ann_geo 28.89%, SR_d 3.884, MaxDD -4.25%, 0/19 neg (worst +10.18) — REAL.
- (VERIFY_BEST agent doing deeper independent rebuild + ledger reconcile in parallel.)

## TRACK C — MORE FREE DATA (dedicated agents, working Twelvedata/FRED/Finnhub keys)
### New dir: tools/quant/data/more_etf/   (43+ ETFs, fail-closed lint + manifest)
- NEW sector ETFs (FULL 2006-2026, 5000 rows) previously MISSING: **XLK, XLU, XLV, XLY, XLP,
  XLC** (2018+), XLRE (2015+), XHB, ITB, IGV, SMH, KBE, KRE, XOP, XME
  -> solves HUNT_CROSSASSET2's blocker (XLK-family missing) -> sector-relative books now buildable.
- Commodity/metals: GDX, GDXJ, SLV, USO
- International equity: EFA, EWG, EWJ, EWL, EWP, EWS, EWU, EWW, EWY, EWZ, FXI, INDA, VWO, EEM
### New dir: tools/quant/data/more_fred/   (26+ series, span-linted)
- KEY: **VXVCLS** (VIX 3M, 2007-2026) — HUNT_VOLOVERLAY said VIX3M/VXV "not on disk"; this unlocks
  the term-structure overlay, the ONLY untested family it flagged. **GVZCLS** (gold vol 2008+),
  **OVXCLS** (oil vol), DFII5/20/30 (real yields), credit DAAA/DBAA/BAA10Y, money MZM/REALLN,
  macro INDPRO/UNRATE/HOUST/PERMIT/UMCSENT/CPIAUCSL, FEDFUNDS/DFF, TB3MS/TB6MS, GASREGCOVW.
### New dir: tools/quant/data/more_crypto/ (10+ coins to raw_td, twelvedata)
- ADA, AVAX, BNB, BTC, DOGE, DOT, ETH, LINK, LTC, POL ... (spans ~2020+, low-corr satellite family)

## NEXT (once data agents DONE)
1. Dispatch HUNTS on the NEW data: (a) sector-relative XLK/XLU/XLV vs XLE/XLB (previously impossible),
   (b) VIX/VXV term-structure overlay (the one untested family), (c) GVZ/OVX vol maps, (d) crypto
   low-corr satellite. All through campaign/bt + TRADE_RECORD_STANDARD + fails the annual gates.
2. AUDIT_FRAMEWORK verdict -> finalize framework (fix any bugs found).
3. Re-run VERIFY_BEST + update FINAL_STATE scoreboard.
