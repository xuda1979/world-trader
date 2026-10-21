# GOAL100 ITER12 — NEW-DATA HARVEST: EIA WEEKLY STORAGE FAMILY (2026-09-06)

## USER GOAL (standing): "use new + add more free data"

## WHAT WAS FOUND

**The EIA weekly natural-gas storage family that C5_newdata CHARTER_2 declared
"unavailable free" is OPEN** — reachable keyless at the dnav mirror
`www.eia.gov/dnav/ng/hist_xls/<ID>.xls`, while `ir.eia.gov` WAF-blocks our egress.
Discovered by probing (the dnav serves XLS for the series that survived EIA's
site redesign; IDs enumerated by scraping `NG_STOR_WKLY_S1_W.htm`).

## DELIVERABLES

1. `tools/quant/data/eia_weekly/` — NEW data dir:
   - `eia_dl.py` — stdlib-only OLE2/BIFF8 parser + fetch + fail-closed lint
     (no xlrd/pandas dependency; handles SST/RK/MULRK/NUMBER/LABELSST/LABEL).
   - `test_eia_dl.py` — 6 tests GREEN (incl. integration vs the real file).
   - 13 certified tidy CSVs + `manifest.csv` (authoritative lint record with
     `steady_from` certification windows) + `README.md` (source, license,
     PIT release-timing rules).
2. Lint discipline: weekly/monthly zero-gap; daily holiday-tolerant (<=6d) with
   steady-era certification (pre-2010 holes + 2005 Katrina halt excluded from
   certification, FULL history retained in CSV).

## CERTIFIED SERIES (13)

| family | series | freq | certified span |
|---|---|---|---|
| NG storage | L48 + east/midwest/southsalt/southnonsalt/west/other/salt (8) | weekly | 2010-01..2026-08 (870 wks, 0 gaps) |
| PET weekly | crude_prod / crude_imports / total_products_supplied (3) | weekly | 1986+/1990+ .. 2026-08 |
| dailies | natgas HH spot / brent spot (2) | daily | 2005-10+ / 1990+ .. 2026-09 |

Cross-check: EIA dnav natgas-HH daily == FRED DHHNGSP **byte-identical**
(max rel diff 0.0 over 5260 overlapping days) — the dailies are a redundancy
cross-check, NOT new domain. The NEW domain is the weekly storage/flows family
(11 series, none previously on disk).

## HONEST VALUE PROBE (not an engine claim)

L48 storage surprise / 5y-band deviation / WoW injection rate, trade next-week
natgas spot, PIT lag T+5d (Wed 10:30 ET publication), 6.4bps one-side full |dW|,
signal-permutation scramble (1000 shuffles):

| config | best | verdict |
|---|---|---|
| all 12 configs | SR 0.29 (WoW-follow g=10), scramble p >= 0.24 | **NEGATIVE** |

Signal is real and cleanly measurable but **fully priced by publication** —
consistent with the campaign's 56-family no-alpha pattern. DEAD_IDEAS 56 -> 57
(HUNT_EIA_STORAGE, scoped honestly to L48-only probe).

## WHAT THE DATA IS GOOD FOR (affordances, untested)

- REGIONAL storage (E/MW/S/W + salt/non-salt split) — basis/regional-spread
  engines, potential decorrelation vs the C5ng weekday book.
- crude_prod/imports/products_supplied weekly — WTI crack-spread and
  refining-margin engines (B2's brwt sleeve is price-spread only; flows data
  was never on disk).
- C5ng champion sleeves: EIA dailies now provide an independent
  second-source mirror for the natgas spot prints (byte-identical = source
  validation of the champion's input data).

## NEXT STEPS (not done here)

1. Regional-storage basis engines (untested affordance, highest affinity).
2. Crack-spread engines from the weekly flows trio.
3. Re-probe `ir.eia.gov/ngs/ngshistory.csv` from unblocked egress for pre-2010
   weekly storage (full-history weekly would extend engines back 16y).
