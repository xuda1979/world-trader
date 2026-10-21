# HUNT_MACRO2 — FINDINGS (iter8) — NEW-DATA HUNT #4

**VERDICT: NEGATIVE for champion improvement — one REAL-but-small standalone found.
Best new signal: NFCIRISK weekly level-gate (risk-high => long-flat QQQ, 5-day publish lag,
real book): SR 0.90, ann 5.3%, MDD -7.4%, 0 neg yrs (2008/09/16/22/23 = exactly 0.0 flat, not
profit), scramble p=0.02, exposure 0.58. Levered to cap: ann 14-17%, SR 0.83-0.89, MDD -22-27%.
BLEND INTO CHAMPION: corr 0.214, dSR NEGATIVE at every weight (-0.012 @5% .. -1.6 @50%).
The gate's flat-period 0.0 years do not hurt neg-count but its 5% ann drags champion's 28.9%.**

## Screen honesty note (168 variants)
- The screen's 0.952 top line was WITHOUT publish lag; realistic lag-4 keeps SR 0.90 (slow
  weekly median — robust to lag), scramble p 0.02@lag4 (0.11@lag6, 0.175@lag8 — marginal).
- JTSJOL monthly gate: SR 0.75, neg 2 (2008-class year -15.6%) — fails yearly.
- RRPONTSYD: dies at lag1+ (0.46, 3 neg). TEDRATE: 0.69-0.81 but 4-6 neg. T10Y3M: 0.61, 5 neg.
- Every other gate: neg 2-8 or SR < 0.5.

## Why not delivered
1. Standalone ann 5-17% << 80% goal; SR 0.9 << 5.
2. Blend HURTS champion SR at all weights (corr 0.21 but its own ann/SR too low).
3. Risk-off gates (medinv family) mostly reduce DD by also removing up-years.

## Gates: ann80 NO | SR5 NO | DD7 marginal | 0-neg YES(only because flat-years count as 0) | lev YES
DEAD_IDEAS += "NFCIRISK/STLFSI4/JOLTS/RRP/TED/T10Y3M macro gates on equity", dead,
"best NFCIRISK gate SR0.90/ann5% standalone; blend dSR<0 all weights; rest 2-8 neg".
Do not re-run: z/median/mom gates on these 14 series vs QQQ/DIA (all 168 combos covered).
HUNT_MACRO2 DONE
