# BLOTTER_TESTER — FINDINGS (iter 6, 2026-09-03)

Tester: BLOTTER_TESTER (adversarial, read-only). Artifacts tested:
- `campaign/scripts/blotter.py` (emitter) → `campaign/results/BLOTTER_HONEST14V3_BALANCED.csv` (61,194 records, 2006-12-29→2026-08-27)
- Champion `GOAL100_HONEST14V3_BALANCED_daily.csv` (5,086 rows, 2006-10-02→2026-08-27) + frozen builder `honest13_build.py`
- Standard: `campaign/TRADE_RECORD_STANDARD.md`

**Baseline integrity (pre-check):** `honest13_build.py --verify-v3` reproduces all 3 committed champion CSVs at max|diff| **9.988e-17** (BALANCED/SAFE/AGGRESSIVE). My independent 2-book rebuild confirms BALANCED=(SAFE+AGG)/2 to **9.988e-17**. Current blotter.py regenerates the delivered CSV **byte-exact**: max|diff| = **0.0** on qty_notional/weight_from/weight_to/price, 0 price_source mismatches. Ledger hygiene: 0 weekend trades, 0 duplicate (date,sleeve) rows, 0 zero/negative qty (min 1.19e-8), BUY 31,232 / SELL 29,962. The 60 champion days before the first ledger trade carry **0.0000x** reb turnover (no missing warmup trades).

⚠️ PROVENANCE NOTE: blotter.py mtime (10:23) postdates the CSV (10:17) and the file was edited during my session (my first read showed the pre-fix `_synth_px`; current file has `_recover_v0`). The final committed code reproduces the artifact exactly (verified 0.0), so provenance holds NOW — but the artifact was emitted by a working tree in flux.

---

## PER-CHECK VERDICTS

### A) RECONCILIATION — PARTIAL PASS (exact vs AGG book; FAIL vs the BALANCED champion it is named after)
- Per-sleeve ledger Σ|qty_notional| vs AGG position-path |diff()|: **EXACT, all 14 sleeves, max rel diff 5.877e-4 ppm** (e.g. brwt15 67.606116 = 67.606116; dualmom 73.890976 = 73.890976).
- Totals: ledger **716.6999x** = AGG path **716.6999x** (ratio 1.000000). SAFE path 484.8517x. **BALANCED champion actually charges 600.7758x** → ledger covers **119.30%** of the champion's charged reb turnover. Root cause: `blotter.position_path()` hardcodes `TGT=0.091, THR=0.03` = the AGGRESSIVE book only.
- **6.0-vs-6.4bps gap (quantified):** builder charges 6.0bps on reb turnover of 600.78x = 36.05% NAV = **1.7860%/yr**; at 6.4bps it would be 38.45% NAV = 1.9051%/yr → **gap = 11.91 bps/yr of NAV = 0.1191%/yr** (mean one-side turnover 29.77x/yr × 0.4bp). Champion ann(geo, 2008+): **43.6122% → 43.4410%, delta −0.1711 pp**. The ledger stamps `cost_bps=6.4` on every record while the PnL charged 6.0 — mislabeled cost.
- Ledger omits 2 charged turnover streams entirely (see B): overlay-vt `tw` 293.37x (0.872%/yr) and throttle `dsc` 8.75x (0.026%/yr).

### B) PNL REPRO — FAIL from the ledger alone (PASS only via builder internals)
- Full-model rebuild (both books, all 4 cost terms): n=5,086, max|diff| vs committed = **9.988e-17**. PASS.
- Ledger-based reconstruction: ledger-as-cost charges **45.87% NAV (2.273%/yr)** vs champion's actual **60.52% NAV (2.999%/yr)** → net gap **−14.65% NAV = −0.726%/yr** (ann 42.6361% vs 43.1279%, −0.4917 pp over full window; daily max|diff| **1.181e-3**, 5,024/5,086 days differ). **WHY (3 components):**
  1. Ledger is AGG-only (overcharges reb by +19.29%: 716.70x vs 600.78x);
  2. **tw (overlay per-sleeve vt turnover) 293.37x = 17.60% NAV (0.872%/yr) has NO trade records**;
  3. **dsc (throttle switching) 8.75x = 0.52% NAV + borrow 6.35% NAV have NO records.**
- The standard's gate #2 ("ledger PnL reproduces champion byte-for-byte") is satisfied only via the builder's internal path, NOT by the delivered ledger. The ledger is not a complete cost record.

### C) LOOKAHEAD — PASS on signals (T+1 verified); MINOR exec-price convention flaw
- Extra-lag probe: recomputing the global vt scale with same-day vol changes the position path on **5,026/9,293 days** (max weight diff 6.2442) → committed path is the lagged one; `gb` uses `rolling(60).std().shift(1)`, throttle uses `eq.shift(1)`. **No same-day signal leak.**
- BUT ledger stamps the **date-t close** as execution price (verified: A5r2 2009-12-16/17/18 ledger px 111.52/110.18/110.21 = SPY close at t, diff 0.000 bps vs t) while the position earns the day-t return; the standard itself says "execution price is the close of t-1". |t-close − (t-1)-close| on A5r2: mean **72.27 bps**, p95 **212.50**, max **1,094.24**. Attribution-level inconsistency (not a signal leak, not a PnL error), but the `price` column is not the executable price for the claimed PnL day.
- 140 records on **96 distinct US federal holidays** (CFX4 71 SYNTH, FF2 39 SYNTH, diescrack 30 REAL) vs the pool's holiday-flat convention; champion holiday-row PnL share −0.67%, holiday notional share 0.025% — small, disclosed rows-kept convention, but should be flagged per-record.

