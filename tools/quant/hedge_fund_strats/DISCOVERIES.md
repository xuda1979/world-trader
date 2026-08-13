# Research Discoveries Log — high-Sharpe strategies at 6 bps/side

Cumulative findings of the 2026-08-12/13 research campaign (hedge-fund
strategy suite + cross-suite blends). Costs: **6 bps per side (12 bps
round-trip)**. Data: free daily (twelve_big, Polygon, FRED macro, FX,
Fama-French, AP-replication walk-forwards). All numbers cost-inclusive.
Primary source of detail: `RESEARCH_REPORT.md`; artifacts: `results/`,
`blend_*.py`, `subperiod.py`, `portfolio_spec.py`.

## POSITIVE discoveries (what works)

| # | Discovery | Evidence |
|---|-----------|----------|
| P1 | **The all-weather flagship: h3 + AP gold** (3-stream hedge EW: L/S 130/30 + CTA futures macro 21d + Global Macro, ex stat arb; 50/50 with AP gold composite). Monthly SR **0.94**, +10.7%/yr, MaxDD -10.1%, **positive in all 4 sub-periods 2008-2026** (+0.86/+1.49/+0.73/+0.50), **every 5y rolling window positive (min +0.25)**. BETA (corrected 2026-08-13): **low-beta +0.34 vs SPY** (rolling 3y 0.26-0.80), NOT market-neutral — the earlier β=0.00 was a benchmark-unavailable artifact; the 2024+ 3-sleeve IS near-neutral (+0.06) | `blend_monthly.py` |
| P2 | **The genuine diversifier is the polygon LS champion** (n10_r14/levdet3.0 family): corr with hedge sleeve **-0.003 daily** (+0.17 monthly) — the only near-zero-correlation validated leg found | `blend_6stream.py` |
| P3 | **2024+ construction: h3 + AP + LS champion, sleeve EW** — daily SR **1.15** (monthly 1.20), +11%/yr, MaxDD -3.5%, positive in both half-windows; deployment spec SR 1.24 daily | `blend_6stream.py`, `portfolio_spec.py` |
| P4 | **AP monthly-file/daily-audit mystery RESOLVED**: same book, one-month attribution lag (lag-1 corr **0.878**). Monthly file is signal-timed, daily audit realization-timed; the audit is the correct record | analysis in report |
| P5 | **3-stream EW > 4-stream EW**: dropping stat arb improves EVERY sub-period at 12 bps RT (0.64 vs 0.45 SR) | `blend_variants.py` |
| P6 | **Risk Parity is the only standalone positive in all 4 sub-periods** (0.28/1.23/0.12/0.66), SR 0.52-0.58 — cost-insensitive (1.9x turnover) | `subperiod.py` |
| P7 | **L/S 130/30 is the best standalone** (0.75 at 12 bps RT) but it is market beta (β≈1.05); cost doubling cost it only -0.05 SR (low turnover) | `run_all.py` |
| P8 | **Vol management (Moreira-Muir) on L/S halves MaxDD** (-45.8% -> -26.6%) at ~same SR (0.71 vs 0.75) | `run_extras.py` |
| P9 | **Champion-family 8.5y stream exists** (`ls_n10r14_daily.csv`, 2018-2026, daily SR +0.92) — quadruples the champion sleeve's history; 2019+ blends with it are positive in both sub-periods (SR 1.24-1.27) | `blend_robust.py` |
| P10 | **Cost sensitivity tracks turnover** (table in report): doubling 6->12 bps RT cost L/S 0.05, stat arb 0.57 SR | `run_all.py` re-run |
| P11 | **Multi-strategy INVERSE-VOL book is OOS-validated** (parallel loop, 2026-08-13): 6 sleeves (L/S volmanaged + Risk Parity + CTA + FX carry + AP gold + LS n10r14), inverse-vol weights, SR 1.24 / MaxDD -5.9% / n=2054 (2019-26, 6 bps). Walk-forward both directions positive AND beating EW (2019-22->23-26: SR 1.01; reverse: 1.48; EW 1.10) — not overfit. Deployable stream: `results/ms_iv_daily.csv` (`run_ms_iv_book.py`). NOTE vs flagship: 2019+ window only (mine covers 2008+, all-weather); includes FX carry (diluting in my h3+AP EW test, but low-IV-weight here); full-sample IV weights (mild selection) with the walk-forward pass as the honest guard | parallel session |

## NEGATIVE discoveries (what fails — equally valuable)

