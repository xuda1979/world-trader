# CHAMP_HUNT_FUND — new decorrelated engine hunt (equity-quality / fundamental-momentum / PIT)

Champion is at the honest frontier (ann 39.50% / SR 3.22 at gross 1.6). To lift it you need a
genuinely NEW decorrelated sleeve with HIGH per-gross IR passing the dAnn>0 gate. The prior screen
that REJECTED the equity-quality family used the model_panel (2016+, restated). Your job: build the
BEST possible cross-sectional equity quality/profitability/fundamental-momentum long-short sleeve
from the data ON DISK, honestly, and measure its per-gross IR and its marginal effect on the champion.

Data: 
- Model panel: alphaportfolio_replication/data/model_panel_full.csv (503 stocks, 2016-08..2026-08,
  has roe/rooa/profitability/b2m/accruals/mom; r_ret1 = CROSS-SECTIONAL RANK of next... VERIFY the
  timing yourself and ONLY use forward returns one month AFTER the signal month — no same-month leak).
- Fundamentals annual: alphaportfolio_replication/data/fundamentals_annual.parquet.
- Price: tools/quant/data/twelve_big + twelve_extend (OHLCV 2006+).

Mandatory honesty (HARD): build signal at month M from data KNOWN by M; earn returns in month M+1
(shift-1, NOT same-month). Measure SR after 6bps/side costs.

Deliverable: the best honest equity-quality LS sleeve (annual SR, halves, corr to CHAMPION daily
book, and the KEY number: champion-overlap ann with 10% of it blended in — must be dAnn>0 to count).
Champion daily: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv.
If it does NOT raise champion ann (dAnn>0), report the exact numbers and REJECT honestly.

Output: FINDINGS.md with the sleeve + blend numbers. Last line: CHAMP_HUNT_FUND DONE