### D) PRICE SANITY — carryv2 189,832 bug CONFIRMED and EXPLAINED; residual labeling defects
- REAL share: **45,607/61,194 = 74.53%** REAL; 15,587 (25.47%) SYNTH. Honest REAL/SYNTH tagging.
- **The 189,832 bug — CONFIRMED, mechanism proven to the digit:** pre-fix `_synth_px` compounded `1+Sd` where **Sd holds vol-target SCALES** (`s=tgt/vol`, cap 8, carryv2 mean **1.413862**), not returns: `(1+1.4139…)cumprod×100 = 189,832.7 EXACTLY at the first ledger date 2006-12-29` (and →inf later; verified overflow). Current code uses V0 (vol-targeted RETURN); delivered carryv2 prices are finite SYNTH 96.47–752.76 (0 REAL records). Fix verified in delivered artifact.
- **Residual defects:**
  - carryv2 can never print REAL: `GLD` is **not in the harness panel** (298 tickers; extended 440 — no GLD). A real gold series EXISTS on disk: `tools/quant/hedge_fund_strats/data_fred/xau.csv` (5,000 rows, 2007-12-21→2026-08-13, 810.80→4,367.22). Labeling a 752.76 synth value "GLD (gold carry)" misleads (spot gold ≈ 4,367 in 2026; synth ≠ GLD price even in 2010 terms).
  - a6r7/QAxasts: prices 0.09–5.19 / 0.52–5.26 are **DGS2/DGS10 YIELDS (%), not futures prices**, yet instrument says "US 2Y/10Y TREASURY FUT" (ZT/ZN ≈ 110). Wrong scale for the named instrument.
  - brwt* "BRENT/WTI FUT SPREAD" priced at the **Brent spot leg only** ($13.77–143.95, `transact_price` uses src[0]); the spread price is never shown. C5ng priced at Henry Hub spot (1.21–30.72) not FUT. A5r2 SPY close 102.20–773.26 is genuinely REAL and plausible.
- Verdict: no implausible values remain in the CSV, but 4 sleeves carry proxy prices on the wrong instrument/scale under a REAL tag.

### E) COST & BORROW — FAIL: borrow absent; cost_bps mislabeled
- **Borrow: ABSENT from the ledger** (no borrow-like column; confirmed by column scan). Charged in PnL: **6.349% NAV over 20.2y = 0.3146%/yr** — dualmom 1.852% NAV (0.0917%/yr), C5ngsum 1.008% (0.0499%/yr), brwt15 0.625% (0.0310%/yr), brwt10 0.590%, brwt5 0.590%, brwt7 0.575%, C5ng 0.439%, carryv2 0.368%, QAxasts 0.302%.
- `cost_bps` = 6.4 on all 61,194 records vs 6.0 charged (gap quantified in A). **Recommend: add `borrow_charge` column + correct cost_bps + records for tw/dsc turnover.**

