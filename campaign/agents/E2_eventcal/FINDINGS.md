# E2_eventcal FINDINGS — Round 1 (2026-09-01)

Harness: campaign/scripts/e2_lib.py + e2_idea*.py. SPY = spy_early(1993-05) stitched to
twelve_big SPY (2006-09+), T+1 via pre-known calendar earning days (no lookahead possible:
all masks are functions of the exchange calendar), 6 bps/side on |Δpos|, vol-target 10% ann
(expanding trailing, min 60d, clip 3x). Gates per GOAL100 brief: full net SR>=1.0, H1&H2>=0.5,
<=2 neg years each >-5%, scramble 200x p<0.05, |corr|<0.15 vs GOAL100_CHAMPION_BALANCED.
All books were also run gross-of-VT in grids; VT never moved any sleeve past SR 1.0.

## Idea 1: Quad-witching (3rd Fri Mar/Jun/Sep/Dec) week windows, SPY long/short — FAIL
Grid of 14 windows [-5..+5] x L/S, full 1993-2026 and 2006+. Best cells:
- short opex DAY [0,0]: gross SR 0.85 (full) / 0.88 (2006+); after VT: SR=0.85, ann=5.49%,
  vol=6.5%, dd=-10.6%, H1=0.63 H2=1.06, negYr=5/33 (0/18 in 2006+, worst yr -2.0%),
  scramble p=0.024 (real), corr=-0.038 vs blend (n=4514).
  FAILS only gate (a): 0.85 < 1.0. Effect is REAL and robust: opex-day SPX mean -58.7bp
  vs +5.2bp other days, Welch t=-7.50, median -52.9bp, winsorized-1% mean -58.6bp,
  every decade negative (-42/-52/-57/-90bp 1990s/2000s/2010s/2020s).
- long pre-week [-3,-1]: SR 0.31. L/S composites long[a,-1] - k*day0: best SR 0.87 (a=-3,k=4),
  3 neg years -> fails (a) and (d).
Verdict: genuine anomaly, 4x/year frequency too low for SR>=1.0 standalone. Do NOT save
(charter: weaker engines don't move the frontier). Candidate note for a multi-event HF round.

## Idea 2: Monthly-opex-day vol (3rd Friday every month) — FAIL
385 opex days 1993-2026. Monthly opex-day mean -21.4bp vs +5.4bp other (Welch t=-5.01,
median -13.4bp, all decades negative, 25/34 years negative) — real but weaker than quad.
Best book short-day0 k=2 + long[-5,-1]: SR 0.52 (H1 0.60/H2 0.42), 8 neg years.
Plain short day0: SR 0.40. ALL cells 0.16-0.52 << 1.0. FAIL (a).

## Idea 3: Treasury refunding cycle (first business Wed Feb/May/Aug/Nov), 10y — FAIL
10y TR synth from DGS10 (carry = y/252 - 8.5*Δy; vol 8.7% ann, 1962-2026). 147 mapped
announcement days 1990-2026. Announcement-day Δy = -0.29bp (nothing; post-ann -0.43bp).
Best window [0,5] long: TR +5.19bp/day vs +2.05 out, but book SR=0.21 (15 negYr);
all 20 grid cells (a,b ∈ {-5..15} x L/S) in [-0.47, 0.22]. Refunding carries no tradeable
timing info on the 10y. FAIL (a).

## Idea 4: Turn-of-quarter window dressing, SPY + EW 298-name panel — FAIL
SPY: first-3-days-of-post-quarter-month +14.4bp/day in-window vs +3.7 out, but long/cash
book SR=0.31 (best of 8 (nl,nf) cells: 0.16-0.31), 11 neg years. Panel EW 2006+: toq(1,3)
SR=0.31, dd -19.2%, H1 0.27/H2 0.35, scramble p=0.040, corr 0.049. FAIL (a),(c).

## Idea 5: Holiday pre/post drift (rule-based NYSE calendar, A4 us_holidays) — FAIL
Corrected classification (only gaps containing a real holiday; 263 events 1993-2026):
SPY pre +7.7bp (t=2.80) AND post +8.6bp (t=3.53) vs +4.1 out — both edges exist gross but
only 8 days/year each side: net books SR=-0.13 (pre), -0.07 (post), +0.08 (pre|post).
2006+ SR: 0.02/-0.11/0.13. A4's earlier "post ≈ 0" was a Monday-classification artifact;
corrected post is positive but still untradeable at 6bps/side. FAIL (a).

## Idea 6: Composite of passing micro-effects (opex-short + pre/post-hol + TOQ + last-Q) — FAIL
24-cell weight grid on SPY 1993-2026. Best SR=0.44 (opex 1x + TOQ-first3), next 0.42/0.42/0.41.
Panel opex-day check: +5.3bp vs +7.9bp other (t=-0.33, n=232) — the opex short does NOT
generalize to the EW panel (it's an SPX-index-microstructure effect), so no panel version.
All composites fail (a) by a wide margin. FAIL.

## ROUND VERDICT
0/6 sleeves saved. The calendar-event class on liquid index/bond proxies tops out at
SR 0.85 (quad-opex short) vs gate 1.0. Every effect measured is directionally consistent
with the event-drift literature (opex-day -58.7bp t=-7.5 is the standout) but event
FREQUENCY (4-16 days/yr) mathematically caps net SR below the campaign bar after 6bps/side.
No decorrelation gate was ever reached (all sub-1.0 SR). Honest plateau: calendar effects
are real but only viable as small overlays on other engines, not standalone sleeves.

### Rescue attempt: multi-index opex short (SPY+QQQ) — FAIL
Panel has only SPY and QQQ as index ETFs. QQQ opex-day 2006+: -10.2bp vs +7.5bp (t=-2.23);
SPY 2006+: -16.0bp (t=-2.94). Equal-weight 2-leg short: quad-only SR=0.58 (dd -11.1%,
6 negYr), monthly SR=0.04. Diversification unavailable -> still fails (a).

Ideas for a hypothetical round 2 (only if charter demands): (i) opex-day short combined with
month-end VIX-options microstructure books to raise frequency; (ii) SPX vs EW-panel opex
SPREAD (index - basket: t=-0.33 on levels suggests spread may differ — needs pair construction);
(iii) day-after-expiry gamma-flip rebalancing on single names in the 298 panel.

ROUND 1 DONE
