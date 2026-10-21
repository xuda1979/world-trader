# HUNT_FF2 — stat-arb / factor timing on Fama-French factor data (iter 5; prior slot died on server error)
Prior HUNT_FF_STRATARB died immediately (API server error, no work done). Do it now.

DATA (verify on disk): download_factors.py exists at repo root; check tools/ or data/ for
ff_factors (CSV/parquet: MKT, SMB, HML, RMW, CMA, momentum UMD). alphaportfolio_replication/
has fundamentals_annual.parquet + factor portfolios (HUNT_FUNDAMENTAL used OP/INV: their
finding = value/growth/profitability screens have ~zero-to-negative predictive power PIT;
momentum redundant with dualmom). READ campaign/agents/loop_team/HUNT_FUNDAMENTAL/FINDINGS.md
FIRST to avoid re-running dead ideas.

UNCHARTED angles (target: SR>=1, corr<0.1 to campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv):
- Factor MOMENTUM/timing on daily-tracked factor proxies IF daily factor data exists (FF factors
  are monthly — if only monthly, DAILY-IZE FORBIDDEN; you may only use daily price series on disk)
- Volatility-managed factor tilts (Moreira-Muir) using VIX gating on the daily equity sleeve panel
- Cross-sectional factor z-spreads from the twelve_big panel (quality-minus-junk daily proxy,
  betting-against-beta daily proxy: BAB = low-vol minus high-vol decile portfolios you build
  YOURSELF from twelve_big prices — daily, real, T+1)
- Time-series momentum on the factor-tilt ETF proxies in twelve_big (MTUM, QUAL, VLUE, USMV if present)
Gates (full): SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each >-5%, 200x 10d-BLOCK position-lag
scramble p<0.05 (position-lag = circular shift of the position series, NOT return permutation —
the literal permutation test is proven vacuous), |corr|<0.15 to the V2 champion, ac1<0.5,
uniqR>=0.08, T+1, 6bps/side, borrow 0.5%/yr.
Deliver sleeves/ + FINDINGS.md with exact stats + explicit PASS/FAIL per gate.
Last line of FINDINGS.md must be exactly: HUNT_FF2 DONE
