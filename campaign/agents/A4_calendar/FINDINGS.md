# A4_calendar FINDINGS

## Round r1 (2026-08-28)

### Idea 1: Turn-of-month, SPY long/cash — FAIL
Grid a_last∈{0,1,2} × b_first∈{2,3,4} days, long SPY 1993-2026, T+1, 6bps/side.
Best full-SR = 0.43 (0,3) / 0.42 (2,3..4). Peak SR < 0.6 gate -> FAIL (all 9 cells below 0.6).

### Idea 2: Holiday effect (pre/post-holiday long SPY) — FAIL
Calendar-gap detection of pre/post-holiday days (298/297 events, 1993-2026).
Gross edge: pre-holiday +9.2bp (t=1.7), post +5.2bp (t=0.7) — after 6bps/side on ~8 switches/yr
the book nets SR=-0.09 (pre-only) / 0.04 (pre|post). H2 SR ~0. Edge not tradeable net of costs. FAIL.

### Idea 3: Halloween / seasonal windows — FAIL
Monthly means confirm seasonality (Nov +12bp, Sep -3.7bp) but:
- Halloween long Nov-Apr: SR=0.48 (< 0.6), 11 neg years, worst -14.2% -> FAIL
- Avoid-September (flat Sep): SR=0.62 BUT 7 neg years, worst year -31.6% -> FAIL gate (d)
Seasonality real but too weak/unhedged as a standalone long/cash book.

### Idea 4: xs TOM on the 298-name panel — FAIL (sign is NEGATIVE)
Equal-weight panel, TOM = last day + first 3 days of month (24% of days), 2006-2026.
Mean per-stock TOM-minus-ROM = **-2.0bp/day** (xs t=-4.0, only 115/298 stocks positive):
in this large-cap panel TOM days are systematically WORSE — opposite of the small-cap literature.
High-vol names no better (-2.3bp) than low-vol (-1.6bp); only 12/21 years positive, 2008/09 hugely negative.
Direction contradicts TOM-on-SPY (positive there), so xs-short-TOM is a candidate but
long-xs-TOM is dead. FAIL as charter-specified (long concentration hypothesis).

### Idea 4b: xs SHORT-TOM (EW panel long except last day + first 3 days) — FAIL
scramble p=0.04 (real effect) and H2 SR=0.67, but full SR=0.39 after 39% vol (raw EW panel,
no vol-target), 3 neg years, worst -12.2%. Vol-targeting pass below. Effect REAL but sleeve too weak standalone.

### Idea 4c: xs SHORT-TOM vol-targeted 10% — FAIL
Vol-targeted SR=0.35 (H1=0.36/H2=0.67), scramble p=0.04, worst year -7.8% — passes (c),(d),(e)
but fails (a) full SR>=0.6. Plateau flat (0.33-0.36) = real effect, just not strong enough.
NOTE: effect direction (TOM days negative for big caps) is itself publishable; save nothing.

### Idea 5: composite calendar overlays on SPY — FAIL
TOM+Halloween SR=0.51 (11 negYr, worst -20.7%); TOM|noSep SR=0.62 (8 negYr, worst -31.1% fails d);
TOM+Hol+noSep SR=0.51; TOM+preHol+noSep SR=0.34. All fail neg-year/yearly gates (long/cash equity beta).
xs pre-holiday EW: gross +18.4bp (t=2.7, 186 events 2006-26) — real but SR=0.21 net. FAIL.
No FOMC dates file found on disk; pre-FOMC drift untested (data gap, listed as future work).

### Idea 6: weekday effects — FAIL (no tradeable, stable pattern)
SPY: Tue +7.8bp (t=2.7) but Mon +6.1, Wed +5.6 — pattern is "most days positive" (equity drift),
not a weekday spread. Panel: Tue +10.4bp t=2.7, Fri +7.4 t=2.1 but Monday sign flips across
decades (+1.1/-17.1/+6.0bp). No stable weekday anomaly to build a sleeve on. FAIL.

### Idea 7: quarter-end window (SPY last2+first2 of quarter) — FAIL
In-window +8.8bp vs out +3.9bp/day — small positive tilt, but the long/cash book nets
SR=0.19 (13 negYr). Equity drift dominates; no standalone sleeve. FAIL.

### Idea 8: xs Halloween (Nov-Apr minus May-Oct, EW panel) — FAIL
Nov-Apr +7.8bp/day (t=2.9) but May-Oct ALSO +7.8bp (t=1.2) — zero seasonal spread in 2006-26
panel (only 11/21 years with Nov-Apr outperform; 2009 alone -86.6% cumulative diff).
The famous Halloween effect is absent post-2006 in equal-weight large caps. FAIL.

### Idea 9: VIX-conditional TOM — FAIL
TOM edge exists in both VIX regimes (+5.0bp low, +8.3bp high) — conditioning adds nothing.
"TOM & VIX>=20" long/flat: SR=0.13. L/S calendar spread (long TOM/short ROM): SR=-0.25 (the
ROM side carries all the return; TOM-vs-ROM timing adds NEGATIVE value once costs applied). FAIL.

