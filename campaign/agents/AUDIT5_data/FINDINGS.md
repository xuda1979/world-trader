# AUDIT5_data — FINDINGS (read-only data-layer audit, 2026-09-01)
Auditor: AUDIT5_data. Scope: campaign/agents/AUDIT5_data/CHARTER.md items 1-5.
All numbers below were computed fresh from files on disk this session. Nothing was modified.

---

## ITEM 1 — SURVIVORSHIP of tools/quant/data/twelvedata / twelve_big panel

### Panel facts (measured)
- twelve_big: 298 CSVs, 2006-09-26..2026-08-12, 5006 rows, ~5000 obs/name. harness/data.py PANEL.
- twelve_extend: 440 files but starts only 2026-08-14 (NOT usable history; misleading dir name).
- 237/298 names already have data on the first date (2006-09-26) — assembled from currently-listed
  names in 2026 => static survivor panel. harness docstring itself calls closes() "adjusted proxy close".
- Panel contains SPY, QQQ, XLF (ETFs), and BOTH GOOG and GOOGL share classes (corr 0.9968).
- Panel close = SPLIT-adjusted only, NOT dividend-adjusted: AAPL 2006-09-26 close 2.7718 =
  77.01/(7*4) exact; price-only CAGR 26.6% vs known ~23% total-return CAGR.

### Quantified bias: panel EW (daily rebal, >=20 concurrent names) vs benchmarks
FF VW market (Mkt-RF+RF, total return):
- Full 2006-09-26..2026-06-30: panel EW ann **14.05%** vs FF mkt **11.36%** => gap **+2.68pp/yr (1.24x)**.
- Net of ~2pp/yr missing dividends (price-only panel), the underlying total-return survivorship
  gap is roughly **+4 to +5pp/yr** — the headline +2.68pp is a LOWER bound.
- Annual gaps (pp): 2007 +7.8, 2008 +6.9, 2009 +13.5, 2010 +5.1, 2011 +3.5, 2012 +1.1,
  2013 +0.9, 2014 +5.4, 2015 +1.3, 2016 +3.4, 2017 +3.7, 2018 +2.5, 2019 +1.0, 2020 +0.1,
  2021 +5.4, 2022 +7.3, 2023 **-5.5**, 2024 **-11.3**, 2025 **-4.9**, 2026 -0.2.
- vs FRED SPX price index (overlap 2016-08..2026-08): panel EW 15.72% vs SPX 13.49% = +2.24pp/yr.
- Annual-rebalance settled-universe variant (>=250d history at formation): panel EW 7.82% vs
  FF mkt 11.20% = **-3.38pp/yr** — the sign FLIPS when returns of late-added names are excluded,
  because names added later (COIN, HOOD, etc.) carry huge post-IPO runs that daily-EW of a
  static list catches but a settled 2006 universe cannot. Bias is regime-dependent, not constant.
- FF SMB over the window is -0.31pp/yr annualized, so the gap is NOT an EW-tilt artifact.

### Which champion sleeves depend on the panel (verified by reading builder code)
- V4 pool (20 sleeves): H21_f5, H21_br (bigmove/pipeline_common.load_ohlcv -> twelve_big,
  BLOCKLIST 6 names), MHX (xgb_multi_horizon.py -> twelve_big 285-name frame), XGB1y
  (bigmove/union_panel.load_union: twelve_big>twelvedata>twelve_liq>polygon ~660 names,
  ETFs excluded), dualmom (A3 r6lib uses harness closes()).
  => 5/20 slots, mean |contribution| share **33.0%** of the vt10 blend.
- QAxasts: FRED-only legs (wti_full, xau, synth 10y, dxy, VIXCLS) — NOT panel equities
  (verified r7_idea5_breadth.py); only its calendar comes from the panel index.
- A1inf/carryv2 (E1 versions): FRED + twelvedata/GLD (ETF 2006-09+, survivorship-free asset).
- a6r7/A1credit/A5r2/r4/r7 (FRED rates/credit/VIX), brwt/brwt5/7/10 (FRED wti_full/brent),
  B3momhml (Ken French FF daily factors), C5ng/C5ngsum (FRED DHHNGSP) — panel-free.
