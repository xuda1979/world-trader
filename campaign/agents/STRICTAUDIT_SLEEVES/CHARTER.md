# STRICTAUDIT_SLEEVES — forensic per-sleeve audit of all 12 STRICTTRADE sub-strategies (read-only)

The STRICTTRADE blend rests on these 12 sleeve CSVs. For EACH, either verify from raw data or FAIL it.
Paths:
  brwt15 agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv (n~6547, 2000+)
  brwt10 agents/COORD/sleeves/brwt10_2000.csv (n~6553, 2000+)
  brwt7  agents/COORD/sleeves/brwt7.csv (n~4566, 2008+)
  brwt5  agents/COORD/sleeves/brwt5.csv (n~4566, 2008+)
  C5ng   agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv (n~7381, 1997+)
  C5ngsum agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv (n~7381, 1997+)
  A5r2   agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv (n~4249, 2009+)
  a6r7   agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv (n~9168, 1990+)
  QAxasts agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv (n~4947, 2006+)
  carryv2 agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv (n~5179, 2006+)
  dualmom agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv (n~4743, 2007+)
  XGB1y  results/sleeve_library/XGB1y_deploy.csv (n~4684, 2008+)

REFERENCE: the older 16-pool audit (agents/AUDIT2_sleeves/FINDINGS.md) PASSed the non-ML
sleeves and FLAGged ML provenance (XGB/H21). AUDIT1/TRUTH_MEMO removed MHX & H21; XGB1y and
dualmom remain. Load each .meta + repro script in scripts/ and agent dirs.

YOUR JOBS (per sleeve, record exact numbers):
1. MECHANICAL SANITY: SR, halves SR, yearly returns (count neg yrs), MaxDD, max single-day
   |return| (flag >20%), lag-1 autocorr, count of interior zero-runs (>=5 consecutive zeros)
   from the CSV alone.
2. ZERO-RUNS: explain EVERY long interior zero-run by the sleeve's design (band gates,
   hysteresis, long-flat, calm filter, hike-cycle veto) OR FAIL it as missing data. Cite the
   exact gate condition + dates. (A5r2's start 2009-09 is the VIX3M data floor; a6r7's 461d
   run is the hike-cycle veto; XGB1y/dualmom have band zero-runs — verify each mechanism.)
3. T+1 DISCIPLINE: find the shift(1)/shift(-1) in each sleeve's repro script. A signal that
   enters PnL on the same bar it is computed = FAIL. Note any same-close conventions.
4. DUPLICATES / REDUNDANCY: brwt5/7/10/15 are 4 variants of the SAME Brent-WTI trade — compute
   their pairwise corr (vt-normalized). Are they 4 independent engines or 1 engine counted 4x
   (33% of the pool)? Same for C5ng vs C5ngsum. A5r2 vs A5r4 (A5r4 was removed as duplicate —
   confirm A5r4 is truly OUT of the 12).
5. PROVENANCE: XGB1y (ML book) — can you reproduce its CSV from committed model code + data,
   or is it a cached/unverifiable artifact like MHX/H21 were? Report corr / max-diff of best
   rebuild, or state UNVERIFIED. dualmom — is its momentum book reproducible from the panel?
6. INSTRUMENT-REALITY cross-check: does each sleeve's trade map to a real tradeable
   (futures/ETF/long-short)? flag natgas spot->futures basis, synthetic bond legs
   (a6r7/QAxasts faithful IEF corr>0.7 per G3), A5r2 VIX-term-structure.

Write campaign/agents/STRICTAUDIT_SLEEVES/FINDINGS.md: per-sleeve verdict table (PASS/FAIL/FLAG
+ reason + numbers) and a pooled-redundancy verdict (how many ECONOMICALLY independent engines
are really in the 12). Last line exactly: STRICTAUDIT_SLEEVES DONE
