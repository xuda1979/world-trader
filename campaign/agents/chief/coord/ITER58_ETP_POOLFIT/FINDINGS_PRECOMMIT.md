# FINDINGS_PRECOMMIT - ITER58 ETP-POOLFIT (sealed BEFORE any candidate pool fit or gate evaluation)
Date: 2026-09-20, GOAL100 session 38. Operator objective verbatim: leverage <= 1.6 / maximize Sharpe / annual return >= 20 pct.
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 cfa9ec4d38158691 / weights a384d6b92e258fd5 (SR 3.820357, cagr 23.9215, gross 1.0, gear-argmax of the flat zone).

## CELL (closure-falsification audit number 2)
#148's DATA-INVENTORY CLOSURE (landed inventory fully measured; new axes require NEW data / rule change) rests on a consumer-role bucketing of references. This cell tests that bucketing for tools/quant/data/more_etf (85 ETP CSVs, R2-R4 vintage, manifest hygiene jump_days=0 / dup_dates=0 / maxgap<=5): the dir is REFERENCED (bench_r5 manifest consumes 7 rows as benchmark passives) but its futures-holding members were NEVER pool-fitted as candidates under the CURRENT objective. Evidence: grep of all coord driver_iter*.py = zero loads of more_etf; ITER27's 29-ETF cell was cboe_hist sector/country/bond/credit/metals-equity, a DIFFERENT universe. Prior verdicts on these series are R5-era STANDALONE-gate results (SR>=1.0 battery, champion SR 3.1810 era, old cost model) on DIFFERENT constructions (USCI-vs-DBC spread anti-signal; DBE-vs-DBP sector RV). Per the 8c-misalignment law (#118) and the ITER42 re-adjudication precedent, standalone-era rejections do not transfer to the current pool-fit objective. This is the #147-class audit-gap pattern measured the #148 way.

## UNIVERSE (mechanical, availability-only; no performance input)
more_etf members classified as futures-holding real-asset ETPs (commodity/currency). Excluded classes, each already measured-closed: equity-sector/country ETFs (ITER27/28), bullion GLD/SLV/IAU (carryv2 in-pool = duplicate class), bond/credit ETFs (a6r7/bund/cad cells). Census screen (ITER23 criterion): IS rows > 500, live >= 2024, manifest PASS. Uniform hygiene bounds pre-sealed: no NaN; calendar gap <= 5d; stale-close run <= 5; max 1d return < 35 pct (split-artifact bound). Result: 13 candidates.
FULL-COVERAGE (8; fit frame 2008-03-31..2017-01-01, 2207 series rows each): DBC GSG DBA DBE DBP UNG USO UUP
LATE-START (5; 2010-11 launches): BNO CORN SOYB WEAT USCI
HYGIENE-EXCLUDED (2, disclosed): CANE (6-day stale run 2013-12-10..18); CPER (8-day launch-era run 2012-09-26..10-08, 374 zero-ret rows = 10 pct of history). Copper recorded DATA-BLOCKED in this vintage, not signal-blocked.

## CONSTRUCTION (ONE, frozen; no sweep)
tsmom-189 vt015 single-stream transplant, byte-verbatim the ITER57-certified machinery: sign(px - rolling(189, min_periods 94)), Wednesday rebalance (wed_rbd), T+1 full-dw via r6lib.wback_rb (6.4bp core), harness vol_target vt_ann=0.15 expanding(60), dropna. A1a recipe fidelity vs the committed QAxasts vt015 CSV: maxdev 9.996e-17, inner 4947 (probe_iter58.log). Per-candidate stream sha16s sealed below; the driver asserts byte-equality and source-CSV sha16s (fail-closed vs concurrent-writer mutation).