- Campaign self-awareness: A3 FINDINGS r1, COORD FINDINGS, B3 FINDINGS explicitly label the
  panel survivorship-biased and rejected xs quality/lowvol factors for that reason. But no
  champion doc quantifies the residual bias on the two panel sleeves that WERE saved
  (dualmom, XGB books). UNVERIFIED: whether the XGB books' SR would survive a PIT universe;
  the books trade L/S top/bottom deciles of a survivor panel, so both legs are tilted to
  winners and their edge is optimistic to an unquantified degree.

### Data-corruption findings in the panel (NEW, not disclosed anywhere in campaign docs)
1. **Corrupt Sunday row 2009-07-26**: exactly one row dated Sunday with a single non-NaN value,
   CVS close 84.09 (true 2009-07-24 close was 34.38; next day 34.05). It is in harness closes()
   and in the A2 r6_lib O/C pickles. Consequences:
   - pct_change() gives CVS +144.6% on 2009-07-26 (Sun) and -59.5% on 2009-07-27, and NaN for
     every other name on 07-27 (row gap) => naive panel EW books -59.5% on 07-27.
   - All-name-EW on 07-26 books +144.6%; overnight ON=Ew(O.shift(-1)/C-1) books +144.6% on
     07-24 and -59.2% on 07-26 (A2 overnight experiments; A2 sleeve NOT in champion).
   - Champion impact is bounded: no champion-pool sleeve books more than ±0.6% on 07-26/27.
     BUT the champion calendar itself inherits the Sunday row: XGB1y_deploy.csv has a
     2009-07-26 row (monthly return spread on the panel calendar), so
     **GOAL100_CHAMPION_V4_BALANCED_daily.csv contains a Sunday-dated +0.276% return**.
     Removing it changes ann 70.1->70.1%, SR 6.25->6.25, MDD -6.4%->-6.4% (immaterial to
     stats, but a live calendar cannot trade Sunday; the build must reindex to bdays).
2. **Ticker-continuity phantom jumps (stitched, unadjusted)**: GM +78.5% on 2010-11-18
   (old-GM $0.49 -> new-GM IPO $34.19 in one series), KDP +82.1% on 2018-07-10 (pre-merger
   Keurig 123.66 -> post 22.19), CVS 2009-07-26 (above). Panel-wide |move|>30% days: 141
   (2008:34, 2009:34, 2020:17...), worst offenders GM(14), AIG(11), C(5), THC(5), UAL(5).
   Sleeve hits found: library EMN.csv books -5.04% on 2018-07-10, h1_book_daily -4.26%
   (neither in champion pool); AP_gold.csv +28.1% on 2010-11-18 is from a different cause
   (xau stitch; also not in champion pool). Champion-level phantom exposure on those dates
   is negligible (V4 BALANCED +0.04% on 2018-07-10).
3. **Single-name bad print**: CMCSA 2024-08-13 twelve_big close 36.6635 vs polygon 39.12
   (ratio snaps back to 1.0 next day). Isolated; only 2/516 overlap days diverge >1%.
4. Cross-source OHLCV consistency (item 5) is otherwise EXCELLENT — see item 5.

## ITEM 2 — FRED series revisions / unit discontinuities

### Two snapshots on disk (data_fred fetched 2026-08-12, data_fred_new 2026-08-31) overlap on
DEXJPUS, DEXUSEU, DGS1, DGS10, DGS2, DGS30, DTWEXBGS, VIXCLS: **ZERO mismatches** on every
overlapping row (exact float compare, tolerance 1e-9 relative). No silent rebases found.
Also zero mismatch: DHHNGSP (natgas.csv data_fred vs newdata vs A3 r7_data copy — md5 identical),
wti.csv vs wti_full.csv overlap, brent.csv vs DCOILBRENTEU.csv overlap.

### DGS2 (1976-06-01..2026-08-27, both copies identical on 1990+ overlap): 35 days with |Δ|>20%.
All are real market moves at near-zero yield levels, no unit change: 2008-09-15 2.23->1.78
(Lehman), 2008-11-24 1.09->1.31, 2009-03-18 0.82 (-21.9%, QE1 day), 2011-08-09 0.19, 2020
COVID cluster (0.86->0.38 etc.), 2021-02-25 0.17 (+41.7%). Percent moves inflate mechanically
as yields ->0 (2021: 0.09->0.11 = +22%). **No data integrity problem.** Min 0.09 (2021-02-05),
zero negative prints.