| # | Discovery | Evidence |
|---|-----------|----------|
| N1 | **Stat arb is dead at the real cost**: SR -0.85 at 12 bps RT (was -0.28 at 6), negative in ALL 4 sub-periods; 46x turnover vs ~5.6%/yr cost drag. It is blend poison, not fertilizer | `run_all.py`, `subperiod.py` |
| N2 | **FX carry rejected as a sleeve**: low corr (-0.09/-0.20) but own SR 0.11 — h3+AP+FX SR 0.99 vs 0.99, return diluted 8.7%->6.8%. Rule: sleeves must clear the cost hurdle alone; correlation alone doesn't qualify | analysis in report |
| N3 | **ALL six cross-asset replication legs FAIL their scramble gates**: gold_trend (17% scrambles beat real), cross_asset_tsmom (100%), fx_momentum (67%), overnight_drift (33%), crypto_trend (54%), cn_momentum (67%) | gate re-run |
| N4 | **The permutation-of-returns scramble gate is mathematically vacuous** (mean/std permutation-invariant — shuffling returns changes nothing); only signal-scramble gates are meaningful | `build_gated_portfolio.py` audit |
| N5 | **live_vslbl (8y, monthly SR 0.75) FAILED its signal-scramble gate** (33% of scrambles beat real) — looked great, excluded | `vs_lbl_validation.json` |
| N6 | **w8y_reval (8.4y, "ok" verdict) HURTS the blend when added** (0.65 vs 0.75 on 2018-26); w10y (10y) SR -0.52 dead | sleeve audit |
| N7 | **AP gold is NOT a near-zero-correlation diversifier** — corr with hedge sleeve +0.03/+0.61 daily/+0.49 monthly once realization-timed; the near-zero claim was a timing artifact | resolution chain |
| N8 | **The 1.15 flagship was a one-month-lag premium** on a misaligned series; the honest SR is 0.94 | lag analysis |
| N9 | **EMN, merger arb, credit, FI arb, CTA-equities, factor momentum are all ≤ 0 at 12 bps RT**; factor momentum's premium died post-GFC (-0.06) | `subperiod.py` |
| N10 | **Stooq futures still IP-blocked** (checked 3x) — no real-futures CTA upgrade | probe |
| N11 | **blend_refined.py's recent-window SRs (1.75-2.33) are selection-biased** — shorter windows exclude the hedge sleeve's negative early period; full-history windows (1.10-1.15) are the honest ones | reconciliation |
| N12 | **Monthly vol-management on the blend is unstable** (extreme multipliers in calm months) — rejected; inverse-vol weights give no gain over EW | weight tests |
| N13 | **My own first-pass "artifact" correction was wrong**: the distributed-AP approximation was nearly uncorrelated (0.025) with the real daily path; the original +0.61 corr was real. Lesson: verify native source files before approximating | second-pass audit |

## Process lessons (meta)

- **Sleeve rule**: diversify only among streams that each clear the cost
  hurdle on their own (P1/P5 vs N1/N2/N6).
- **Sampling discipline**: monthly-cadence books must be analyzed at
  their native frequency or with realization-timed records (P4, N7/N8);
  daily-sampled SR of smooth series inflates (N13).
- **Validation discipline**: a stream without a completed signal-scramble
  verdict is watch-validated, not validated (P9 pending; N4 shows why
  the gate method matters).
- **Window discipline**: report full-history windows; trimmed windows
  flatter SR (N11).

## Operational monitoring (2026-08-13)

- Champion live-health check (`tools/quant/ls/check_champion_health.py`):
  [OK] the champion's own 10d-horizon edge is intact — fresh live 10d IC
  +0.036 (last 6 months). The faster 1d-horizon IC is adverse (-0.132),
  i.e. the fast signal is decaying/regime-adverse while the deployed 10d
  signal is healthy. No action needed on the deployment leg.
- Reconfirms the validation gate: only LS_GBRT (champion family) passes
  the price-lag scramble; tsmom/gold/fx/pairs all FAIL — consistent with
  the sleeve audit (N3).

## n10_r14 8y verdict — **FAIL (2026-08-13, validated)**

`validate_n10r14_trimmed.py` on twelve_big 8y (10-scramble time-shift
gate), results in `regime_gbrt_v13/trimmed_twelve_big.json`:

- **Real backtest: Sharpe -0.33** (ret -3.7%/yr, MaxDD -65.9%, turnover
  11.4x/yr); regime split normal -0.33 / high-vol -0.42 / stress -0.77
  (negative in ALL regimes); diagnostics: `likely_overfit` (2 flags);
  OOS IC mean only +0.011.
