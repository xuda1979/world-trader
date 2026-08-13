
## Update 2026-08-12 (loop fire) — Final end-to-end verification + pending user decision

### Verification (clean run, both deployable configs)
- vt10: SR 1.407 / 16.21% / -10.33% (half 1.560/1.296), drag 0.18%/yr
- vt6:  SR 1.404 / 11.61% / -7.61% (half 1.534/1.304), drag 0.18%/yr
Exact reproduction of the logged numbers after all script edits across
fires. The champion is stable and reproducible.

### Pending USER decision (ls framework, deferred not applied)
run_live_signal.py still points at the twelvedata tw320d4 config
(results/validation_test/tw320d4_deep_full/config.json) which FAILS on
the current extended panel (SR -0.19 on 20y, +0.03 on 8y). The ls
framework's LIVE RECOMMENDATION (RESEARCH_LOG L2165): migrate to the
polygon champion (n10_r14, SR 1.42, scramble PASS, polygon data only) or
re-derive a twelvedata factor set. The minimal twelvedata fix
(start_date=2018-01-01) yields only SR ~0.31-0.94 on 8y.
SURFACED to the user, not applied (per the ls framework's own
"user decision" marker). Until decided: do NOT run the current live
config on the extended panel; the champion composite (this project)
is unaffected (transparent signal, verified stronger on new data).

## Update 2026-08-13 (loop) — polygon panel data-incident + champion fragility finding

- A refresh I ran truncated tools/quant/data/polygon 516 -> 500/501 rows via
  Polygon's free-tier 501-bar cap, destroying the 2024-07 leading history (now
  unrecoverable: original panel was ACCUMULATED over days; Polygon won't serve
  bars beyond the ~501 rolling window; data gitignored). Backfilled leading rows
  from twelvedata (seam + overlap verified). Details in RESEARCH_LOG 2026-08-13.
- FINDING: the champion's SR 1.686 does NOT reproduce on any recoverable data
  state. A/B matrix [RESEARCH_LOG 2026-08-13]: restored-516 0.26, truncated-500
  -0.24, clean-poly-501 -0.49, fully-twelvedata-633r 0.38, original 516 = 1.686
  (gone). The edge depended on the ICIR screen selecting
  [liq_turnover mom_12_1m range_vol_60d resid_mom_6m vol_60d], which needs the
  exact accumulated 516-row panel. "likely_overfit" flags were correct.
- INDEPENDENT: AP composite (ls_polygon_daily.csv, built 08-12 21:51, same data,
  pre-incident) shows full SR 1.573 / 2025 1.252 / 2026 2.443 / 2026-07+ 4.207 —
  the data supported ~1.6; the fragility is config-level, not a market collapse.
- CURRENT: live panel = twelvedata-backfilled 516-row (best available: correct
  factor set, coherent signal, honest SR ~0.25). Do NOT trust 1.686 for sizing.
- Next: (a) make refresh append-only [DONE - refresh_polygon_panel.py rewritten,
  tested no-damage]; (b) recommend re-acquiring full polygon history via paid plan
  OR re-baselining the champion on a self-consistent long source; (c) add a
  screen-stability guard (do not emit live signal if IC screen falls back to the
  momentum-heavy set).

## Update 2026-08-13 (loop) — FINAL: polygon champion is OVERFIT (consolidated)
Controlled A/B throughout this session proved the n10_r14 champion's advertised
SR 1.686 is NOT robust. Decisive experiment: ±1 historical row (500 vs 501
trading dates, identical factor set) swings SR ~0.8 (+0.49 -> -0.32). No
reproducible panel state gives a stable SR (0.26/0.49/0.86/1.686 all artifacts).
Failed fixes (all logged, reverted): +ohlc factor family, redundancy-aware
fallback de-dup, cadence densification. The real edge is a FRAGILE ~0.3-0.5 SR on
current polygon data; 'likely_overfit' flags were correct. Full details in
RESEARCH_LOG 2026-08-13 (consolidated verdict).
Operational: do NOT size to 1.686; treat as speculative/paper until re-baselined
on real long history (paid Polygon) or panel-length ensemble averaging. The earlier
"n10_r14 8y OOS FAIL (p=1.000, SR -0.33, unreproducible)" commit (N14) foreshadowed
exactly this - this session forensically confirmed it.

## Update 2026-08-13 (loop) — CAPSTONE: polygon champion DECOMMISSIONED (edge illusory)
Controlled test traced the live-516 (+0.35) vs twelvedata-516 (-0.10) SR gap to a
SUB-BASIS-POINT volume difference: polygon reports exact share counts (float64),
twelvedata rounds volume to nearest 100 (int64) - e.g. 44155331 vs 44155300
(0.00007%). That rounding-level difference in the `liq_turnover` factor inverts SR
by 0.45. The champion's edge is NOT real - it is an artifact of volume-data
precision. All reported SRs (1.686/0.86/0.49/0.35) were precision-state artifacts;
ensemble mean -0.36 (0% positive).

ACTION: live signal DECOMMISSIONED - forces HOLD (action: HOLD, trend_gate
'HOLD (decommissioned: illusory edge)', zero positions). Do not trade this
strategy until re-derived on a volume-consistent feed with an acceptance gate that
an independent volume feed does not invert SR. Details in RESEARCH_LOG 2026-08-13.

## Update 2026-08-13 (loop) — IV book sleeve audit (n10r14 = vol-diversifier, not alpha)
The IV book's largest-weight sleeve ls_n10r14 (0.384 inverse-vol) has no standalone
alpha (proven illusory in RESEARCH_LOG 2026-08-13), yet REMOVING/capping it LOWERS book
SR (1.24 -> 1.08) and WORSENS MaxDD (-5.9% -> -9.3%). It adds value purely as a
low-vol, low-correlation diversifier. Capping at 0.20-0.25 gives SR 1.14-1.18 with
half the concentration - recommended robustness trade. Full table in RESEARCH_LOG.

## Update 2026-08-13 (loop) — DEPLOYED: IV book rolling inverse-vol (SR 1.44, n10r14 de-risked)
Applied the sleeve audit: run_ms_iv_book.py now weights the 6-sleeve IV book with
ROLLING-126d inverse-vol (no lookahead) instead of stale full-sample. Result:
SR 1.24 -> 1.44, MaxDD -5.9% -> -5.5%, half-split 1.41/1.06 -> 1.55/1.32, and the
n10r14 concentration de-risked 0.38 -> 0.16 weight. Robust across window choices
(42/63/126/252 all beat old). ms_iv_daily.csv regenerated. This is the healthy,
OOS-validated, now-de-risked multi-strategy book -- THE deliverable of the line.
