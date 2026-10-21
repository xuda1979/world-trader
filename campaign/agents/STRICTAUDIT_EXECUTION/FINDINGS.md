# STRICTAUDIT_EXECUTION — adversarial audit of instrument-real + broker-real cost claims
Agent: STRICTAUDIT_EXECUTION | Date: 2026-09-02 | Method: code read + independent re-derivation from raw data + my own reconstruction of the blend + authoritative NYSE holiday calendar. Read-only; no campaign file modified. All numbers below recomputed by me unless marked "claimed".

TARGET: campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv — the claim that it is
"tradeable on real instruments, byte-verified, NYSE calendar, broker-real costs + borrow fees".

---

## 0. HEADLINE VERDICT

The committed CSV's REPORTED METRICS ARE REAL and I reproduce them exactly (§1). The construction
is NOT byte-reproducible (no builder script exists anywhere on disk or in git — §2) but my
independent reconstruction brackets it closely (daily corr 0.98, §2.3) and shows the cost layer
is present and NOT double-charging the embedded 6bps (§4). The calendar claim is WRONG in one
direction: the series contains ZERO weekends/holidays (clean), but it also silently DROPS 98
NYSE-OPEN days (foreign/bond holidays, half-days) and does NOT accumulate holiday P&L as the
memo documents — a ~+2.8pp/yr conservative error (§5). The borrow-fee story is materially
mis-stated: dualmom holds NO shorts (long-only, verified by exact rebuild), so its claimed
borrow is fiction; XGB1y is the only short book and holds ~42 names/side, not ~10-20 (§6).
The "instrument-real" claim is INCONSISTENTLY applied: no corr-0.03-class paper legs remain,
but the VIX-spot leg of QAxasts (its own attribution says it carries nearly ALL the edge),
the natgas SPOT prints, the WTI/Brent SPOT spread and the synth-2y leg are all spot/synthetic
proxies whose futures basis is UNVERIFIED because no futures series exists on disk (§3).
Financing on per-sleeve vol-targeting leverage (capital-real gross mean 2.17x, max 8.0x) is
NOT charged; charging it at T-bill+25bp costs 5.6%/yr (§7).

Bottom line: the headline numbers (49.4% ann, SR 5.24, MaxDD -6.05%, 0/19 neg years) are honest
recomputation of the file that exists, but "byte-verified + broker-real + NYSE calendar" is
overclaimed in four specific, quantified places.

---

## 1. REPORTED METRICS — ALL REPRODUCED EXACTLY from the committed CSV
n=4522 rows, 2008-03-31..2026-07-31 (18.3y calendar span; memo says "17.9y" — understated by ~0.4y).
- ann 49.36% (claimed 49.4) | SR daily 5.24 (5.24) | SR monthly 3.46 (3.46)
- Monthly-SR bootstrap (2000 reps, my seed): CI95 [3.02, 3.96] vs claimed [3.02, 4.01] — consistent
- MaxDD -6.05% (claimed -6.1); worst 3y subwindow -6.05% (2021-07-21..2024-08-27); every 3y and
  calendar-year window shallower than -6.1%: CONFIRMED
- Negative years 0/19: CONFIRMED; worst (lowest) year +20.7% (2026 partial); best 151.1% (2023): CONFIRMED
- OOS 2017+: ann 55.85%, SR 5.54, DD -6.05% (claimed 55.9%): CONFIRMED
- LOYO 46.7% (drop 2023) .. 51.0% (drop 2022): CONFIRMED
- 0 zero-rows (|r|<1e-12): no phantom flat days.

