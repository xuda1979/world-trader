# STRICTAUDIT_CONSTRUCTION — adversarial rebuild of the 12-sleeve STRICTTRADE blend (read-only)

TARGET: campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv (12 instrument-real sleeves,
  49.4% ann, SR 5.24, MaxDD -6.1%). It is built from THESE 12 sleeve CSVs (net-of-6bps already
  embedded inside each sleeve file):
    brwt15  agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv
    brwt10  agents/COORD/sleeves/brwt10_2000.csv
    brwt7   agents/COORD/sleeves/brwt7.csv
    brwt5   agents/COORD/sleeves/brwt5.csv
    C5ng    agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv
    C5ngsum agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv
    A5r2    agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv
    a6r7    agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv
    QAxasts agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv
    carryv2 agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv
    dualmom agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv
    XGB1y   results/sleeve_library/XGB1y_deploy.csv

DOCUMENTED CONSTRUCTION (from GOAL100_TRUTH_MEMO.md §16 and FINAL_REPORT):
  per-sleeve vt10 (60d trailing vol shift(1), cap 8x) -> plain EW -> global vt -> 126d
  DD-throttle (shift(1), cut to 50% or FT) -> instrument-real costs (futures 1.5-5bps,
  equity L/S 15bps) + stock borrow fees (50bp generic, 20% of shorts HTB at 300bp) -> NYSE
  calendar only (holiday returns accumulated into next trading day). Short-proceeds rebate
  EXCLUDED. Implied gross ~1.4x (mean), max ~4.4x.

YOUR JOBS (adversarial; find the bugs):
1. REPRODUCIBILITY GAP: There is a canonical builder for the OLD 16-pool champion
   (campaign/scripts/champion_build.py) but NOT for the 12-sleeve STRICTTRADE with
   borrow-fees & instrument costs. HUNT for any committed script that builds the STRICTTRADE
   CSV (grep scripts/, agents/). If none exists, STATE IT as a finding: the headline file is
   NOT byte-reproducible from committed artifacts. Try to reconstruct it; report the max
   corr / max|daily diff| you can achieve vs the committed CSV able to.
2. REBUILD ATTEMPT: implement the documented pipeline yourself (vt -> EW -> global vt ->
   throttle -> costs+borrow). Construct the BALANCED variant and compare to the committed
   CSV: corr, mean|diff|, max|diff|, ann/SR/DD. Where does it diverge? Classify each
   divergence (borrow fees? NYSE reindexing? cost double-count? throttle params?).
3. NO-LOOKAHEAD audit of YOUR OWN reconstruction code: confirm rolling(60).std().shift(1),
   throttle uses trailing peak shift(1), no same-day signal use anywhere.
4. HIDDEN-LEVERAGE: compute the implied gross/exposure path (sum of per-sleeve |vt scale|/12
   and post-throttle). Report mean/max. Does "no leverage / weights sum 1" hold in the
   normalized-accounting sense and the real-capital sense? Quantify financing if charged on
   gross>1x (T-bill +25bp) — how much does ann change?
5. COST DOUBLE-COUNT: the sleeves already embed 6bps; the STRICT layer adds instrument costs
   (1.5-15bps) + borrow. Are these additive (correct) or does the 6bps get counted twice?
   Audit whether the committed CSV reflects gross sleeves minus borrow minus instr costs, or
   net-of-6bps minus MORE costs (over-charging) or minus nothing (under-charging).

Write campaign/agents/STRICTAUDIT_CONSTRUCTION/FINDINGS.md with exact numbers and a final
VERDICT: REPRODUCIBLE / NOT-REPRODUCIBLE + the corrected ann/SR/DD if your reconstruction
differs. Last line exactly: STRICTAUDIT_CONSTRUCTION DONE
