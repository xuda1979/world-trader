# A3 round 2 — Momentum-family sleeves (r1 lesson: static chars invert; momentum is panel-bias robust)
1. 12-1 momentum (skip last month) xs on 298 panel: monthly, top/bottom tercile, 6bps T+1.
   Test sub-periods + sector-neutral version (sector from fundamentals? if unavailable, size-neutral).
2. Momentum + crash-avoidance: momentum held only when SPX>200d MA (regime gate, no lookahead).
3. Vol-scaled momentum: weight names by inverse 21d vol.
4. Momentum quality: momentum conditioned on low idio_vol (features parquet has idio_vol).
5. 52-week-high proximity (George-Hwang): rank by close/252d-high, long top tercile.
6. Momentum on the EXT panel (440 names, 2020+ only) as a robustness cross-check (not a sleeve).
Standard gates. Append FINDINGS.md. Last line: ROUND r2 DONE.
