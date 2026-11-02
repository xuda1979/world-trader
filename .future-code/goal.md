# Session Goal

## Goal
Keep research using new data.

## What this means (this round: v71_stale_refresh_20261022)
The V7.1 OOS-decay monitor (regenerated today 18:37:50 by the daily scheduler,
campaign/work_backtest_oos/V71_OOS_DECAY_REPORT.csv) reports **5 of 20 monitored
sleeves STALE** (>35d freshness): brwt7.csv (38d, **17.03% V7.1 weight — largest
stale exposure in the book**), a6_r2_pair_residmom_fm1926.csv (52d, structural
Dartmouth F-F lag), diescrack__prefix.csv (38d), cnpair_M0_RM0_L60Z1.5.csv (38d),
A1_carry_seasonal_v2.csv (37d). Per the documented workflow (STANDUP_LOG 2026-10-08
RED decomposition: "refresh is the documented workflow"; ITER62_REFRESH_WAVE1/work/
TASK2_refreshability_audit.md execution order), the round is: refresh the raw leaves
with accruals through ~2026-10-21, re-emit the stale sleeves append-only with overlap
byte-verify (proven refresh_2026_09_25/reemit_sleeves.py pattern, fail-closed),
re-run the monitor, and re-pin the raw-data manifest if the raw tree changed.

## Checklist
- [ ] Inventory the 5 stale sleeves: builders, raw leaves, source liveness, last-row dates
- [ ] Refresh raw leaves (keyless sources; ET-market-hours rule for price feeds; today
      ~19:00 +0800 = ~07:00 ET Thu = market closed, compliant)
- [ ] Re-emit stale sleeves append-only + overlap byte-verify, fail-closed; champion
      trio and book weights UNTOUCHED (no composition decisions — decay/advisory_prune
      flags on C4/D_xlu_ief/a6_r2 are operator decision items, not this round)
- [ ] Re-run V7.1 decay monitor; expect stale 5 -> 0 or fully-attributed residual
- [ ] Raw-data manifest re-emit + re-pin with ledger note if raw tree changed
      (baseline pin: 11,876 files / 87 axes / tree sha16 cedac0a96ea250e3, commit de05d9e5)
- [ ] Fail-closed tests GREEN vs re-pinned manifest (6/6) + suite delta attributed
- [ ] Standup log entry, independent verification, Status: completed

## Standing constraints
- Explicit-pathspec commits only (2,900+ untracked artifacts at repo root).
- Champion trio STAGED-UNCHANGED; sealed engine code unchanged; no results/ metric
  touched without an honest beat.
- Frontier-closure law (#147/#148): new hunts need NEW data or rule change.
- Raw-data provenance manifest GREEN or deliberately re-pinned with ledger note.
- Addendum B runbook: refresh price feeds only outside ET market hours; append-only
  extends with byte-verify overlap only (tol 1e-10/1e-12 precedent).
- H1 collector healthy (20261021 archived, 9/9 symbols, 9/9 factor rows); next
  HUNT_H1_TAILFACTOR adjudication ~early Dec 2026 unchanged.

## Status: in_progress
Round opened 2026-10-22 ~19:00 +0800. Highest-impact next step identified: execute
the documented stale-sleeve refresh wave (ITER62 TASK2 execution order applied to
today's 5-sleeve stale set).
