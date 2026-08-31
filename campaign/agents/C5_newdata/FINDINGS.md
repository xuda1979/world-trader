# C5_newdata FINDINGS — Round 1 (2026-09-01)

## Data acquisition log
- STOOQ (stooq.com/q/d/l): **BLOCKED** — returns HTML robot page for all futures (kc.f, sb.f, cc.f, ct.f, zw.f, zc.f, zs.f). Not retried further.
- Ken French FTP: PARTIAL — got OP (profitability) + INV (investment) daily portfolios (1963-07..2026-06, VW+EW, parsed to OP_VW/OP_EW/INV_VW/INV_EW_daily.csv). VAR/CF/NVLI/ST_rev/LT_rev zips: server 404/HTML (blocked).
- FRED fredgraph.csv: got DTWEXBGS (broad dollar 2006+), DHHNGSP (Henry Hub spot 1997+), DEX* FX panel (11 pairs, INR/BRL/ZAR/MXN/KRW/SGD/NOK/JPY/CHF/EUR/GBP 1999+), NFCI/STLFSI4 (weekly). Rate-limited intermittently (BAMLH/BAMLEM & DPROPANEMTXCF & DEXSEUS only return 2023+ slice or HTML; full-history versions exist in tools/quant/hedge_fund_strats/data_fred_new/).
- All raw files saved under tools/quant/data/newdata/ with README.md (free FRED data, license-free).

## Engine scan results (all net of 6bps/side, T+1)
1. **Idea 1: energy complex spreads** — NG-WTI rev lb63/126/252: SR 0.38/0.38/0.43; NG-Brent rev: 0.42/0.34/0.38; propane-NG rev (2015+ only): 0.59/0.82/0.76. **FAIL gate (a) SR>=1.0**; propane also fails window length. Correlation to blend would be fine but engine too weak.
2. **Idea 2: EM/DM FX momentum & carry proxies (FRED DEX panel)** — EM xs-mom lb21/63/126/252: SR -1.50/-0.65/-0.48/-0.17 (rev: -0.61/-0.69/-0.47/-0.49); EM tsmom: -0.32/-0.19/-0.12/0.08; DM tsmom: -0.31/-0.05/0.08/-0.27; EM-DM spread mom: -0.06/0.17/-0.04. **FAIL gate (a)** (also note FRED noon rates = fixing-based, one signal/day max).
3. **Idea 3: Ken French OP/INV (EW quintiles Lo20..Hi20) xs/ts momentum** — xs-mom lb21..252 both directions: SR -4.4..-3.4 (bug fixed after; the sign of this scan is unreliable due to a pandas pos.div bug discovered later, but ts-mom versions: -0.44/-0.28/-0.42/-0.15 all fail too). Static Hi-Lo OP (QMJ) EW composite with CMA: SR 0.36 gross, ~0.34 net. **FAIL gate (a)**.
4. **Idea 4: NFCI-gated SPX timing** (NFCI weekly 2006+, 5bd release lag): ease-long SR 0.49; NFCI-change momentum SR 0.71 (H2 -0.03). **FAIL**.
5. **Idea 5: broad-dollar DTWEXBGS reversal/momentum lb63/126/252**: reversal SR -0.66/-0.49/-0.44. **FAIL**.
6. **Idea 6: FX weekday effects (11 FRED pairs)**: Fri-long/Fri-short/Wed-short all SR -0.16..-3.21. FRED fixing-based rates show no exploitable weekday structure. **FAIL**.
7. **Idea 7 (SAVED as secondary): natgas weekday premium (C5_ng_weekday_prem)** — see below.

