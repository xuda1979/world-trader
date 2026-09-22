# HUNT_EIA_PADD — EIA regional PADD petroleum-storage cross-section (honest gate)

Date: 2026-09-22. This closes the seam that AUDIT_R7REDO R8 §7c pre-identified as
"WORTH A ROUND": the certified-but-never-mined 192-series weekly petroleum stock
matrix (`tools/quant/data/eia_weekly/petstk_*.csv`, 1984/1990..2026-08, lint ok,
harvested 2026-09-07 by DATA_ORGANIZE) plus the weekly flows trio, against the
DEAD_IDEAS row 57 scope note ("REGIONAL storage + crude prod/imports/supplied
remain UNTESTED affordances").

## What was tested (3 pre-registered stages, all IS<2017 selection only)

**Stage 1 — regional dysregulation → outright prices (24 configs).**
Cross-sectionally demeaned 5y-seasonal deviations of PADD 1a/2/3/4/5 crude-excl-SPR,
distillate, finished-gasoline stocks (15 series, 1990..2026, n=1913 weeks each),
aggregate dysregulation signed, traded on WTI / NYH ULSD / NYH RBOB / Brent daily
spot returns. PIT: week-ending-Fri stamp, report prints next Wed 10:30 ET, signal
available +5d (Thu), position from next business day. Costs 6.4bps full |dW|.
**Best IS monthly SR 0.173** (crude→ULSD dir+1); bar is 1.0. All 24 configs < 0.18.

**Stage 2 — mechanism-faithful LOCATIONAL BASIS engines (11 configs).**
Exactly the construction R8 7c proposed: PADD2 Cushing glut → WTI−Brent; PADD1a
distillate tightness → NYH−Gulf ULSD basis; PADD1a gasoline → NYH−Gulf gasoline
basis; relative (p1a−p3), (p2−p3) deviations; PADD dispersion regime on the spread.
**Best IS monthly SR 0.104** (E2). Nothing within 10x of the bar.

**Stage 3 — weekly FLOWS affordances (12 configs).**
Crude production, imports, supply(prod+imports) — both 104w z-score and 5y seasonal
deviation, both directions, on WTI. **Best IS monthly SR 0.192.**

## Verdict

**NEGATIVE — the EIA petroleum-stock seam is closed.** 47 configurations across three
mechanism families, none above IS SR 0.20 against a 1.0 adoption bar. This is
consistent with (and now extends) the L48-aggregate natgas result: the EIA weekly
publication is priced by the market at print. The regional cross-section — the one
untested hypothesis the campaign ledger itself flagged — carries no incremental
information either in outright or basis form on free EIA spot dailies.

Honest scope notes:
- EIA *spot* dailies are the price legs; futures roll/carry structures were NOT
  tested (a futures term-structure engine on PADD imbalances remains formally
  untested but is the same mechanism that failed here in basis form).
- Products-supplied weekly (WGTSTUS1w) was declared in eia_dl.py but never landed
  on disk (file absent, manifest row missing) — recorded as a data gap, not tested.
- Sub-PADD 1b/1c granularity exists on disk but the PADD1a-level signals were
  already ~0; finer splits of a null signal were not pursued (diminishing returns).

## Ledger action

DEAD_IDEAS row appended: "EIA PADD regional petroleum-storage cross-section
(outright/basis/flows engines)" — dead, source HUNT_EIA_PADD, evidence "47 configs
across 3 stages, best IS SR 0.19 (flows), 0.17 (outright), 0.10 (basis) vs 1.0 bar;
priced at publication like the L48 aggregate".

## Artifacts
- `honest_gate_padd.py` — stage-1 screen (reproducible; screen_results.csv)
- `stage2_basis.py` — basis engines (stage2_results.csv)
- `stage3_results.csv` — flows engines
- Pin tests: `campaign/bt/tests/test_eia_padd_closed.py`

V7 champion UNCHANGED (reproduce_v7.py still all-PASS; nothing in the champion
builder or ledger touched by this hunt).
