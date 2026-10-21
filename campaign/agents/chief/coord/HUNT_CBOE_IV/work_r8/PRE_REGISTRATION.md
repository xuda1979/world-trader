# HUNT_CBOE_IV R8 - PRE-REGISTRATION (written BEFORE any candidate was built or any result seen)

Agent: HUNT_CBOE_IV. Round 8. Champion of record (do not touch):
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
sha256 8d7e711e6d05a2b1b77f06f18d850a90159924dd3df975a4f49bd407ad8fd079,
n=4806, 2008-03-31..2026-08-28, CAGR 37.4923%, SR 3.1951, MDD -6.6922%, 0 neg yrs,
cost 5.2734 bp/yr full_dw, gross 1.600.

## 0. Ledger read-first (v1 section 5 no-retest rule)

Read `campaign/results/DEAD_IDEAS.csv` (154 rows) before pre-registering. The
vol / implied-vol families already logged DEAD:

| row | family | evidence |
|---|---|---|
| 23 | SR-lift vol/timing overlay (60+ variants) | champion whitened, max dSR +0.035 |
| 32 | short-VIX MA regime timing | drift not timing |
| 44 | **VXV/VIX term-structure overlay on champion** | whitened; max real dSR -0.292 (31 variants); satellite A SR 0.612 but 4/19 neg + poslag p 0.08 = drift |
| 45 | GVZ/OVX gold/oil vol regime timing | overlay dSR -1.27..-3.6; 0 pass of 16 |
| 58 | **vol-surface risk-off gates / standalone vol-timing (VVIX/SKEW/VIX-TS/GVZ/OVX)** | 167 variants, best SR 0.78 < 1.0 |
| 67 | vol-gates on champion (VVIX cond / SKEW tail / 9d>3m) | 0/34 dAnn > +0.3pp |
| 72 | VIXCLS>30 sustained-21d vol-regime overlay | dAnn -1.63..-4.36pp |
| 119 | CBOE put/call 1995-2019 frozen archive overlays | 148/148 dAnn>0 FAIL |

**Therefore the FRONT-END (1M/3M) VIX term structure, VVIX, SKEW, GVZ, OVX level/z
gates, and generic rv63/z vol gates are ALL PRE-TESTED AND DEAD. I do not re-run them.**
The v1 section-5 rule permits a listed family only with a pre-registered NEW CORNER; the
corners below are chosen to be genuinely distinct from every row above.

`HUNT_VXV_TERM/FINDINGS.md` anti-repeat guidance is accepted as a prior: "Any future
overlay needs a signal with |corr(r_t, s_{t-1})| >~ 0.15 AND monotone quintiles - nothing
on disk qualifies (max 0.068)." My corners must clear that bar to have any hope.

Also noted: the champion already contains **A5r2 = `A5_vol_cond/A5_r2_contango_rateshock`**
(a contango/rateshock sleeve, relw 0.864). Any new vol/contango-flavoured sleeve risks
being a re-expression of A5r2. **I will report corr to A5r2 explicitly for every
candidate**, and corr to the champion, and state whether the candidate is a re-skin of A5r2.

Data-span discipline (V2 section 9a): span_class bounds 2007-01-01 / 2013-01-01. A series
whose true start is after 2013-01-01 is `inception_fail` and NOT hunt-eligible. VIX1D is
expected to be inception_fail (post-2023) and is therefore a DIAGNOSTIC ONLY - I will
not build a hunt-eligible sleeve on it.

## 1. Pre-registered corners (3 candidates, fixed now)

Signal construction is fixed here; thresholds are chosen on a PRE-COMMITTED grid and the
chosen point must pass the plateau gate on ALL neighbours (v1 3b). No post-hoc tuning:
if a candidate fails, it is reported as a failure with no parameter re-search beyond the
pre-declared grid.

