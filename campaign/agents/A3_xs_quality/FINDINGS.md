# A3_xs_quality — FINDINGS (round r1, 2026-08-28)

Environment: 298-name panel (twelve_big, 2006-09..2026-08), T+1 monthly L/S engine
(`campaign/agents/A3_xs_quality/engine.py`), 6 bps one-side, vol-target 10% via trailing
expanding window (min 60d, cap 5x), PIT rule for fundamentals: FY y usable only from
Jul-1 y+1. Engine self-test (12-1 momentum) behaved sanely (SR -0.05, IC-consistent).

**Headline: ALL charter families FAIL gates on this panel. Root cause is the panel itself —
current S&P-500 constituents => survivorship bias that inverts/kills quality, investment,
and low-risk premia (shorting "bad" names shorts the survivors that later became megacaps).**

## Idea 1 — Profitability (Novy-Marx, op_income/TA, NI/TA fallback) — FAIL
- Backtest (terciles 1/3-1/3, 2010-2026): SR **-0.21**, H1 0.02 / H2 -0.44, 12 neg years,
  worst -19.6% (2013), ann -2.9%.
- Diagnostic: mean monthly rank IC = **-0.0029**, ICIR -0.09; IC negative in 11/17 years.
- Verdict: zero (slightly negative) predictive power; script `idea1_profitability.py`.
- Note: strict gross profitability (rev-cogs)/TA infeasible — cogs coverage only 31% of
  fundamentals rows (revenue 57%); used op_income/TA (86% coverage) + NI/TA fallback.

## Idea 2 — Investment / asset growth (Cooper et al, low-minus-high) — FAIL
- Terciles: SR **-0.05**, H2 -0.26, 8 neg years, worst -25.3% (2023); 20/20 concentrated:
  SR -0.00. Mean IC -0.0026, ICIR -0.08. Script `idea2_investment.py`.

## Idea 3 — Composite quality z(profit, low leverage, ROE stability) — FAIL
- SR **0.04** (ann 0.6%), H1 0.09 / H2 -0.01, 8 neg years. Mean IC +0.0025, ICIR 0.08.
- Sub-signal ICs (PIT, full window): leverage IC -0.0026, ROE-stability IC -0.0039,
  NI/TA IC -0.0070 — all dead. Script `idea3_composite.py`.

## Idea 4 — Low-risk (long low idio_vol / short high) — FAIL (INVERTED on this panel)
- After fixing feature-date alignment (features are month-end dated; aligned asof <= t,
  staleness <= 40d): 2017-2026, SR **-0.50**, worst -31% (2020), 9 neg years.
- Full IC screen of daily_features (all sign = "anomaly" direction, i.e. long-low):
  idio_vol -0.018 (ICIR -0.39), beta_12m **-0.054 (ICIR -0.63)**, vol_1m -0.031,
  downside_6m -0.042, corr_6m -0.036, skew_6m -0.008, kurt_6m -0.012, price vol12m -0.035.
  => The low-risk anomaly is *sign-inverted* 2017-2026 on this survivorship-biased panel.

## Idea 5 — Inverse-risk blend (long high beta+corr+downside z-blend) — FAIL (near miss)
- Economically this is regime-chasing, not the documented anomaly; tested for completeness.
  With honest vol targeting (fixed engine trimming): 1/3-1/3 SR 0.55 (H1 0.37/H2 0.81,
  worst -7.1%); 20/20 SR 0.54 (H1 0.34); 40/40 SR **0.61**, H1 0.37 / H2 0.93, 1 neg year
  but worst **-6.0% (2022) < -5% gate** => gate (d) FAIL. Not saved — and the rationale
  ("short low-vol") contradicts the leverage-constraint literature, so gate (f) is weak too.
- Bugs found & fixed en route: vol-target must be computed AFTER trimming to the active
  window (pre-signal zeros deflate trailing vol => over-leverage); scramble_test reshape.

## Conclusions for r2 planning
1. Do NOT retry fundamental quality/investment on this panel without a point-in-time
   universe (delisted names). Any "quality" edge here is indistinguishable from zero.
