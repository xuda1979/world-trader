# TASK 2 — Raw-leaf refreshability audit for the 8 stale sleeves (V7.1 wave-1)

Date: 2026-10-15. Operator frame: V7.1 decay monitor (V71_OOS_DECAY_REPORT.csv as-of
2026-10-15) reports 8/20 monitored sleeves STALE (freshness > 35d). Champion
RAWEW13v2_WEIGHTED_GEAR16 intersects the stale set in ZERO members — this wave is
pure refresh-debt, not an admission event. Champion-of-record CSVs are NOT touched.

## Stale inventory (weight-ordered, exposure from V7.1 weights where present)

| Sleeve | Fresh (d) | Last obs | V7.1 w% | Book |
|---|---|---|---|---|
| C4_construct_v2 | 48 | 2026-08-28 | 17.03 | DECISION_CHAMPION pool (via pools) |
| TREASFUT_intlcarry3_lag1_NEG | 75 | 2026-08-01 | 3.41 | DECISION_CHAMPION |
| A5_r7_credit_composite | 49 | 2026-08-27 | 3.41 | DECISION_CHAMPION (also C4 pool) |
| inter_gasreg_nyh_gulf_L60Z1.0 | 45 | 2026-08-31 | — | DECISION_CHAMPION |
| crack_crack321_nyh_L60Z1.0 | 45 | 2026-08-31 | — | book (EIA family) |
| inter_dieseljet_L60Z1.0 | 45 | 2026-08-31 | — | DECISION_CHAMPION |
| a6_r2_pair_residmom_fm1926 | 45 | 2026-08-31 | — | book |
| D_xlu_ief | 43 | 2026-09-02 | — | book |

Zero HARD entries; zero decay-alarm contamination (decay pair D_xlu_ief/a6_r2
sub-threshold, per 2026-10-15 triage). Classification below is per-sleeve.

## Raw-leaf state on disk (2026-10-15, measured this session)

- `tools/quant/hedge_fund_strats/data_fred/`: wti 09-15, brent 09-15, vix/us2y/us10y/hy_oas 09-21, dxy 09-18
- `tools/quant/data/eia_weekly/`: gasoline_nyh/gasoline_gulf/ulsd_nyh/ulsd_gulf/jet_gulf 09-22, natgas_HH 09-01, crude_prod_weekly 09-11
- `tools/quant/data/more_etf/`: XLU 09-02, IEF 09-04; twelvedata/IEF.csv 09-22 (OHLCV fallback present), XLU absent there
- `tools/quant/data/fx_hist/` (ECB): all pairs 09-07
- `tools/quant/data/ff_factors/`: F-F daily factors last row 20260831
- `tools/quant/data/twelve_big/` panel (298 names): 09-22
- `tools/quant/hedge_fund_strats/data_fred_new/` (A5_r7 leaves DAAA/DBAA/DGS10/DFF): 08-27

## Endpoint probes (all live, read-only, 2026-10-15)

1. **FRED fredgraph.csv** — HTTP 200; DAAA/DBAA/DGS10/DFF current through 2026-10-13
   (DAAA 6.17, DBAA 6.67, DGS10 5.21). FRED_KEY present in .env.local.
2. **ECB eurofxref-hist.zip** — HTTP 200.
3. **EIA dnav hist_xls (KEYLESS)** — all six needed series HTTP 200: RNGWHHDd,
   RBRTEd, EER_EPMRU_PF4_Y35NY_DPGd (gasoline_nyh), EER_EPMRU_PF4_RGC_DPGd
   (gasoline_gulf), EER_EPD2DXL0_PF4_Y35NY_DPGd (ulsd_nyh), EER_EPJK_PF4_RGC_DPGd
   (jet_gulf). Series IDs verified against the spec table in
   `tools/quant/data/eia_weekly/eia_dl.py` lines 44–62 (first probe used wrong IDs
   → 404; corrected). api.eia.gov v2 403s without key but is NOT needed — dnav XLS
   is the canonical keyless path per eia_dl.py.
4. **TwelveData** (real TWELVEDATA_KEY from .env.local) — XLU data through
   2026-10-14; api_usage 3/8 per-minute, 3/800 daily (basic plan; 8 req/min limit).