### C1_VOLBACK - vol-curve BACK-END slope + curvature (NEW CORNER)
- **Why new:** every prior test (row 44, 58) used the FRONT end only: VIX vs VXV(VIX3M),
  i.e. the 1M/3M segment. The 3M/6M segment and the curve's CONVEXITY were never tested.
  The back end is a distinct information segment (longer-horizon risk appetite, less
  contaminated by the 1M's short-lived event spikes).
- Signal: `s = VIX3M/VIX6M - 1` (back-end slope) and `c = VIX6M - 2*VIX3M + VIX`
  (positive convexity = upward-curving curve). Risk-on when the back end is in contango
  and/or curvature is positive.
- Instrument: SPX (official CBOE OHLCV) long/flat, T+1, vol-targeted to 10% ann trailing.
- Grid: z-score lookback L in {21, 63, 126, 252}; gate |z| threshold in {0.5, 1.0, 1.5};
  slope-only vs curvature-only vs both.
- Pre-committed primary: L=63, |z|>1.0, slope+curvature combined.

### C2_VRP - variance risk premium: implied (VIX) minus REALIZED from official SPX OHLC
- **Why new:** row 23 is rv63/z-based vol gates (a realized-vol level gate, no implied
  leg); rows 44/58 are term-structure. The IV-minus-RV SPREAD is a different object - it
  measures the price of variance insurance, not the level of vol. Not in the ledger.
- Signal: `vrp = VIX_t - RV_t` where RV is annualized Parkinson (high/low) realized vol
  over a trailing window, both known at t (used at t+1). High vrp = insurance rich =
  risk-on (harvest premium); negative vrp = insurance cheap/stress = risk-off.
- Instrument: SPX long/flat, T+1, vol-targeted 10% ann trailing.
- Grid: RV window in {10, 21, 63}; z-score lookback {63, 252}; threshold {0.5, 1.0}.
- Pre-committed primary: RV window 21d Parkinson, z-lookback 63, z>0 long / z<0 flat.

### C3_VOLDISP - cross-asset implied-vol DISPERSION (VIX, GVZ, OVX)
- **Why new:** row 45 tested a 2-asset gvzovx_z ratio/combo and its level gates. A
  3-asset cross-sectional dispersion (how spread out the implied-vol complex is across
  equity/gold/oil) is a different construct; it has no direct 2-asset analogue.
- Signal: z-score each of VIX, GVZ, OVX on a trailing window, then take the cross-
  sectional std of the three z's. Low dispersion = one common vol factor = risk-on;
  high dispersion = idiosyncratic stress = risk-off.
- Instrument: SPX long/flat, T+1, vol-targeted 10% ann trailing.
- Grid: z-lookback {63, 126, 252}; threshold {0.5, 1.0, 1.5}.
- Pre-committed primary: lookback 126, risk-off when dispersion z > 1.0.
- **Flagged WEAK a priori**: the ledger already killed gvzovx_z; this is the closest of
  my three corners to a listed dead family and I expect it to fail. Declared here so a
  negative is not a surprise and a positive cannot be a p-hack.

## 2. Pre-committed test plan (identical for all three)

1. **Data inspection first.** Confirm each CBOE file's true content (underlying OHLCV vs
   option statistic) and true start date. Report coverage honestly; do NOT assume.
   Any series starting after 2013-01-01 is inception_fail (diagnostic only).
2. **Standalone sleeve track (V2 section 0 NEW-SLEEVE):** build [date,ret] net series with
   6.4bps on FULL |dW|, borrow 0.5%/yr on shorts, vol-target 10% trailing, gross <= 1.6.
   Then `bt.gates.run(r_eff, ref=champion, sig=positions, leak_check=True,
   beats_passive=True, spy=, ief=, cta=)`. Report the full gate dict.
3. **Leak probe:** `bt.leakcheck.leak_probe`, report same_period_corr, same_period_p,
   lag_scan, leak verdict. |corr| to same-period returns must be ~0.
4. **IS/OOS + pre/post-2010 stability table (MANDATORY):** SR and ann on
   pre-2010 / 2010+ and IS(<2017-01-01) / OOS(>=2017-01-01). An effect concentrated
   pre-2010 is a FAIL.
5. **Champion correlation** and **A5r2 correlation** reported for every candidate.
6. **Overlay/blend track (V2 section 8):** ladder over w in {0.025,0.05,0.10,0.15} (and the
   relever-to-cap variant), reporting dAnn (HARD 8c), dSR/dH2 (8d), dMDD (8b),
   halves of the delta (8f), plateau (8g).
7. **Placebo (V2.1 section 14):** route by |corr to champion|: Class A (>0.50) = 8h as flown;
   Class B (<0.40) = B1 level-matched null, p95 bar; straddler [0.40,0.50] = both,
   stricter wins. Use the ratified reference impl `HUNT_VOL2/work_r7/class_b_placebo.py`
   where applicable rather than reimplementing.
8. **Honest verdict** per candidate: ADOPT / REJECT / UNJUDGEABLE, with a one-line repro
   command, plus a DEAD_IDEAS row text for the coordinator.

## 3. Anti-p-hack commitments
- The grid is fixed above; I report the WHOLE grid, not just the best point.
- I will not report an in-sample-only SR as skill.
- A clean negative is a good result and will be written as such.
- If a corner is unmeasurable for span reasons, I will say UNJUDGEABLE, not REJECT.

Signed off before building: HUNT_CBOE_IV, R8.