2. Risk features have stable NEGATIVE anomaly ICs (i.e., high-beta/high-risk outperformed)
   through a megacap bull regime — I refuse to save that as a sleeve on rationale grounds;
   it is the same trade as short-vol/momentum-crash insurance.
3. If r2 allows: PIT universe reconstruction from fundamentals (shares/equity history) to
   de-bias the panel, or apply quality as a *tilt overlay* on other agents' sleeves rather
   than a standalone L/S.
ROUND r1 DONE

# A3_xs_quality — FINDINGS (round r2, 2026-08-28) momentum family

Environment: same panel/engine as r1; new r2lib.py weight-based backtester
**verified identical to engine.backtest (max daily net diff 0.0)** — supports arbitrary
weights (needed for gating/inverse-vol/regime combos). All runs T+1, 6 bps one-side,
trailing expanding vol-target 10%.

## Idea 1 — 12-1 momentum xs, tercile L/S — FAIL
- SR **0.03** (H1 −0.24 / H2 0.22, 8 neg yrs, worst −19.3% 2009); 6-1m SR −0.03; 9-1m SR −0.02;
  cap-neutral (PIT shares×px, Jul-1 y+1 PIT) SR 0.02; liquidity-neutral SR −0.01; inv-vol-wtd SR 0.02.
- Confirms r1: cross-sectional momentum is dead on this survivorship-biased panel.

## Idea 2 — Momentum + SPX/200d-MA regime gate (FF Mkt-RF+RF cum, 1926+) — FAIL as L/S
- Gated L/S SR 0.25; gate-longs-only (keep shorts) SR **−0.08** — shorts of "losers" are the
  toxic leg (they short future megacaps). Momentum per se remains unusable.

## Idea 3 — Vol-scaled momentum (inv 21d vol weights) — FAIL: SR 0.02 (same as EW).

## Idea 4 — Momentum conditioned on low idio_vol (features parquet, 2016-08+) — FAIL
- L/S SR 0.37, negYr 2 but H2 0.24; dual-mom low-iv variant SR 0.74, worst −7.2% → gate (d) fail.
- Long-only 12-1 top tercile: SR 0.76, H1 0.55/H2 0.94, but 3 neg yrs, worst −15.8% → gate (d) fail.
- 52-week-high proximity (idea 5, George-Hwang): L/S SR **−0.30** (inverted!), LO SR 0.72,
  3 neg yrs → fail. Sector-neutral infeasible (no PIT sector map; used cap/liq proxies).

## Idea 5 — DUAL MOMENTUM (Antonacci): xs 12-1 top-tercile LONG-ONLY, flat unless market gate ON — **PASS, SAVED**
- `QA_dualmom_band121`: gate = FF market vs 200d MA with ±3% hysteresis band (in only above
  1.03×MA, out only below 0.97×MA), invested 75% of days.
- FULL SR **0.89**, H1 **0.99** / H2 **0.80** (2007-10..2026-08, ann 9.6%, vol 10.8%,
  MaxDD −24.5%), neg years **1/20** (2022 −4.3% > −5%), cond corr to mkt when on 0.92.
- Gate (b) plateau: 25-cell (MA win × band) grid → 21/25 cells within 20% of peak SR (peak 1.01);
  yearly-gate profile robust in 9/25 cells; chosen (200, 0.03) interior, not a spike.
- Gate (e) scramble (200 reps, cost-inclusive): xs-permute p=1.000; both-destroy p=1.000.
  IMPORTANT null: cost-naive scramble (nulls w/o 6bps) gives p≈0.90 and false doubt — always
  cost-inclusive nulls. Gate-only EW-universe null: SR 0.86 but 4 neg yrs (fails gate d) —
  the xs tercile concentration is what fixes the yearly profile (+0.03 SR, 4→1 neg yrs);
  shuffled-xs with intact gate fails yearly gate. The gate alone does NOT pass the contract.
- Library corr: max 0.78 (Multi_Strategy_SharpeW) — equity-beta-shaped, expected for a gated
  long-only; mean |corr| 0.27 over 42 sleeves. Coordinator should weight that in blending.
