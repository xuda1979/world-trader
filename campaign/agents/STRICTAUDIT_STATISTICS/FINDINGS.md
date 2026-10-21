# STRICTAUDIT_STATISTICS — adversarial statistical audit of SR 5.24 / 0-negative-years (read-only)
Agent: STRICTAUDIT_STATISTICS | Date: 2026-09-02 | Target: `campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv` (committed 28c892b, mtime 2026-09-01 18:33). Scratch scripts+data: `scratch/`. No campaign file modified.

## 0. VERDICT SUMMARY (one paragraph)
Headline stats on the committed CSV **verify exactly** (ann 49.4%, SR_d 5.24, SR_m 3.46, MaxDD −6.05%, 0/19 neg years, OOS-2017+ 55.9%, LOYO 46.7–51.0%, worst-3y-window DD −6.05%). The charter's hypothesized "negative-autocorrelation inflation" is **empirically absent** — daily autocorr is positive (lag2 +0.060, lag5 +0.078; VR(21d)=2.07) — but the flip side is real and bigger: **the daily SR 5.24 overstates lower-horizon risk** (monthly 3.46, non-overlap-21d 3.72, quarterly 2.80, annual-frequency 1.88). The **flagship CSV is NOT regenerable from the repo**: its builder script is not in git, and the closest documented-pipeline rebuilds reach corr 0.91–0.98 but ann 51.5–57.2% @ SR 4.02–4.95 (vs committed 49.4% @ 5.24). It also **omits 92 genuine NYSE trading days** (zero-filling them: ann 48.4%, SR 5.18). The SR is NOT carried by its best days (removing top-10 days: SR 5.65) and survives drop-one-sleeve everywhere except XGB1y (−10.4pp ann keystone). Bottom line: defensible investor-horizon Sharpe ≈ **3.5 monthly / ≈2.8 quarterly**, ann ≈ 48–52%, 0/19 plausible but partly favorable tail-luck; the unregenerable builder is the same defect class that killed MHX/H21 and must be fixed before "bet today".

## 1. HEADLINE REPRODUCTION (committed CSV alone)
n=4522, span 2008-03-31..2026-07-31 (18.33y), rows/yr max 250. Measured vs claims:
| Metric | Claim | Measured | Verdict |
|---|---|---|---|
| ann (mean×252) | 49.4% | 49.4% (CAGR 63.0%, vol 9.4%) | EXACT |
| SR daily | 5.24 | 5.24 | EXACT |
| SR monthly | 3.46 | 3.46 | EXACT |
| MaxDD | −6.1% | −6.05% (peak 2021-11-05, trough 2022-05-27, recovered 2022-07-08) | EXACT (claim rounds down −6.1; conservative) |
| 0/19 neg years | 0/19 | 0/19; worst +20.7% (2026 partial), best +151.1% (2023) | EXACT |
| OOS 2017+ ann | 55.9% | 55.9% | EXACT |
| LOYO (arith ann, drop one year) | 46.7–51.0% | 46.7% (drop 2023) … 51.0% (drop 2022 or 2015) | EXACT |
| worst 3y-window DD | ≤ −6.1% | −6.05% (2020-11-05..2022-05-27) | consistent within rounding |
| monthly-SR bootstrap CI | [3.02,4.01] | month-resample CI [2.99,3.94] (5k draws, monthly SR 3.42) | reproduced ±0.07 |