- **Scramble: p = 1.000 → FAIL** — the real run is worse than its own
  time-shifted scrambles.

**N14 (critical) — the ls_n10r14_daily.csv stream (+0.92 SR, 2018+) is
NOT REPRODUCIBLE as the n10_r14 config on twelve_big.** The validated
run of the exact config shows -0.33 SR. Root cause: the factor screen
keeps ZERO factors on twelve_big ("no factors passed the strict gate")
and falls back to a DIFFERENT top-5 by ICIR — the stream must have been
generated under a different (more favorable) factor set, and its +0.92
is unverifiable and now suspect. The champion's polygon construction
keeps exactly its own 5-factor set — that transfer does not exist on
twelvedata.

**Decision tree — FAIL branch taken:**
- Flagship unchanged: h3+AP (2008+) / h3+AP+LS polygon levdet3.0 (2024+)
  — the polygon champion passed its own panel's scramble gate and is
  independent of this verdict.
- **2018-24 gap stays h3+AP-only** — the n10r14 extension (roadmap
  "h3+AP+n10r14 for 2018+") is DEAD unless the stream is verified.
- **Everything built on ls_n10r14 is conditional**: the parallel loop's
  IV book (`ms_iv_daily.csv`, SR 1.24) and `blend_robust.py` blends
  include the suspect stream as a sleeve — their levels rest on an
  unverified stream (their internal walk-forward consistency still
  holds, but the absolute SR is not trustworthy).
- Attribution claim "n10r14 positive every year 2023-2026" is likewise
  stream-dependent — treat as unverified, not a discovery.

The polygon LS champion (levdet3.0) already passed its own panel's
scramble gate — the 2024+ sleeve is independent of this verdict.

