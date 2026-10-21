
## [DATA] Short-interest data investigation + SEC FTD build (2026-09-14)
- **Q (user): "did you use short interest rate data in champion? you should."**
- **Finding 1 — NOT used:** verified all 12 champion sleeve inputs (brwt10/7/5, C5ng,
  C5ngsum, A5r2, a6r7, QAxasts, carryv2, dualmom, diescrack, CFX4) are trend/carry/energy;
  NONE is short-interest based. Confirmed via grep across all sleeve files.
- **Finding 2 — data built:** SEC Fails-to-Deliver (FTD) archives (208 raw zips on disk,
  2017-08+) built into `tools/quant/data/sec_ftd/ftd_daily.csv` (2167 days, market-wide
  fails + notional, TDD-parser linted). Other SI sources on disk/available: FINRA
  consolidated short interest (altdata6, recent), Finnhub short interest (altdata,
  altdata2, recent).
- **Finding 3 — no standalone predictive power (tested):** market-level FTD shorting-pressure
  z-score vs SPY 2017-2026: corr(ftd_z, next-day SPY) = 0.004-0.005; low-pressure days ann
  21.2% vs full 14.5% and high-pressure 13.1%, but the tiny corr shows no reliable timing.
- **Finding 4 — structural blocker (the honest frontier, consistent w/ ITER14/16):** all
  short-interest sources (FINRA/Finnhub/FTD) begin 2017+, which is AFTER the champion's IS
  weight window (<2017-01-01), so any short sleeve earns relw=0 in the current builder
  (same as CFX4). It cannot raise the champion at the honest fixed-1.6-gross dAnn>0 gate.
- **Verdict:** short-interest data is a legitimate family, but neither it nor the other tested
  decorrelated families clears the adoption gate; champion remains at the honest frontier.
  The FTD series is now on disk and reusable for a future >20yr SI history or a
  cross-sectional equity short-squeeze sleeve once per-stock float/price is assembled.
