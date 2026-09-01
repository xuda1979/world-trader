# G3_ratesfut — FINDINGS (self-executed; GLM 429)
## a6r7 (2y policy momentum) instrument reality: FAITHFUL synthetic
- a6r7 uses synthetic 2y TR = -1.9*d(DGS2)/100 + y/252. Real 2y proxy tradeable.
- corr(synth 2y TR, real IEF 7-10y) = 0.721; corr(synth 10y TR, IEF) = 0.955.
- The 2y trend (hike/cut cycle) message lives almost entirely in the SIGN of the yield
  move, which real ETFs capture. Sleeve is instrument-real (SHY/ZT futures approximation
  faithful). KEPT in strict champion.
- Note: the 461d zero-run is the hike-cycle veto (documented); unchanged by instrument choice.
- Cost: IBKR audit already charged 5bps + futures carry; sleeve SR 1.29-1.32 in audit_harness.

ROUND DONE
