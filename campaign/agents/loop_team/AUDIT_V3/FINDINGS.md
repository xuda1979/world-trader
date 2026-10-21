# AUDIT_V3 — FINDINGS (2026-09-03)
Adversarial audit of GOAL100_HONEST14V3 (14 engines) + FF2_DUALGATE tradeability + leverage/neg-yr honesty. READ-ONLY elsewhere; scratch scripts in scratch/. All stats 2008-03-31..2026-08-27 unless noted (n=4713). My own loader/rollup re-implemented from scratch (a_rebuild.py), no committed-builder import for the rebuild.

## VERDICT TABLE
| # | Target | Verdict | Key numbers |
|---|--------|---------|-------------|
| 1 | BYTE-REPRO V3 | **PASS** | 3/3 CSVs max\|diff\| 9.99e-17..9.996e-17; own-loader rebuild 6/6 files ~1e-16; headline 43.61/3.924/-4.92/0-neg reproduced |
| 2 | FF2 TRADEABILITY | **FAIL (research-only, confirmed) — but immaterial to V3** | SPY-proxy SR 1.030→0.771; FF2 delta on V3: ann −0.22pp, SR_d +0.019 |
| 3 | LEVERAGE ≤1.6 honesty | **VIOLATION CONFIRMED** | V3 gross mean 3.477x, p95 7.216x, max 10.798x; 90.9% of days >1.6x; @1.6x cap V3 ann 17.0–20.0% |
| 4 | 0/19 NEG YRS scope | **PASS 2008+ / FAIL full-window** | 2006 stub −1.38% (61 days); min 2008+ year +13.94% (2011) |
| 5 | COST 6.4 / call-rate / shortability | **FLAG (small undercharge, big uncharged financing)** | 6.0bps charged; 6.4bps costs −0.29pp ann (43.40% vs 43.69% my-baseline); effective 5.82bps on rebuild surface (EXEC credit −0.053%/yr); margin financing on 3.48x gross NOT charged |
| 6 | NEW phenomenology (ac1/uniqR sweep) | **PASS** | max ac1 +0.081 (brwt5); min uniqR 0.159 (diescrack, 84% zeros by design); blend ac1 −0.066, uniqR 1.000 |

## T1 — BYTE-REPRO (PASS)
- `honest13_build.py --verify-v3`: GOAL100_HONEST14V3_BALANCED max|new−old|=9.988e-17, SAFE 9.996e-17, AGGRESSIVE 9.986e-17 — all IDENTICAL (<1e-12), no index mismatch (5086 rows each, 2006-10-02..2026-08-27).
- Independent rebuild with my OWN loader/rollup/vt/build (a_rebuild.py): all 6 committed files (V3 and V2 sets) IDENTICAL at ~1e-16, row counts equal (5086).
- Headline (emit convention, 2008-03-31+): BALANCED ann_geo 43.61%, SR_d 3.924, SR_m 4.016, MDD −4.92%, vol 9.34%, 0/19 neg, worst yr +13.94%; SAFE 37.51%/3.927/−4.87%; AGGR 49.96%/3.912/−5.42%. Commit-msg claims (43.6/3.92/4.02/−4.92/0/19) reproduced exactly. Worst rolling-3y DD = −4.92% (same as full MDD). OOS17+ arith 40.62% (SR 4.10, n=2496) vs claimed 40.6% — match.

## T2 — FF2 TRADEABILITY (FAIL as a product; immaterial to V3 numbers)
What FF2 actually holds:
- Book A "long MOM" = the FF daily momentum factor: avg of 2 VW big/small HIGH-prior-30% portfolios minus avg of 2 LOW-prior portfolios (6 size×mom books, sorts re-daily, prior return day −250..−21, 202606 CRSP). That is a daily-rebalanced L/S book of hundreds of US stocks — no single instrument, no momentum ETF on disk (MTUM/QSPT absent). Book D "long Mkt-RF" = VW market minus RF (proxy: SPY, but RF then uncharged ⇒ small SR gift).
- Gates use only LAGGED info (rv63 z of the paper series itself, VIX 252d-MA z; shift(1) verified in final1.py). No same-day leak: corr(posD_t, r_t)=+0.006 vs corr(posD_t, r_{t+1})=+0.086 in my rebuild check. But the A-gate is computed on the UNTRADEABLE L/S book's own vol — live you cannot observe it.
- SPY-proxy re-run (identical gates, r=SPY instead of paper factors): SR 1.030→0.771, ann_geo 8.94%→6.68%, MDD −11.24%→−13.11%, negy 2/19→3/19; corr(paper, spy-proxied)=0.784. ⇒ ~25% of FF2's SR exists only in the paper CRSP construction. **RESEARCH-ONLY, as the commit disclosed. Trade-record instrument: NONE on disk; fallback proxy = SPY (twelve_big/SPY.csv close series, path used: SR 0.771 variant).**
- Data integrity: FF daily file = 26,274 rows, **zero** −99.99 prints (incl. 2008+); 174 NYSE bdays/2008+ absent from FF index (holidays) — handled by reindex alignment. FF2 raw file ends 2026-06-30 (vintage); the V3 champion's last 42 days (2026-07-01..2026-08-27) carry ZERO FF2 contribution; champion earned +5.65% on those 42 days from the other 13 engines. 2026 YTD +17.86% through 8/27 — the 0-neg-2026 claim does NOT depend on the FF2 gap (FF2 hypothetical at its 3.55bp/day mean over 42d = +1.49%; no path to a negative year). Flag: any V3 number beyond 2026-06-30 is 13-engine.
- Contribution (family() NEW3 vs NEW2, my rebuild, 2008-03-31+):
  - V3 14eng: ann_geo 43.61%, SR_d 3.924, SR_m 4.016, MDD −4.92%
  - minus FF2 (13eng): ann_geo 43.83%, SR_d 3.905, SR_m 3.993, MDD −4.96%
  - **FF2 delta: −0.22pp ann, +0.019 SR_d, +0.023 SR_m, +0.04pp MDD — cosmetic.** Pool11-only: 44.89%/3.976/−5.40% (all 3 new sleeves at slot 0.10 cost −1.28pp ann, improve MDD +0.48pp — the standing dilution-for-DD convention).