### DHHNGSP (1997-01-07..2026-08-25): 70 days |Δ|>20%. Verified real: Feb-2021 Uri freeze
(3.76->23.86->8.56), 2003-02 cold snap (6.73->18.48), Jan-2026 cold snap (4.96->30.72 on
2026-01-23, then -68.5%), 2018-01/2019-03/2021-02 events. **No unit changes.**

### DCOILBRENTEU: 8 days |Δ|>20%, all Gulf-War-1 (1991-01-17 30.28->21.10) or COVID Apr-2020
(-24.7% 2020-03-09, +47.5% 2020-04-22...). wti_full: 15 days incl the real negative print
-36.98 on 2020-04-20 (not a data error; it is the actual front-month settlement; campaign
sleeves treat Apr-2020 WTI prints as unpriceable in carryv2 and B3 rejected oil momentum
for this reason). **No unit changes.**

## ITEM 3 — Ken French formation dates / PIT
- Champion uses KF data ONLY via B3momhml = F-F_Research_Data_Factors_daily + Momentum factor
  daily files (verified: campaign/scripts/B3_momhml_composite_ref.py). These are contemporaneous
  daily RETURN series of published portfolios, not formation-date constructs; B3 computes
  pos=sign(mom+0.2*hml) and earns pos.shift(1)*ret => T+1, PIT. No June-formation leakage
  applies. File vintage: "created using the 202606 CRSP database" — factors through 2026-06-30;
  the champion series ends 2026-08-28, so Jul-Aug 2026 rows in B3momhml are NaN->0 padded
  (B3 contribution is 1/20 weight, no lookahead, but the sleeve is STALE in the final 2 months).
- The KF 10_Portfolios_Prior_12_2 / 48-49 industry files on disk are used only by C1 scripts
  whose sleeves are NOT in any champion pool. Daily-constructed momentum (PRIOR_RET -250/-21)
  and industry files carry formation inside the published return; T+1 usage (c1_lib bt():
  pos.shift(1)) is PIT-correct.
- Caveat already disclosed by campaign: FF factor returns are paper portfolios (tradeability,
  capacity) — correct and acknowledged in GOAL100_CHAMPION.md 8.2/9.2.

