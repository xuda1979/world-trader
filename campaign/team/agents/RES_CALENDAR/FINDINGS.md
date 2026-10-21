# RES_CALENDAR FINDINGS

## Round r1 (2026-09-08) — charter domain: calendars / macro-seasonal / known-schedule events

METHOD: honest pipeline throughout — T+1 via bt.engine.lag_signal; trailing expanding VT10
(shift-1, floor 0.2, cap 3.0); cap_leverage 1.6; 6.4bps/side full |dW| (entry included);
borrow 0.5% on shorts; margin 4.5% on (gross-1). Acceptance via bt.gates.run with
sig= + leak_check default-ON + corr-to-champion (GOAL100_RAWEW13v2_WEIGHTED_GEAR16).
Known-schedule effects traded AFTER the release only (bt.align conventions).

### DATA-LINT FINDING 1 (blocking, high value): on-disk FOMC schedule file is CORRUPT
`tools/quant/data/newdata/fomc_dates.csv` fails validation against the public FOMC calendar:
2021 has 4 rows, NONE of them a real decision day (file 2021-01-26 / 03-04 / 06-27 / 09-02 vs
real 01-27 / 03-17 / 04-28 / 06-16 / 07-28 / 09-22 / 11-03 / 12-15); 2022 has 2/8 (both wrong);
2023 has 3 rows + one with day2=NaN (row 105), 0/8 real; 2024 4/8 (all wrong). Fail-closed:
DO NOT USE for any PIT backtest. Pin: tests_r1.py::test_ondisk_fomc_csv_is_corrupt_2021plus.

### REBUILD: FOMC announcement-day calendar 2008-2025 (direct HTTP, no browser)
Rebuilt from federalreserve.gov (fomccalendars.htm + fomchistorical{year}.htm, one GET per
year, urllib, UA-tagged). Parser: `<Month> D-D ... Statement` (calendars page) / `... Meeting`
(historical pages); cross-month renderings "Jan/Feb 31-1" and "Oct/Nov 31-1" mapped to
Feb-1 / Nov-1 decision days (2017, 2018, 2023 affected). 2020 COVID: Mar 2 unscheduled meeting
=> statement 8am Mar 3 (decision day = 2020-03-03); Mar 17-18 became the special Sunday
Mar-15 phone meeting. FINAL: 145 days, 8/year every year except 2020 = 9. Saved:
work/fomc_ann_final.json (+ raw HTML snapshot work/fed_source_calendars.html). Pinned:
tests_r1.py::test_rebuilt_calendar_matches_public_knowledge. TEAM ACTION SUGGESTED: replace
the corrupt newdata/fomc_dates.csv with this file.

### Idea 1: FOMC day-after equity short (trade after release, no lookahead) — REAL, FAILS (a)/(d)
EW basket of 82 more_etf ETFs (2008+, clip +-25%, >=250 obs): day-after-FOMC mean -24.50bp/day,
t=-2.54 (n=144; final calendar), control +1.66bp. Effect is 1-day only (drift profile k=0
+28.96bp t=+3.15 is the ann-day itself - NOT tradeable same-close without PIT breach on the
2pm release... ann-close entry IS PIT-legal 14:00<16:00 and used; k>=2 dead). Honest book
(short at ann-day close via sig on ann-day rows, VT, costs): net SR 0.263, ann +0.44%,
7 negYr, worst -1.85%. GATES: sr 0.471(unit-scaled) FAIL; halves 0.58/0.35 FAIL(h2);
neg_years 7>2 FAIL; uniq 0.030<0.08 FAIL; corr 0.005 PASS; scr_p 0.000 PASS; leak PASS.
Root cause of failure: FREQUENCY CAP - 8 events/yr * 1-day hold cannot carry 12.8bps/event
round-trip + yearly gate. gross SR ceiling ~0.69, net ~0.36.