- NEW FINDING — corr wire: corr(FF2, V2 BAL)=+0.1449 (delivered claim, PASS by 0.005), but corr(FF2, **V3** BAL)=**+0.1658 > 0.15** — the wire was measured vs V2; vs the blend it actually joins, FF2 breaches 0.15. Moot (removing FF2 restores V2), but the <0.15 decorrelation claim for the V3 blend is over-stated.

## T3 — LEVERAGE HONESTY (VIOLATION CONFIRMED)
- V3 BAL capital-real gross (|full-weight matrix| sum, mean of A/B, throttle on, 2008-03-31+): **mean 3.477x, p50 3.203x, p95 7.216x, max 10.798x**; 90.9% of days >1.6x; 95.3% >1x. (Throttle-off 3.502x; full-window-from-2006 3.425x; SAFE 3.045x; AGGR 3.910x.)
- The commit-msg "3.45x mean / p95 7.18x" is **V2's** exact recomputed numbers (V2: 3.453x / 7.183x / max 10.749x). V3's own are marginally higher (above). Same story, slightly stale label.
- **V3 VIOLATES the capital-real ≤1.6x goal — confirmed, on 91% of days.** No financing is charged on the >1x gross (disclosed GOAL80 convention). Re-quotes at real 1.6x gross cap:
  - V3 BAL @1.6x, no margin charge: ann_geo **20.04%**, SR_d 4.194, MDD −3.37%, 0/19 neg, worst yr +6.85%
  - @1.6x + 2.0%/yr margin on (gross−1): ann_geo **18.70%**, SR_m 3.492, MDD −3.50%
  - @1.6x + 4.5%/yr margin: ann_geo **17.04%**, SR_m 3.205, MDD −3.66%
  - V2 BAL @1.6x+4.5%: 17.22% (no-margin 20.22%); POOL11 @1.6x+4.5%: 18.43% (no-margin 21.51%)
- Statement: under the goal's own leverage cap, V3 delivers ~17–20%/yr, NOT 43.6%. The 43.6% headline is a 3.48x-gross number with free financing.