## ITEM 4 — DHHNGSP print stamping (could a 'Wednesday close' contain Thursday info?)
- FRED documentation notes are NOT on disk anywhere in the repo (no cached docs; only raw
  fredgraph.csv downloads). I could not access the network. => **FRED's official stamping
  convention: UNVERIFIED from primary documentation.** What I can verify empirically:
  - Print dates Mon-Fri only, ~1/day, holiday-skips present (e.g. no 2023-11-23 print),
    Fri->Mon gaps 1331, larger weekend gaps rare (52). No weekend prints.
  - EIA Henry Hub spot assessments for trade-day T are conventionally published the following
    morning (this convention is what A1's own findings state for EIA daily prints: "EIA daily
    prints publish next morning" — campaign/agents/A1_trend_cta/FINDINGS.md:161). If that
    holds for DHHNGSP, a print stamped date T is UNKNOWN until T+1 morning.
  - The C5ng sleeve's weekday signal itself is calendar-only (needs no price print), but its
    calm filter uses lr_t = log(S_t/S_{t-1}) at decision time t; under next-morning publication
    that filter uses one not-yet-published value. Severity test (I re-ran the exact sleeve
    engine with an extra 1-day information lag): SR drops 1.74 (lag0) -> 0.25 (lag1) -> -0.85
    (lag2). Same collapse for the unfiltered variant: 1.56 -> 0.16 -> -0.85.
  - READ CAREFULLY: this does NOT mean the sleeve is lookahead — T+1 execution (gr=pos*lr.shift(-1))
    books the t->t+1 return, which under next-morning publication is still partly
    unknowable at decision time t. The honest live convention is position set AFTER the T+1
    morning print, earning T+1->T+2; that is lag1 in my test = **SR 0.25, i.e. ~85% of the
    sleeve's published edge vanishes under a 1-day publication-lag convention**. The campaign
    applied this exact lag reasoning to the crude-brent spread member of carryv2 (A1 FINDINGS:
    zero-lag SR 1.71 "books the pre-publication move"; honest lag-2 SR 0.41 — and carryv2 SAVED
    the 0.41 version) but did NOT apply it to C5ng/C5ngsum when admitting them to the champion
    pool. This is the single most material data-timing risk I found. C5ng+C5ngsum = 2/20 slots;
    coordinator's own drop-one shows C5ng -1.1pp ann at champion level. If both natgas sleeves
    collapse to ~0.25 SR-equivalent post-lag, champion ann loss is roughly 1-2pp and its
    decorrelation benefit shrinks. Needs a PIT-rebuild verdict (position at T+1 close after
    print publication) before live use.
  - Counter-evidence to publication-lag collapse: the raw weekday anomaly measured on
    stamp-to-stamp returns (Fri +91.8bp, Thu -115.7bp, Wed -47.0bp mean t->next) is a real
    property of the published series; the question is only at which clock-time the trader can
    act. UNVERIFIED: exact EIA publication time (network access unavailable).

## ITEM 5 — twelve panel OHLCV cross-check (10 random names vs other sources on disk)
Random 10 (seed 5, restricted to multi-source names): XLF, JPM, NKE, TGT, ADBE, SBUX, JNJ,
AMGN, DHR, CMCSA.
- vs twelve_liq (123 shared names): n=5000 overlapping days each; mean |relative diff| 0.000%,
  0 days >1% diff, return corr 1.000000 (min 0.999991 DHR).
- vs twelvedata (82 shared): same result, corr 0.999991-1.000000, 0.000% mean diff, 0 days >1%.
- vs polygon (82 shared, 2024-07-22+): 9/10 names identical to the 4th decimal (corr 1.000000);
  CMCSA: mean diff 4.25% driven ENTIRELY by the single 2024-08-13 print (36.6635 vs 39.12);
  the other 515 days match (2/516 return days >1%).
- Plus 10 more random names (seed 7): 0 OHLC internal-consistency violations (high>=max(o,c,l),
  low<=min(o,c,h)), 0 nonpositive prices, 0 date regressions, 0 weekend rows (each name's own
  file is clean; the ONE Sunday row in the merged panel comes from CVS's file).
- twelvedata dir: 101 files — this is an OLDER small panel; twelve_big (298) supersedes it.
- twelve_extend: 440 files but ALL rows 2026-08-14..2026-08-17 only — it contains NO history
  despite harness/data.py's comment "440 names (newer listing coverage)". Any code calling
  D.closes(extended=True) gets a 4-day stub. No champion sleeve does (verified: loaders above
  use PANEL or union of big/liq/polygon), but this is a live landmine.

## VERDICT SUMMARY
| Item | Verdict |
|---|---|
| 1 Survivorship | CONFIRMED, +2.68pp/yr naive-EW price-only vs FF TR (+4-5pp/yr div-adjusted est.), regime-dependent (negative 2023-25); 5/20 V4 slots (33% of vt10 contribution) exposed; XGB books' SR optimistic by unquantified amount — UNVERIFIED under PIT universe |
| 1b Panel corruption | CVS Sunday row (in champion calendar, benign to stats), GM/KDP stitch jumps (not in champion), CMCSA 2024-08-13 bad print |
| 2 FRED revisions | CLEAN — two independent snapshots bit-identical on overlap; all >20% moves are documented market events (Uri 2021, COVID 2020, Lehman 2008, Gulf War 1991, Jan-2026 cold snap) |
| 3 KF PIT | CLEAN for champion (FF factors, T+1); B3momhml stale after 2026-06-30 (FF vintage), zero-padded |
| 4 DHHNGSP stamp | **UNVERIFIED from FRED docs** (not on disk, no network). Empirically the saved C5ng edge collapses 1.74 -> 0.25 SR under a 1-day publication-lag convention; carryv2's oil member was de-risked this way but C5ng was NOT. Flag for PIT rebuild. |
| 5 OHLCV cross-check | CLEAN — 10 names vs 3 other sources: 0.000% mean diff, corr 1.000000, 1 isolated bad print (CMCSA 2024-08-13) |
| — twelve_extend | BROKEN/EMPTY (4 days only) — correct the harness comment or remove |

AUDIT DONE
