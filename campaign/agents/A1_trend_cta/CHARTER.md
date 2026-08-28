# A1 — Time-series momentum / CTA on macro assets
Families to try (in order):
1. 12m/6m/3m ts-momentum on FRED macro series (xau, wti, brent, copper, natgas, spx, dxy, us10y, us2y) with 63d/252d lookbacks, 21d rebalance, vol-targeted 10%.
2. Dual momentum: sign of 252d AND 63d trend must agree.
3. Trend on FF factors (Mkt-RF, SMB, HML, Mom) — factor timing lite.
4. Cross-asset risk parity + trend overlay (long-only, trend-gated).
Notes: fx pairs (data/fx, 8 pairs 2007+) also in scope. Costs matter: macro futures-like books trade rarely (21d) -> ~2-4 bps/day drag max. Use futures-proxy assumption from prior suite (they modeled ETF/futures costs at 6bps/side).
Watch out: wti.csv vs wti_full.csv (full has longer history); copper_monthly is MONTHLY — use only for slower books or resample honestly.