## T4 — 0/19 NEG YRS SCOPING (PASS 2008+, FAIL full-window)
- 2008-03-31..2026-08-27 yearly (%): 2008 41.76 (from 3/31 — Q1-08 crash excluded by start cut), 2009 35.48, 2010 50.44, 2011 13.94, 2012 42.03, 2013 24.20, 2014 30.96, 2015 39.07, 2016 55.57, 2017 58.44, 2018 50.54, 2019 58.27, 2020 88.98, 2021 37.22, 2022 26.55, 2023 52.63, 2024 54.76, 2025 53.43, 2026 17.86 (thru 8/27). **0/19 negative, min +13.94%.**
- FULL window: **2006 stub 2006-10-02..2006-12-29 (n=61) = −1.38%** (FINAL_STATE's "−1.4% pre-live warmup" accurate); 2007 = +45.58%. Goal "profit>=0 every year" is TRUE only under the 2008+ scope caveat and must be quoted with it; the pre-2008 window is a warmup, not a live year.

## T5 — COST / CALL-RATE / SHORTABILITY (FLAG)
- Charged: 6.0bps/side on ALL turnover surfaces (blend tw + throttle dsc + per-sleeve rebuild reb). Total one-side turnover 1801bps/day ⇒ 2.72%/yr drag. GOAL specifies 6.4bps ⇒ **0.4bps gap = 0.18%/yr undercharge.**
- Re-run at 6.4bps on every surface (+0.4bps on FF2's internal 1.92%/day): ann_geo 43.40% (vs 43.69% my-baseline, which omits the tiny dualmom HTB uplift term — committed file is 43.61%), SR_d 3.909, MDD −4.96%, still 0/19 neg. **PASS; −0.29pp.**
- EXEC-adjustment nuance: pool sleeves with true quoted cost <6bps (brwt family 1.5bps, a6r7/C5ng/C5ngsum 5bps) receive a rebate ((6−exec)×ΔcapW); net across surfaces the effective rate = **5.82bps/side** (rebate −0.053%/yr). Defensible (equalizes each pool sleeve to its own quoted cost) but means the blend pays slightly BELOW 6bps on average; a hard 6.4bps floor everywhere would cost ~+0.35%/yr total vs baseline.
- Borrow: 0.5%/yr on short legs at slot weights (SHORTF), dualmom uplifted to ~1.1% (HTB) — total 0.326%/yr 2008+. Long/flat books (FF2, diescrack, CFX4, C5ng) pay 0.
- NOT MODELED (state honestly): (a) IBKR call-rate financing on the 3.48x mean gross — at 4.5%/yr this is −11.1%/yr, THE dominant gap vs the 100% goal; only the ≤1.6x re-quotes above include it; (b) stock-specific hard-to-borrow beyond flat 0.5%/1.1%; (c) shortable-universe constraints; (d) FF2's shorts are untradeable paper books anyway (see T2); (e) no securities-lending credit on longs.

## T6 — PHENOMENOLOGY SWEEP (PASS, no XGB1y trap)
| sleeve | n | ac1 | uniqR | zerofrac | flag |
|---|---|---|---|---|---|
| brwt15 | 6511 | −0.042 | 0.333 | 0.667 | – |
| brwt10 | 6517 | −0.047 | 0.616 | 0.383 | – |
| brwt7 | 4534 | +0.043 | 0.622 | 0.378 | – |
| brwt5 | 4534 | **+0.081** | 0.631 | 0.369 | – (max ac1 in pool) |
| C5ng | 7324 | +0.004 | 0.781 | 0.217 | – |
| C5ngsum | 7324 | +0.063 | 0.473 | 0.527 | – |
| A5r2 | 4212 | −0.015 | 0.769 | 0.232 | – |
| a6r7 | 9162 | +0.013 | 0.552 | 0.128 | – |
| QAxasts | 4904 | −0.004 | 0.993 | 0.008 | – |
| carryv2 | 4974 | −0.098 | 0.988 | 0.011 | – |
| dualmom | 4700 | −0.086 | 0.743 | 0.257 | – |
| diescrack | 4605 | −0.057 | **0.159** | 0.841 | lowest uniqR, passes 0.08; long/flat book |
| CFX4 | 1799 | −0.146 | 1.000 | 0.000 | – (short history 2019+, disclosed in iter4) |
| FF2 | 4652 | −0.072 | 0.760 | 0.240 | – |
| V3_BAL blend | 5086 | −0.066 | 1.000 | 0.000 | – |
No sleeve has ac1>0.5 or uniqR<0.08. No flattened-monthly-PnL pathology.

## SUMMARY (brutally honest)
1. The V3 file is exactly what the builder says it is (byte-repro + independent rebuild, ~1e-16). Headline numbers verified.
2. FF2 is research-only (paper CRSP factor proxy; SPY-proxy loses 25% of SR, corr 0.78) — as disclosed — and contributes −0.22pp ann / +0.02 SR to V3: **V3 ≈ V2 in substance.** Its corr vs the blend it actually joins is 0.166, breaching the 0.15 wire (was measured vs V2).
3. V3 massively violates the ≤1.6x capital-real leverage goal (3.48x mean, 91% of days >1.6x, financing uncharged). At the goal's own cap: ~17.0–20.0%/yr, SR ~3.2–4.2, MDD ~−3.5%, still 0 neg yrs. The 43.6% headline must never be quoted without the leverage qualifier.
4. "Profit ≥ 0 every year" holds 2008+ only (min +13.94%); 2006 stub −1.38%. The 2008 start cut also flatters 2008 (+41.76% from 3/31).
5. Cost honesty: small gaps (0.4bps/side = 0.18%/yr; effective 5.82bps after rebates) — survive 6.4bps fully (43.40%). The dominant unmodeled cost is margin financing on gross>1.
6. No new phenomenology red flags.

TRADE-RECORD NOTE (for future trade audit): the only NEW engine added in iter5 is FF2_DUALGATE — research-only, intended instruments DO NOT EXIST on disk (FF MOM = daily-rebalanced CRSP 6-book L/S momentum; no ETF). Fallback proxy instrument = SPY (twelve_big/SPY.csv), price path = SPY adjusted close 2008-01-02..2026-06-30, variant stats SR 0.771/ann 6.68%/MDD −13.11%. The other 13 engines are previously-audited sleeves (iter4/iter5 records).

AUDIT_V3 DONE