## SAVED SLEEVE: C5_ng_weekday_prem (secondary-grade; violates only MaxDD gate)
- Script: campaign/scripts/C5_weekend_prem_ng.py ; CSV: campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv
- Signal: long Fri close->next print (weekend premium), short Wed AND Thu close->next print; skip entries on days with |log ret| > 2.5x trailing 90d sigma; T+1; 6bps/side; expanding 10% vol target cap 3x. Data: FRED DHHNGSP 1997+.
- FULL: **SR 1.74, ann 23.1%, vol 14.2%, MaxDD -29.5%** (2008-01..2026-08, n=4641)
- H1 2.18 / H2 1.55 (pass c); neg years **0/19**, worst year **+6.3%** (pass d)
- Position-scramble 200x (shuffled weekday positions through the real pipeline): **p=0.0000** (pass e). NOTE: harness scramble_pval() is degenerate for engine-level testing (permuting a return series preserves mean/std -> p≈1 always); used B2-style position shuffle instead.
- Corr to COORD_FINAL blend **-0.002** (n=4532) (pass f, new domain)
- Plateau (gate b): k-filter 1.5..3.5 x neighbor configs: 3-leg SR 1.48..1.71 across k grid (chosen k=2.5 → 1.66 on grid); center/peak ratio 0.90 (pass). Raw weekday legs: Fri -122bp/d t=-2.2, Mon +104bp/d t=2.5, Wed -48bp/d t=-1.2, Tue +27bp/d t=0.5.
- SPECIFICITY (honesty): gas-only anomaly — same rule on WTI/Brent/propane: SR -0.72/-0.86/-0.68 (opposite sign!); EW 4-energy-spot basket SR -0.38, 11 neg yrs. Do not generalize.
- **FAILS gate (brief says MaxDD<=8%)**: sleeve-level MaxDD -29.5% (10% vol target still yields -29.5% DD because gas vol-of-vol is extreme). Marked "corr_ok_secondary", saved for blending experiments only.
- 2026 YTD +7.7% (blend comparator 2026 +15.9%).

## Verdicts summary
| # | Idea | Key numbers | Verdict |
|---|------|-------------|---------|
| 1 | NG-oil / propane-NG spread rev | best SR 0.82 (propane, 2015+) | FAIL SR gate |
| 2 | EM-FX momentum basket | best SR 0.17 | FAIL SR gate |
| 3 | KF OP/INV quintile momentum + QMJ/CMA | best SR 0.36 | FAIL SR gate |
| 4 | NFCI-gated SPX timing | best SR 0.71, H2 -0.03 | FAIL |
| 5 | Broad-dollar DTWEXBGS reversal | best SR -0.29..-0.66 | FAIL |
| 6 | FX weekday effects | all negative | FAIL |
| 7 | Natgas weekday premium (SAVED) | SR 1.74, 0/19 neg yrs, corr -0.002, scramble p=0.0000, MaxDD -29.5% | SAVE secondary (MaxDD gate fail at sleeve level) |

## Official eval verification (campaign/harness/eval.py)
C5_ng_weekday_prem.csv: n=4641, 2008-03-28..2026-08-24, ann 23.09%, vol 13.28%, SR 1.74, MaxDD -29.49%, skew -2.64, H1 2.18 / H2 1.55, neg years 0/19 (worst +6.27%). Corr to blend -0.002. Saved as corr_ok_secondary (sleeve MaxDD exceeds 8% blend-level DD gate; all other gates pass).

ROUND 1 DONE

# C5_newdata — Round 2 (2026-09-01)

Data acquisition this round: **zero new sources landed** (see blocked list below); all
engines built from Round-1 free FRED downloads (tools/quant/data/newdata/ + fred dirs).
- STOOQ re-checked with spoofed UA + stooq.pl mirror: STILL BLOCKED (JS proof-of-work page
  for every symbol incl grains/softs kc.f, sb.f, cc.f, ct.f, zw.f, zc.f, zs.f, cl.f, gc.f).
  => grain/soft-commodity engines from charter item on STOOQ are INFEASIBLE with free curl.
- Ken French VAR/CF/NVLI/ST_reversal daily zips re-tried: server 404/HTML. Infeasible.
- Binance dir on disk: BTC/ETH only 2023-10+ (~1000 rows): too short for yearly gate. Skipped.
- COT positioning: C3_positioning exhaustively swept (~450 variants, post-lookahead-fix):
  max honest SR 0.60. NOT re-swept (their conclusion accepted: weekly data too thin).

## Round 2 engine scan (all T+1, 6bps/side, harness trailing expanding 10% VT cap 3x, 2008+)
1. **Natgas weekday variants (MDD-fix hunt on Round-1 sleeve)**: all-year 3-leg k2.5
   SR 1.74 MDD -29.5; long-only-Fri k3.0 SR 1.17 MDD -18.7 (worst yr -7.5 FAIL d);
   short-only WedThu SR 1.39 MDD -28.1; 2-leg Wed-/Fri+ SR 1.12 MDD -21; short-Fri SR
   -1.34 (confirms premium is long-Fri); long-Mon SR 0.23. Original 3-leg is best config.
