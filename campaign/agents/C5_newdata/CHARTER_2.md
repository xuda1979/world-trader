# C5 Round-2: extend the PROVEN natgas weekday + cash-market calendar family

Round-1 lesson: natgas Fri->Mon weekday premium (SR~1.0-1.1 honest, calendar-scramble p=0.016)
is REAL (storage economics: Fri short-covering premium). Extend:

1. Rebuild C5_ng_weekday_prem WITHOUT the calm filter and without vt; report each component's
   contribution honestly (the saved sleeve's meta overstates SR 1.74 vs honest 1.08 — rebuild
   C5_ng_weekday_prem_v2 with honest numbers in meta; agent must use full_stats on the vt series).
2. Weekday structure in the natgas FUTURES proxy via 6-9bp: no — keep spot, but test
   Tuesday/Wednesday legs separately (Wed t=1.88 weak); keep only t>=3 legs (Mon, Fri).
3. WTI/Brent WEEKDAY books (t-stat scan first; earlier scan says no effect — verify and document).
4. Natural-gas STORAGE cycle: EIA weekly storage surprises unavailable free — use natgas spot
   momentum gated by calendar month (injection Nov-Mar withdrawal seasonality of volatility).
5. POWER/coal proxies? none on disk — document and skip.
6. FRED weekly+ series with Friday-release timing: DGS1MO bill weekday structure 2001+;
   DEX* EM-FX weekday effects (INR/BRL/KRW/MXN/SGD/SEK/NOK vs USD) — scan all, keep t>=3.
7. Equity factor-panel weekday: KF daily 48-industry EW returns weekday structure (1926+!) —
   Monday effect in industries, any t>=3 across 48 -> composite book of industry-weekday
   effects with honest multiple-testing control (Bonferroni: require t>=4 given 48 tests,
   or replicate sub-periods).

Deliver sleeves only if gates pass. Log all numbers in FINDINGS_2. Last line: ROUND 2 DONE
