# E3_volregime FINDINGS

## Idea 1 — Vol-shock reversion (VIX z(21d)>2 or VIX>thr -> hold SPX 5-10d): FAIL
Grid: thr{15,20,25,30} x zthr{1.5,2.0} x hold{5,10}, T+1, 6bps, vt10 trailing-only, 2007-01+.
Best cell (VIX>15|z>1.5, hold 5): SR=0.47 ann~6% negy=3 worst=-23.4% H1=0.34 H2=0.63.
ALL cells SR 0.32-0.47. Reference SPX B&H vt10 same window: SR=0.48 negy=4 worst=-22.4%.
Verdict: signal adds NOTHING vs buy-and-hold (SR identical), fails gates a (SR>=1.0),
d (3-4 neg yrs, worst -16..-24%). Panic 5d mean-reversion drift is already in B&H.
No sleeve saved.

## Idea 2 — Vol-of-vol (21/63d std of dVIX) gating SPX or natgas: FAIL
SPX: low-vov book best SR=0.51 (lb=21,q=.90) negy=5 worst=-18.9% — below B&H ref 0.48 on
risk-adjusted basis with worse drawdown profile; high-vov book SR<=0.27. Gate is just a
degraded vol filter on a B&H engine.
Natgas: long-when-lo-vov (lb=63) SR=0.52 vs B&H ref 0.48 — no edge, negy=4, H1=0.28<0.5.
Best vov-gated natgas does not beat its own B&H reference and fails gates a,c,d.
Verdict: vol-of-vol carries no cross-sectional timing info at daily horizon here.
No sleeve saved.

## Idea 3 — Term-structure SPEED ((VIX3M-VIX) 5d change) momentum on SPX: FAIL
Note: no VIX3M on disk; downloaded CBOE free VIX3M_History.csv (2009-09+; index starts only
2009, short span) saved to campaign/agents/E3_volregime/vix3m_free.csv. Proxy (5d dVIX z)
also tested pre-download: all cells SR<=0.41. Real VIX3M grid z{-1,-0.5,+0.5,+1} x hold{5,10}:
best event cell SR=0.44 (flatten z<-0.5 hold 10) negy=4. Long-unless-flatten SR=0.72 ann=5.5%
negy=4 worst=-8.4% H1=0.60 H2=0.83 — better than B&H but fails a (0.72<1.0) and d (4 neg yrs).
Verdict: term-structure speed has weak marginal info vs VIX level at daily horizon; VIX3M
history too short (16.7y, 2009+) to be a flagship sleeve anyway. No sleeve saved.

## Idea 4 — VIX integer-threshold crossings (20/25/30) -> next-5d SPX drift: FAIL
T+1, 6bps, vt10, 2007+. Best cell cross>30 hold=5: SR=0.51 ann=5.6% negy=2 worst=-0.5%
H1=0.55 H2=0.47 — fails gate a (0.51<1.0). Only 53 events in 19.8y (2.7/yr), 11 in 2022
alone; 2022 had +1.54% avg fwd-5d (bear-rally harvest) but tiny sample. cross>20 (149 ev)
and cross>25 (102 ev) SR 0.13-0.37, 5-8 neg yrs. Raw avg fwd-5d after cross>30 = +1.54%
vs 0.21% all-days — real drift but too sparse/weak to be a sleeve. No sleeve saved.

## Idea 5 — Gold vol regime (xau 21d vol z gates gold book): FAIL
xau (FRED 2007-12+), vol z(252d) gates{hi>1, lo<-1, calm<0.5} x dir{+1,-1}, T+1 6bps vt10,
2008-06+. Best cell calm&long SR=0.50 — WORSE than gold B&H vt10 ref (SR=0.59), negy=6,
H1=0.25<0.5. Short-gold cells all negative. Verdict: gold realized-vol regime contains no
directional timing info for gold; gate only degrades B&H. No sleeve saved.

## Idea 6 — Cross-asset vol dispersion (std of 21d vols of SPX/NG/gold/copper/U10) gates
## SPX-vs-gold 2-asset book: FAIL
Copper starts 2010-05 so evaluation 2010-05+ (also tested w/o copper — same shape). Full
threshold grid z{-1..2}: monotonic in thr, best long-SPX-else-gold SR=0.65 (thr=1..2,
plateau edge — no interior peak), negy=6, H1=0.31<0.5. Inverse (riskon=gold) SR=0.70 negy=3
H1=0.64 H2=0.76 — fails gate a (0.70<1.0). Reference 50/50 SPX+gold B&H vt10: SR=0.90 —
dispersion gate UNDERPERFORMS static 50/50 by 0.20 SR. Verdict: cross-asset vol dispersion
is dominated by SPX vol itself and adds no allocation skill. No sleeve saved.

## Idea 3+6 fusion — fast term-structure-flatten switches SPX->gold (VIX3M free download):
## FAIL
Best cell zthr=-1.5 hold=10: SR=0.69 ann=5.2% negy=4 H1=0.41 — fails a and c; reference
50/50 SPX+gold B&H vt10 = SR 0.91 dominates. Also note VIX3M history only 2009-09+ (16.9y).
Verdict: the flatten wave can dodge some SPX drawdown but gives up far more upside; gold
is a worse parking asset than cash-like mixtures the champion already holds. No sleeve.

## ROUND 1 VERDICT (E3_volregime)
All 6 charter lanes + 1 fusion tested honestly (T+1, 6bps/side, vt10 trailing-only expand-
window min60 clip3, scramble 200x planned on any passing sleeve). ZERO sleeves saved —
every engine either (i) failed to beat its own asset B&H vt10 reference (ideas 1,2,4,5,6),
(ii) failed SR>=1.0 / halves>=0.5 (all), or (iii) rests on <20y short-history data (VIX3M
2009+). Vol-event DAILY drift books do not clear the new SR>=1.0 bar; the panic-reversion
premium is already inside SPX B&H. Honest note: A5's contango sleeve (SR 1.02) uses the
same VIX family at monthly horizon with term-structure LEVEL — E3's daily EVENT framing
adds nothing decorrelated. Lane closed for this data inventory.

ROUND 1 DONE
