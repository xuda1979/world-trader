# C2_ratescurve — Full US Treasury curve + global rates (NEW DOMAIN)

Mission: build high-SR engines from the full DGS curve (1MO..30Y daily from FRED), breakevens
(T10YIE, T5YIE, T5YIFP), real yields (DFII10), credit (hy_oas, baa-aaa), international 10y
(au10y ca10y ch10y ez10y gb10y jp10y nz10y). Pass ALL gates.

IDEAS (in order):
1. Curve reversal: daily changes in 2s10s / 5s30s / 3m10y spreads are mean-reverting around
   trailing mean -> position curve flattener/steepener via 2y vs 10y returns approximation
   (e.g. long 2y ret - pos*x*10y ret; use duration-approx: 2y dur~1.9, 10y dur~8.5).
2. Level + curve regime: when curve inverted (10y-2y<0), steepener has carry; combine with
   momentum of the spread change.
3. Breakeven mean-reversion: T10YIE/T5YIE z-score reversion (inflation expectations overshoot
   in risk-off and mean-revert); trade via TIPS-vs-nominal proxy (DFII10 vs DGS10 spread reversion).
4. Real-vs-nominal (DFII10 vs DGS10) spread momentum/reversal.
5. Global 10y bond momentum (au ca ch ez gb jp nz us): cross-country TS momentum, EW book,
   vol-normalized; also pairwise spreads (US-JP, US-DE) mean reversion.
6. Credit (hy_oas z-score reversion gated by VIX level) — prior attempts exist (A5) so focus
   on curve + breakeven novelty; check corr vs library Credit_* sleeves first!
7. 3M-1MO bill-spread anomaly (2001+ window only — document the shorter window honestly).

NOTES:
- Bond returns must be APPROXIMATED from yield changes x duration (e.g. ret ~ -dur*dy + carry).
  Document approximation honestly. Alternatively use existing bond_trend.py approach.
- Curve trades: subtract 6bps on turnover; these are low-turnover engines (multi-day holds).
- Corr gate: vs library AND Coord blend. Credit sleeves already exist — differentiate!

HONESTY: All gates in GOAL100_AGENT_BRIEF.md.
