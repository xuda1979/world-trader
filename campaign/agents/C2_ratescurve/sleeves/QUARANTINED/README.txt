QUARANTINED 2026-09-01 (C2 round 2 audit): C2_fly2AB_75 SR 1.85 as-saved is INVALID.
Units bug: fret = -D*dy with dy in pct-points gives PERCENT-scale gross returns, but costs
were subtracted as decimal (to*6e-4) -> 6bps charged as 0.006bp on a 100x-larger PnL scale.
Honest rerun (decimal fret, per-leg 6bps): FULL SR -2.04, ann -7.6%, mdd -78.8%, 21 neg years.
Gross edge is real (pre-cost SR ~1.5) but costs ~21%/yr vs gross 1.7%/yr. See FINDINGS.md #1.
