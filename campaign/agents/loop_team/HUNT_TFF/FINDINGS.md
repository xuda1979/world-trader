# HUNT_TFF — FINDINGS (iter9) — NEW-DATA HUNT #5

**VERDICT: NEGATIVE — 156 variants (13 TFF families x 4 trader categories + dealer-assetmgr
DIFF + lev-money crowd fades/moms, mapped to their natural proxies), ZERO reach SR 0.3.
Best: dow_emini lev-money fade -> DIA 0.275 (6 neg yrs); sofr asset_mgr mom -> TLT 0.234
(2 neg, worst -4.6%). The 52 new category series carry NO daily-tradable edge at 6.4bps on
daily proxies — weekly CFTC positioning is public, delayed, and slow by construction.
TDD: 5 tests pass (z no-lookahead, fade/mom signs, 3-day live-lag, DIFF series). bt 28 GREEN.**

## Why DIFF family (the one genuinely new idea) fails
Dealer-minus-assetmgr z measures inventory stress; the signal's information ratio dies after
the 3-day COT lag + T+1: best 0.203 (gbp diff mom, 8 neg). Weekly cadence = max ~26 independent
observations/year; costs at 6.4bps x turnover dominate the drift.

## Gates: ann80 NO | SR5 NO | DD7 NO | 0-neg NO (best 2-9 neg)
DEAD_IDEAS += "TFF trader-category z/diff/fade on proxies", dead, "156 variants, 0 >= 0.3 SR;
best 0.275/6neg; DIFF (new family) 0.203/8neg".
Do not re-run: z26 fade/mom on any tff_*.csv -> SPY/QQQ/DIA/TLT/IEF.
HUNT_TFF DONE
