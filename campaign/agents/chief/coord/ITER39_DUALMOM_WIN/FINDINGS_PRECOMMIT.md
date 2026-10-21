# ITER39 FINDINGS_PRECOMMIT - DUALMOM GATE MA-WINDOW (WIN) 1-D SLICE AT FROZEN BAND=0.03
Sealed BEFORE any candidate computation. Session 19 cont. (2026-09-19 ~13:2x CST), operator objective
verbatim unchanged ("keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual
return can't be smaller than 20%.").

## MOTIVATION DISCLOSED AT SEAL TIME (ITER35 second-seal pattern, tension stated head-on)
ITER38 (precommit 8a1c571db36f9770, same session) measured the FULL acceptance-printed BAND axis
{0.01..0.05} of the dualmom hysteresis gate: single-peak curve, admitted escape cell BAND=0.02 at
IS-SR 4.199008 = bar + 0.000376 (shadow-price scale), REVEALED and REJECTED on G7 (FS SR 3.750604 <
3.751429, 1/5 bins positive). The band axis left NO open direction on itself. Seal #1 pre-named the
WIN slice as "the natural SECOND seal if this one leaves a one-sided open direction" - that literal
condition did NOT fire. This seal proceeds anyway ON ITS OWN DETERMINISTIC MOTIVATION, disclosed
here rather than papered over: (i) WIN is the OTHER axis of the same 2-D acceptance plateau grid
(r2_scan5.py: win {150,175,200,225,250} x band {0.01..0.05}), fully acceptance-printed, zero new
points; (ii) the sweep rule is the mirror of seal #1 (window-at-frozen-threshold) and covers the
win axis ENTIRELY - as a FAMILY measurement this is not a mining drift but the completion of the
pre-named program; (iii) dualmom carries 5.7226 pct of the champion book (measured at the ITER38
A2 anchor). Post-seal rule: after WIN, the dualmom gate family is FULLY measured; FRAC=1/3 has NO
printed acceptance grid (sweeping it would need NEW points = mining-adjacent) and stays refused
absent the zb-midpoint-style deterministic convention being explicitly pre-committed in a future
seal. The xs 21/252 lookbacks remain strategy identity (frozen, degenerate treatment).

## GRID + RULE
Sweep WIN at FROZEN BAND=0.03. GRID = {150, 175, 200, 225, 250} = EXACTLY the acceptance-printed
win axis, anchor 200 centered. min_periods COUPLED to win (rolling(win, min_periods=win) - derived
variable, not a second scalar; same coupling rule as the ITER37 tsmom MAW axis). WIN_F=200 module
constant of the ITER38 builder becomes the sweep parameter; BAND hard-frozen at 0.03 inside the
builder. Everything else byte-frozen per seal #1 (xs 21/252, FRAC=1/3, VT 0.10/expanding60/cap5,
6.4bps FULL |dW|, monthly T+1).

## METHOD + FILTER SET (verbatim canon)
Identical to seal #1: pool mirror 2008-03-31 / fit rows 1809 / k_covered 11 / Wmax_sf <= 2.0 at
k=11 / IS-MDD >= -6 pct / 0 IS-neg yrs / IS-SR > 4.198632 + 1e-4 jitter; global argmax over
admitted cells (tie-break |WIN - 200| then WIN); ONE reveal; G1-G8 verbatim (G7 = 5-bin OOS dSR
>= 4/5 positive AND min bin >= -0.10 AND FS SR > 3.751429); STOP RULE verbatim: 0 admitted ->
honest negative no reveal; gate fail -> REJECT no second reveal; 8/8 -> ADOPTABLE verdict only
(no auto-swap). Champion sha asserted pre==post. Coverage law: every cell expected on the
IDENTICAL stream calendar (first eligible MES 2007-09-28 is win-independent - A1 proves it at
win=200; larger win only delays MA availability pre-2007, inside the FF 1926+ history, so the
gate state at the first eligible MES is ffill-stable; asserts fail-closed, ITER30-A2 amendment
pattern if breached).

## A1
The generator is the SAME re-type as seal #1, restructured to parameterize win (ma computed per
win from the cached FF market; band=0.03 frozen constant). anchor_iter39.py re-runs regen-vs-saved
at (win=200, band=0.03) BEFORE this driver: the assert is the same class (< 1e-12, index
identical). Byte-identity of the driver's builder block to anchor_iter39.py is maker-asserted via
ast extraction (same machinery as seal #1). D17 panel pre-patch carried verbatim.

Driver: driver_iter39.py derived from driver_iter38.py by deterministic asserted-exactly-once
substitutions (maker persisted as make_driver_iter39.py); frozen pool blocks ast-text-identity
vs driver_iter36.py AND driver_iter37.py AND driver_iter38.py at run start; precommit sha asserted
at run start; log to driver_iter39.log.