### Idea 10: short-TOM-days-only (short EW panel on TOM days, flat else) — FAIL
Gross TOM-day edge is only -3.7bp/day on the EW panel and vol-targeting on a 24%-exposure
book gives SR=-0.45 after costs+leverage churn. Shorting costs kill it. FAIL.
SUMMARY SO FAR: the only tradeable direction found = LONG the rest-of-month (avoid TOM days) —
real (scramble p=0.04) but SR 0.35-0.39, below gate.

### Idea 11: ROM-long on EXT panel (440 names) — BLOCKED BY DATA BUG
EXT panel EW return explodes (ann +1928%!) — penny/OTC tickers (AFRMF, AIXXF, ...) with
junk fills/units. EW over 440 raw names is meaningless without per-name hygiene.
(Removed 63 duplicate-date rows in EXT as data hygiene; raw EW still unusable.)
scramble p=0.03 but numbers are garbage — honest verdict: NOT EVALUABLE as EW.
Filtered/median construction is future work. FAIL (data).

### Idea 12: ROM-long on hygienic EXT (price>=$5, 5%-trimmed mean, 226 names) — FAIL
std 0.25/day and max +19.3 returns persist in EXT even after filters (bad tick data) —
trimmed book SR=-0.17, H2=-0.56. EXT panel data not usable for calendar work without deeper
cleaning (out of scope). FAIL (data quality).

### Idea 13: ROM-long + seasonal weight tilt (1.25x Nov-Apr / 0.75x May-Oct) — FAIL (best so far)
Big-cap EW 298, avoid TOM days, seasonal tilts, vol-targeted 10%:
SR=0.41, H1=0.40, H2=0.65, negYr=3 (worst -4.3% passes d!), scramble p=0.04.
Passes (c),(d),(e) but full SR 0.41 < 0.6 -> FAIL (a). Better halves balance than plain ROM.

### Idea 14: SPY ROM-long 1993-2026 (with/without seasonal tilt) — FAIL
SR=0.30/0.31, H1 weak (0.16-0.19). The xs version on big-caps (idea 13, SR=0.41) is better;
SPY-level ROM is weaker. FAIL (a),(c).

### Idea 15: paycheck-cycle window (dom 24-31 + 1-3) — FAIL (closest yet)
SPY gross edge: in-window +7.9bp vs out +2.3bp (t=3.5!). Panel version unstable (t=1.4, 11/21 yrs).
SPY sleeve net vol-targeted: SR=0.49 (H1=0.48 H2=0.53, scramble p=0.02, decade SRs 0.49/0.34/0.65)
— consistent across halves and decades, 9 negYr (worst -10.9%) fails (d); SR<0.6 fails (a).
This is the strongest calendar sleeve found; combines conceptually with ROM (paycheck ⊃ TOM).

### Idea 16: composite pay|noSep (long dom24-3 OR not-Sep, 95% expo) — FAIL (2nd closest)
SR=0.64 ✓(a!) but negYr=5, worst -19.8% FAILS (d). pay×seasonal(flat Sep): SR=0.51,
worst -6.5% ✓d but SR<0.6 ✗a. The SR-vs-yearly tradeoff never resolves on SPY alone:
long/cash calendar books inherit 2008 equity beta. No SPY-only calendar sleeve passes ALL gates.

### Idea 17: paycheck window × MA200 / VIX conditioning — FAIL
pay&aboveMA200: SR=0.22; pay&hivix: SR=0.31 (6 negYr, worst -8.5% but SR<0.6);
pay long-below/short-above: SR=-0.26 (trend-conditioning destroys the calendar edge).
Conditioning reduces exposure without improving SR. FAIL.

## ROUND r1 VERDICT (A4_calendar)
17 ideas tested across TOM, holidays, Halloween/Sep, quarter-end, weekday, paycheck cycle,
VIX/trend-conditioned variants, xs panel versions, SPY 33-year proxy.
- NO sleeve passed ALL gates. Best candidates:
  * pay|noSep composite: SR=0.64 (passes a,c) but 5 negYr worst -19.8% fails (d)
  * paycheck-window: SR=0.49, H1/H2 0.48/0.53, scramble p=0.02, decades 0.49/0.34/0.65 —
    fails only (a) 0.6 and (d) 9 negYr
  * xs ROM-long big-cap EW: SR=0.41, scramble p=0.04, worst yr -4.3% — fails only (a)
- Calendar effects on long/cash equity books cannot clear the vol-neutral yearly gates.
  They are candidate OVERLAYS (e.g., tilt weights of existing equity sleeves) — recommend
  coordinator test: tilt existing long-equity sleeves toward ROM/paycheck windows.
- Data gaps noted: no FOMC dates file (pre-FOMC drift untested); EXT panel unusable for
  calendar work (bad ticks; 63 dup-date rows fixed).
ROUND r1 DONE

## Round r2 (2026-08-28) — overlays/tilts on existing sleeves (charter r2)