## 2. REPRODUCIBILITY OF THE CHAMPION FILE — **FAIL (no builder exists)**
2.1 HUNT: grepped all of campaign/scripts/, campaign/agents/, tools/, entire repo, git history
(commits 28c892b / fdf0807 / c3695bd introduced only the CSVs + JSON, never the generating code),
branches (hermes/*), /tmp. **No script that builds GOAL100_STRICTTRADE_BALANCED_daily.csv,
GOAL100_IBKR_STRICT_BALANCED_daily.csv or the borrow-fee/cost layer is committed anywhere.**
The canonical champion_build.py builds the OLD 16-pool only. Same gap as STRICTAUDIT_CONSTRUCTION's
charter predicted. GOAL100_FINAL_STATE.md's "committed, byte-verified" claim is TRUE for the 12
sleeve CSVs (10 of 12 re-verified by me/AUDIT2; see 6.4) but FALSE for the champion blend.
2.2 The GOAL100_STRICTTRADE.json meta is also malformed: "excluded" contains the string
"A1credit - fail on real LQD/HYG (synthetic-BAA paper edge)" as a pool name.
2.3 MY RECONSTRUCTION (documented pipeline: per-sleeve vt10 60d trailing shift(1) cap8 -> EW ->
global vt -> 126d rolling-peak throttle shift(1), FR=0.5, A=(TGT.085,THR.04), B=(TGT.11,THR.03),
BAL=mean):
- vs committed, holiday-DROP mapping: n=4522, corr 0.9815, mean|Δ|=9.15bps/day, max|Δ|=2.99%
- my raw ann 57.2% (TGT .0975) / 50.3% (TGT .085) vs committed 49.36% -> committed sits ~0.9pp
  BELOW my .085 reconstruction, i.e. ≈ instrument costs (1.27pp, §4) + borrow (0.2pp, §6).
- holiday-ACCUMULATE mapping (as documented): corr drops to 0.9409, MSE 10x worse than drop
  mapping -> the builder DROPPED holiday rows rather than accumulating (§5).
- st = 0.9653·ft (FINAL_TRUTH_BAL) on 4414 common dates, R²=0.886 — the strict series is a
  de-credit, de-August, vol-matched cousin of the 14-sleeve FINAL TRUTH, as claimed.

## 3. INSTRUMENT MAPPING — per-sleeve verdicts
| Sleeve | Underlying data (verified on disk) | Tradeable at stated cost? | Verdict |
|---|---|---|---|
| brwt5/7/10/15 | FRED DCOILBRENTEU/DCOILWTICO **SPOT** (harness fred('brent'/'wti')); NO futures series anywhere on disk | CL/BZ futures spread is a real trade; 1.5bps plausible; but spot→futures basis never quantified (G1 found no futures data) | REAL-PROXY, basis UNVERIFIED |
| C5ng/C5ngsum | FRED DHHNGSP **SPOT** prints (7441 weekday-only prints, none Sat/Sun) | NG futures tradeable; basis & roll unquantified; publication-lag open (§8) | REAL-PROXY, basis UNVERIFIED |
| A5r2 | SPY closes (twelve_big, real) + VIX/VIX3M as SIGNALS only | 6bps conservative vs real SPY ~2-3bps; long-only; vt cap 2.0 = Reg-T boundary | REAL |
| a6r7 | FRED DGS2 → synth 2y TR | my re-computation: corr(synth2y TR, IEF)=0.721 (n=4962) CONFIRMS G3; SHY/ZT data NOT on disk so "SHY-faithful" is UNVERIFIED, only the IEF cross-check exists | REAL-PROXY (rates, faithful) |
| QAxasts | legs: WTI spot, gold spot, synth-10y (corr to IEF 0.955, my n=4960 CONFIRMS), −DXY spot, **−VIX SPOT** | 4/5 legs fine; **the VIX leg is not a tradeable instrument** (VIX spot has no roll/carry; short-VIX futures differ materially); the sleeve's own meta says "VIX-leg alone SR 1.08; drop-VIXS 0.25" — i.e. nearly ALL edge sits in the non-tradeable leg | **FLAG: paper-like leg**, same class of test that killed A5r7/A1credit was NOT applied here (no VIX-futures series on disk → basis UNVERIFIED) |
| carryv2 | wti/brent spread z-fade, natgas winter (both SPOT, ffill'd to bdays), xau spot + tbill accrual | futures equivalents exist; basis unquantified; note members 2/3 ACCRUE T-BILL WHEN FLAT (carry embedded) | REAL-PROXY, basis UNVERIFIED |
| dualmom | 298-name twelve_big panel; long-only top tercile + FF 200d-MA gate | REAL; 15bps mid-cap L/S cost is conservative for a LONG-ONLY book | REAL |
| XGB1y | gkx PIT preds parquet (24.7MB, Aug 20) → monthly book → daily spread | 15bps L/S plausible; shorts ARE held (deciles, §6) | REAL book, provenance FLAG (6.4) |
Pool composition check: JSON pool = exactly the 12 files above; A5r7/A1credit correctly excluded
(I verified removal: corr(st−ft, A5r7)=-0.67, corr(st−ft, A1credit)=-0.60 — the removed sleeves'
signature is absent). Note the 12 files are ~7 economic engines (4×brwt + 2×natgas slots).

## 4. COST CROSS-CHECK vs 6bps-embedded sleeves — NO double-charge, layer IS applied
- Sleeve CSVs already embed 6bps (verified in each repro script: brwt `tup*cost/1e4`, a6r7
  `turn*6/1e4`, A5r2 `to*6/1e4`, C5ng `turn*6e-4`, dualmom `turn*COST/1e4`).
- Instrument layer turnover (my computation, accounting weights, 2008-03..2026-07): one-side
  turns/yr — carryv2 7.51, XGB1y 2.53, a6r7 1.76, C5ngsum 1.43, dualmom 1.06, brwt5/7/10/15
  0.90-1.02, A5r2 0.87, C5ng 0.81, QAxasts 0.61. Total instrument drag at the stated bps
  (1.5/5/6/5/8/5/15/15) = **1.27pp/yr** (= 127bps of turnover-weighted cost; portfolio drag per
  +1bp uniform = 0.020pp). Adding 1.27pp + 0.2pp borrow to my TGT-.085 recon (50.3%) gives
  ~48.8% ≈ committed 49.36% (Δ -0.9pp, within convention noise).
- VERDICT: the committed series charges the sleeves' OWN net returns MINUS an incremental
  instrument-cost layer of the right order; it does NOT skip the layer and does NOT double-count
  the 6bps. The residual double-charge direction is CONSERVATIVE (A5r2 charged 6bps incremental
  on top of its own 6bps ⇒ effectively 12bps; dualmom 15 ⇒ ~21bps).

## 5. NYSE CALENDAR — CLEAN of phantom rows, but NOT "NYSE calendar" and NOT accumulated
- Weekend rows: 0. NYSE-holiday rows: 0 (of 173 holidays in span, authoritative calendar incl.
  Good Friday, Juneteenth 2022+, Sandy 10/29-30/2012, Bush 12/5/2018, Carter 1/9/2025).
- BUT 263 missing weekdays = 173 NYSE holidays + **90 NYSE-OPEN weekdays silently dropped**:
  18× Columbus Day, 14× Veterans Day (US bond holiday, NYSE OPEN), 10× Easter Monday, 8× Summer
  Bank Holiday, 8× Early-May Bank Holiday, 5+4× Boxing Day(+subst), 4× day-after-Thanksgiving,
  1× Platinum Jubilee (6/2/2022), 1× Queen's funeral (9/19/2022), 1× Royal Wedding (4/29/2011),
  1× VE Day (5/8/2020), 1× Juneteenth-observed Friday (6/18/2021, NYSE OPEN), plus ~17 further
  substitution/half-day artifacts (e.g. 2018-12-24, 2018-12-31, 2017-07-03). SPY traded on every
  one I checked. The st calendar is the union of the 12 SLEEVES' print calendars (FRED/futures-
  like/UK-flavored), not the NYSE calendar.
- "Holiday P&L accumulated to next trading day" is FALSE for this file: on the 234 post-holiday
  rows, MSE vs compounded-of-gap reconstruction is 10x WORSE than vs simple drop (§2.3).
- Materiality: the raw blend's 171 NYSE-holiday rows carry mean +29.0bps/day, +49.6pp of simple
  cumulative P&L = 4.4% of total ≈ **+2.8pp/yr that DROPPING removes** — i.e. the calendar flaw
  is in the CONSERVATIVE direction here (opposite sign to the +0.75pp inflation the memo fixed
  in the old champion), but it means the documented convention and the file disagree.
- The one Sunday row inherited from the panel (2009-07-26, all-zero) is correctly absent.

## 6. BORROW-FEE ACCOUNTING — claim materially mis-stated; net effect ~0.2pp, conservative
(a) Is the fee subtracted? **UNVERIFIED at byte level** (builder missing, §2). My reconstruction
    with a plausible fee schedule lands on the committed ann (§4), consistent with ~0.2pp borrow:
    XGB1y avg accounting weight 19.6% × 100bp/yr fee (80%×50bp + 20%×300bp) = **0.196pp/yr**.
(b) Short inventory REALISM:
  - dualmom: **HOLDS NO SHORTS.** Code (campaign/scripts/QA_dualmom_band121.py) is long-only
    top-tercile; my exact rebuild from raw panel reproduces the committed CSV with corr 1.00000000,
    maxdiff 9.97e-17 (n=4743). Beta to FF mkt +0.34. The memo's "equity L/S books (dualmom, XGB1y)
    hold ~10 mid/large-cap shorts" is **FALSE for dualmom** (its 15bps cost is also then
    conservative, not tight).
  - XGB1y: shorts ARE held — median 426 names/month with preds ⇒ decile ≈ **42 names per side**
    (not "~20"); book is dollar-neutral so short notional ≈ the sleeve's 19.6% NAV weight.
(c) Rebate excluded: cannot be read off the artifact (no builder). The committed level is
    consistent with exclusion (a Fed−50bp rebate on ~0.2 of NAV ≈ +0.4-0.7pp would be visible in
    my 0.9pp gap); treat as PROBABLY-excluded, formally UNVERIFIED.

## 7. HIDDEN LEVERAGE / FINANCING — the IBKR §15.2 numbers don't survive re-measurement
- Capital-real gross exposure (EW of per-sleeve |vt scale|, the scales the sleeves actually
  apply): **mean 2.17x, p95 3.12x, max 8.00x** (brwt/a6r7 caps 5-8, A5r2 cap 2.0).
  The memo's "mean 1.43x, max 4.44x, long leg ≤1.62x, Reg-T compliant" matches the normalized
  accounting weights (which sum to 1 by construction) — my measure is the one that costs money.
- Financing on (gross−1x) at 4.75% (T-bill+25bp): **5.60%/yr mean**. Charged against the
  committed series: **ann 43.8%, SR 4.65, DD -8.79%** (my daily-accrual approximation).
  The memo's "margin interest ~0" is only true in the normalized-weights accounting, not in
  capital terms. This is the largest single caveat on the 49.4% headline. (It IS disclosed as
  "internally vol-targeted" in §15/16, but never charged in any STRICTTRADE artifact.)

## 8. NATGAS PUBLICATION-LAG (charter job 5) — bounded, material to DD, NOT to ann
- Data: DHHNGSP prints on weekdays only (1403 Mon, 1533 Tue, 1531 Wed, 1503 Thu, 1471 Fri over
  7441 prints); Fri→Mon weekend gaps exist as single log-steps, so same-close signal → next-print
  P&L is internally consistent. Whether the print is available AT the close it is stamped is
  UNVERIFIED (no network) — the open item stands.
- My direct 1-day-lag simulation of the C5 signal (shift signal & filter by 1 print):
  SR 1.74 → **1.48** (-15%), ann 23.1% → 20.2%. The memo's "-85% edge" haircut is far more
  extreme than the mechanical lag-1 effect I measure.
- STRICTTRADE-level (my reconstruction): dropping both natgas sleeves: ann 57.2% → 54.6%
  (**-2.6pp**); 85%-edge cut: -1.4pp, and DD worsens -9.94% → -10.93% at the same vol target.
  The memo's claimed lag-variant (ann HIGHER at 52.4-52.6%, DD only -7.0/-8.4%) could NOT be
  reproduced by me — no lag-variant artifact file exists in campaign/results. I can only confirm
  the conservative bound: the blend holds without natgas, but the DD story under the lag stress
  is UNVERIFIED and my evidence points the other way.

## 9. SLEEVE-LEVEL provenance re-checks (what "byte-verified" covers)
- dualmom: rebuilt from raw panel, corr 1.00000000, maxdiff 9.97e-17, n=4743 — EXACT (§6b).
- XGB1y: **PROVENANCE FLAG.** The daily sleeve is a month-constant spread (within-month std=0,
  verified). Its month totals match the Aug-20 committed blob of gkx_1y_deploy_monthly.csv with
  corr 0.9987 (0/210 months exact, max month diff 2.87e-2, max daily diff 1.5e-3) and the CURRENT
  working-tree csv (regenerated Sep-1 16:07, AFTER the audit) with corr 0.9438. AUDIT2's
  "corr 1.000000, cum-diff 7e-13, 204/213 exact" is not reproducible against ANY artifact now on
  disk (git HEAD holds the Aug-20 blob e594622b; the generator state of Aug-28, when the sleeve
  was written, is not committed). Edge magnitude is essentially unaffected (corr ≥0.94, totals
  within 3% in overlapping months) but "byte-verified" is FALSE for this sleeve today.
- brwt family: repro script committed (backtest_brwt_spread_rev15.py, spot-based, exact
  construction verified by AUDIT2; data files present: DCOILWTICO/DCOILBRENTEU).
- A5r2/a6r7/QAxasts/carryv2/C5ng/C5ngsum: repro scripts + raw data present (verified paths);
  AUDIT2's byte-exact verdicts stand for these.

## 10. SUMMARY TABLE — claims vs my verdicts
| Claim (FINAL_STATE / TRUTH_MEMO §16) | My verdict |
|---|---|
| "12 instrument-real sleeves" | PARTIAL: 12 files ≈ 7 economic engines; no corr-0.03 paper legs; QAxasts VIX-spot leg flagged; natgas/WTI/Brent/synth-2y = spot proxies with UNVERIFIED basis |
| "all byte-verified" | FALSE for the champion blend (no builder exists) and now for XGB1y (provenance gap); TRUE for 10-11 of 12 sleeves |
| "NYSE calendar" | CLEAN of phantom rows (0 weekend, 0 holiday) but 90 NYSE-open days dropped; accumulation documented ≠ accumulated |
| "broker-real costs" | YES, layer present, ~1.27pp/yr, not double-charged, conservative direction |
| "borrow fees charged (50bp+20%×300bp)" | UNVERIFIED at byte level; economically ~0.2pp; dualmom-shorts claim FALSE; XGB1y shorts real (~42/side) |
| "short-proceeds rebate excluded (conservative)" | UNVERIFIED, consistent with exclusion |
| ann 49.4% / SR 5.24 / DD -6.1% / 0 neg yrs / OOS 55.9% / LOYO 46.7-51.0 | ALL CONFIRMED on the committed file |
| "no financing needed (gross 1.43x)" | CONTESTED: capital-real gross 2.17x mean / 8.0x max; financing @4.75% = 5.6pp/yr ⇒ ~43.8% @ -8.8% if charged |
| span 17.9y | understated; actual 2008-03-31..2026-07-31 = 18.3y |

## 11. WHAT WOULD MAKE THIS BETTABLE
1. Commit the STRICTTRADE builder (12 files → calendar → vt → throttle → costs → borrow) with a
   --verify mode, and regenerate the JSON without the malformed excluded entry.
2. Re-base the calendar to true NYSE days (incl. Columbus/Veterans/Good-Friday-Eve half-days) and
   accumulate holiday P&L exactly as documented.
3. Correct the memo: dualmom has no shorts; XGB1y ~42/side; drop the "gross 1.43x" claim in favor
   of the 2.17x/8.0x capital-real measure, or charge financing and headline ~43.8% @ -8.8%.
4. Quantify VIX-futures basis for QAxasts' dominant leg (or re-leg it to VIX futures data);
   quantify NG/CL/BZ futures basis (needs futures series; none on disk today — G1's finding stands).
5. Re-freeze XGB1y against a committed generator state.

STRICTAUDIT_EXECUTION DONE
