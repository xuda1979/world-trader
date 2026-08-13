
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