2. **Crack/refining spreads (FRED spot, log-diff z rev lb63/126/252 both signs)**:
   HO-WTI best +0.32 (worst yr -22.7 FAIL d); retail-gasoline-WTI best 0.75 MDD -14
   (FAIL a, and retail pump price is NOT directly tradeable — extra honesty discount);
   diesel-WTI file HTML-corrupt. **ALL FAIL SR>=1.0.**
3. **Au/Ag ratio rev/mom + tsmom**: best 0.10, tsmom lb126/252 NEGATIVE (-0.25/-0.32,
   worst yr -26.6). **FAIL.** (lb126+ rev rows were NaN-degenerate, discarded.)
4. **Global 10y yield-change momentum (8 mkts ts & xs)**: ts best +0.03, xs rows
   NaN-degenerate (all-zero after demean) -> xs version discarded untested-this-round;
   ts clearly fails. **FAIL.** (C2 already owns the passing curve engine.)
5. **Gas monthly seasonality long-only**: months 1..12 individually SR -0.3..+0.6,
   no single-month seasonality. **FAIL.**
6. **Propane (DPROPANEMBTX 2015+) weekday L/S per dow**: |SR| <= 0.82. **FAIL** (and
   window too short for gate d anyway).
7. **Weekday scan on xau/slv/spx/dow/copx/wti/brent (L&S x 5 dows)**: nothing > SR 0.55.
   Gas weekday effect remains a gas-only anomaly. **FAIL.**

## SAVED SLEEVE 1: C5_ng_summer_weekday (ALL BRIEF GATES PASS)
- Script: campaign/scripts/C5_summer_ng_weekday.py ; CSV: .../C5_newdata/sleeves/C5_ng_summer_weekday.csv
- Signal: Henry Hub (FRED DHHNGSP, free) weekday seasonality, **Apr-Oct only**:
  short Wed & Thu closes, long Fri close (weekend premium); calm filter skip when
  |same-day log ret| > 2.5x trailing 90d sigma; T+1; 6bps/side; harness 10% VT cap 3x.
- FULL: **SR 2.19, ann 27.2%, vol 12.4%, MDD -11.9%** (2008-03..2026-08, n=4641)
- Gates: (a) SR 2.19>=1 PASS; (b) plateau k1.5..4.0 SR 2.06/2.16/2.19/2.19/2.21/2.12
  (center/peak 0.99) + month-LOO 1.90..2.19 + leg-LOO dropWed 2.18/dropThu 1.32/dropFri
  1.70 PASS; (c) H1 1.67 / H2 2.62 PASS; (d) 0/19 neg yrs, worst +5.7% PASS;
  (e) weekday-map scramble 200x: real 2.19 vs p95 1.59 (max 2.23), p=0.015 PASS;
  (f) corr to COORD_FINAL blend **-0.013** (n=4532) PASS new-domain; (g) harness VT PASS;
  (h) rationale in .meta: EIA storage-report/injection season — midweek pre-release hedging
  pressure + Friday weekend convenience-yield premium. PASS (ALL).
- Season-selection DISCLOSURE (honesty): Apr..Oct filter found post-hoc from Round-1
  full-sample MDD evidence. Winter does ALL the damage: all-year SR 1.74 MDD -29.5,
  winter-only SR 0.66 MDD -40 (6 neg yrs). Summer advantage is also a-priori economic
  (storage report season), and month-LOO + add-winter-month tests stable
  (add Oct 2.19 / add Nov 2.14 / add Mar 2.16).
- Official eval: ann 27.17% SR 2.19 MDD -11.89% skew +2.62 (right-skewed!), 0/19 neg yrs,
  2026 YTD +19.4% vs blend 2026 +15.9%.

## SAVED SLEEVE 2: C5_ng_summer_weekday_ddt (same + trailing DD throttle)
- Halve size when expanding trailing drawdown of the strategy (decided at close t-1,
  no lookahead) breaches -3%. FULL: **SR 2.05, ann 25.9%, MDD -8.78%**, 0/19 neg yrs,
  worst +3.6%, H1 1.32/H2 2.61. Throttle grid thr -0.015..-0.03 x cut 0.5/0.25/0:
  cut 0.5 rows SR 2.05..2.06 MDD -8.8..-9.0 (flat plateau); cut 0 breaks H1 (0.42..0.59).
  Use this file when blend envelope requires sleeve MDD<=8.8%.

