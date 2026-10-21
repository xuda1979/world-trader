# AUDIT_C5NG_DD_DAY — FINDINGS

## Result: GENUINE MARKET MOVE — the champion MaxDD driver day is real, tradeable history; NOT a data artifact

Date: 2026-10-10. Trigger: /loop iteration-1 DD-anatomy work found the
champion MaxDD -3.7339% (2024-01-11) is dominated by C5ng's -21.795%
sleeve day (w=17.94%, contribution -3.91%). Before treating the DD as
irreducible (or re-weighting around it), the day had to pass a
data-quality gate: artifact vs market. This audit is that gate.

## The raw print under question

`tools/quant/data/newdata/DHHNGSP.csv` (FRED DHHNGSP = EIA Henry Hub
daily spot, $/MMBtu), Jan-2024 window:

| date | price | note |
|---|---|---|
| 2024-01-09 Tue | 3.25 | |
| 2024-01-10 Wed | 3.25 | |
| 2024-01-11 Thu | 3.15 | |
| 2024-01-12 Fri | **13.20** | +319% single-print spike |
| 2024-01-15 Mon | (no print) | MLK holiday |
| 2024-01-16 Tue | 3.25 | -75.4% reversion |

Winter Storm Heather (Jan 14-16 2024 Arctic outbreak) context.

## Five independent confirmations that 13.20 is genuine

1. **EIA live website today** (eia.gov/dnav/ng/hist/rngwhhdD.htm): the
   weekly row "2024 Jan- 8 to Jan-12" lists 2.72, 3.25, 3.25, 3.15,
   **13.20** — the current official EIA series carries the same print
   (checked 2026-10-10; not a stale-tree fossil).
2. **Independent in-tree source, different fetch chain**: EIA dnav
   RNGWHHDd via `eia_weekly/natgas_HH_spot_daily.csv` (fetched 2026-09-06,
   stdlib XLS parser, different downloader/fetch-date than the FRED CSV)
   prints 13.20 on 2024-01-12. FRED-vs-EIA overlap 5265 days, 0
   mismatches.
3. **FRED monthly aggregate corroborates**: MHHNGSP Jan-2024 monthly avg
   = 3.18; the daily series' own Jan-2024 average = 3.176 — i.e. FRED's
   monthly aggregation of the daily series INCLUDES the 13.20 print
   (excluding it, the daily avg would be ~2.80). The print is in the
   publisher's own upstream aggregation.
4. **Two additional in-tree FRED copies** (hedge_fund_strats/data_fred/
   natgas.csv 2026-09-26; A3_xs_quality/r7_data/DHHNGSP.csv): all print
   13.20 on 2024-01-12.
5. **Cross-asset coherence**: UNG (natgas futures ETF, independent price
   family) +8.4% on 2024-01-12, -15.1% on 2024-01-16 — the futures
   complex shows the same up-then-crash shape across the storm window
   (futures tracked the Feb contract; magnitudes differ by design; the
   SHAPE matches). AUDIT5_data's spike census already verified the
   DHHNGSP family's big prints (Uri 2021, Jan-2026, 2003) as real with
   "no unit changes"; the 01-12-2024 print is the same class:
   cold-snap spot spike.

## Why the sleeve lost -21.795% on it (mechanics, fully reproduced)

Reconstruction matches the committed sleeve file to 9.97e-17
(`E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv`, value -0.2179459352455247
on 2024-01-11):

- C5ng is the natgas weekday-premium sleeve: short Wed+Thu, long Fri,
  90d-sigma*2.5 spike filter on positions, 10% vol target, 6bp cost.
- The Thu 2024-01-11 SHORT was live and legitimate: |lr(01-11)|=0.031
  << threshold 0.160 — the spike was the *overnight 01-11→01-12 move*,
  unknowable at the Thu close decision time. The short earned
  lr(01-12)=+1.4328 gross: -1.4328.
- The spike filter DID fire on Fri 01-12 (|lr|=1.43 > 0.160), killing the
  Fri long — the sleeve avoided the -140% reversion leg. Exit before the
  spike was impossible without lookahead.
- Vol-target scale that day: 0.1521 (expanding vol 65.7% ann already
  includes the day's own -1.4328 net in the expanding window; the
  same-day contamination slightly DE-levered the position vs the
  spike-free counterfactual 0.168 — conservative direction).
- -1.4328 × 0.1521 = -0.21795 = the committed sleeve value. Zero
  turnover that day (position was -1 since Wed; no exit cost).
- C5ngsum (summer variant, Apr-Oct active, Nov-Mar flat) correctly shows
  0.0 through the window; worst C5ngsum days are elsewhere
  (-4.98% 1998-10-28). The summary's "C5ngsum flat (summer-inactive)"
  statement is confirmed with the correct convention.

## One disclosed PIT subtlety (pre-existing, NOT a defect of this day)

`vol_target` scale[t] uses expanding std INCLUDING net[t], and net[t]
books pos[t]·lr[t+1] — i.e. the scale applied to day t embeds the t→t+1
return (a same-day self-reference). On this day the contamination was
conservative (scale 0.152 vs counterfactual 0.168 → the spike de-levered
itself by ~10%). As-implemented vs scale.shift(1): SR 1.633 vs 1.602,
worst day -21.79% vs -24.03%. This class was already flagged in
AUDIT5_data item 4 (publication-lag severity test; separate remediation
track), does not change THIS day's verdict, and is recorded here for the
DD charter to inherit: any DD-reduction construction must not rely on
the same-day scale reference.

## Verdict for the DD program

The MaxDD driver is **irreducible market risk of a 17.9%-weight natgas
weekday-premium sleeve eating a +143% overnight cold-snap spot spike**.
It is genuine, T+1-causal, cost-accounted, and already partially
mitigated by the sleeve's own spike filter (which dodged the reversion
leg). Data-quality gate PASSED: proceed to the construction-level DD
charter (block caps / DD-aware objectives) with the day treated as REAL
tail, not as a data error to be cleaned.

NO champion files, data files, or sleeves were modified by this audit.
Read-only verification + web confirmation. Frontier unchanged.

DONE audit_c5ng_dd_day_20261010
