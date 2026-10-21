# K1_tailhistory FINDINGS (agent K1_tai_trend) — 2026-09-16
- REJECT direction (a) trend x inverse-252d-excess-kurt on CORN+QQQ: best net SR 0.46 (kurt126) / 0.26 (kurt252 primary) << 1.5 gate; scramble FAIL 0.255<0.401; inv-kurt scaling UNDERPERFORMS plain trend (0.26 vs 0.43); 7 negYr; halves fail. No param plateau (0.11..0.46 scattered).
- REJECT direction (b) short-variance harvest via VIX gate: edge absent GROSS — QQQ leg ann -4.73% SR -3.64 (VIX=SPX implied vs QQQ realized basis bleed); SPY same-index control ann -0.52% SR -0.56 (no daily-granularity VRP at VIX^2 proxy). Full cost stack (6bps + 0.5% borrow + 4.5% margin) -> net SR -0.01..-9.65; vt10 ruin (MaxDD -100%). Skew -5.7, xkurt 64.
- Champion untouched: SR 5.18 ann 61.7% @1x (recomputed). Best K1 gap: 4.72 SR. K1_sleeve.csv NOT saved (SR>=1.5 unmet; corr gate moot).
- Units defect caught & discarded pre-report: first B run used VIX/16 (percent points as fractions) -> SR 28 / ann inf — impossible; root-caused to (VIX/√252)^2 without /100; rerun clean. Logged for honesty.
DONE K1_tail