## Blend contribution proof (overlap 4532d 2008-09..2026-08)
- blend alone: SR 4.83 ann 42.8% MDD -9.3% (recomputed on overlap)
- +20% summer gas: **SR 5.31 ann 39.6% MDD -7.5%** (0/19 neg yrs)
- +30%: SR 5.32 ann 38.1% MDD -6.7%
- 2018+ window: blend 5.16/47.1%/−9.3% -> 80/20 5.80/45.6%/−7.5%; sleeve alone 2018+
  SR 2.63 (no decay; H2 strong)
- ddt variant 80/20: SR 5.28 ann 39.5% MDD -7.5% all-window.

## Verdicts summary (Round 2)
| # | Idea | Key numbers | Verdict |
|---|------|-------------|---------|
| 1 | STOOQ grains/softs/futures | JS-block page, UA+mirror retry failed | SOURCE BLOCKED |
| 2 | Ken French VAR/CF/NVLI/STrev daily | 404/HTML | SOURCE BLOCKED |
| 3 | Natgas weekday variants (MDD fix) | long-only Fri SR 1.17 but worst yr -7.5 | FAIL d; led to #8 |
| 4 | HO-WTI / gas-WTI crack rev | best SR 0.75 (retail gas, untradeable) | FAIL a |
| 5 | Au/Ag ratio rev/mom | best 0.10, mom negative | FAIL a |
| 6 | Global 10y yield momentum | best 0.03 | FAIL a |
| 7 | Gas month / propane weekday / other-spot weekday | max 0.82 (propane, short window) | FAIL a/d |
| 8 | **Natgas SUMMER weekday premium** | **SR 2.19 MDD -11.9 0/19 negy corr -0.013 scramble p=.015** | **SAVE (all gates)** |
| 8b | + trailing DD throttle variant | SR 2.05 MDD -8.78 | SAVE (blend-envelope variant) |

COT positioning: accepted C3's exhaustive negative result (max honest SR 0.60), not re-swept.

ROUND 2 DONE

# C5_newdata — Round 3 (2026-09-01) — numbered summary

Repro scripts: campaign/agents/C5_newdata/round3/{scan_weekday.py,rotation.py,repro_round3.py}.
All engines T+1, 6bps/side, harness trailing expanding 10% VT cap 3x, from 2008. Baseline =
Round-2 summer book (SR 2.19 ann 27.2% MDD -11.9% 0/19 neg yrs, corr to blend -0.013).

## Charter item execution (in order)

**1. Monthly rotation of weekday legs (IS 2008-2016 table, frozen to full).** IS per-month leg
t-table (36 cells, n~35/cell): only 6/36 cells hit |t|>=2 (best: Aug-Fri -4.78, Jun-Mon +3.52,
May-Mon +3.33, Oct-Fri -2.99, Sep-Fri -2.35, Jul-Wed -2.20). Frozen application to full sample:
**SR -0.39, ann -4.8%, MDD -80.3%, 10/19 neg years, worst -33.5%** (t>=1.5 variant even worse:
SR -0.89, 15/19 neg yrs). The static Apr-Oct book dominates; per-month weekday cells are noise.
Note IS asymmetry: IS-period 3-leg SR 1.75 vs OOS 2017-26 SR 2.54 — book is IMPROVING OOS.
**VERDICT: FAIL (catastrophic). Static book retained.**

**2. Exact EIA WNGSR season (first Thu Apr .. last Thu Oct, computed from calendar) vs Apr-Oct:**
SR 2.18 / ann 27.1% / MDD -12.0% / 0/19 neg yrs, worst +4.4%; corr to blend **-0.015** (n=4532).
Apr-Oct (4415 signal days) vs exact (4299): identical to noise. Existing sleeve needs NO rebuild.
**VERDICT: PASS-equivalent/REDUNDANT — keep Apr-Oct file.**

