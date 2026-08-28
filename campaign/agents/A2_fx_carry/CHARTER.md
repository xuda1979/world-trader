# A2 — FX carry + value + momentum (data/fx, 8 pairs 2007+)
Families:
1. Carry: rank by trailing 3m interest-rate differential proxy (use FRED tbill3m for USD; for foreign: use stooq ca10y/ch10y/gb10y/jp10y/au10y/nz10y/ez10y from data_fred) — long high-yield vs low-yield currency, top-2/bottom-2, monthly.
2. Carry + trend filter: only hold carry leg if 50d trend agrees.
3. FX momentum: 63d/126d ts-mom per pair, vol-weighted.
4. Vol-scaled carry: scale by inverse 21d realized vol of the pair.
Note: 2007+ start => 18.5y window; halves = 2008-2016 / 2017-2026. FX is a small book (8 pairs) — capacity/covariance matters; keep the book G1 (gross<=1).