METHOD NOTE (honesty): base CSVs already net 6bps; a tilt w_t (decided at close t from
data<=t) multiplies ret_{t+1} and pays 6bps on |Δw| at t+1; vol-target wrapper uses
expanding trailing-only stats (min 60d). Scramble = mask day-roll (200-1000 draws, seed 7),
which destroys calendar alignment while preserving up-day fraction — the correct test for
overlays. Additional guard: |corr| to base < 0.95 (else the "sleeve" is a near-duplicate
of the base and adds nothing to a blend targeting mean |corr| < 0.15).

### Idea 18: paycheck x ROM tilt on LIB:L_S_130_30 (charter item 1) — FAIL
Full grid (w_pay 0.5-1.25 x Sep-delever 0-1.0, all VT-10%): best SR=0.74 (H1 0.74/H2 0.74,
1 negYr worst -3.1%). Decomposition: base raw SR=0.85 -> VT-only 0.71; paycheck tilt DeltaSR=0.00
(0.71->0.71 at w_pay=1.0 AND at 0.75/1.25); flat-Sep only +0.03 (0.71->0.74). The paycheck
component is a NO-OP on this sleeve (r1's SPY pay-edge does not transfer to L/S book).
Sep-delever passes a,c,d but FAILS (e): day-roll scramble p=0.155; month-permutation null
p=0.25 (de-levering Feb gives 0.79, Mar 0.78 — better than Sep's 0.74 in-sample). September
specialness NOT established on L_S_130_30. Do not save.

### Idea 19: quarter-end / turn-of-year windows (charter item 2) — FAIL (one real sub-effect)
qend tilt (last ~4 + first ~4 days of quarter): SR 0.69-0.70, scramble p=0.43-0.61 — dead.
TOY bump (Dec20-Jan10 x1.25) on LIB:L_S_130_30_volmanaged: SR 0.80->0.82, TOY-window mean
+21.5bp/day vs +6.5bp out-of-window, neg in only 3/18 years; scramble p(1000)=0.044 (REAL);
plateau across 8 window variants SR 0.80-0.83 (no spike); monotone in weight (x1.1:0.81 ...
x2.0:0.87). BUT negYr=4 fails (d) and corr-to-base ~0.97 (near-duplicate). Same bump on plain
L_S_130_30: scramble p=0.135 fails (e). The TOY effect is real but cannot clear ALL gates on
any base tested. Do not save.

### Idea 20: composite weekly overlay (charter item 3) — FAIL (borderline, rejected)
Best composite (TOY x1.25 x flat-Sep 0.25 on volmanaged): SR=0.89, H1=0.88/H2=0.89,
negYr=2 (2015, 2016), worst -2.0%, dd small — passes (a),(c),(d) — but scramble p(1000)=0.088
FAILS (e); p is seed/sample-size fragile (0.055-0.110 across 200-draw seeds). Generality
fails: same composite on L_S_120_20 p=0.156, plain L_S_130_30 p=0.194. Composite of two
weak masks = weaker evidence, not more. Do not save.

### Idea 21: "October crash-season defensive" pivot (charter item 4) — FAIL
Lagged-VIX-pctile (252d trailing rank of prior-day VIX, strictly <=t) de-lever of Sep-Oct on
L_S_130_30: SR DROPS below VT-only baseline at every threshold (0.64-0.70 vs 0.71; thr=0.9
w=0 is worst 0.64), scramble p=0.50-0.97. All-year VIX-pctl defensive: best cell thr=0.9
w=0.5 SR=0.73 but 3 negYr + p=0.20. High-VIX conditioning destroys value on this L/S book
(it is net-short-crash, so VIX spikes coincide with its best days). Hypothesis rejected.

## ROUND r2 VERDICT (A4_calendar)
4 charter items tested, 0 sleeves saved — no overlay/tilt passed ALL gates. Two near-misses:
  * TOY bump (real by scramble p=0.044, plateaued) fails yearly gate + near-duplicate corr 0.97
  * TOY x flatSep composite (SR 0.89, 2 negYr, worst -2.0%) fails scramble p=0.088 @n=1000
Structural conclusions for the coordinator:
  1. Calendar tilts on L/S equity sleeves add +0.00 to +0.09 SR at corr>=0.92 to the base —
     they are NOT new sleeves and would not diversify the blend (mean |corr| target 0.15).
     The library equity sleeves are already the better vehicle; calendar timing is a
     refinement, not a source of independent return.
  2. Only calendar effect that survived honest scramble testing in r1+r2: turn-of-year
     (Dec20-Jan10). Everything else (paycheck, Sep, quarter-end, holiday, weekday, Halloween)
     is either absent post-2006 in large caps or indistinguishable from random-window de-lever.
  3. FOMC dates still unavailable on disk (pre-FOMC drift untested; needs a dates source).
  4. Suggest: treat TOY-strength as a candidate micro-tilt inside the coordinator's equity
     sleeve construction (not as a separate sleeve), and stop allocating calendar ideas to
     standalone/overlay equity books.
ROUND r2 DONE
