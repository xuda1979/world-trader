# STRICTAUDIT_EXECUTION — adversarial verification of instrument-real + broker-real cost claims (read-only)

TARGET: the claims that GOAL100_STRICTTRADE_BALANCED_daily.csv is "tradeable on real instruments
(futures, ETFs, long-short), byte-verified, NYSE calendar, broker-real costs + borrow fees."
The 12 sleeves and their claimed realisms (from GOAL100_TRUTH_MEMO §16 / IBKR §15):
  brwt5/7/10/15  WTI/Brent FUTURES pair (net ~zero gross), 1.5bps
  C5ng, C5ngsum  natgas FUTURES proxy for SPOT prints, 5bps (basis risk disclosed)
  A5r2           SPY long (gated), 6bps, no short
  a6r7, QAxasts  2y/10y UST synth via SHY/IEF/futures, 5-8bps (IEF corr 0.72-0.96)
  carryv2        WTI/gold/10y futures, lag-1 honest
  dualmom, XGB1y  equity L/S books, 15bps, shorts with 50bp generic / 20% HTB at 300bp borrow

YOUR JOBS (hunt for the unverifiable / wrongly-costed):
1. INSTRUMENT MAPPING: for every sleeve, confirm the price series it trades actually exists
   on disk as a real instrument and the trade is executable at the stated cost. Check the
   repro scripts + data paths. Flag anything that is a synthetic/approx that cannot be
   directly traded (e.g. natgas SPOT vs front futures; synthetic BAA/LQD credit legs — the
   2 removed sleeves A5r7/A1credit were REJECTED on this exact ground; verify the remaining
   12 have NO such paper-leg).
2. BORROW-FEE ACCOUNTING: the equity L/S books (dualmom ~285 names, XGB1y ~20 names) charge
   50bp generic + 20% of shorts at 300bp. Verify: (a) is this fee actually subtracted from the
   STRICTTRADE series, and at what cadence? (b) is the short inventory realistic — do the
   books actually hold those shorts? (c) short-proceeds rebate is claimed EXCLUDED
   (conservative) — confirm the series does NOT include a rebate.
3. COST CROSS-CHECK vs the 12 sleeve files: the sleeve CSVs already embed 6bps. Does the
   STRICTTRADE series correctly add ONLY the incremental instrument cost (1.5-15bps) and
   borrow, or does it double-charge the 6bps, or skip the instrument cost? Quantify the
   per-bps drag on ann to judge materiality.
4. NYSE CALENDAR: the series must contain ONLY NYSE trading days (holiday P&L accumulated to
   next trading day, no weekend rows). Build a real NYSE holiday calendar 2008-2026 and test
   the CSV dates: list any weekend or known holiday that appears as a row. Also flag phantom
   flat days (zeros on valid trading days where a position should be live).
5. REBASED/PHANTOM-REVISION risk: FRED spot prints (natgas) publication-lag — is there any
   evidence the series uses same-day prints that would not be tradable (calm filter)? Report
   the natgas-lag risk exposure. (Known open item: C5ng SR 1.63->~0.25 if lag applies, but
   blend impact is what matters — quantify the STRICTTRADE-level impact of cutting natgas edge 85%.)

Write campaign/agents/STRICTAUDIT_EXECUTION/FINDINGS.md: per-sleeve instrument verdict
REAL/PAPER/UNVERIFIED + cost-accounting verdict + calendar verdict, and the corrected ann/SR/DD
if any material mis-costing is found. Last line exactly: STRICTAUDIT_EXECUTION DONE