- Repro: `campaign/scripts/QA_dualmom_band121.py`; CSV+meta in sleeves/.
- Rationale: Antonacci dual momentum — hold relative strength only when market absolute
  momentum positive; hysteresis band (standard whipsaw control) is what repairs 2022 (−6.7%→−4.3%)
  and 2008/2018 (→0.0). Documented TS-mom/MA-timing literature basis.

## Idea 6 — EXT panel (440 names) cross-check — VOID (data polluted)
- EXT daily returns contain broken adjustments: single-day prints up to +4,439,900%
  (AIKO/AFCL/AFRMF), realized ann vol 128% on a 10%-vol-targeted sleeve, 2020 "+603%".
- Cross-check impossible without data repair; flagged for coordinator (do NOT use twelve_extend
  for returns until re-cleaned).

## r2 conclusions
1. FIRST SAVED SLEEVE for A3: QA_dualmom_band121 (all 7 gates). Edge decomposition honest:
   mostly regime-timing (gate), xs momentum contributes concentration/turnover trimming —
   but the xs concentration is *necessary* for the yearly gate; neither component alone passes.
2. Scramble nulls MUST reprice costs on null runs (harness convention), else false negatives.
3. Panel diagnosis unchanged: xs L/S premia (momentum, quality, low-vol) are unreliable here;
   the surviving sleeve earns via regime-timed long-only exposure, i.e., partial beta —
   blend coordinator should treat it as a defensive-timing overlay, not pure alpha.
ROUND r2 DONE

# A3_xs_quality — FINDINGS (round r4, 2026-08-30) vt15 budget + charter families

Environment: same panel/engine (T+1, 6bps one-side); new r4lib.py (weights builder,
vol-target FIXED back to r1 convention: trim to active window THEN trailing expanding vt —
first r4 run forgot trim and showed vt10 SR 0.85 vs true 0.89; corrected before any verdicts).
Mission bar: SR>=0.8 ann>=12% |corr|<=0.3 to CHAMPION_FINAL; halves both >=0.4 at vt15.

## Idea 0 — QA_dualmom re-vol 10%->15% (charter fast win) — FAIL
- vt10 repro exact (SR 0.89, H1 0.99/H2 0.80, worst -4.3%) then vt grid: SR stays 0.89,
  but worst year scales LINEARLY: vt11.5% -4.9%, vt12.5% -5.3%, **vt15% -6.4% (2022)**
  => gate (d) fail. Max vt passing gate(d) = 11.6% (ann 11.2%, worst -4.9%) — but that is
  a 0.997-corr near-duplicate of the saved sleeve; NOT saved (duplicate rule).
- Charter's "ret->~14% SR stays" was arithmetically true but gate-blind: -4.3% x 1.5 = -6.4%.

## Idea 1 — 12-1 momentum LONG-ONLY top-quintile, MA gate, vt15 — FAIL
- Charter cell (12-1, top 15%, MA150): SR 0.99, H1 1.12/H2 0.83, 1 neg yr BUT worst **-8.6%**
  => gate (d) fail. 54-cell grid (lb/skip/frac/MA win): SR range 0.90-0.99, halves always pass,
  yet worst-year spans -2.2%..-12.7% across adjacent cells — yearly-gate pass/fail is a param
  lottery (gate-shopping gw200 cells that pass would be dishonest; rejected whole family).
- ALL cells corr 0.63-0.68 to champion => breaches |corr|<=0.3 mission cap regardless.

## Idea 2 — Statistical sector-momentum, top-2 clusters, gated, vt15 — FAIL (near miss, rejected honestly)
- Charter said reuse A1 clustering; VERIFIED A1 dirs contain no clustering code (only
  cta_gated_program_v1.py macro-CTA) => rebuilt minimal PIT version: monthly hierarchical
  clustering (average linkage) of trailing-252d return correlations, K clusters, top-K by mean
  252-42 momentum, positive-momentum members equal-weight, FF-MA200/3% gate.
