# C2 Round-3: rates domain at 6bps — the answer is LOW-TURNOVER structure (flyC lead)

Round-2 lesson: gross edge real (flyC 1.75!) but costs 7-13%/yr kill it. The edge is days-scale
z-mean-reversion; 6bps x daily turnover is fatal. Remaining honest options:
1. flyC (10s20s30s) WEEKLY-step z: sample z at weekly frequency, hold position 5 sessions
   (turnover /5), verify gross edge survives (gross SR was 1.75 daily-sampled; weekly ~?).
   If weekly gross >= 1.2 and turnover ~0.1/day => costs ~1.3%/yr => net could pass.
2. Same for flyA/flyB: weekly-step z, 5-day holds, 6bps — param grid {w50,75,126} x {thr 1.0,1.5}.
3. MONTHLY reversion on 2s10s (40y of data): monthly z of spread level, 21-day holds,
   turnover ~0.05/day — costs negligible; test SR honestly (may be too slow — document).
4. Event-driven: FOMC-day +1 drift in 2y? (FOMC calendar from FRED? not free-structured —
   skip if unavailable).
5. 20y (DGS20) belly fly: 10s20s30s already = flyC; try 5s20s30s, 2s20s30s variants.

Report exact turnover and cost drag per config. All gates on any save. Last line: ROUND 3 DONE