### F) SPARSE-GAP skipna UNDERCHARGE — CONFIRMED and reproduced exactly
- AGG book: charged (skipna) **716.7x** vs held-across **746.4x** (**+4.1%** — the coordinator's "~4%"/"716.7 vs ~746" verified). Flat-across bound: 1,732.8x.
- BALANCED champion: charged **600.8x = 1.7860%/yr**; honest alternatives: all-held 625.0x (1.8581%/yr), all-flat 1,506.0x (4.4772%/yr), **per-instrument-convention HYBRID (futures held + equity flat) 764.3x = 2.2722%/yr**.
- **Undercharge vs hybrid = 9.81% NAV total = 0.4861%/yr** (~27% of reb cost; ~0.49pp off the 43.6% headline if fixed). Strict equity-flat-only miss (A5r2+dualmom, both books): 327.1x = 19.62% NAV = 0.9723%/yr gross of the futures-held credit. Per-sleeve gap-days: CFX4 80.6% NaN days but trivial turnover (0.09x); a6r7 biggest uc_flat 140.40x.
- Verdict: builder cost model undercharges gap re-entry/exit; blotter faithfully reproduces the (under)charged number — the bug is in `honest13_build`, not the emitter.

### G) INSTRUMENT COMPLETENESS — PASS
- 14/14 sleeves mapped to a named instrument; 61,194/61,194 records non-null instrument. Caveats from D (4 sleeves' names vs price-scale mismatch; carryv2→xau.csv fix available).

### H) NEW ENGINE COMPLIANCE — standard exists, gaps identified
- `campaign/TRADE_RECORD_STANDARD.md` mandates: date(T+1), sleeve, instrument(real name), side, price(REAL/SYNTH), qty_notional, weight_from/to, cost_bps≥6.4, reconcile gates. **FF2/CFX4/diescrack are in the ledger** (FF2 from 2008-03-31, CFX4 from 2019-12-03 — sleeve starts, not bugs). Required additions for ANY new engine: (i) real instrument name + on-disk price path stated in FINDINGS; (ii) `book` tag (SAFE/AGG/BAL); (iii) `borrow_charge`; (iv) exec price at t-1 close; (v) holiday-trade flag; (vi) ledger must cover 100% of charged turnover in BOTH books.

---

## BUG LIST (severity-ranked)

| # | Sev | Bug | Exact evidence |
|---|-----|-----|----------------|
| 1 | **CRITICAL** | Ledger is not a complete cost record: built from AGG book only (`TGT=0.091` hardcode) and omits tw/dsc/borrow → ledger-based PnL ≠ champion | 716.70x vs 600.78x charged (119.30%); daily max|diff| 1.181e-3, 5,024/5,086 days; net cost gap −14.65% NAV (−0.726%/yr); tw 293.37x (17.60% NAV), dsc 8.75x, borrow 6.35% NAV missing |
| 2 | **MAJOR** | carryv2 synth-price bug (189,832) — confirmed, explained, fixed in delivered CSV, but fix history shows emitter is provenance-fragile | Pre-fix `(1+Sd)` with Sd=scales (mean 1.413862) → **189,832.7 exactly at 2006-12-29**; delivered CSV 96.47–752.76 (0 REAL); file edited mid-session, current code reproduces 0.0 |
| 3 | **MAJOR** | Sparse-gap skipna undercharge in `honest13_build` | AGG 716.7 vs 746.4 held (+4.1%); BAL 600.8x/1.7860%yr vs hybrid-honest 764.3x/2.2722%yr → **0.4861%/yr undercharge** (9.81% NAV/20.2y) |
| 4 | **MAJOR** | `price` column not the named instrument's executable price for 4 sleeves | a6r7/QAxasts: DGS2/DGS10 yields 0.09–5.26 labeled "TREASURY FUT"; brwt*: Brent leg 13.77–143.95 labeled "FUT SPREAD"; carryv2 "GLD" never REAL though xau.csv exists on disk (5,000 rows, →4,367.22) |
| 5 | **MAJOR** | cost_bps mislabel: ledger 6.4 vs builder 6.0 | gap 11.91 bps/yr = 0.1191%/yr; ann 43.6122%→43.4410% (−0.1711pp); violates standard gate #4 |
| 6 | **MAJOR** | Borrow absent from ledger | 6.349% NAV total = 0.3146%/yr (dualmom 0.0917%/yr largest); standard gate #4 requires it |
| 7 | MINOR | Exec-price timestamp: t-close stamped for a t-return position (standard says t-1 close) | A5r2 |t − (t-1)| mean 72.27 bps, p95 212.50, max 1,094.24 |
| 8 | MINOR | 140 holiday-trade records (96 dates) vs pool holiday-flat convention | CFX4 71 / FF2 39 / diescrack 30; holiday PnL share −0.67%, notional 0.025% |
| 9 | MINOR | No gross-exposure/NAV context in ledger (leverage not testable from records alone) | capital-real gross mean 3.425x, p95 7.369x, max 13.10x (re-derived; disclosed 3.45x/7.18x) — reconstructible only from the path, not the ledger |

## FIX PLAN (coordinator-actionable, ordered)
1. **Emit per-book ledgers** (SAFE+AGG, `book` column; BAL = 0.5·A+0.5·B per record-pair) from `position_path` parameterized by (TGT,THR) — removes the 0.091 hardcode.
2. **Record ALL cost streams**: add trade rows for overlay-vt `tw` (293.37x) and throttle `dsc` (8.75x) turnover; add `borrow_charge` (daily, per shortF sleeve) and `cost_total` columns. Gate: Σ(ledger cost columns) − champion charged cost < 1e-12 daily.
3. **Fix the cost model in honest13_build** (per-instrument gap convention: futures ffill-held, equity fillna(0)-flat): +0.4861%/yr cost, re-emit champion (~43.1% ann expected); charge 6.4bps everywhere or relabel 6.0 (+0.1191%/yr if 6.4).
4. **Fix price maps**: carryv2→`xau.csv` (REAL gold); price 2y/10y with futures prices or relabel instrument "US 2Y/10Y YIELD (yield in %, not futures price)"; price brwt as spread level or relabel "Brent spot leg"; set exec price = t-1 close.
5. **Freeze discipline**: emit only from a committed tree; add `blotter.py --verify` (byte-repro of the CSV like honest13_build) to the standard's gate; add holiday flag column.
6. **Standard v2**: mandatory columns book/borrow_charge/exec_price_ref + "ledger PnL == champion to 1e-12 FROM THE LEDGER ALONE" as the admissibility gate (current gate is satisfiable via builder internals and is vacuous as written).

BLOTTER_TESTER DONE