5. `.env.local` keys available: ALPHAVANTAGE_KEY, FINNHUB_KEY, TWELVEDATA_KEY,
   FRED_KEY, POLYGON_KEY. No EIA key needed (keyless dnav path).

## Per-sleeve classification

ALL 8 REFRESHABLE. None BLOCKED. None requires the fenced BAML/ICE path
(DATA_BAML_REPAIR fence untouched; no sleeve below consumes BAML*).

| Sleeve | Classification | Refresh path | Notes / hazards |
|---|---|---|---|
| A5_r7_credit_composite | REFRESHABLE | FRED fredgraph → `data_fred_new/{DAAA,DBAA,DGS10,DFF}.csv`; re-run a5_r7 builder (a5_r7_lib.py fred_new()) | FRED live to 10-13. Leaves 49d stale. Canonical sleeve at campaign/agents/A5_vol_cond/sleeves/ |
| C4_construct_v2 | REFRESHABLE (derived) | refresh pool members first (esp. A5_r7), then re-run r2lib.py 16-pool EW-of-vt10 | Staleness inherited from pools; 17.03% V7.1 weight = largest stale exposure |
| inter_gasreg_nyh_gulf_L60Z1.0 | REFRESHABLE | eia_dl.py keyless dnav XLS → eia_weekly/; re-run EIA-family engine | dnav endpoints verified live |
| crack_crack321_nyh_L60Z1.0 | REFRESHABLE | same EIA path (needs wti/brent from data_fred + ulsd_nyh) | data_fred wti/brent at 09-15; EIA dnav live |
| inter_dieseljet_L60Z1.0 | REFRESHABLE | same EIA path (ulsd_nyh + jet_gulf) | dnav live |
| D_xlu_ief | REFRESHABLE | TwelveData → more_etf/ (XLU; IEF if beyond fallback); re-run hunt_sector2_r2.py | XLU live to 10-14; 8 req/min budget; fail-closed lint (start<=2007-01-01, max gap<=10d, |ret|>50% on <=3d) |
| a6_r2_pair_residmom_fm1926 | REFRESHABLE (check FF first) | panel twelve_big fresh 09-22; FF daily factors at 20260831 — verify Dartmouth has Sep published before pulling; then a6_r2 builder | harness_shim reads ff_factors; if Sep not yet published, refresh is a no-op extend and sleeve staleness is measurement-window artifact (same class as triage decay-pair note) |
| TREASFUT_intlcarry3_lag1_NEG | REFRESHABLE (monthly-stamped) | IRLTLT01xx FRED inputs extended 2026-06→2026-08 on 09-30; net_intl(lag_m=1) needs next monthly stamp (Sep-2026) | Jun-2026 OECD restatements (CA 3.42→3.388, DE 2.97→2.964) already disclosed and handled on 09-30 |

## Re-emit machinery to reuse (proven pattern)

`campaign/work_backtest_oos/refresh_2026_09_25/reemit_sleeves.py` — canonical-builder
re-run with overlap byte-verify (tol 1e-10 / 1e-12), append-only extend, fail-closed.
Its reemit_report.json precedent: brwt7/a1/rc/fxd1/treasfut all overlap_ok=True.
The 8 now-stale sleeves were NOT in that wave — that is the backlog this ITER62 wave
clears.

## Supersession note

`v7_refresh_audit.json` (2026-09-22) contains ERR leaf-parse entries ("Expected 1
fields in line 3/4") for several of these sleeves — old audit-script parser bug.
This manual audit supersedes it for the 8-sleeve wave-1 set.

## Execution order (task #3, dependency-aware)

1. A5_r7 leaves (FRED) → re-emit A5_r7 sleeve
2. EIA spots (eia_dl.py, keyless) → re-emit inter_gasreg / crack_crack321 / inter_dieseljet
3. TwelveData XLU (+IEF) → re-emit D_xlu_ief
4. FF factors Sep check (Dartmouth) → a6_r2 re-emit if extendable
5. C4_construct_v2 re-emit (pools now fresh)
6. TREASFUT next monthly stamp check (Sep-2026 stamp availability)
7. Re-run V7.1 decay monitor → expect 8→0 stale, exit GREEN
8. Raw-data manifest re-emit/re-pin if raw tree changed (`campaign/scripts/raw_data_manifest.py --emit`; current pin tree sha16 662cc9db40d2d355)
9. Standup log entry
