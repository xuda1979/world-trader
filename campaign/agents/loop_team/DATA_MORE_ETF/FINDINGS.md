# DATA_MORE_ETF FINDINGS (2026-09-03, iter7)

Task: download MORE free sector/international/commodity daily ETF OHLCV (charter list) into
tools/quant/data/more_etf/. DATA-ONLY, no backtests. Superpowers rigor applied.

## RESULT (verification-before-completion: fresh evidence below)

- 45/46 charter target symbols fetched, linted OK, written to tools/quant/data/more_etf/<SYM>.csv
  (columns date,open,high,low,close,vol; ascending dates; header verified).
- 1 symbol FAILED deterministically: **EID** — TwelveData: "symbol or figi parameter is missing or
  invalid" (retry: same error); Finnhub quote returns all-zeros {'c':0,...,'t':0} = ticker does not
  trade. Nearest plausible real ticker for the intended exposure is EIDO (MSCI Indonesia) — NOT
  fetched (not in charter list); recommend coordinator approve before use.
- 11 charter targets already existed in tools/quant/data/twelvedata/ (XLE,XLB,XLF,XLI,EWA,GLD,HYG,
  IEF,LQD,TLT,AGG) — per charter, NOT overwritten, NOT re-fetched.
- Total new rows on disk: **217,522** across 45 files. Sweep: `ALL 45 LINT PASS, total rows=217522`.
- Span coverage: 2000-06-23 (EWT) .. 2026-09-02 (all). API outputsize=5000 cap → most series start
  2006-10-17. Inherently short series (fund inception, verified against rows): XLC 2018-06-19
  (2063 rows), XLRE 2015-10-08 (2741), INDA 2012-02-03 (3666), GDXJ 2009-11-10 (4228),
  DBC/GSG 2008-01-02 (4699/4697), EEM 2008-01-02 (4697, see dedup below), JNK 2007-12-04 (4716),
  EMB 2007-12-19 (4705), BIL 2007-05-30 (4847), UNG 2007-04-18 (4876).
- max_gap_days: 5 (weekends) for all US-traded; EWT = 7 (Lunar New Year exchange closure — plausible);
  XLC/XLRE = 4. zero_ret_rows: highest BIL 1823/4847 (37.6% — T-bill price stability, plausible),
  SHY 442/5000 (8.8% — short-duration, plausible); all equity ETFs 13-151.
- manifest.csv: 46 rows (45 OK*, 1 FAIL EID); re-verified against on-disk files:
  `manifest-vs-disk mismatches among 45 files: NONE`.
- Writes contained: `git status --porcelain tools/quant/data/` outside more_etf = **0 paths**.

## TDD evidence (failing-test-first)

- RED: test_datalint.py (10 tests) run BEFORE implementation → `ModuleNotFoundError: No module named
  'datalint'` (collection interrupted). Screenshot in transcript; gate existed only after.
- GREEN: datalint.py implemented → `10 passed in 0.02s`.
- Fail-closed properties tested: bad header, descending dates, duplicate dates, non-positive close,
  NaN close, high<low, <2 rows, zero-return counting, manifest row shape.
- Later added missing-file guard (EID absent crashed consistency check) — guard verified to raise
  `tools/quant/data/more_etf/EID.csv: file not found`; full suite re-run `10 passed` (no regression).

## BUGS FOUND + ROOT CAUSES (systematic-debugging)

1. **TwelveData dual-vendor duplicate rows for EEM/EWT** (LINTFAIL at fetch time — gate caught it):
   - Symptom: EEM.csv, EWT.csv rejected "dates not strictly ascending at 2012-10-12->2012-10-12".
   - Root cause: API returns TWO interleaved vendor feeds over 2012-10-12..2021-11-05: EEM raw
     5000 rows / 3492 unique dates / 1508 dup dates; EWT identical shape (5000/3492/1508).
     Pairs are same-OHLC for EWT (1508/1508 identical); EEM differs in volume low digits
     (35969600 vs 35969528) and 163/1508 opens differ 0.5c (41.35000 vs 41.34500).
     Duplication is systemic, not pagination-induced: pre-2012 window also has 106 dup dates
     (e.g. 2012-05-11 close 39.96500 vs 39.97000 — genuinely different vendor closes).
   - Fix: deterministic keep-first-occurrence per date; re-fetch BOTH windows fresh
     (end_date=2012-10-11 + full), dedup each, combine, lint BEFORE atomic os.replace.
   - Result: EEM 1205(−106)+3492(−1508)=4697 rows 2008-01-02..2026-09-02 maxgap=5 zret=33;
     EWT 3095(−106)+3492(−1508)=6587 rows 2000-06-23..2026-09-02 maxgap=7 zret=151.
     EEM pre-2008 history not obtainable within 5000-row cap under duplication (dup density
     consumed budget) — documented limitation, manifest status OK+EXTEND.
   - Process bug also found & fixed: first extend attempt wrote before linting and crashed mid-run,
     leaving corrupt on-disk EEM.csv (106 non-ascending pairs measured) which a naive rebuild then
     ingested (KeyError). Final rebuild fetches fresh, lints tmp, atomic-replaces — intermediate
     states never trusted.
2. **Charter internal duplicates** (minor): XLV, TIP, SLV listed twice in charter groups; SLV was
   both "sector" and "commodity" target. Deduped before fetching (46 unique TODO).

## INDEPENDENT CROSS-VALIDATION (Finnhub, same-day 2026-09-03)

5-symbol spot sample, TwelveData last-row close vs Finnhub live quote — ALL MATCH exactly:
XLK 183.60==183.6 | SMH 550.48==550.48 | EEM 67.15==67.15 | DBC 31.93==31.93 | SHY 81.64==81.64.
Plausibility multiples (2006-10-17-ish → 2026-09-02 close): XLK 16.24x, XLY 6.30x, XLU 2.45x,
GDX 2.73x, EWT 2.82x — consistent with known asset-class histories (tech >> utilities/gold miners).
Raw API ordering verified DESCENDING empirically (desc_raw=True on all 46) before reversing —
charter note confirmed by observation, not assumed.

## RATE LIMITS / SAFETY

~55 TwelveData calls total (46 batch + 2 EID retries + 5 EEM/EWT window calls + 2 idle),
sleep(8)s between every call, one 429-backoff path armed (never triggered — 0 HTTP 429s observed).
6 Finnhub calls (5 spot-checks + 1 EID lookup). Well under 800/day free cap.

## NEW COVERAGE ENABLED (for future engines — NOT backtested here per charter)

18 sector/industry ETFs (XLK,XLY,XLP,XLU,XLV,XLRE,XLC,KBE,KRE,ITB,XHB,SMH,IGV,XOP,XME,GDX,GDXJ,SLV —
incl. the 7 previously-absent SPDRs XLK/XLY/XLP/XLU/XLV/XLRE/XLC), 17 international single-country/broad
(EEM,VWO,EFA,EWJ,EWG,EWU,EWP,EWL,EWT,EWY,EWZ,EWW,FXI,INDA,EWK,EWS), commodities/rates/credit
(USO,UNG,SHY,JNK,TIP,VNQ,EMB,BIL,IAU,DBC,GSG,GDX,GDXJ,SLV). All series END 2026-09-02 —
immediately joinable with existing champion data ending 2026-08-12.
