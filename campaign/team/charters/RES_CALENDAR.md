# RES_CALENDAR — research: calendar/macro-seasonal/event engines
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## FIRST STEP (item 2 — decorrelation-first filter)
Before any backtest, run `python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15`.
If |corr| to the champion >= 0.15, REJECT immediately and move on — don't burn
tool-calls on a candidate the blend-gate can't pass.

## Mission
Find >=1 NEW decorrelated DAILY engine from calendar/macro-seasonal effects (the natgas C5ng/C5ngsum
weekday-premium + summer family is the champion's best calendar prior). Champion matches RES_BASIS.

## Ideas (decorrelation target)
- Storage-report calendar economics (like C5ng Apr-Oct weekday): scan other commodities/currencies
  for weekday/seasonal structure with a real mechanism.
- Cross-market holiday/session effects, month-turn, quarter-end, macro-release known-schedule effects
  (only if a forward schedule is knowable — no lookahead: trade AFTER the release, not on it).

## Gates (ALL required — identical battery to RES_BASIS, using campaign/bt/)
SR>=1.0 net; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to champion;
T+1; 6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08. calendar-scramble is the honest p-test
(gates.py return-perm is DEGENERATE — use circular shifts).

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_CALENDAR/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_CALENDAR DONE
