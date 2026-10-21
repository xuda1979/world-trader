# HUNT_BASIS2 — cross-commodity basis/spread mean-reversion (reassigned slot, iter 4)
Prior slot HUNT_BASIS died on API 429. Prior family knowledge: brwt (Brent-WTI futures pair,
z-rev 1.5 gate) is the single best sleeve family in the champion; gold-silver, wti-ng, copper
FAILED in earlier rounds (E4_globalidx / D-series). Your job is the REMAINING untapped basis pairs.

DATA on disk (verify yourself, do not assume):
- tools/quant/data/ and tools/quant/hedge_fund_strats/ (futures CSVs: check what exists — CL, CO,
  NG, HO, RB, GC, SI, HG, C, S, W, LC, CT etc. whatever is actually there)
- FRED spots (DCOILBRENTEU, DCOILWTICO, DHHNGSP, GASREGW etc.); alphaportfolio panels (equities only)

GOAL: find >=1 DAILY decorrelated sleeve with: SR>=0.6 (2008+), H1>=0.3 & H2>=0.3,
0 neg yrs tolerance: <=2 with each >-5%, 200x block-scramble p<0.05, |corr|<0.15 to
campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv (use this champion now, not L16),
flatten gate: ac1<0.5, uniqR>=0.08. T+1 execution, 6bps/side on turnover, borrow 0.5%/yr on
short notional if any short leg. NO flattening (real daily path), no lookahead (trailing only).

Mechanics that worked for brwt: z-score of log spread over trailing window, position only when
|z|>1.5, vol-target 0.08, cap 8. Try: crack spreads (HO-CL, RB-CL), NG calendar-cycle proxies,
gold-platinum, copper-gold ratio, live-cattle-feed (corn), soy-crush. If futures data absent,
FRED spot pairs are admissible with disclosed basis risk.

Deliver: sleeves CSVs in this dir + FINDINGS.md with exact stats per candidate and
explicit PASS/FAIL per gate. A REJECT with exact numbers is a valid result — do not fake passes.
Last line of FINDINGS.md must be exactly: HUNT_BASIS2 DONE