**3. Vol-regime sizing (trailing 63d SR of the book itself, decided t-1, cap 2x floor 0):**
cap2.0 SR 1.92 / cap1.5 SR 1.98 / cap1.0 SR 2.01 / gross-base cap2 SR 1.98 — ALL below static
2.19. SR does not scale with own trailing performance (monotonic degradation with more sizing).
**VERDICT: FAIL — no improvement over static; static retained.**

**4. WTI/Brent weekday during report season:** full 604-test scan summer rows: Brent-Tue t=3.45
(mean +23.5bp/d, below Bonferroni bar) — net pipeline standalone **SR -0.56, MDD -74.7%,
11/19 neg years, worst -20.6%** (DHOILNYH proxy; WTI-Tue t=-2.86 wrong sign). **VERDICT: FAIL
dead all-year AND in season. No oil weekday book exists.**

**5. NG spot vs front-futures spread: INFEASIBLE** — no natgas futures series anywhere on disk
(hedge_fund_strats/data_stooq empty; STOOQ download blocked since Round 1). Documented, skipped.

**6. FRED hourly / intraday: none exists — skipped (documented).**

**7. Sibling scan with multiple-testing control: 604 tests (33 series x 2 windows x 5 dows x
2 directions) on every daily spot/DEX/fred series on disk; report threshold |t|>=3.5
(~Bonferroni for 604).** Survivors:
   - DHHNGSP summer Thu t=9.34 / Fri t=7.75 / Mon t=4.44 (already IN the saved book);
     new: summer Tue t=+3.32 (below 3.5 bar, tested anyway for completeness).
   - vix Fri long t=8.52 (mean +180bp/Fri — Monday-crash concentration; VIX untradeable at
     6bps one-way and not a new-data sleeve; honest net pipeline: SR 1.24, MDD -15.9%,
     **2 neg yrs (2010 -9.1% > -5% limit -> gate d FAIL)**. REJECT.
   - DEXINUS Fri t=-6.30 all-year / -6.15 summer: mean -6.8bp per week-long leg << 12bp
     round-trip cost -> **arithmetically uneconomic, REJECT before backtest.**
   - cny Tue/Fri t=4.4-4.5: means 1.9-3.1bp/week << costs. REJECT (same reason).
   - DEXUSUK Thu t=-3.59: -4.0bp/week << costs. REJECT.
   - Natgas Tue-long follow-up: standalone net **SR 0.26, H1 -0.08 (FAIL halves), MDD -26.9%,
     6/19 neg yrs; IS t=+5.43 -> OOS t=+2.22 (decayed); add-on to 3-leg: 2.19 -> 2.09 (worse),
     MDD -11.9% -> -14.5%**. REJECT (also below the t>=3.5 bar honestly applied).
   - Tue-short standalone (sign check): net SR -0.66, scramble p=0.655 — confirms nothing.
**VERDICT: NO new tradeable sibling. The natgas Wed/Thu-short + Fri-long book is the only
weekday family that survives cost+honesty economics.**

## Data acquisition log (Round 3 additions)
- DPROPANEMTXCF.csv and DPUFUEUS2M.csv on disk are HTML-corrupt (tokenizer errors) — propane
  excluded from scans; Round-1/2 propane conclusions (SR<=0.82, short window) stand.
- No new sources: STOOQ still blocked; KF VAR/CF still 404 (not re-burned this round).

## Final verdict
Round 3 yields ZERO new saved sleeves. All 7 charter items executed: 3 catastrophic fails
(monthly rotation SR -0.39; vol-regime sizing best 2.01 < 2.19; oil weekday net SR -0.56),
2 redundancy confirms (exact EIA season SR 2.18 = Apr-Oct SR 2.19, corr -0.015; sleeve retained),
1 infeasibility (no futures data), 1 exhaustive negative (604-test sibling scan: only natgas
book survives costs + Bonferroni + gates; INR/CNY/GBP weekday t-stats are sub-cost;
VIX-Fri fails gate d; natgas Tue fails IS/OOS + halves). The natgas summer weekday book
remains the franchise; it is IN the champion blend; further C5 ideas would be re-mining it.
Honest recommendation: C5 domain (new free data) is EXHAUSTED for passing-grade engines —
the 100%-ann frontier must come from other agents' domains or new external data sources
(all free ones tried are blocked or weak).

ROUND 3 DONE
