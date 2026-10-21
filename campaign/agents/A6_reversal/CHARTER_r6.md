# A6 r6 — NEW-FAMILY directive (joint goal SR_m>=2.0, ann>=20%, MaxDD<5%)
A6 family closed by your own r5 statement — this round you get OTHER families:
1. **Pair-trading lite**: top-40 most-correlated same-sector pairs in the panel (compute 252d corr on
   126d window monthly), trade z-score of spread (252d), enter |z|>2 exit 0, dollar-neutral, 6bps/side
   on trades, vol-target 10%. Classic stat-arb, unexplored on THIS panel (prior project's stat-arb failed
   on different data with z15 exits).
2. **Lead-lag**: large-cap (top 50 by dollar vol) 1d return predicting small-cap (bottom 50) same-day
   next return — build long lagged-winners small-cap book, weekly.
3. **52w-high momentum** (your r1 idea 5, never fully worked): close/252d-high ratio, long top tercile,
   MA150 gate, vt15.
4. **Earnings-drift proxy**: 1m earnings-announcement window momentum (proxy: names with new 52w highs
   + revenue growth in latest fundamentals) — crude but orthogonal if it works.
Gates: SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%, scramble<0.05, plateau, corr<0.35.
Append FINDINGS.md; last line ROUND r6 DONE.