## 2. REPRODUCIBILITY OF THE FLAGSHIP (FATAL-class, new finding)
- **No builder script for GOAL100_STRICTTRADE_BALANCED_daily.csv exists in the repo** (searched all `*.py` in git history and working tree for "STRICTTRADE"; only the CSV+JSON meta were committed in 28c892b). The JSON records the 12 pool names but **not** which brwt files (4 brwt slots; candidates: B2 brwt_spread_rev15, COORD brwt10_2000/brwt7/brwt5/brwt5_2000/brwt_ens/brent_wti_spread, E1_brwt_2000) nor the cost convention.
- Rebuilding with the **documented champion_build.py pipeline** (per-sleeve trailing-vt10 cap8, EW of vt legs, global vt 0.085/0.11 @ throttle 4%/3% FR0.5 LB126, 6bps) gives:
  - all four brwt slots = B2 file: **corr 0.9116, ann 51.5%, SR 4.02, DD −7.48%**
  - brwt = COORD 10/7/5 + B2-15: **corr 0.9797, ann 57.2%, SR 4.95, DD −7.28%**
  - no tested combination regenerates the CSV (best max|diff| 3.7e-2/day); committed SR 5.24 exceeds every rebuild (4.0–5.1); committed ann 49.4% is *below* every rebuild (51.5–57.2%).
- Prior-audit standard (byte-identical --verify, max dev 1e-16, applied to champion_build.py and all FINAL_TRUTH sleeves) is therefore **NOT met for the flagship artifact**. This is the same provenance-defect class that removed MHX and H21. **UNVERIFIED: exact construction of the one number marketed as "the number you can bet today".**
- Note: my first rebuild attempt produced SR 1.16 — that was **my own** artifact (union-index NaN contamination of rolling windows), caught and corrected; per-series vt is required. No such bug affects committed-file stats in §1 (CSV-only).

## 3. CALENDAR FORENSICS (both flagship and predecessor)
- Flagship contains **0** NYSE-closed days (checked full Rule-7.2 list 2008-26 + Sandy + mourning days) and 0 weekend rows — the phantom-holiday fix is real in this file.
- **BUT the flagship is missing 92 genuine trading days** (cross-checked against raw AAPL panel in `tools/quant/data/twelvedata/`): every Columbus Day and Veterans Day 2008-2025, Juneteenth 2021-06-18, Dec 24/26/27/31 stubs (e.g. 2016-12-27, 2021-12-27/28), and scattered days (2011-04-25, 2011-08-29, 2015-08-31, 2018-01-05, 2020-04-13/20, 2020-05-08, 2021-05-03…). The operative calendar is evidently a **vendor-panel intersection, not the NYSE calendar**. Zero-filling the 92 days: ann 49.4→48.4%, SR 5.24→5.18%, DD unchanged, still 0/19. Effect modest but the "NYSE tradeable calendar" description is **not literally true**.
- The predecessor FINAL_TRUTH series ("NYSE-only, holidays accumulated" per TRUTH_MEMO §"FINAL TRUTH") **contains 22 NYSE-closed dates** (Good Fridays 2009-2025, Sandy 2012-10-29/30, Bush mourning 2018-12-05, …) with non-zero PnL — that claim is false for FINAL_TRUTH; the flagship fixed 21 of these but over-deleted.
- Trading-day-impact upper bound of everything calendar-related: ≈ −1.0pp ann, −0.06 SR.