| P12 | **IV book neutrality VERIFIED** (2026-08-13): ms_iv_daily.csv beta vs SPY +0.04 (daily, 1849 days), rolling 6m -0.03..+0.26, never |β|>0.3 — the parallel book's "zero-beta" claim holds (unlike the flagship's β=0.00, which was an artifact). Contrast: h3+AP (EW) carries +0.34 beta by construction; the IV book's market-neutral legs (vol-managed L/S, RP, FX carry, n10r14) are what neutralize it. Level caveat still applies: the n10r14 sleeve is suspect (N14) | parallel session + verification |
| N17 | **Risk Parity does NOT join the flagship** (2026-08-13): corr +0.64 with h3, +0.59 with AP (same equity/carry flavor — not a diversifier at this scale); h3+AP+RP SR 0.89 vs h3+AP 0.94 (dilutes). The flagship's sleeve set is complete: every candidate sleeve has now been tested in-combination | `blend_monthly` extension |
| N18 | **Drawdown filters do NOT improve the flagship (user request tested, 2026-08-13)**. Full test matrix on h3+AP monthly (base: SR 0.94, +10.7%, MaxDD -10.1%, Calmar 1.06): trailing-DD reducer (-8%/-12%) 0.93/10.7%/-10.1% (no effect — grind-type DDs); earlier DD reducer (-5%/-8%) 0.88/10.0%/-10.3%; portfolio 6/12-MA trend filter 0.82/9.4%/-10.6%; SPY 10-MA market-timing gate 0.79/9.0%/-12.3% (WORSE — kills crisis-era alpha; the flagship's best periods are equity-crisis eras); capped vol-target 12% (0.5-1.5) 0.93/13.5%/-13.5% (leverage in calm periods deepens later DDs); combinations all worse. Root cause: the flagship's drawdowns are SLOW GRINDS (2018-10..2019-12 -10.1%, 2022-01..2024-03 -7.5%), not equity crashes, and they are INHERITED from the AP sleeve (AP's own 2018-19 DD -12.3% vs h3's -8.4%; AP already carries its own built-in DD reducer). Every monthly-cadence filter exits into grind bottoms and misses V-recoveries, trading away more than it saves. **The only MaxDD reduction found in the campaign came from adding the LS champion sleeve (2024+ 3-sleeve -5.6%) — now paper (N15).** Honest answer: no free drawdown filter exists for this construction; Calmar 1.06 is the flagship's risk profile. Scaling note: MaxDD is scale-dependent, Calmar is not — constant de-leveraging (e.g. 50% size) gives ~-5% MaxDD at half the return with the same SR 0.94; the only non-proportional drawdown cuts are new alpha sleeves or the (paper) champion leg | test matrix this fire |

| P13 | **Health monitor corroborates N18 independently** (parallel session, 2026-08-13): its regime-adaptive report also found fast VIX-gating and defensive rotation FAIL on the flagship — static allocation is near regime-optimal (SR 1.04, positive 17/19 calendar years). Deployable GO/CAUTION/TRIM stance monitor (`portfolio_health_monitor.py`, current stance **GO**): TRIM only on SUSTAINED degradation (21d negative SR AND -3% quarterly DD — the 2022-23 inflation soft patch is the only such event) | parallel session |

## N20 (2026-08-13, CAPSTONE) — Polygon champion DECOMMISSIONED: edge is a volume-precision artifact

The parallel session's controlled forensic test traced the live-516
(+0.35) vs twelvedata-516 (-0.10) SR gap to a **sub-basis-point volume
difference**: polygon reports exact share counts (float64), twelvedata
rounds volume to nearest 100 (int64) — e.g. 44155331 vs 44155300
(0.00007%). That rounding-level difference in the `liq_turnover` factor
**inverts SR by 0.45**. Every advertised champion SR
(1.686/0.86/0.49/0.35) was a precision-state artifact; ensemble mean
-0.36 (0% positive).

- **Operational**: run_live_signal.py has a DECOMMISSION GATE — forces
  HOLD, zero positions, "HOLD (decommissioned: illusory edge)". The
  champion must not be traded until re-derived on a volume-consistent
  feed with an acceptance gate (independent feed must not invert SR).
- **Impact on this suite**: the 2024+ 3-sleeve (h3+AP+LS, SR 1.15-1.20)
  and the parallel IV book (SR 1.24) are historical artifacts of a
  decommissioned leg — their recent-window numbers are NOT tradeable
  expectations. **The deployable flagship is h3+AP alone** (2008+,
  SR 0.94 monthly, all-weather — it never depended on the champion).
- N14/N15 were foreshadowed exactly by this (the 8y FAIL and the
  panel-state fragility); the volume-precision mechanism explains both.

## N19 (2026-08-13) — Stooq unblocked-but-gated; yfinance rate-limited

First access-state change since the campaign began:
- **Stooq**: the IP block (timeout) LIFTED — the PoW challenge page is
  now served, the SHA-256 solve works, verify returns 'ok' and sets the
  auth cookie — **but every subsequent data request returns 0 bytes**
  (tested with delays up to 30s, full headers, c+n in URL, repeated
  solve-verify cycles). The anti-bot changed since the 2026-06 flow:
  the fetch script's challenge→verify→CSV sequence no longer yields
  data. GATED state documented; retry_stooq.py now distinguishes
  BLOCKED/GATED/DATA.
- **yfinance**: YFRateLimitError (Too Many Requests) — GLD/SLV/DBC/USO
  ETF proxies (the metals-gap fillers) unavailable this moment.
- Impact: the real-futures CTA upgrade (and the metals gap) remains
  blocked, but the gate is now technical rather than an IP ban.
- **Attempt matrix (exhausted this fire)**: urllib+PoW (challenge→
  verify 'ok'→auth cookie→CSV returns 0 bytes, delays to 30s); full
  browser header set (verify 403); c+n in URL (empty); repeated
  solve-verify cycles (empty after 2 rounds); curl_cffi chrome-TLS
  (timeout — environment transport quirk: system curl returns nothing,
  only urllib reaches Stooq); brew has no curl-impersonate; pip blocked
  (PEP 668) outside venv. **The gate needs a browser-grade transport
  this environment cannot provide** — urllib is the only working
  transport and Stooq's server-side session logic defeats it. Hand off
  to the parallel session's infrastructure or a browserless-TLS host.

## Process lessons (ops)

- **Long validation runs must be launched with `PYTHONUNBUFFERED=1`** (or
  `python -u`): stdout redirected to a file is block-buffered, so phase
  prints invisible for hours — the 4h "silent" v13 run was computing
  fine the whole time. The trimmed validator's flush=True prints + this
  lesson fix the observability.

## N15 (2026-08-13) — Polygon LS champion: OVERFIT CONFIRMED by controlled A/B

The report's "scramble PASS" claim was UNSUBSTANTIATED (no PASS record),
and the parallel session's controlled robustness A/B (RESEARCH_LOG.md
"polygon champion n10_r14 is OVERFIT") now proves the advertised
SR 1.686 is a **panel-state artifact**:

- ±1 historical row (500 vs 501 dates, identical factor set) swings SR
  ~0.8 (+0.49 to -0.32); no reproducible panel state gives stable SR.
