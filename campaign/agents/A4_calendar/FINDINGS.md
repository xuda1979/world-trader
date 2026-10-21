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

## Round r4 (2026-08-30) — charter: TOY concentration book, composite union, champion tilt fallback

METHOD NOTE (integrity fix): the shared-lib `scramble_p` (used in r1) is DEGENERATE — it
np.rolls the RETURN STREAM against itself, leaving mean/std (hence SR) floating-point-identical:
on pure noise it returns p=0.0 (verified; correct test → ~0.5), and it printed the same p for
every grid cell. r1's scramble p-values (0.02-0.04) are UNRELIABLE; no saved sleeve was affected
(nothing in r1 passed gate (a) anyway; sleeves dir empty). r2/r4 use the correct form: roll the
MASK/TILT against the fixed return path and rebuild the full T+1+cost+VT pipeline (5d/21d
multiples, 1000 draws). All r4 p-values below use the corrected test.

### Idea 22 (charter 1): TOY-levered SPX concentration — FAIL
Long SPX (1993-2026 proxy) only in a year-end window, cash otherwise, T+1, 6bps on |Δpos|
incl. vol-target churn, VT via trailing-only expanding std (shift-1, min 60d, lev cap 3x binds
→ vt10/15/20 identical).
Grid 3 starts × 3 ends × 3 VT (27 cells): best SR=0.48 (10/25-1/15, ann 12.7% ✓) but
10 negYr worst -24.5%, MaxDD -61%, H1 0.42/H2 0.59, honest scramble p=0.070 — fails
(a) SR<0.6, (d), (e). Charter-specified Nov1-Jan15: SR=0.43, 11 negYr worst -43%.
Charter's 2008 worry CONFIRMED: winter 2008-09 = -43.0%/-0.5% (bear-market Nov-Jan offers no
protection); 2008+ subwindow SR=0.37, 6 negYr. Big负 years: 2000 -27, 2007 -15, 2015/16 -16/-11,
2018 -14, 2022 -12. The r2 TOY bump (positive mean in Dec20-Jan10) is real but far too small to
carry a concentrated long-equity book through equity winters. FAIL all of (a),(d),(e).