## 4. CHARTER JOB 1 — SOURCE OF THE SHARPE (decomposition + autocorr penalty)
- Point estimates: mean 19.6bps/day, vol 59.3bps/day → 49.4% @ 9.4%. Daily SR 5.24; monthly 3.46.
- **Autocorrelation is POSITIVE, not negative** (charter premise false): daily lag1 −0.013, lag2 +0.060, lag3 +0.064, lag5 +0.078, lag10 +0.055, lag21 +0.032; monthly lag1 +0.217. Non-overlapping variance ratios: VR(5)=1.15, VR(21)=**2.07**, VR(63)=3.91, VR(252)=7.55. Mean-reversion does **not** inflate the daily SR.
- Consequence: the daily SR **overstates multi-week risk**. Honest Sharpe by horizon: daily 5.24 → non-overlap-21d **3.72** → monthly **3.46** → quarterly **2.80** → annual-frequency (calendar-year) **1.88**. An investor who can only rebalance monthly gets ≈3.5; annual-frequency evaluation is ≈1.9.
- Block-bootstrap of the daily SR (block L=1..252, ≥300 reps): mean 5.25–5.36, CI [4.40,6.35] at L=252 — resampling barely moves it because daily SR is a point-in-time statistic; the correct penalty is the horizon adjustment above, not block shuffling.
- Diversification: vt-normalized pairwise corr mean 0.131, median 0.0002; PCA EV1 = 28% of variance. But the 12 "engines" are **12 slots of ~7 families**: {4×brwt (intra 0.43-0.99)}, {C5ng/C5ngsum 0.52}, {A5r2/QAxasts 0.75, A5r2/dualmom 0.88, dualmom/XGB1y 0.84, QAxasts/XGB1y 0.62}, {a6r7}, {carryv2}. Effective family count ≈ 6-7, not 12.
- Where the SR comes from: EW-of-12 vt10 legs alone = SR 4.61 @ ann 28.2% (XGB1y vt-leg SR 5.48 at cap-8 leverage = the largest single contributor); global vt leverages to 47.5/61.5% ann; throttle+costs trim to ~51.5% @ SR 4.0 in my rebuild. The committed 5.24 requires construction details not in git (§2).

## 5. CHARTER JOB 2 — 0/19 NEGATIVE YEARS CREDIBILITY
- Sleeve negative years 2008-26 (raw files, 2008-09+): brwt×4 0, C5ng 0, C5ngsum 0, carryv2 0, QAxasts 1 (2009), dualmom 1 (2022), A5r2 2 (2011,2022), a6r7 2 (2014,2021), XGB1y 3 (2012,2015,2022). Blend 0/19.
- Plausibility: under an IID per-year P(neg)≈0.15 for the blend, P(19 straight positives) ≈ 4.6% (at 0.30: 0.1%). So 0/19 is a **~5%-prior event** — attainable by genuine diversification but it should not be sold as expected; one bad year is not a bug, its absence is luck + construction.
- Consistency check: worst year +20.7% is 2026-partial; the claim survives my every drop-one/drop-two rebuild (0 neg years in all 12 drop-ones and all drop-twos). 2026 turning negative needs ≈ −24% over the remaining ~110 trading days ≈ a 3σ move (vol 9.4%) — unlikely, not impossible.
- Verdict: **statistically plausible, not a vol-target artifact**, but fragile as a marketing claim; drop-XGB1y keeps 0/19 but guts OOS (46.4% vs 59.2% ann).

