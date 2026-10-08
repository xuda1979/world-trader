# CHARTER: HUNT_NG_REGIONAL — regional (non-L48) natgas storage cross-section

Pre-registered BEFORE any result computation. Date: 2026-10-08.
Gates: coord/GATES_CONTRACT.md verbatim (SR >= 1.0 full-window net after costs,
plateau, halves >= 0.5, <=2 neg years > -5%, scramble 200x p<0.05, corr vs
champion, vt 10% trailing, economic rationale).

## Why this seam is open (provenance)

DEAD_IDEAS row 57 (HUNT_EIA_STORAGE) killed ONLY the L48-aggregate natgas
storage signal and records verbatim: "REGIONAL storage + crude prod/imports/
supplied remain UNTESTED affordances (13 series certified+linted,
tools/quant/data/eia_weekly/)". Rows 66/65 (HUNT_EIA_PADD) then closed the
PETROLEUM side (PADD regional stocks + crude flows, 47 configs, dead) — but
the REGIONAL NATGAS storage cross-section itself was never hunted: row 57's
test used only ng_storage_L48_weekly.csv. Verified today: no
campaign/agents/* hunt consumes ng_storage_{east,midwest,salt,southsalt,
southnonsalt,west,other}_weekly.csv (grep-clean), and no DEAD_IDEAS row names
them. AUDIT_R7REDO R8 §7c named the regional+product seam "worth a round"
before the PADD hunt; the natgas-regional half of that recommendation is the
open remainder.

## Data (certified, on disk, committed manifest 3a94f43736fd9737)

8 weekly series, 2010-01-01..2026-09-11 (n=872 each; refreshed to 2026-09-25
in the live EIA source, the disk vintage is the frozen test input):
east, midwest, salt, southsalt, southnonsalt, west, other (+ L48 aggregate
for reference only, NOT a signal input). Publication timing: EIA weekly
natural gas storage report, Thursday 10:30 ET; row 57's pricing result
("fully priced at publication") is the standing null this hunt must beat.

## Pre-registered mechanism families (18 configs total, fixed now)

Signal core: each region's storage vs its own 5y seasonal band (surplus/
deficit), then CROSS-SECTIONAL construction across the 7 regions. All signals
computed on weekly print dates, position applied T+1 (Friday close), held
until next print (weekly rebalance). Cost 6.4bps one-side FULL |dW|. Books:

F1 dysregulation level (4 configs): z = (storage - 5y-seasonal-median)/5y-
   seasonal-MAD per region, winsorized. Long deficit regions / short surplus
   regions, dollar-neutral, equal-magnitude; variant signs (fade vs follow)
   x band windows (5y vs 4y).
F2 dysregulation momentum (4 configs): 4-week change of F1's z, same
   construction, both signs, z-diff raw vs vol-normalized.
F3 salt-vs-nonsalt spread regime (4 configs): salt (southsalt+salt) minus
   nonsalt (southnonsalt+east+midwest+west+other) aggregate dysregulation
   spread — the salt complex is the marginal injection swing supply; its
   stress states (z below -1.5 / -2.0 thresholds, hysteresis off) gate a
   natgas-complex long/short tilt vs its 63d trailing mean (the only
   directional family; the complex leg uses DHHNGSP from newdata/ at T+1).
F4 L48-vs-sum(regions) residual (3 configs): the aggregation residual
   (L48 - sum of 7) as a data-integrity/flow-proxy signal, both signs, raw
   and z forms — tests whether revisions/report-timing residual carries
   information (low prior, completeness).
F5 relative-region momentum basket (3 configs): rank regions by 4w storage
   build rate vs 5y seasonal; long bottom-quartile-build / short top-quartile
   on the STORAGE Future-adjacent proxies — NOTE implementability: regional
   storage is not directly expressible in liquid instruments; the honest
   expressible form is a natgas-complex (DHHNGSP) tilt SCALED by the
   cross-sectional dispersion (the spread between the most and least
   deficit regions), both dispersion signs.

18 configs total; all 18 run once; no post-hoc additions (stop rule: if
F1-F5 all fail the 1.0 bar, the seam is closed and a DEAD_IDEAS row
"Regional (non-L48) natgas storage cross-section" records the best numbers;
no second round on this seam without NEW data (2010 floor is EIA's own
publication limit, verified live today: dnav hist_xls NW2_* starts 2010-01,
API v2 monthly regional starts 2011-01, ir.eia.gov WAF-blocked).

## Predictions (sealed)

P1 F1 fails ~0.2-0.4 SR: the L48 aggregate result (0.29 best) priced at
   publication extends to the regional cross-section IF the market prices
   the aggregate; only genuinely NEW regional information (salt stress)
   could differ.
P2 F3 (salt stress) is the only family with a chance of clearing halves:
   salt is the marginal swing supply and its depletion states are where
   regional information leads the complex price; still likely < 1.0 on the
   16y span.
P3 F4 is a null/data-integrity control: expected |SR| < 0.15.
P4 Correlation vs champion likely positive for F3/F5 (natgas complex tilt
   overlaps C5ng) — if so, even a 1.0-pass would be marked corr-secondary
   and face a higher effective bar at pool-admission (IS-SR 4.218504).

## Caps

- No champion/weights/manifest/suite file touched.
- Sleeve CSV only if a family clears ALL gates; else honest negative +
  DEAD_IDEAS row (coordinator adds it).
- All numbers from the frozen disk vintages (no re-download; the manifest
  pins them).