### Idea 23 (charter 2): composite calendar union (TOY∪paycheck∪ROM), ±MA200 — FAIL
Long-SPX union of TOY + paycheck (dom 24-3) + ROM (avoid last day + first 3), vt15:
union no-MA SR=0.47, 10 negYr worst -83%, dd -98% (ROM's 2008 dominates); union+MA200
(trailing-only, shift-1) SR=0.52, H1 0.49/H2 0.56, but 13 negYr worst -51.7%, dd -65%,
scramble p=0.464 — the union's timing is indistinguishable from a random ~40%-of-days long book.
MA200 gate destroys value everywhere (paycheck: 0.48 no-MA → 0.19 with MA; TOY: 0.32 → 0.26)
— trend-conditioning removes exactly the crash-window days that dominate the yearly gate, but
also removes the drift. FAIL (a),(d),(e). Structural: any union of equity windows is still a
long-equity book with 40-60% exposure; no calendar union can fix 2008/2000/2022.

### Idea 24 (charter 3 FALLBACK): TOY/paycheck tilt on the OFFICIAL CHAMPION — FAIL (bar not reached)
Base = campaign/results/CHAMPION_FINAL_daily.csv (official; 2008+: daily SR 1.87, monthly SR
2.00, ann 8.39%, 0 negYr). My 6-leg EW reconstruction corr=0.88 to official (leg windows differ)
→ used official for honesty. Tilt w_t = 1 + mask·(m-1), T+1, 6bps on |Δw|, scramble = roll tilt
calendar vs fixed champion path.
- TOY ×1.25/1.5/1.75/2.0: mSR 2.01/2.01/2.01/2.00 (base 2.00) — ΔmSR ≤ +0.01, Δann ≤ +0.45%,
  scramble p=0.147-0.183 (FAIL e), corr to base 0.98-1.00 (near-duplicate), H1 drifts DOWN
  (1.62→1.59). Champion TOY-window mean +3.9bp/day vs +3.3bp out (raw +0.6bp edge — much weaker
  on the champion than the +21.5bp found on LIB:L_S_130_30_volmanaged in r2; the r2 effect does
  NOT transfer to the diversified book). Fails the charter bar (mSR≥2.05 AND real).
- paycheck ×1.25-2.0: champion pay-window mean 3.1bp vs 3.4bp OUT — the SPY paycheck edge is
  ABSENT in the champion book; every tilt lowers SR (1.87→1.55 at ×2) and adds a neg year
  (worst -3.1% at ×2). FAIL.
Also note: 19/19 champion TOY-window year-sums mostly positive but small (median ~+57bp/yr);
×2 TOY adds only +0.45% ann — immaterial at near-1.0 correlation.
### ROUND r4 VERDICT (A4_calendar)
All 3 charter items tested, 0 sleeves saved (sleeves dir remains empty — nothing in 4 rounds
cleared ALL gates). r4 conclusions:
1. Concentrated calendar books (TOY / union windows, long-SPX) max out at SR ~0.48 with
   8-13 negative years and -25% to -83% worst years: calendar timing cannot survive equity
   winters as a standalone book. CONFIRMED at larger scale than r1.
2. The TOY edge is real but tiny and base-dependent (+21.5bp/day on L_S_130_30_volmanaged in
   r2, +0.6bp/day on the champion in r4) — it is NOT a portable premium; do not chase it further.
3. MA200/VIX/trend conditioning on calendar windows strictly destroys SR (consistent r1+r2+r4).
4. INTEGRITY: fixed a degenerate scramble test inherited from the r1 lib; all r4 p-values use
   mask-roll vs fixed returns; prior r1 scramble p-values should be treated as void (no saved
   artifact was affected).
5. Recommendation to coordinator: stop allocating calendar ideas to this agent; if the blend
   needs return, the lever is sleeve WEIGHTS or new sleeves, not calendar overlays (r2+r4 show
   overlays give ΔmSR ≤ +0.01 at corr ≈ 1.0).
ROUND r4 DONE

## Round r6 (2026-08-30) — NEW-FAMILY charter: overnight-TOM, opex week, TOY-standalone

METHOD: same honest pipeline as r4 (T+1, 6bps/side on |dpos|, VT trailing-only expanding
min-60d shift-1 cap 3x, scramble = roll calendar MASK vs fixed return path, 5d/21d multiples,
1000 draws seed 7). Overnight books: night return = open_{t+1}/close_t - 1, 12bps/night held
(6bps close t + 6bps open t+1); panel hygiene price>=$5 as in r1.

### Idea 25 (charter 1): overnight-TOM intersection, EW 298 panel — FAIL (hypothesis refuted)
**The overnight premium is ABSENT in this panel**: EW overnight 2006-26 = +1.7bp/day gross
(t=1.1, insignificant; 111bp/day vol); intraday leg = +3.0bp/day (t=2.2) — the OPPOSITE sign
of the 1980-2020 overnight-premium literature (drift here lives intraday, consistent with
r1's finding that big-cap TOM days are weak). Intersection shows NO concentration: overnight
in-TOM(1,3) = +1.4bp (t=0.6) vs out-of-window +1.7bp (t=0.9) — TOM does not help.
Net of 12bps/night: ALL-night vt10 SR=-1.47 (ann -77.6%); best cell TOM(1,2) vt10 SR=-0.85;
even TOM-only holds with the most favorable accounting (ONE round trip per month = 1.44%/yr
cost vs 0.67%/yr max gross) = -0.77%/yr. No window/VT cell (9 tested) above SR -0.6.
Scramble p=0.92-0.98 (scrambles do BETTER - i.e. the real calendar placement is if anything
worse than random). A2 intel: overnight book on this panel cannot reach SR 0.8 net; the
charter premise "if A2's overnight SR is real, this should exceed it" is moot — it is not real
gross. Direct test of the A2 premise = the deliverable here. 0 saved.

### Idea 26 (charter 2): opex-week (3rd-Friday week + week after) long SPX — FAIL
SPY proxy 1993-2026, exposure 48% of days (charter cell pre=4/post=5 trading days around
3rd Friday). In-window mean +2.0bp/day (t=1.1) vs out +6.1bp/day (t=3.4): opex weeks
UNDERPERFORM the rest of the month. Charter cell vt15: SR=0.08, H1 0.00/H2 0.18, 16/34 negYr
worst -51.1% (2008), dd -97%. Plateau variants (wk only SR -0.05, wk-after -0.26, wk+3d 0.10,
2d-pre -0.25, expiry-Friday-only -1.09) — none above 0.10; VT 10/15/20 identical (cap binds).
Scramble p=0.93. 2008+ subwindow SR=0.04, 8 negYr. No options-expiry drift to harvest long-only
net of costs; fails (a),(c),(d),(e) by an order of magnitude. 0 saved.

### Idea 27 (charter 3): TOY Dec20-Jan10 standalone long SPX vt15 — FAIL (even with relaxed gates)
The TOY bump itself replicates (in-window +9.9bp/day t=2.0 vs out +3.8bp; exposure 5% of days)
but as a standalone vt15 book over the honest 33y window: SR=0.32, H1 0.26/H2 0.40, 14/34
negYr worst -19.4% (2016, the Feb-2016 VIX spike New-Year window), dd -31%. Charter-relaxed
gates (negYr<=3, worst>-8%) still failed: 14 negYr vs <=3 allowed, worst -19% vs -8% floor.
Window plateau (12/15-1/10: 0.23, 12/20-1/5: 0.28, 12/20-1/15: 0.27, 12/25-1/10: 0.19) is a
low plateau, not a spike; scramble p=0.107 (not significant standalone at 33y; consistent with
r2 p=0.044 on a shorter window being fragile). 2008+ subwindow SR=0.36. The effect is real but
tiny (+6.1bp/day x 22 days/yr ~ +1.3%/yr raw) — cannot carry a concentrated equity book
through its own bad years (2016 -19%, 2022 -5%). Confirms r4 conclusion #2: do not chase TOY
as a standalone. 0 saved.

## ROUND r6 VERDICT (A4_calendar)
All 3 charter items tested, 0 sleeves saved (sleeves dir remains empty after 6 rounds).
1. NEW-FAMILY intel (highest value of the round): the overnight premium is ABSENT gross on the
   298 large-cap panel (+1.7bp/day t=1.1); intraday is the positive leg (+3.0bp t=2.2). Any A2
   overnight construction on this panel is DOA gross, independent of cost accounting. The
   overnight-TOM intersection shows no concentration (1.4 vs 1.7bp).
2. Opex-week effect: absent/inverted (2.0 vs 6.1bp/day out). No monthly options-expiry drift.
3. TOY standalone: real bump (+9.9 vs +3.8bp/day), but SR 0.32 with 14 negYr over 33y —
   calendar windows remain un-saveable as standalone long/cash books under the yearly gate.
4. CONSISTENT 6-ROUND CONCLUSION for the coordinator: no calendar-timing family tested
   (TOM/paycheck/holiday/Halloween/weekday/quarter-end/opex/TOY/overnight) produces a sleeve
   passing ALL gates; the only robust signals (TOY bump, ROM avoidance) are 1-6bp/day tilts
   worth +0.3-1.3%/yr, suitable only as micro-tilts inside existing sleeves, not standalone.
ROUND r6 DONE