## PROBE FACTS (pre-seal; probe_iter58.log)
DBC  2008-01-02 2026-09-04 n=4701 ISrows=2207 stale=2  maxr=0.0794 src=107cbc3535218ec1 stream=0960fbcf54e6a149
GSG  2008-01-02 2026-09-04 n=4699 ISrows=2207 stale=1  maxr=0.1208 src=77d1870c43c1f940 stream=8ec1fdc0a9cf84f7
DBA  2007-01-05 2026-09-04 n=4948 ISrows=2207 stale=2  maxr=0.0861 src=7a12c1e0d6f11f65 stream=dc2a31ace529b50d
DBE  2007-01-05 2026-09-04 n=4948 ISrows=2207 stale=1  maxr=0.1405 src=8bcb758694cbcb30 stream=8102082229a070c7
DBP  2008-01-02 2026-09-04 n=4699 ISrows=2207 stale=1  maxr=0.1471 src=82b2823c288088ee stream=2e09fcdc029df9d0
UNG  2007-04-18 2026-09-04 n=4878 ISrows=2207 stale=2  maxr=0.2485 src=74c775cf9d3a17ff stream=d9cf23ca4141a139
USO  2006-04-10 2026-09-02 n=5132 ISrows=2207 stale=1  maxr=0.2532 src=10a90c071ec36a96 stream=fdfb60bdecd84fe7
UUP  2007-03-01 2026-09-04 n=4911 ISrows=2207 stale=3  maxr=0.0602 src=9e093cb4f376f99f stream=ed0482bd2e17aa00
BNO  2010-06-02 2026-09-04 n=4091 ISrows=1659 stale=5  maxr=0.2191 src=165133b3cf7bbdd4 stream=a76a2d21f61f7c8d
CORN 2010-06-09 2026-09-04 n=4086 ISrows=1654 stale=2  maxr=0.1459 src=a579ceacc2dc1d21 stream=ecad35713c1293cc
SOYB 2011-09-19 2026-09-04 n=3763 ISrows=1331 stale=2  maxr=0.0967 src=b53ab1388a569b6b stream=4387402ed5c4b327
WEAT 2011-09-19 2026-09-04 n=3763 ISrows=1331 stale=2  maxr=0.1561 src=33c6813fc1c5db93 stream=48a27ad7cfb65e94
USCI 2010-08-10 2026-09-04 n=4043 ISrows=1611 stale=1  maxr=0.1088 src=2d02edf741bf4881 stream=b8a77a8d54149f45

## PRE-SEAL AMENDMENTS (both disclosed, both BEFORE any candidate stream was adjudicated)
A1 stale gate: the FX rule (stale run <= 1) is mis-specified for ETP closes (legitimate penny-repeats; zero-return rows are real prints for thin ETPs). Re-specified to run <= 5 for ALL candidates uniformly after DBC tripped it. LOOSER direction, disclosed; bound identical for every candidate; no per-candidate tuning.
A2 machinery: r6lib.wback_rb requires DataFrame frames; single-stream Series wrapped with to_frame. Machinery only, no science content.
No direction gate is applicable: sign-trend is symmetric long/short (ITER57's direction gate existed only for the USD_x foreign-long inversion choice).

## FIT AND GATES (verbatim ITER57 driver machinery)
Frozen block (fit_relw / apply_cap / project_wmax / build_book) text-identity asserted vs driver_iter41/36/49. 13-pool + candidate ONE-AT-A-TIME; NO joint multi-candidate fit (not pre-registered, disclosed). Filters: IS-SR > 4.218504 + 1e-4 (jitter), IS-MDD >= -6 pct, 0 IS negative years, Wmax_sf <= 2.0 (scale-free: max_share x k_covered), fit-row shrink g8 <= 2 pct. ONE global IS-argmax among admitted; ONE reveal; stop rule: fail => no second reveal. Reveal gates G1-G8 verbatim from driver_iter57 (FS ann >= 20 pct, gross <= 1.6, FS MDD >= -7 pct, 0 FS neg years, CFX4 = 0, Wmax_sf <= 2.0, G7 OOS police = >= 4/5 positive bins AND min bin >= -0.10 AND FS SR > 3.820357, g8 <= 2 pct).

## PREDICTIONS (sealed pre-run)
P1 the late-start 5 fail G8 structurally (fit-row shrink far above 2 pct); their IS rows are still recorded for the ledger.
P2 energy members (USO UNG DBE BNO) earn near-zero weight (partial duplicate of the diescrack/C5ng energy trend exposure).
P3 UUP earns zero weight (FX trend measured-closed at relw 0.00000 exactly, ITER57).
P4 only the broad/agri members (DBC GSG DBA DBP) can live at the IS bar.
P5 modal global verdict: NO-ADMISSION (6 of 6 prior novel sleeves rejected at this bar) => no reveal, honest negative, 33rd axis.

## INTEGRITY
Champion pair sha16 pre == post asserted by the driver. Suite pins land same-session (mutation-proven RED before GREEN); manifest LEDGER_AXES 32 -> 33 with row (etf-fut-etp,[58]) in the SAME landing (era-pin duty, #148 precedent). px_convention = close_price (not TR; distributions leave small negative gaps - disclosed; 189d MA robust to them). Data vintage = more_etf R2-R4 (landed 2026-09-07/08), NOT re-fetched - the cell measures the LANDED vintage, byte-pinned above.
