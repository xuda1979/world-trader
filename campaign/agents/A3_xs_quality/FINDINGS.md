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
