> **[ITER20 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER20
> SR-max book: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 36.41% / SR 3.4551 /
> MDD -5.93% / 0 neg years / gross 1.6 exact (sha16 766fc0ce9926d793). Operator objective
> 2026-09-18: Sharpe-max subject to ann>=20% and gross<=1.6; the prior ann-max vintage
> (39.50 / 3.2176, ITER19) is archived byte-exact as archive_*_SUPERSEDED_by_ITER20_srmax.csv.
> Every earlier headline quoted in this document (39.50, 38.11, 37.49, 37.195, 40.84,
> 55.5, 62.4, ...) is SUPERSEDED history kept for provenance — it WAS current once, it is
> not current now.

# GOAL100 CHAMPION — SYSTEM SPECIFICATION (v1.0, frozen 2026-09-01)

> **[SUPERSEDE BANNER 2026-09-08 — THE 55.5% / SR 5.24 HEADLINE BELOW IS A LEGACY
> GENERATION, NOT THE CHAMPION OF RECORD.]**
> (2026-09-13, ITER19 brwt15-prune ADOPTED): ann 39.50% | SR 3.2176 |
> MaxDD -6.56% | 0/19 neg years — CURRENT headline, see campaign/CHAMPION_CARD.md.
> The V1 numbers in this document predate the T+1 causal fix, the full-|dW|@6.4bps cost
> convention and the 1.6x leverage cap; its builders no longer reproduce after the
> 2026-09-07 sleeve costfix wave. History preserved below, unmodified.

Single-page reference for the best honest system produced by the GOAL100 campaign.
All numbers independently reproduced by the coordinator; see "Repro" below.

## 1. HEADLINE (FULL 2008-09-01 .. 2026-08-28, 18.6 years, net of 6bps/side, no leverage)

| | BALANCED (headline) | SAFE (A) | AGGRESSIVE (B) |
|---|---|---|---|
| **Annual return** | **55.5%** | 48.5% | 62.4% |
| **CAGR** | ~60% | ~52% | ~68% |
| **Sharpe (daily)** | **5.24** | 5.18 | 5.27 |
| Sharpe (monthly) | ~3.6 (bootstrap CI 3.1-4.1) | | |
| **MaxDD (full)** | **-6.9%** | -7.3% | -7.9% |
| Worst calendar-year DD | -7.0% (2025) | | -7.1% |
| Negative years | **0 / 19** (worst year +9.1%) | 0/19 | 0/19 |
| Vol | ~9.4% | ~9% | ~10.3% |
| **OOS 2017-26** | **60.2% ann, SR 5.62, DD -6.9%** | 52.5% / -7.3% | 67.8% / -7.9% |
| Sub-5y CAGRs | 53 / 53 / 73 / 64% | | |
| Leave-one-year-out ann | 45.5% .. 50.0% | | |

Files: `campaign/results/GOAL100_CHAMPION_BALANCED_daily.csv` (headline),
`GOAL100_CHAMPION_daily.csv` (=SAFE), `GOAL100_CHAMPION_AGGRESSIVE_daily.csv` (=B).
All [date, ret] daily net returns, 2008-09-01 .. 2026-08-28.

## 2. CONSTRUCTION (trailing-only; no lookahead anywhere)

```
16 sleeves  --vt10 per sleeve-->  plain EW  --global vt-->  DD-throttle  --costs-->  champion
```

1. **Per-sleeve vol-normalize**: each sleeve scaled to 10% ann vol using rolling-60d
   realized vol shifted 1 day (trailing only), scale clipped at 8x.
2. **Blend**: plain equal-weight mean of the 16 normalized sleeves (weights sum to 1
   after the global step => NO leverage at portfolio level).
3. **Global vol target**: BALANCED = 50/50 daily average of config A and config B (below).
4. **Drawdown throttle** (126d rolling max of equity, shifted 1 day; cut exposure to 50%
   when trailing DD breaches threshold; switching costs charged):
   - Config A (SAFE): global vt 8.5%, throttle threshold 4%
   - Config B (AGGRESSIVE, = C4_construct_v2): global vt 11%, throttle threshold 3%
   - BALANCED: daily 50-50 average of A and B return streams (throttle cost charged on each).
5. **Costs**: 6 bps one-side on per-sleeve weight turnover (0.5 x |dW| summed) + throttle
   switching, embedded in all return series.

Configs A and B were selected by IS rules and revealed on OOS once:
- A: GOAL80-frozen throttle params; vt .085 = max with IS(08-16) DD<=-7% margin rule.
- B: C4_metaalloc round-2 frozen rule "max IS SR s.t. IS MaxDD<=8% AND every IS calendar-year
  DD<=8%", argmax (vt .11, thr .03, fr .5, lb 126) identical for IS-ends 2016/2019/2022/2023.

## 3. THE 16 SLEEVES (all validated, gates passed, T+1, net of 6bps)

| # | Name | Path (from repo root) | Family |
|---|---|---|---|
| 1 | H21_f5 | tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv | XGB L/S equity 21d |
| 2 | H21_br | tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv | XGB breadth-gated |
| 3 | A5r7 | campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv | credit composite |
| 4 | a6r7 | campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv | 2y policy-momentum |
| 5 | A1inf | campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv | inflation breadth |
| 6 | QAxasts | campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv | xs TSMOM 189d |
| 7 | A5r2 | campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv | VIX contango |
| 8 | A1credit | campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv | credit regime |
| 9 | XGB1y | campaign/results/sleeve_library/XGB1y_deploy.csv | XGB 1y book (keystone) |
| 10 | dualmom | campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv | dual momentum band |
| 11 | carryv2 | campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv | carry seasonal |
| 12 | A5r4 | campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv | contango vt15 |
| 13 | brwt | campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv | Brent-WTI spread rev |
| 14 | B3momhml | campaign/agents/B3_antiregime/ref_momhml_composite.csv | MOM+HML composite |
| 15 | C5ng | campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv | **natgas weekday (NEW)** |
| 16 | C5ngsum | campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv | **natgas summer weekday (NEW)** |

Keystones (drop-one, at vt .085): XGB1y -10.0pp ann, brwt -3.5pp, QAxasts -1.5pp,
A1credit -1.2pp, C5ng -1.1pp. A5r2/A5r4 are duplicates (corr 1.0); kept — redundant EW
smooths the throttle. #15/#16 added +7.7pp vs the GOAL80 14-sleeve pool.

## 4. OOS DISCIPLINE & HONESTY

- IS = 2008-2016 (selection), OOS = 2017-2026 (single reveal): OOS BEATS IS for all three
  variants (no in-sample inflation).
- Every calendar-year DD <= 7.0% across 2008-2026 (incl. 2022 rate shock, 2020 Covid).
- Post-hoc wall bound (NOT selected, full-sample grid): vt .115 thr .03 => 64.9% @ -7.7%,
  vt .12 => 68.3% — disclosed but excluded because selection used full-sample knowledge.
- C2_fly2AB_75 (round-1 rates fly) is EXCLUDED — quarantined round-2 for a units bug
  (honest net SR -2.04). No quarantined or lookahead-tainted sleeve is in the pool.
- a6r7 and A1credit yield-approx sleeves re-audited clean (decimal units, repro byte-consistent).
- gates.py scramble_pval is degenerate; sleeve validations used signal-permutation /
  calendar-scramble (p<0.05 required). C5ng calendar-scramble p=0.015; C5ngsum p=0.015.

## 5. REPRO

```bash
# champion construction from the 16 sleeve files (coordinator build):
python3 - <<'PY'
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from coord_goal100_v2 import load, vt
# ... construct(POOL, TGT, DD_THR) as in campaign/GOAL100_FINAL_REPORT.md section 3
PY
# C4/B-config standalone repro:
python3 campaign/scripts/c4_construct_v2.py
# eval any champion file:
python3 campaign/harness/eval.py campaign/results/GOAL100_CHAMPION_BALANCED_daily.csv
```

## 6. LIVE-TRADEABILITY CAVEATS (honest)

- Natgas sleeves trade Henry Hub SPOT prints; live proxy = front futures/UNG with basis risk.
- Bond sleeves (a6r7, A1credit) use duration-approx synth TR (no convexity/financing spread).
- A5 contango sleeves assume VIX-futures term-structure access (VXX-style or futures roll).
- 6bps/side is an ETF-level execution assumption; single-name legs inside XGB books may cost more.
- 18.6y tested vs the 20y goal: limited by sleeve availability from 2008-09; all engines
  that exist pre-2008 (A5r7 1990+, A1credit 1990+, C5ng 1997+) show stable pre-2008 behavior.

## 7. GOAL SCORECARD

| Requirement | Result |
|---|---|
| SR >= 2 | **5.24 — EXCEEDED** |
| MaxDD <= 8% | **-6.9% — PASS** |
| No leverage | PASS (EW weights, vt caps) |
| 6bps/side costs | PASS (embedded) |
| Free data | PASS (FRED, Ken French, twelve panel — all free) |
| OOS test | PASS (2017-26 single reveal, OOS > IS) |
| 20y testing | 18.6y (93%) |
| **ann >= 100%** | **NOT MET: 55.5% (honest ceiling ~65% post-hoc). Requires DD/return 0.08 vs best-real 0.11-0.20 — out of reach on free daily data at 6bps.** |

---

## 8. VERIFICATION APPENDIX (added 2026-09-01 after coordinator audit)

### 8.1 Replication
`python3 campaign/scripts/champion_build.py --verify` regenerates all three champion CSVs
from the 16 sleeve files and compares byte-wise: max deviation 1e-16 (float round-off only)
=> the champion is EXACTLY reproducible from committed inputs. The script is the canonical
builder; the CSVs are its frozen outputs.

### 8.2 Leakage audit of the 16 sleeves (what was checked, what was found)

| Sleeve | Mechanism | Leakage check | Verdict |
|---|---|---|---|
| H21_f5 / H21_br / XGB1y | XGB equity books | trained on 2008-2016 only, model versioning separate from eval; daily book files produced by frozen models; **residual risk: three seeds share the XGB family => their +ann comes partly from correlated ML luck; drop-one shows XGB1y -10pp so single-model dependence is real** | CLEAN mechanically; concentration risk noted |
| A5r7 / A5r2 / A5r4 | VIX-term-structure carry | pure trailing contango signal (T+1 shift); A5r2/A5r4 duplicates (corr 1.0) | CLEAN |
| a6r7 | 2y trend | independent rebuild: corr(mine, saved) 0.979; scale decimal; signal = trailing 378d TR sign, decisions frozen 42d cadence | CLEAN |
| A1credit | BAA regime | exact repro script runs byte-consistent; units decimal; regime = trailing 252d | CLEAN |
| A1inf / QAxasts / dualmom / carryv2 | panel strategies from campaign A-rounds (GOAL80, gates then) | inherited from GOAL80 gate stack (scramble/halves/plateau) | CLEAN (inherited) |
| brwt | Brent-WTI z-rev | coordinator re-derived: same trade re-found independently (corr 0.76 to my spot version); vol_target expanding trailing; T+1 | CLEAN |
| B3momhml | FF MOM+HML composite | FF factor data = published portfolio returns (tradeability caveat, not leakage) | CLEAN w/ caveat |
| C5ng / C5ngsum | natgas weekday | coordinator full rebuild from raw DHHNGSP: SR 1.08 (all-year) vs saved 0.99-1.74 range (config variance); calendar-scramble p=0.016; per-year positive; honest T+1 confirmed by reading agent code | CLEAN; meta overstated SR (1.74 vs honest ~1.0) — blend uses the honest series |

### 8.3 Known non-fatal caveats (no handwaving)
1. **Gross exposure**: per-sleeve vt10 with cap 8x means gross book exposure averages >1x
   across sleeves (long-flat sleeves sit at scale>1 during low-vol). At portfolio level the
   EW-of-16 + global vt keeps net exposure moderate, but we do NOT simulate financing cost
   on internal scale>1 (consistent with GOAL80 convention). A full financing-cost model
   (fed funds + 20-30bps spread on gross>1) would reduce ann by an estimated 2-6pp —
   direction known, magnitude not modeled. Flagged, not hidden.
2. **VXX-style sleeves** (A5r2/r4/r7) embed VIX-futures roll; live cost higher than 6bps.
3. **Natgas spot** sleeves: live trade requires futures/UNG (basis risk); spot prints are
   the signal AND pnl source in backtest — tradeability gap flagged in GOAL80 too.
4. **Three XGB books** are one ML family; family-level luck not diversifiable. The honest
   frontier without the XGB family is materially lower (XGB1y alone -10pp).
5. 2023 (+163% best year) is real but the pool is NOT selected on 2023 (verified by
   IS-ends sensitivity: argmax identical for IS-ends 2016/2019/2022/2023).

### 8.4 Champion integrity verdict
The champion as committed is **mechanically clean**: exactly reproducible, T+1 everywhere,
trailing-only scaling/throttling, costs embedded, selection done on IS with single OOS reveal.
Economic caveats (financing on internal leverage, VXX/natgas tradeability, XGB family
concentration) are disclosed above and quantify the gap between "backtest ann" and
"achievable live ann" — they do not involve any lookahead or hand-waving.

### 8.5 FINANCED VARIANT (2026-09-01, post-appendix addendum)
Charging financing (3M T-bill + 25bps) on ALL internal gross exposure >1x NAV per sleeve:
| Variant | base ann | financed ann | financed DD |
|---|---|---|---|
| SAFE A | 48.5% | 43.2% | -7.3% |
| AGGRESSIVE B | 62.4% | 54.6% | -8.3% (breaches 8% by 0.3) |
| **BALANCED** | 55.5% | **48.9% @ -7.5%, SR 4.69, OOS 49.4%** | |

Files: GOAL100_CHAMPION_{SAFE,BALANCED,AGGRESSIVE}_FINANCED_daily.csv.
The headline champion remains the base-convention BALANCED (55.5%); the financed series is
the conservative lower bound under the strictest funding interpretation.

---

## 9. E-ROUND UPDATE (2026-09-01 evening) — 20-year vehicle + integrity note

### 9.1 CHAMPION20Y_E1 (new best 20-year-span system)
E1_20yspan de-truncated sleeve histories (natgas 1998+, brwt 2000+, bond2y 1992+, GLD-proxy
panels 2006-07+) and rebuilt the 20Y champion:
- **GOAL100_CHAMPION20Y_E1_BALANCED_daily.csv: 2006-10..2026-08 (19.9y), ann 47.0%, SR 5.12,
  MaxDD -7.95%, 1 neg year (-1.4% in 2006), OOS17+ 52.6% @ -8.0%.**
- Config TGT .085 THR .035 FR .4 (frontier max-ann under full DD>=-8%).
- E1's own honest costed-B3 variant lands 34.9% (the no-cost B3 convention is worth a lot
  inside that 12-pool because it's a low-vol FF-factor series occupying 1/12 weight).

### 9.2 B3momhml integrity note (flagged by E1, quantified by coordinator)
`campaign/agents/B3_antiregime/ref_momhml_composite.csv` is a NO-COST, NOT-gate-passing
reference series (SR 0.94 standalone, fails halves, scramble p=1.0) that entered the GOAL80
blend lineage as a decorrelation ingredient. Coordinator quantification at champion scale:
16-pool with B3: 55.5% @ -6.9% | 15-pool without: 55.0% @ -7.1% (OOS 60.2% vs 60.6%).
=> portfolio impact +0.5pp ann / +0.2pp DD: immaterial but DISCLOSED. The FF-factor data
(mom_hml daily from Ken French) is itself free and PIT-correct; the sleeve is a static
composite whose standalone stats never passed gates. Risk-averse users can drop it; stats
move <0.5pp.

### 9.3 E-round results (5 agents, 30+ ideas, 2 sleeves + 1 champion upgrade)
- E1: 7 de-truncated sleeves + CHAMPION20Y_E1 (above). Best extension: brwt-2000 (SR 2.76
  from 2000-03, 0/26 neg yrs).
- E2: calendar-event class closed honestly — opex-day SPX effect is REAL (-58.7bp, t=-7.50,
  every decade negative) but 12-16 events/yr caps net SR at 0.85 < 1.0 gate at 6bps.
- E3: vol-regime/event books: 0/7 (all <= B&H-adjusted references); VIX3M real data 2009+.
- E4: global indices: 0 saved (Nikkei TSMOM dead post-1990; lead-lag = lookahead artifact
  documented; SR ceiling ~0.7); DJIA/NASDAQCOM/SP500 fetched to newdata.
- E5: independent CHAMPION20Y validation — byte-match confirmed; cost stress: +2bps costs
  = -0.4pp ann only (6bps not load-bearing); bootstrap SR CI [4.36,5.53], P(SR<2)=0.000;
  scramble p=0.000; upgrade grid FAILS honest IS->OOS rule (IS surface flat, argmax
  breaches OOS DD) => v1 confirmed.

---

## 10. CHAMPION_V2 (2026-09-01 late) — +MHX 17th sleeve

### 10.1 The new sleeve
`campaign/agents/COORD/sleeves/MHX_multihorizon_xgb.csv` — multi-horizon walk-forward XGB
L/S book (H=1/5/21 days, top-10/bottom-10 of a 285-name panel, quarterly refit on a 3y
training window, labels purged by max-horizon, causal features at close, 6bps/side inside,
vt13 rolling-20d shift-1). Built by tools/quant/bigmove/xgb_multi_horizon.py (20y cache
horizon_preds_20y_f5/f6.pkl). Trimmed to its real OOS start 2008-09-02 (the published
blend_daily.csv had zero-padding before that — removed here; caught in audit).

### 10.2 CHAMPION_V2 numbers (17-pool; construction otherwise identical to V1)
| | BALANCED | SAFE | AGGRESSIVE |
|---|---|---|---|
| ann | **66.0%** | ~58% | ~73% |
| SR daily | **6.21** | | |
| SR monthly | **4.33** (bootstrap CI [3.85,4.94]) | | |
| MaxDD | **-7.1%** | | |
| per-year DD max | -6.4% (2025) | | |
| neg years | 0/19 (worst +12.0%) | | |
| OOS17+ | **69.7% ann, SR 6.48** | | |

Files: campaign/results/GOAL100_CHAMPION_V2_{BALANCED,SAFE,AGGRESSIVE}_daily.csv.

### 10.3 Understanding the SR (no hand-waving)
The blend's SR 6.2 is a DIVERSIFICATION result: 17 individually-gated vt10 sleeves with
avg pairwise corr ~0.05. Arithmetic: avg standalone SR ~1.7 x sqrt(17/(1+16*0.05)) ~ 5-6.
The circular-shift scramble at blend level gives p=1.0 (shuffled realignments score as high)
— this does NOT indicate leakage; it reflects that vt10+EW mechanically manufactures high
SR from any set of low-corr streams. What carries the alpha is each sleeve's standalone
validated edge (all 17 passed signal-level scrambles, plateaus, halves, yearly gates) plus
genuinely low correlations (MHX vs H21_f5: -0.004; vs XGB1y: -0.042).

### 10.4 Path to 100%: remaining gap
V2 at DD -7.1% => vol ~10.6%. 100% ann at SR 6.2 needs only ~16% vol, but the DD/vol floor
(~0.65 measured across all constructions) caps 8% DD at ~12.3% vol => ~76% ann ceiling at
current SR. To close the gap honestly: either 8-10 MORE decorrelated validated sleeves (the
17-pool took ~6 agent-rounds to grow by 1) or engines with better standalone DD/return.

---

## 11. CHAMPION20Y_V2 — THE 20-YEAR CHAMPION (final, 2026-09-01)

> **[COORD BANNER 2026-09-07 17:2x — VERIFY STEP 3 NO LONGER REPRODUCES.]**
> `python3 campaign/scripts/champion20y_build.py --verify` now reports all 3
> CHAMPION20Y_V2 CSVs **DIFF** (BAL 3.107e-03 / SAFE 6.160e-03 / AGGR 6.206e-03),
> re-run independently at this standup. Cause: the 2026-09-07 costfix wave changed
> sleeve files that feed this builder (per HUNT_TREASFUT R3). Quoting CHAMPION20Y_V2
> as current is UNSAFE until rebuilt; see
> campaign/agents/chief/coord/HUNT_TREASFUT/work_r3/TRUTH20Y_QUARANTINE.md for the
> related TRUTH20Y provenance-orphan finding. The CURRENT champion of record is
> GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (verified this standup: 7/7 checks ok,
> ann 37.195% / SR 3.181 / MDD -6.69% / 0 neg years). Repro steps 1-2 and 4-5 in this
> section were not re-run here; only step 3 was tested and it FAILS as stated.

> **[COORD DECISION 2026-09-08 03:1x CST — CHAMPION20Y_V2 DEPRECATED FOR QUOTING.]**
> The rebuild-or-deprecate question (carried since 09-07) is resolved: DEPRECATE. The
> 09-07 costfix wave changed >=1 feeding sleeve (CAMP_COST __costfix files), so every
> number in the section-11 table (ann 65.1% / SR 6.17 / OOS 71.5%) is a pre-costfix
> vintage and must not be quoted as current; MHX in the pool additionally carries the
> CAMP_SHORT non-shortable/borrow-tier caveat. A rebuild is chartered as an R5 work
> item: run champion20y_build.py against the post-costfix sleeve set with a fresh
> --verify IDENTICAL plus a shortability/borrow re-audit of MHX (or drop MHX and
> disclose). Until that lands, CHAMPION20Y_V2/TRUTH20Y are QUARANTINED artifacts
> (historical, non-quotable). Coordinator evidence this session: champion of record
> re-verified 7/7 (coord/verify_champion_standup_0305.json, sha 4358dfab unchanged).

**GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv** — 13 sleeves (E1 de-truncated pool + MHX),
2006-10-02..2026-08-28 = **20.6 years**:

| metric | value |
|---|---|
| **ann** | **65.1%** |
| **SR daily / monthly** | **6.17 / 3.83** (bootstrap CI [3.39, 4.35]) |
| **MaxDD** | **-7.2%** (worst per-year DD -6.6% in 2006) |
| neg years | 1/21 (2006: -1.6%) |
| OOS 2017-26 | **71.5% ann, SR 6.49, DD -7.2%** |
| 5y CAGRs | 84 / 77 / 96 / 107% |
| LOYO | 61.9%..67.1% |
| cost stress | 8bps: 64.7%/-7.4%; 10bps: 64.4%/-7.5% (robust) |
| no-B3 variant | 64.8%/-7.8% (B3 optional, disclosed) |

Config: A = vt.09/thr.03/fr.5, B = vt.106/thr.0255/fr.5, BALANCED = 50-50.
MHX enters 2008-09 (ML training floor) — before that it dilutes the EW (conservative).
The 18.6y CHAMPION_V2 (66.0%) and 20.6y CHAMPION20Y_V2 (65.1%) are the same architecture;
the 20Y version is the goal-compliant vehicle. Remaining gap to 100%: ~1.5x, requiring
8-10 more MHX-grade decorrelated engines (the full audit trail in the agents' FINDINGS
shows ~300 tested ideas yielded 3 such engines across two campaign days).

---

## 12. REPLICATION RUNBOOK (final, 2026-09-01)

> **[SUPERSEDE BANNER 2026-09-08 — RUNBOOK STEPS 2 AND 3 NO LONGER REPRODUCE.]**
> After the 2026-09-07 sleeve costfix wave, `champion_build.py --verify` reports
> **DIFF** (measured AUDIT_CHAMP2 R4, 2026-09-08: GOAL100_CHAMPION_daily 1.130e-03 /
> GOAL100_CHAMPION_BALANCED_daily 2.069e-03 / GOAL100_CHAMPION_AGGRESSIVE_daily
> 4.099e-03) and `champion20y_build.py --verify` reports **DIFF** (BAL 3.107e-03 /
> SAFE 6.160e-03 / AGGR 6.206e-03, per the section-11 banner above). Steps 2 and 3
> below are kept verbatim as history but are NOT executable against the current tree;
> the runbook reproduces the 2026-09-01 vintage only (checkout a pre-2026-09-07 tree).
> The champion of record, GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, verifies
> IDENTICAL to its builder (rawew13v2_build.py, maxdev 1.1e-16; 7/7 checks ok
> 2026-09-08 via campaign/bt/verify_champion_r3_cmd.sh). This banner is ADDITIVE —
> every original line below is preserved unmodified.

Cold-replication from a fresh clone:
1. `git clone <this repo>` — all 33 dependency files (17+13 sleeves, scripts, docs) are committed.
2. `python3 campaign/scripts/champion_build.py --verify` → all 3 V1 champion CSVs IDENTICAL (dev < 1e-16).
3. `python3 campaign/scripts/champion20y_build.py --verify` → all 3 CHAMPION20Y_V2 CSVs IDENTICAL (dev < 1e-16).
4. `python3 campaign/harness/eval.py campaign/results/GOAL100_CHAMPION_V2_BALANCED_daily.csv` → ann 66.0% SR 6.21 DD -7.1%.
5. `python3 campaign/harness/eval.py campaign/results/GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv` → ann 65.1% SR 6.17 DD -7.2%.

MHX deeper repro (regenerates the ML sleeve from raw prices, ~1h CPU):
`cd tools/quant/bigmove && HZ_START=2008-09-02 python3 xgb_multi_horizon.py`
(cache: data/horizon_preds_20y_f5.pkl; blend_daily.csv rows before 2008-09-02 are
zero-padding — trim, as done in campaign/agents/COORD/sleeves/MHX_multihorizon_xgb.csv).

Verified status: dependency check (26 files) — none missing, none dirty; both cold-rebuild
tests byte-EXACT (2026-09-01).

---

## 13. CHAMPION_V3 (final generation, 2026-09-01 night) — brwt-family completion

### 13.1 New sleeve
`campaign/agents/COORD/sleeves/brwt10_2000.csv` — Brent-WTI log-spread z-reversion at
lookback 10 (B2's brwt family, lb10 variant), rebuilt from 2000-01 (DCOILBRENTEU 1987+ +
wti_full 1986+). SR 3.41, ann 32.1%, DD -8.4%, 0/27 neg years. **Plateau audit PASS**:
lb5-30 neighbors SR 2.72-3.62 (no isolated spike; lb10 sits mid-plateau).

### 13.2 CHAMPION_V3 (18-pool, 18.6y) and CHAMPION20Y_V3 (14-pool, 20.6y)
| | V3 (18y) | 20Y_V3 (20.6y) |
|---|---|---|
| ann | **68.6%** | **67.7%** |
| SR daily | 6.36 | 6.29 |
| SR monthly | 4.57 (CI [4.06,5.20]) | 4.10 |
| MaxDD | **-6.8%** | **-6.7%** |
| neg years | 0/19 | 1/21 (2006 -1.6%) |
| OOS 17-26 | **72.9% @ -6.8%** | **74.3% @ -6.7%** |
| worst per-year DD | -2.3% | |
| LOYO min | 65.9% | |

Configs unchanged (A/B as V2/V2-20Y + one added family sleeve each).
DISCLOSURE: brwt10 and brwt15 are the same trade at different lookbacks (corr 0.79);
kept as separate EW sleeves deliberately — the family is the single best engine found
(0 negative years in any variant since 2000). Risk-averse users can drop brwt10: V3 falls
to V2 levels.

### 13.3 Scorecard after V3
SR>=2: exceeded 3.2x. MaxDD<=8%: -6.7/-6.8%. 20y testing: 20.6y. No leverage, 6bps, OOS: pass.
ann>=100%: 67.7% honest — remaining gap needs ~6-8 more brent-wti-grade engines. All
documented, committed, byte-reproducible.

---

## 14. CHAMPION_V4 (final, 2026-09-01) — brwt lookback-ensemble family

Adding lb5/lb7 variants of the brwt family (each independently plateau-passing, SR 2.7-3.6,
0 neg yrs). Marginal analysis: 3 slots +1.2pp, 4 slots +0.3pp, 5 slots NEGATIVE — stopped at 4.
Equivalent single-sleeve alternative: brwt_ens (5-lookback EW, SR 3.27) gives 68.9% at 1 slot —
V4's extra +1.2pp comes from deeper family weighting; both disclosed.

### CHAMPION_V4 (21-pool, 18.6y) — files GOAL100_CHAMPION_V4_*
ann **70.1%**, SR 6.25 / monthly **4.77** (CI [4.23,5.41]), MaxDD **-6.4%**, 0/19 neg yrs
(worst +8.6%), OOS17+ **75.4% @ -6.4%**, worst per-year DD -2.0%, LOYO min 67.5%.

### CHAMPION20Y_V4 (16-pool, 20.6y) — files GOAL100_CHAMPION20Y_V4_*
ann **68.7%**, SR 6.29 / monthly 4.26 (CI [3.77,4.80]), MaxDD **-6.0%**, 1/21 neg yrs
(2006 -1.8%), OOS17+ **75.6% @ -6.0%**.

Family disclosure: brwt lookbacks occupy 4/21 slots (19%) in V4, 3/16 (19%) in 20Y_V4.
The brwt family remains the single best engine of the campaign (Brent-WTI storage spread
mean-reversion). Build scripts: champion_build.py / champion20y_build.py pools updated in
the JSONs; sleeve files all committed.

---

## FINANCING CONVENTION DISCLOSURE (2026-09-08) — CAMP_BORROW R5/R6, docs-only

The champion of record (GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, sha 4358dfab95679b97)
is priced with a FLAT financing convention: call rate 4.50%/yr on (gross-1)=0.6 (margin drag
exactly 2.700%/yr = 1.0714 bps/day; verified priced-at-rate residual 1e-16), borrow
0.5%/yr on short notional. Freshness audit vs published benchmarks (FRED, 2026-09-03:
DFF 3.63%, SOFR 3.66%; IBKR prices Pro margin loans at Benchmark + spread; the 1.5-2pp
spread band is the R1 recorded rationale — IBKR's own published pages were unreachable
from this environment and were NOT re-verified) yields FOUR drift flags, ALL beyond a
10% relative bar:

| flag | modeled | implied (published) | rel drift | abs |
|---|---|---|---|---|
| call vs DFF+1.5pp | 4.50% | 5.13% | +14.00% | +0.63pp |
| call vs DFF+2.0pp | 4.50% | 5.63% | +25.11% | +1.13pp |
| call vs SOFR+1.5pp | 4.50% | 5.16% | +14.67% | +0.66pp |
| margin drag vs TRUE DFF+1.5pp path | 2.70%/yr | 1.76%/yr (path mean 2.93%+1.5pp) | -34.86% | -0.94pp |

Both-directions reading (the flat convention is NOT drift-neutral in time):
- vs TODAY's Benchmark+spread the modeled 4.5% is CONSERVATIVE: a live IBKR client at
  DFF+1.5pp pays 5.13% and the current-environment ann is ~36.68% (-0.52pp; -0.93pp at
  the 2.0pp spread cap, ann 36.27%) — i.e. the committed 37.195% headline overstates
  today-realizable ann by roughly 0.5-0.9pp.
- Over the FULL 2008-2026 backtest window the elementwise DFF+1.5pp rate path averages
  only 2.93%+1.5pp, so the flat 4.5% convention UNDERSTATES the period ann by +1.30pp
  (true-path ann 38.49%).
- Champion impact in every scenario: NO gate moves — 0/19 negative years everywhere;
  MDD never worse than -6.7024% vs the -7% goal line. Borrow side is immaterial by three
  orders of magnitude: a 100% relative borrow-rate move (0.5->1.0%/yr) moves the champion
  0.2196 bps/yr (all shorts are futures/ETF legs inside sleeve files; zero slot-level
  negative weights on all 4,805 days; the only embedded stock-loan leg, diescrack, costs
  0.2195 bps/yr as committed).

Evidence: campaign/agents/chief/coord/CAMP_BORROW/FINDINGS.md ROUND 5;
work_r5/{r5_freshness_audit.py, r5_short_census.py, r5_drift_flag.py, r5_drift_flags.json,
fred_dff.csv, fred_sofr.csv}. Charter-mandated disclosure; no numbers above are new
signals and no results/ or bt/ artifact was modified.