## 6. CHARTER JOB 3 — DROP-ONE SENSITIVITY (EW-of-11 via documented pipeline; my rebuild = §2 corr 0.91 variant)
Base rebuild: ann 51.5%, SR 4.02, DD −7.48%, 0 neg, OOS 59.2%.
| Omit | Δann (pp) | ΔSR | OOS ann | Note |
|---|---|---|---|---|
| brwt15/10/7/5 (each) | +1.2 | +0.39 | 60.4% | the 4 identical-family brwt slots *dilute* — dropping any one helps |
| C5ng | −1.0 | −0.14 | 59.4% | |
| C5ngsum | −0.2 | −0.11 | 58.5% | |
| A5r2 | +0.4 | −0.09 | 59.6% | |
| a6r7 | −0.9 | −0.09 | 57.7% | |
| QAxasts | −1.3 | −0.08 | 57.7% | |
| carryv2 | **+2.2** | −0.12 | 62.0% | a **drag** on return (DD worsens to −9.4% if removed) |
| dualmom | +0.0 | −0.15 | 59.9% | |
| **XGB1y** | **−10.4** | **−0.80** | **46.4%** | **keystone CONFIRMED in the 12-pool** (AUDIT2's −10pp in the 16-pool holds) |
Drop-two weakest standalone-SR sleeves: {carryv2,dualmom} ann 53.9% SR 3.69; {carryv2,A5r2} 54.3%/3.77; {dualmom,A5r2} 50.6%/3.81 — no collapse; no single sleeve is load-bearing for survival EXCEPT XGB1y (keystone: −10.4pp ann, −0.80 SR, OOS −12.8pp). One sleeve family (ML monthly book) supplies the single largest share of headline edge → concentration risk is real and under-disclosed in the "12 engines" framing.

## 7. CHARTER JOB 4 — SELECTION / MULTIPLE TESTING
- Candidate universe: ~330 ideas claimed in memos; on disk: 44 sleeve CSVs under `agents/*/sleeves/` + 42 in `sleeve_library/`; 86 evaluable (≥1000 obs in window). Their SR distribution: deciles [−0.19, 0.04, 0.89, 2.00, 3.28]; 22 sleeves > SR2, 12 > SR3, 8 > SR4 (incl. removed MHX 5.32/5.20 — a reminder that files this good DID occur and were fake).
- Under the null (zero true skill), with SE(SR_ann)=0.33 (n=4522), E[max of 330 iid nulls] ≈ 0.8 and P(any null reaching 5.24) ≈ 0. **Selection alone cannot produce SR 5.24** — the number is not a pure data-mining artifact *if the sleeves' PnL is honest* (prior audits verified T+1/zero-runs byte-exactly on all 12 inputs).
- Time-stability: OOS split 2017-21: ann 55.1%, SR 4.85, DD −4.6% | 2022-26: 56.7%, 6.69, −4.6% — **edge is stable/rising OOS, not decaying**. 5y-rolling SR: 4.76 (08-12) … 4.31 (18-22) … 6.24 (21-25); lowest 3.96 (11-15). Annual SR by year (§8 table): min 2.74 (2015), max 10.57 (2023) — never below 2.7.
- Real residual risks are therefore not statistical: provenance (§2), calendar (§3), instrument-reality of the vol-collapse sizing (§9), natgas publication-lag (open, prior audit).

## 8. CALENDAR-YEAR TABLE (committed series)
Year: ret | SR — 2008(part): +43.6% | 5.02 · 2009: +60.8% | 5.88 · 2010: +58.5% | 5.37 · 2011: +47.0% | 4.67 · 2012: +25.8% | 2.88 · 2013: +52.7% | 4.87 · 2014: +47.8% | 4.45 · 2015: +23.2% | 2.74 · 2016: +100.3% | 8.31 · 2017: +70.7% | 6.59 · 2018: +62.5% | 5.64 · 2019: +88.6% | 7.62 · 2020: +91.6% | 3.90 · 2021: +41.1% | 3.39 · 2022: +21.6% | 2.96 · 2023: +151.1% | 10.57 · 2024: +82.6% | 8.04 · 2025: +79.6% | 7.09 · 2026(part): +20.7% | 3.57.

## 9. CHARTER JOB 6 — TAIL RISK & EVENT DEPENDENCE
- Distribution: skew +4.46, excess kurt 89.4. Worst day −3.68% (2008-09-19); **best day +14.72% (2020-09-01) = 7.8σ** at 9.4% vol.
- Mechanism traced: on 2020-09-01 the brwt spread-reversal leg printed +3.08% raw while its 60d trailing vol had collapsed to **1.58% ann**, so vt10 scale = 6.34 (cap 8) and **all four brwt pool slots** (≈1/3 of the book) rode 6.3× positions into the Hurricane-Laura Brent-WTI snap-back; blend +5.9%, global vt ×1.8 → +14.7% committed (FINAL_TRUTH +10.8%, so this artifact predates STRICTTRADE). Second-best day +7.28% (2021-03-31) is the same mechanism (trailing vol 0.88% → scale ≈11 pre-cap). This is a **short-vol-like sizing signature**: gains concentrated when spread vol is collapsing; the observed asymmetry (best brwt vt day +19.5% vs worst −7.5%) is the luck of 2 events, not a structural property. Costs/limits of this sizing are disclosed nowhere in the memos.
- Net tail-dependence of the HEADLINE, however, is LOW: removing top-1/5/10/20 days → ann 48.6/47.4/46.4/44.9%, SR **5.53/5.63/5.65/5.64** (removing best days *raises* SR — they add vol faster than mean), DD unchanged, 0/19 intact. Removing bottom-1/5/10 days → SR 5.29/5.41/5.52. Share of total log-PnL: top-10 days 6.0%, best year 2023 10.5%; multiple ex-2023 = 2566× (vs 6445×). **The SR is diffuse, not black-swan-driven; 0/19 is not bought with the right tail.**
- Mertens SE (skew/kurt-adjusted): SE(SR_ann)=0.33, t=16; NW(21d) 95% CI [4.68,5.80]; NW(63d) [4.61,5.87]. The daily SR is statistically enormous *as measured on this sample*.

## 10. CHARTER JOB 5 — BOOTSTRAP CIs
- Monthly-SR: point 3.46; month-resample CI **[2.99,3.94]** (claimed [3.02,4.01] — reproduced within method noise). Lower bound comfortably clears SR≥2 → **goal PASSES at monthly horizon**.
- Daily-SR: IID CI [4.62,5.90]; block(252d) CI [4.40,6.22]; NW-21 [4.68,5.80].
- Annual-frequency SR = 1.88 — the only horizon at which the goal SR≥2 would fail (not part of the claim, but disclosed).

## 11. ITEMS UNVERIFIED (explicit)
1. **UNVERIFIED — flagship builder**: no script in git regenerates GOAL100_STRICTTRADE_BALANCED_daily.csv; pool JSON omits file mapping and cost model. All §1 stats are recomputed from the CSV itself and DO match claims; the *construction* does not reproduce (best corr 0.98, ann off by up to +7.8pp, SR by up to −1.2).
2. **UNVERIFIED — which brwt files the four pool slots use** (B2 vs COORD vs E1); best-fit = COORD brwt10/7/5 + B2-15 (corr 0.98) but not exact.
3. **UNVERIFIED — natgas publication-lag** (prior audit open item; unchanged here).
4. **UNVERIFIED — FINAL_STATE's "all byte-verified"** is true for sleeve CSVs (AUDIT2) but NOT demonstrable for this champion assembly.
5. Reason for the 92 missing trading days in the flagship calendar (vendor paging vs deliberate filter) — mechanism inferred, not proven.

## 12. HONEST BOTTOM LINE
- What survives: every claimed summary statistic of the committed CSV reproduces exactly from the file; the system's edge is time-stable (OOS 2017-21 ≈ 2022-26), not dependent on its best days, not a multiple-testing mirage, and 0/19 negative years holds in every leave-one-sleeve-out I ran.
- What the headline hides: (a) the daily SR 5.24 is the most flattering horizon — the investor-horizon Sharpe is ≈3.5 monthly / ≈2.8 quarterly (CI lower bound ≈3.0 still clears the ≥2 goal); (b) "12 engines" ≈ 7 decorrelated families with one ML keystone (XGB1y −10.4pp ann if removed) and a 4-slot Brent-WTI block that actually dilutes; (c) the two biggest windfalls come from vol-collapse-scaled brwt sizing (up to 6.3× within cap-8) — tradeable but a hidden short-vol posture; (d) the flagship CSV cannot be regenerated from the repository (builder absent, best corr 0.98) — the very defect class the campaign's own audits used to delete sleeves; (e) the calendar misses 92 real trading days (−1.0pp ann, −0.06 SR if filled).
- Defensible claim after corrections: **ann ≈ 48–52%, monthly SR ≈ 3.4–3.7 (CI ≈ [3.0, 4.0]), quarterly ≈ 2.8, MaxDD ≈ 6–8%, 0/19 negative years in-sample (a ~5%-prior outcome, not an expectation)**. The robust system is real; "SR 5.24" should be quoted only as a daily-frequency statistic, and only after the builder is committed and the CSV regenerates byte-exactly.

STRICTAUDIT_STATISTICS DONE