### Idea 2: UNG (natgas-futures ETF) short-Thursday — REAL, FAILS (a)/(d)
Weekly scan 82 ETFs x 5 dows x 2 windows (410 tests, Bonferroni bar |t|>=3.5): survivors =
EMB/SHY/BIL Monday (distribution ex-date ARTIFACT - see Idea 4) and UNG Thursday -37.1bp
t=-3.53 (n=946) - the only REAL structure. NOT the champion's C5ng spot effect: UNG is
futures-based, effect is ALL-YEAR (C5ng is Apr-Oct spot), and corr to champion 0.081<0.15.
Net (short held Thu, entry Wed close): SR 0.354, ann +1.82%, 6 negYr, worst -4.36%, MDD -17.4%.
GATES: sr FAIL; h1 0.39 FAIL; negYr 6>2 FAIL; corr 0.081 PASS; scr_p 0.11 FAIL(solo); leak PASS.
Grid (entry x hold x season) best cell 0.383 — plateau, not spike, but far under 1.0.

### Idea 3: composite 50/50 (FOMC day-after + UNG Thursday) — best of round, FAILS (a)/(d)
decorrelated pair (both mechanisms survive on different assets/frequencies). FINAL numbers
(145-day calendar): SR 0.592, H1 0.544 / H2 0.640 (halves PASS), 5 negYr>2 FAIL (worst -2.21%
PASS), ac1 -0.009, uniq 0.209, corr to champion 0.080 PASS, 200x block-scramble p=0.015 PASS,
leak PASS. Composite pass=False. Repro: sleeves/repro_r1.py [5]. Pinned in tests_r1.py.

### Idea 4: DATA-ARTIFACT intel (high value): income-ETF "month-end/weekday" effects are FAKE
Bond/income ETFs (BIL/SHY/AGG/BND/TIP/EMB/LQD/HYG) show large NEGATIVE month-turn
(BIL MT1+1 -4.5bp t=-8.5; HYG -19.1bp t=-6.1) and Monday (EMB -8.5bp t=-3.7) effects.
These are MONTHLY-DISTRIBUTION ex-date drops priced in close-to-close returns, not alpha:
- sign pattern flips exactly at asset class (non-dist equity ETFs MT-positive: QQQ +8.0bp,
  VWO +16.9bp, EWT +17.1bp, GDXJ +36.9bp - all |t|<2.6); - magnitude ~= monthly yield
  (BIL -4.5bp ≈ 1mo T-bill yield); - persistent post-2015 (HYG 2015+ -16.5bp t=-5.8) yet
  median-driven and NOT shortable economically (short seller pays the distribution).
Any calendar hunt using unadjusted ETF closes MUST exclude distribution ex-dates or use
total-return data; A4/E2 SPY-based results are unaffected (SPY dist = quarterly, small).

### Idea 5: pre-FOMC drift + USD/FX + rates legs — thin, rejected at screen
pre-ann-day on NASDAQ +8.1bp t=0.64 (nothing). UUP (USD ETF) ann-day -13.7bp t=-2.33 /
day-after +9.4bp t=+1.78: ~14bp/event vs 12.8bps round-trip = uneconomic at 8/yr. DXY index
ann-day -7.9bp t=-2.81 (index untradeable). VIX ann-day -21.0% t=-2.58 (untradeable, C5 r3
already rejected VIX books). 10y yields ann-day move not sign-stable post-2015. All REJECT
at screen; no honest book built.

## ROUND r1 VERDICT (RES_CALENDAR)
0 sleeves saved (charter: REJECT-with-numbers). The known-schedule macro family is REAL on
the equity side (day-after-FOMC t=-2.54 to -2.75, scramble-p 0.000-0.015 in books, corr to
champion <=0.08) and UNG-Thursday is real gross (t=-3.53), but event frequency (8/yr + 52/yr
thin-net) mathematically caps net SR ~0.35-0.60 vs the 1.0 bar — same wall E2 hit on opex/
quarter-end events. Best-of-round composite: SR 0.592, halves 0.544/0.640, negYr 5, corr
0.080, scr p=0.015 — REJECT on (a) SR<1.0 and (d) neg_years 5>2.
Deliverables: work/fomc_ann_final.json (clean PIT calendar, replaces corrupt file),
work/fed_source_calendars.html (raw snapshot), sleeves/repro_r1.py (thin repro),
tests_r1.py (4 TDD pins, all green), corrupt-file + distribution-artifact intel above.
Ideas for any future round (only if re-chartered): (i) total-return index data to rescue
the bond-ETF month-end signal class; (ii) CPI/NFP known-schedule file (no free PIT source on
disk); (iii) pool UNG-Thu with RES_BASIS carry legs if a decorrelated pair emerges.

RES_CALENDAR DONE