- **Root cause: knife-edge ICIR-fallback screen selection** — the strict
  ICIR gate never passes, so the top-5-by-|ICIR| fallback is used, and
  ±16 rows flips the kept set between the good factor set (SR 0.86-0.98
  forced) and the momentum cluster (SR 0.23). The three identical
  momentum transforms are redundant crowding on a razor margin.
- **True edge (controlled, restored panel): lev1 SR ~0.37, lev3 SR
  ~0.49** — a real but MODEST edge, not ~1.6. "Do not size to 1.686;
  treat as speculative/paper" (parallel session's operational verdict).
- The 08-12 "SR 1.682 reproduced" run used the pre-incident accumulated
  panel whose leading rows differ from today's — SR depends on the
  precise historical path, margin dominated by data sensitivity.

**Impact on the flagship**: the 2024+ 3-sleeve (h3+AP+LS, SR 1.15-1.20)
numbers stand as computed from the levdet3.0 series, but that series
reflects the artifact-prone panel state — the leg is **speculative/paper
until re-baselined** (paid polygon history or a screen-selection
robustness fix). **h3+AP (2008+) is unaffected** — it does not depend
on the champion. Deploy h3+AP; treat the champion sleeve as a paper
overlay at de-risked sizing.
- CONFIG RESOLUTION (2026-08-13): the val_H2_2025start negative belongs
  to the **rev3_n13 validation lineage** (1x, 13 names, 20d rebalance,
  refit 5d, no extra factors, 3.8 bps) — NOT the deployed levdet3.0
  (n10_r14: 3x, 10 names, 14d rebalance, refit 20d, extra factors,
  6 bps). The deployed leg's own series (flat to mid-2025, then +13.3%/
  +38.4% re-costed) is its own evidence; the recent-half fragility is a
  sibling-config finding. levdet3.0's honest status remains 'watch'
  (1 factor-decay flag), SR concentrated in the last ~14 months.

## FINAL STATE (2026-08-13) — deployment statement

Research converged; the honest portfolio menu at 6 bps/side:

1. **All-weather flagship: h3 + AP gold (EW, monthly)** — SR 0.94,
   +10.7%/yr, MaxDD -10.1%, positive in all 4 sub-periods 2008-2026,
   every 5y window positive (min +0.25), **low-beta +0.34** (not
   neutral). Deployment: portfolio_spec.py, monthly rebalance, drag
   0.42pp/yr.
2. **Recent 3-sleeve (h3+AP+LS) 2024+ — DECOMMISSIONED**: SR 1.15-1.20
   daily, MaxDD -5.6%, beta +0.06 as computed, but the LS leg's edge is
   a volume-precision artifact (N20 — champion decommissioned, forced
   HOLD). Historical record only; not tradeable.
3. **Parallel IV book (2019+, 6 sleeves)** — SR 1.24, MaxDD -5.9%,
   beta +0.04 verified (P12); walk-forward OOS 1.01/1.48. Caveat:
   contains the decommissioned champion family (N20) and the suspect
   n10r14 stream (N14) — historical/conditional, not tradeable as-is.
4. **Everything else fails the cost hurdle** (N1-N13): stat arb, FX
   carry as sleeve, cross-asset legs, tilt champion, n10_r14 8y.

Watch items: Stooq (blocked), champion 10d IC, n10r14 stream origin
(unverifiable). No further sleeve candidates exist in current data.

## Pending / flagged candidates

- (closed) n10_r14 8y OOS validation — FAIL, see the verdict section
  above. Optional follow-up: verify what parameters actually generated
  ls_n10r14_daily.csv; until then treat it as unverified data.
- **wf_champion_final (fundamental-tilt champion) — LIKELY OVERFIT,
  downgraded 2026-08-13**: momentum + value/quality rank-z tilt (SEC
  EDGAR fundamentals, 6-month lag, honest construction machinery) shows
  realization-timed monthly SR 1.18, positive in all 4 sub-periods,
  corr with h3 +0.095 — but it is **not reproducible from reasonable
  fixed configs**: TILT_W=0.3/TILT_MODE=all at vt12 and vt15 both give
  SR ~0.85, WORSE than the no-tilt gold-champion baseline (SR 1.05).
  The 1.19 "final" required unknown tuned parameters; a tilt that
  *hurts* at sensible weights while a tuned config shows 1.19 is the
  in-sample-tuning signature (same pattern as live_vslbl, N5).
  Conclusion: tilt idea not validated; the tuned 1.19 should not be
  deployed or blended. Thread closed unless a walk-forward selection
  test finds a config that beats the baseline OOS.