- Base cell K12/TOP2: SR 0.78, 7 neg yrs => fail. 12-cell scan (K 8/12/20 x TOPK 2/4 x
  126-21/252-42): best **K20/TOP2/252-42: SR 1.10, H1 1.32/H2 0.88, 1 neg yr (-1.7% 2021),
  ann 17.5%, vol 15.8%, maxDD -28%, scramble p=0.995 (200 reps cost-incl)** — passes ALL
  standard gates a-f. Rejected ONLY on: (i) corr to champion **0.395 > 0.3 mission cap**;
  (ii) corr **0.604 to my own QA_dualmom_band121** — same gated long-only equity exposure;
  (iii) NO plateau in K (K8: 3-5 neg yrs; K12: 2-7; only K=20, my grid edge, works).
  Yearly profile suspiciously pristine (2009 +56% ... worst any year -1.7%) — regime-gated
  momentum post-2008 on survivorship-biased panel; would not trust OOS.

## Idea 3 — Earnings-momentum proxy (6-1 mom conditioned on fresh PIT fundamentals) — FAIL
- Freshness mask (FY filed within 14 or 24 months, avail Jul-1 y+1): 0/8 cells pass.
  Best: SR 0.87, H1 1.17/**H2 0.61**, 4 neg yrs, worst **-13.3%**, corr 0.64-0.67.
- Diagnosis: fresh24 ~= fresh14 results nearly identical => the fundamentals-availability
  conditioning is INERT on this panel (coverage too uniform among current constituents);
  the signal is just momentum, and momentum LO inherits the same deep drawdown years.

## r4 conclusions
1. vt15 breaks gate (d) for every member of my gated-long-only family (2022 loss -4.3% at
   vt10 scales to -6.4..-8.6%); the r4 ann>=12% + worst-year>-5% combo is infeasible for
   this family at ANY vt — ann and tail scale together linearly.
2. The mission |corr|<=0.3 cap is the binding constraint, not SR: every gated long-only
   equity variant lands 0.37-0.68 vs CHAMPION_FINAL. A3 cannot add a mission-compliant
   sleeve from price-only panel signals; next round should go short-side/overlay/conditioned
   or accept duplicate status.
3. Honest retraction discipline: caught my own vol-target trim bug in run #1 of the round
   (vt10 SR 0.85 vs true 0.89) before any verdict was recorded; all r4 numbers use corrected
   pipeline (r4lib.sret).
4. Idea2-K20 documented as best near-miss (script + numbers above) for coordinator interest;
   NOT saved per mission corr cap + duplicate-vs-own-sleeve + no-plateau grounds.
ROUND r4 DONE

# A3_xs_quality — FINDINGS (round r6, 2026-08-30) NEW-FAMILY directive

Environment: same panel (298 names, 2006-09..2026-08); new r6lib.py general-rebalance
backtester (any rb dates, T+1, 6bps on both legs, trailing expanding vt10) — VERIFIED
identical to r2lib on the saved dualmom construction (corr 1.000, maxdiff 0.0, SR 0.89/H1
0.99/H2 0.80 repro exact). Charter gates: SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%,
circular-shift scramble p<0.05, plateau, corr<0.35 to CHAMPION_FINAL.

**Infra bug caught before any verdict: r6lib v1 held STALE positions through gate-off
periods (only invested month-ends registered as rebalance dates). Cross-check vs verified
r2lib diverged on 2007-12-03 (79 phantom names); fixed by writing a Wt row (zeros=flat)
at EVERY rebalance date. All r6 numbers use the verified pipeline.**

## Idea 1 — Daily seasonal momentum (trailing-2y same-weekday mean excess ret, weekly reb) — FAIL
- Long-only top-Q: SR **0.85** (LO 20%: H1 1.15/H2 0.74, 2 negYr, worst -6.3%) — passes all
  charter PERFORMANCE gates but **corr_champ 0.641 / corr_old 0.704 >> 0.35** => same
  equity-beta trap as r4 (a long-only xs tilt on this panel IS the market).
- L/S tercile: SR **-0.28**, 12 negYr (short leg shorts future megacaps — r1 lesson re-confirmed).
- Beta-hedge salvage (long book - beta x FF-mkt, hedge costs billed): beta=1.0 SR 0.25,
  beta=0.8 SR 0.58 (corr 0.362, worst -12.9% fail), beta=1.2 negative. NO beta gives both
  SR>=0.7 and corr<=0.35; the seasonal tilt alone has no standalone edge.

## Idea 2 — Beta-rotation (monthly long bottom-beta-quintile, FF-mkt MA200 gate) — FAIL
- Base (b252, gate 200/3%, Q20): SR 0.58, H2 0.34 fail, corr_champ 0.45, corr_old 0.613.
- Ungated: SR 0.48, worst -17.2%. Resid-beta (SMB/HML-stripped): identical 0.58.
- frac=0.40 variant passes r6 performance gates (SR 0.73, H1 1.0/H2 0.47, 3 negYr, worst
  -5.9%) but **corr_champ 0.517, corr_old 0.712** => FAIL. Bottom-beta-tilt is again just
  equity exposure with the same gate as my saved sleeve (corr to dualmom 0.61-0.71).

## Idea 3 — Volume-shock reversal event book (down>3% on >3x vol, long 5d) — FAIL (closest)
- Best low-corr family: corr_champ 0.20-0.37, corr_old 0.34-0.45 — structurally different
  from everything in the library, as the charter hoped.
- Grid (drop 2-5% x vx 2-3 x hold 5-15d x K 5-10): SR peaks 0.72 at (2%, 2.5x, 10d, K5),
  corr 0.351 — and SR/corr move TOGETHER: every cell with corr<0.35 has SR<=0.65.
- Full battery on best cell, CORRECTED construction (numpy pairwise-outer scatter; SR 0.685,
  corr_champ 0.3439): H1 0.57/H2 0.81 pass, 3 negYr pass, worst -6.9% pass, plateau GOOD
  (6/6 neighbors SR 0.67-0.70 within 20% — no spike), BUT **circular-shift scramble FAILS:
  real 0.685 vs null95 0.772, p=0.185 >> 0.05** — event timing indistinguishable from a
  shifted event mask; the drift premium the book harvests is not shock-conditional enough.
- CONSTRUCTION CAVEAT (documented for honesty): original loop builder printed SR 0.72/
  corr 0.3508 for the same params; minimal-semantics test (pandas iloc 2-array setitem ==
  numpy pairwise-outer) supports the corrected 0.685/0.3439; either way corr sits ON the
  0.35 boundary and scramble fails (p would be ~0.15-0.25 at SR 0.72 vs same nulls).
  Verdict FAIL under both constructions; cell would be boundary-gate-shopping anyway.

## Idea 4 — Dispersion regime retiming of QA_dualmom (21d xs-std vs trailing median) — FAIL
- Charter rule (high dispersion => carry dualmom): SR 0.89 -> **0.56** (69 days on, worst
  -6.9%) — destroys the sleeve; high xs dispersion is NOT when dualmom works here.
- Inverse (low dispersion on): SR 0.70, H1 0.72/H2 0.71, 2 negYr, worst -4.8% — but
  **corr to OLD dualmom 0.734 > 0.7 charter cap** and SR did NOT improve >= 0.1 (0.70 < 0.89).
  Fails both charter pass-as-new conditions. q60/q75/q90 quantile variants: SR 0.16-0.39.

## r6 conclusions
1. FOUR new families, ZERO saves — first round where the binding gate is corr, not SR:
   every long-only xs construction on this panel carries 0.43-0.73 corr to champion /
   0.61-0.73 to my own dualmom (r4 conclusion #2 re-confirmed on 3 fresh families).
2. The one genuinely orthogonal family (volume-shock events, corr 0.20-0.37) has real but
   too-weak timing: SR 0.685 fails circular-shift scramble at p=0.185. The event book's
   average drift premium exists but is not shock-specific on this panel.
3. Charter's dispersion idea is cleanly falsified: dispersion retiming REMOVES alpha from
   the gated-momentum sleeve here (0.89 -> 0.56 under the charter rule).
4. Advice to coordinator: A3's contribution remains QA_dualmom_band121 alone; a corr<=0.35
   mission sleeve will not come from price/volume-only panel signals — needs a different
   asset class (carry/CTA/credit) or fundamental PIT universe (r1/r4 conclusions stand).
5. Infra lessons persisted in r6lib.py docstring: (a) every rebalance date needs an explicit
   Wt row (zeros=flat) else stale positions; (b) pandas iloc 2-array setitem == numpy
   pairwise-outer (verified) — use the explicit numpy form in hot loops for clarity.
ROUND r6 DONE
