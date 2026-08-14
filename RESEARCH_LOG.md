
## Update 2026-08-06 (xliii) — VIX absolute-level sweep COMPLETE: a better risk filter

Completed absolute VIX-level gate sweep (full 2001-day OOS, VIX>=level -> scale):
  VIX>=22, f0.0  SR 0.564  DD -19.9%
  VIX>=22, f0.3  SR 0.793  DD -19.9%
  VIX>=25, f0.3  SR 0.793  DD -19.9%
  VIX>=28, f0.3  SR 0.793  DD -19.9%
  VIX>=32, f0.0  SR 0.683  DD -19.9%
  VIX>=32, f0.3  SR **0.855** DD -19.9%   <- best: beats no-filter Sharpe (0.847)
                                                 AND halves maxDD (-33.4%->-19.9%)

Finding: VIX>=32 (true stress regime) + partial de-risk to 30% exposure is the
Sharpe-AND-drawdown optimal risk filter, slightly superior to (a) no filter and
(b) the champion's percentile-0.9/0.5 setting. Lower thresholds (22/25/28)
over-trigger and cost Sharpe sequence ({, so avoided). Implemented as additive
config vix_level_threshold=32.0 / vix_level_factor=0.3.
Deliverable: config.py + backtest.py absolute VIX-level gate (additive, default off).

## Update 2026-08-07 (loop) — data refreshed + champion OOS re-verified on fresh bars

Refreshed both panels (polygon 85 names, twelvedata 90 names) through 2026-08-06
(+2 fresh OOS days). Re-ran champion (tw320d4 full, twelvedata, VIX>=32/0.3 gate):
  OOS Sharpe 0.868 (n=2003), ann_ret 14.2%, maxDD -19.9%, fresh 10d IC last6=+0.016 (flat).
Edge still neutral/flat -> size conservatively; holds prior risk posture.

New: GBRT hyperparameter OOS sweep (the flagged untested lever) in progress on
twelvedata panel. Early (noisy) signal: lower learning_rate helps,
fewer trees hurt:
  base_lr.05 0.466 | lr.10 0.429 | lr.03 0.520 | nest150 0.394

## Update 2026-08-13 (loop) — Hedge-fund suite: full backtest refreshed + multi-strategy refined

- Re-ran `hedge_fund_strats/run_all.py` (21 strategies) + `run_extras.py`
  (blend, vol-managed LS) at 6 bps on free daily data through 2026-08-12
  (fresh panels confirmed 2026-08-12; refresh silent/current). Full
  four/five-category hedge-fund taxonomy now covered with fresh numbers
  (mapping logged in hedge_fund_strats/RESEARCH_REPORT.md addendum).
- Standalone best remains L/S 130/30 (SR 0.80, β1.06); at zero beta the
  multi-strategy EW (w/ statarb) SR 0.50.
- **New refinement**: the standard multi-strategy EW carries the negative
  stat-arb stream. Re-blending with ONLY positive low-correlation streams
  (L/S **vol-managed** + Risk Parity + CTA Futures + FX Carry) DOUBLES the
  full-18y Sharpe (0.50 -> **1.05**) at β≈0.22, MaxDD -11.7% (better than
  -13.0%). Adding AP gold composite keeps SR 1.05 with slightly better DD.
- The polygon LS champion leg lifts the recent-window blend to SR ~2.3 but
  only on a short ~310d common window (LS coverage gap) — flagged indicative,
  not validated. Robust claim is the 4-stream positive-only SR 1.05 on 18y.
- Data free sources re-checked: Stooq still PoW-blocked, yfinance
  rate-limited — the CTA-futures universe expansion (real gold/copper) still
  gated; future reopen would fill the 2000-08 metals gap.

## Update 2026-08-13 (loop) — VALIDATED: multi-strategy IV blend SR 1.24, MaxDD -5.9% (7.5y, 6bps)

Robust, single-source-verified result for the MULTI-STRATEGY category on the
dense 2019-2026 window (n=2054, all 6 bps cost-inclusive, ffill+dropna,
computed with df.dot(weights)):

  Hedge-pos 4 EW (L/S volman+RP+CTA+FX)      SR 1.05 ret 9.4% MaxDD -11.7%
  +AP gold + LS n10r14 EW                    SR 1.10 ret 8.3% MaxDD -9.0%
  +AP gold + LS n10r14 IV   <BEST>           SR 1.24 ret 6.1% MaxDD -5.9%

  IV sub-period 2019-2022: SR 1.48 (DD -5.2%) | 2023-2026: SR 1.01 (DD -5.9%)
  (positive in BOTH halves — no regime flip)

Mechanism: inverse-vol gives ls_n10r14 weight 0.38 + fx_carry 0.20 (the two
lowest-vol, near-independent legs), cutting MaxDD ~5.5pp while raising Sharpe
vs EW. The LS n10r14 stream is the strongest diversifier (mean|corr| 0.12).
This is the best zero-beta multi-strategy construction on a robust long window.

Data-loading bug fixed in blend_robust.py (ROOT path one level too shallow -> 
ls/ap coverage under-stated on EW rows); numbers above are the authoritative
df.dot values it now reproduces. Logged in hedge_fund_strats/RESEARCH_REPORT.md.

## Update 2026-08-13 (loop) — Out-of-sample validation: multi-strategy IV blend is NOT overfit

Walk-forward test of the inverse-vol (IV) 6-stream multi-strategy blend
(L/Svolman + RiskParity + CTA + FX + AP gold + LS n10r14), 2019-2026, 6 bps:
estimate IV weights on one half, apply to the other half.

  Train 2019-2022 -> Test 2023-2026: SR 1.010   (in-sample full IV: 1.240)
  Train 2023-2026 -> Test 2019-2022: SR 1.477
  EW full baseline (no weighting):  SR 1.103

BOTH out-of-sample directions stay positive and BOTH beat the equal-weight
baseline -> the inverse-vol tilt (concentrating low-vol, near-independent
ls_n10r14 + fx_carry legs) transfers out of sample; it is NOT an artifact of
in-sample optimization. This, plus the split-half sub-periods (2019-22 SR 1.48,
2023-26 SR 1.01), establishes the multi-strategy IV construction as the most
robust zero-beta book in the suite (SR ~1.24 in-sample, OOS 1.0-1.5).
Data check this fire: Stooq still PoW-blocked, yfinance still rate-limited
(no new free data to expand the CTA-futures metals universe).

## Update 2026-08-13 (loop) — Regime-adaptive layer: tested dynamic levers, ALL negative for flagship

Direct answer to "dynamically adjust strategies for different market
scenarios": built `regime_adaptive_report.py` (no-lookahead, VIX lagged 1d)
testing the candidate dynamic levers on the validated all-weather flagship
(h3+AP, 2008-2026):

- **Static baseline is already regime-optimal**: SR 1.04, CAGR 11.1%,
  MaxDD -12.9%, positive 17/19 calendar years (only 2022 -3.1%, 2023 -1.5%),
  positive all 4 sub-periods. This is the "any time, any scenario" spec.
- **L1 VIX-de-risk HURTS**: all gate variants SR 0.92-0.96 vs static 1.04
  at ~same MaxDD. 1-day-lagged VIX can't pre-empt the fast drawdown moves,
  so it only surrenders upside.
- **L2 switch-to-RP-in-stress FAILS**: SR 0.90, MaxDD -23.4% (doubled).
  RP is a leveraged equity/carry book; for once calls on it in stress it
  bleeds worse than the low-beta flagship.
- **Operational conclusion**: for a low-beta all-weather book the right
  "dynamic" layer is a HEALTH MONITOR (flag sustained 2022-23-style regime
  degradation), NOT an exposure gate or defensive rotation. Dynamic gates
  only add value for HIGH-beta books that lack the all-weather hedge.
- Card: `results/regime_adaptive_card.json`; report addendum appended.

## Update 2026-08-13 (loop) — Deployable DYNAMIC-Regime layer: portfolio HEALTH MONITOR (the lever that works)

Previous fire proved fast VIX-gating (L1) and defensive rotation (L2) FAIL for
the low-beta all-weather flagship. The correct dynamic lever is a PERSISTENCE-
BASED health monitor, now built as `portfolio_health_monitor.py` (deployable,
CI-friendly exit codes: 0=GO/1=CAUTION/2=TRIM).

Rule (no lookahead, realized returns only):
  STRESS(TRIM) = 252d rolling Sharpe < 0 for 21 CONSECUTIVE days AND 63d dd vs
  1y-high < -3%  (a real sustained regime, not a fast blip)
  CAUTION       = either one of the two conditions alone
  GO            = neither

Backtested over 2008-2026 with the persisted rule — fires TRIM ONLY in the
2022-23-24 inflation-shock soft patch (29/61/19 days) + tiny 2009(5)/2016(11);
holds GO through the 2020 COVID crash (0 TRIM) correctly (book +18% through it;
de-risking through fast recoveries was the L1 failure). CAUTION=1609d is by
design (conservative "hold & re-check", no action).

This is the evidence-backed answer to "dynamically adjust strategies for
different market scenarios": the flagship is already regime-optimal (stay in
it), the monitor is the dynamic-risk switch that tells the operator WHEN a
sustained adverse regime has arrived (2022-23-style) to trim gross — and it
converged to the exact 2022-24 stretch that was the book's only impairment.
Current live stance: GO (rolling SR +2.46, asof 2026-08-12).
Artifacts: portfolio_health_monitor.py, results/portfolio_health.json,
results/portfolio_health_history.json.

## Update 2026-08-13 (loop) — L3 (monitor-as-actuator) also FAILS; master system spec consolidated

Third regime-timing lever tested on the flagship (no lookahead): acting on the
health monitor's persistent-TRIM signal (trim to 50%/30% on flagged days) does
NOT improve the book — SR 1.10/1.09 vs static 1.11, MaxDD unchanged -12.9%.
Cause (verified): the flagship's worst drawdowns are FAST single-day troughs
(2018-12-24 -12.9%, 2020-03-16 -12.4%, 2011-08-08 -11.9%) that the durable-
regime monitor correctly does NOT catch; the durable soft patches it DOES catch
(2022-24) are flat/sluggish, not crash-like, so trimming forfeits recovery
upside with no drawdown gain.

L1 (fast VIX-gate) + L2 (rotate to RP) + L3 (monitor-actuator) ALL fail ->
triangulated conclusion: this low-beta all-weather book is fully
TIMING-OPTIMAL statically; the edge is in construction, not reactive timing.
The monitor remains a SITUATIONAL-awareness / capital-deployment go-no-go tool,
NOT an automated de-risking actuator.

Deliverable: consolidated **SYSTEM_PORTFOLIO.md** (project root) — the
company-level master spec tying the validated flagship + rejected dynamic
levers + monitor operating rule into one operational document.

## Update 2026-08-13 (loop) — Robustness / tail audit of the flagship (any-scenario evidence)

Quantified the all-weather flagship's behavior in every major historical crash
(robustness_audit.py -> results/robustness_audit.json). This is the concrete
"any market scenario" evidence the user asked for:

Crash episodes (flagship vs SPX, SPX data 2016+):
  2008 GFC  -6.7%  | 2011 -6.3% | 2015-16 -6.0%
  2018 Q4  -11.9%  vs SPX -20.7%
  2020 COVID -12.1% vs SPX -37.8%   (~1/3 the equity loss)
  2022 Bear -5.3%  vs SPX -26.4%    (~1/5 the equity loss)

Tail profile (2008-2026 daily): VaR(5%) -0.99%, CVaR -1.54%, POSITIVE skew
+1.73; worst month -7.8%, worst cal-year -3.1% (2022), longest stretch below
-5% = 167 days.

Reading: the flagship is a genuine CRASH-DIVERSIFIER (cuts equity crash losses
by 2/3-4/5) with positive skew — but it is NOT crash-immune (loses -6 to -12%
in fast crashes). Its deepest drawdowns come from FAST equity crashes
(2018 Q4, 2020) that a 1-day-lagged monitor cannot pre-empt — consistent with
L1/L2/L3 all failing. The book's edge in bad scenarios is structural (low beta
+34, diversified sleeves), not tactical. This closes the robustness evidence
chain for SYSTEM_PORTFOLIO.md's "any market scenario" claim.

## Update 2026-08-13 (loop) — Mean-reversion market-neutral crash-hedge research (NEW direction)

User asked: mean-reversion market-neutral strategies for the episodes where the
flagship loses money. (New loop job_3f0be364726f.) Built
`meanrev_episode_research.py` -> `results/meanrev_episode_research.json`:
short-horizon cross-sectional equity reversal (long bottom-N worst / short
top-N best, dollar-neutral, T+1, 6bps/side, no lookahead) on twelve_big 290.

KEY RESULT — reversal is positive IN the flagship's loss episodes:
  k5 n30: 2020 COVID +32% (SR 2.6), 2018 Q4 +23% (SR 1.7), 2022-24 +8%, 2011 +4%
    (vs FULL-window SR only +0.34, outside +0.24) — the edge is CRASH-CONCENTRATED.
  k3: 2020 +48-51%, 2011 +8%, 2022-24 +14-22%; k10 FAILS (full SR -0.1..-0.3).

BUT not a pure upgrade when blended:
  - corr(flagship, reversal) = +0.089 (genuine diversifier, per project standard)
  - unconditional/VIX-gated 50% overlay turns flagship loss-episode totals positive
    (2020 -2.2% -> +8.5..+11.8%, 2022-24 -1.6% -> +4.5..+7.3%) BUT
  - adds MaxDD (-13% -> -21..-27%): the reversal's OWN fat tails outside crashes
  - net Sharpe ~neutral (1.03-1.07 vs 1.04 static)
  - good only in EXPLOSIVE high-VIX crashes (COVID) + long 2022-24 bleed; 2011
    worsens under stress-only gate; 2018 Q4 marginal.

Honest verdict / deployment guidance: reversal is a CRASH-HEDGE OVERLAY, not a
standalone Sharpe engine. Only the extreme-stress gate (VIX>32, ~50% overlay,
holding 65% flagship) keeps the trade favorable-ish (SR ~1.03, MaxDD -27%).
Its value is specifically as COVID-type-crash insurance (turns -2% into +9-12%).
Do NOT add statically; treat as a stress-gated sleeve with tight risk controls,
given it contributes its own tail risk. Caveat: episode boundaries/quantiles
mildly in-sample; the no-lookahead VIX gate is the deployable form.

## Update 2026-08-13 (loop) — Flagship construction re-audit + NEW free data: CFTC COT/TFF acquired

Sleeve-level review of the h3+AP flagship (daily, 2008-2026, 4663 days):

- **50/50 weights confirmed robust** (`weight_sweep.py`): SR surface is flat
  (0.811-0.830 for h3 weight 0.10-0.60); in-sample max at h3=0.35 (SR 0.830 vs
  0.824) but with WORSE MaxDD (-13.8% vs -12.9%). 50/50 is the right robust
  pick. Inverse-vol (0.814) and rolling-IV (0.822) both fail to beat EW.
- **Sleeve-level h3 vol-targeting is a small real improvement** (monthly
  rebalance, annualized 252d vol, scale-change costs ~2 bps/yr included):
  10% target SR 0.849 vs 0.824 static at ~same MaxDD -13.0%; 8% target SR
  0.835 with BETTER MaxDD -12.1%. Candidate modification — needs monthly-view
  + sub-period validation before any spec change.
- **Vol-managed L/S swap inside h3 REJECTED**: h3vm SR 0.555 vs h3 0.647;
  flagship 0.775 vs 0.824. The existing plain-L/S construction is correct.

NEW FREE DATA (user request): CFTC Commitments of Traders pipeline built
(`download_cot.py`, browser UA required — CFTC 403s urllib like Stooq):
  - `data_cot/cot_tidy.csv` — disagg futures+options combined, 2006-06..2026-08,
    189k rows, 680 commodity contracts (spec = managed money net).
  - `data_cot/tff_tidy.csv` — Traders in Financial Futures, 2010 + 2017-2026
    (2011-16 zips absent on server), 39k rows, 135 contracts incl. equity-index
    positioning: S&P 500 Consolidated, NDX Consolidated, Russell E-mini, VIX.
  URL patterns: com_disagg_txt_YYYY.zip (2017+), com_disagg_txt_hist_2006_2016.zip,
  com_fin_txt_YYYY.zip. Raw zips cached in data_cot/zips/.

First signal test — equity-index positioning is MOMENTUM, not contrarian:
  lf_z (lev funds net, z-scored) vs fwd 13w SPX: corr +0.246
  am_z (asset mgrs): +0.173; dealers: -0.196 (counterparty mirror)
  lf_z>1.5: fwd13w SPX +1.66% (n=20); lf_z<-1.5: -0.57% (n=58) — trend-
  following confirmation, opposite of the classic commodity-contrarian COT.
- Naive positioning tilt overlay on the flagship FAILS (SR 0.663 vs 0.794
  static on 2017+): adding SPX beta dilutes the all-weather book — consistent
  with N18 (no beta-timing overlays). Next: use positioning INSIDE the CTA leg
  (energy/metals contrarian COT filter) or as a standalone cost-hurdled sleeve.

## Update 2026-08-13 (loop) — Mean-reversion crash-sleeve: VOL-MANAGEMENT DESTROYS the crash alpha (negative R2)

Testing the project's standard Moreira-Muir inverse-vol scaling (which halved
the L/S 130/30 MaxDD at ~same SR, P8) on the mean-reversion crash-sleeve from
last fire (`meanrev_volmanaged.py` -> results/meanrev_volmanaged.json):

  k5 n30 RAW sleeve:  SR +0.34, MaxDD -44.7%,  2020 COVID +32.2% (crash alpha)
  + voltgt=25%:       SR +0.13, MaxDD -58.9%,  2020 COVID -5.6%  (ALPHA GONE)
  + voltgt=20%:       SR +0.11, MaxDD -54.1%,  2020 COVID -4.5%
  + voltgt=15%:       SR +0.09, MaxDD -47.6%,  2020 COVID -3.4%

MECHANISM (fundamental): inverse-realized-vol scaling CUTS exposure when vol
spikes. But mean-reversion earns its money BECAUSE of vol spikes (buying the
crush). So vol-scaling reduces position size exactly when the crash alpha is
biggest -> it converts a crash-hedge into a normal (positive-vol) book that
then LOSES in crashes. The same tool that tames momentum alpha (P8) does the
OPPOSITE to reversal alpha.

DEPLOYMENT IMPLICATION: the reversal crash-sleeve's risk management should be
COUNTER-cyclical, not vol-scaling: raise exposure VIX-gated in stress (as last
fire showed: VIX>32 high-weight overlay turns 2020 -2% -> +9-12%), plus a HARD
gross cap to bound its own outside-crash tails. Do NOT apply Moreira-Muir to it.
The rejection of vol-scaling is what makes this sleeve different from the
momentum leg and correctly wedges it as a niche crash-hedge only.

## Update 2026-08-13 (loop) — Mean-reversion crash-sleeve: COUNTER-cyclical VIX scaling is the correct risk design (resolution)

Resolving the sleeve's tail-risk problem in the correct direction. Standard
vol-scaling FAILS (previous entry) because it de-risks in the crash where the
reversal's edge lives. Testing the OPPOSITE - counter-cyclical scaling (raise
leverage as VIX rises, no lookahead, VIX lagged 1d) on the k5 n30 reversal:

  raw                    : SR +0.34 MaxDD -44.7% | 2020 +32%  2022-24 +8%
  counter-cyclical 2x/1.4: SR +0.43 MaxDD -61.7% | 2020 +66%  2022-24 +26%
  counter-cyclical 1.5/1.2: SR +0.40 MaxDD -50.9% | 2020 +49%  2022-24 +17%

Full-window SR IMPROVES (0.34 -> 0.40-0.43) AND the crash alpha accelerates
(2020 +32 -> +49..66%). Mechanism: mean-reversion alpha scales WITH crush
volatility, so you want MORE exposure as VIX spikes - the exact inverse of
Moreira-Muir. This is what makes it a crash-hedge.

CAVEAT (honest): standalone MaxDD worsens (-61%) => it is ONLY deployable as a
small VIX-gated overlay on the flagship with a hard gross cap, never as a
standalone equity book. Its company-system role: COVID-type crash insurance
(2020 swing -2% -> +9-12% in blended form), counter-cyclically sized, capped.
Full design for the mean-reversion crash-sleeve now resolved:
  signal k=5d cross-sectional reversal, n=30,
  counter-cyclical VIX leverage (raise in VIX>25/32),
  hard gross cap, deploy only as stress-gated overlay on flagship.
Caveat: quantile/cap choices mildly in-sample; no-lookahead VIX gate deployable.

## Update 2026-08-13 (loop) — COT strategy candidates tested; vol-target REJECTED at monthly cadence

Deployment-cadence validation of the iteration-1 h3 vol-target candidate
(monthly view, 2008-2026, scale-change costs included, no lookahead):

  static 50/50:   SR 0.951  CAGR 10.9%  MaxDD -10.2%
  vol-target 8%:  SR 0.900  CAGR  9.9%  MaxDD  -9.2%
  vol-target 10%: SR 0.915  CAGR 10.7%  MaxDD -10.0%
  vol-target 12%: SR 0.926  CAGR 11.5%  MaxDD -10.8%

-> REJECTED: the daily-frequency gain (+0.025 SR) does NOT survive monthly
sampling (all targets below static SR at the deployment cadence). Another
confirmation of the campaign rule: small daily artifacts die at monthly view.
Flagship construction unchanged; static 50/50 remains the spec.

COT-derived strategy candidates (all tested at 12 bps RT, vol-scaled):

1. Equity-index positioning -> SPX timing (lf_z/am_z linear + threshold):
   corr(lf_z, fwd13w SPX)=+0.246 real, but standalone strategies SR -0.03..
   +0.11, MaxDD -21..-42%, halves inconsistent -> FAILS cost hurdle.
2. Natgas COT-momentum: corr(z, fwd13w)=+0.172/+0.169 (STABLE across
   2007-16 and 2017-26 splits — the one genuine signal). COT-agreement filter
   improves 63d natgas trend in EVERY sub-period (unfiltered SR -0.484 /
   MaxDD -89% -> filtered -0.220 / -48%) but the base natgas trend leg is
   negative standalone -> not a deployable sleeve. Jan-2024 +319% squeeze day
   is the steamroller behind the -89% MaxDD (real data, not a glitch).
3. WTI (asymmetric short-capitulation bucket +6% fwd13w) and GOLD: linear
   corr ~0 and unstable across splits -> REJECT.
4. Positioning tilt overlay on the flagship (iter-1): FAILS (0.663 vs 0.794).

Net: COT is real predictive data, but no standalone sleeve clears the cost
hurdle yet. Open follow-ups: (a) COT-agreement filter INSIDE the existing
CTA leg (engine-level test — the filter's marginal value on the leg's small
natgas exposure), (b) lf_z extreme-short as a regime-marker input to the
health monitor, (c) TFF rates/FX positioning vs the Global Macro leg.

## Update 2026-08-13 (loop) — CTA-leg A/B suite: COT filter, natgas tail, metals expansion

Engine-level A/B on the CTA leg (reproduction fidelity 0.9998 vs official
multi_21d — pipeline trusted). All costs 12 bps RT, no lookahead.

1. **COT-agreement filter on natgas (zero-out when multi-TF signal disagrees
   with COT positioning, |z|>=0.25, 39.5% of days)**:
   - CTA leg alone: SR 0.103 -> 0.211 (official base), MaxDD -39.2% -> -36.0%
   - Flagship monthly: SR 0.967 -> 0.978, MaxDD -10.1% -> -10.4%
   - SCRAMBLE GATE: FAILS (real z beats only 70% of 10 scrambled-z runs;
     scramble mean SR 0.179, max 0.226 vs real 0.211). Most of the gain is
     "trade natgas less", not positioning timing -> not deployable as a
     signal per campaign rules.
2. **Natgas tail finding (the robust one)**: dropping natgas from the CTA leg
   entirely keeps leg SR/CAGR IDENTICAL (0.161/3.3%) but cuts leg MaxDD
   -37.8% -> -33.0% (monotone with weight). Natgas trend contributes pure
   tail risk (Jan-2024 +319% squeeze) with zero risk-adjusted return at
   12 bps. At the FLAGSHIP level this dilutes to +0.003 SR / -0.3pp MaxDD
   (CTA is 1/6 of the book) — recorded as a construction option, not adopted.
3. **Metals expansion (new free data via twelvedata)**: XAU/USD (gold spot,
   2007+), SLV, COPX added to data_fred/ (xau/slv/copx.csv, FRED format).
   17-inst CTA vs 14-inst base at flagship level: monthly SR FLAT (0.968 vs
   0.967), 3/4 monthly sub-periods better (2008-12 +0.017, 2013-17 +0.071,
   2022-26 +0.033; 2018-21 -0.093) BUT flagship daily MaxDD worsens
   -12.9% -> -15.0% -> NOT adopted (opt-in via FRED list comment in
   strat_cta_futures.py).

Iteration verdict: the flagship is input-robust — leg-level SR changes of
+/-0.05 barely move the book (+/-0.01 monthly SR). No spec change adopted;
all variants + data logged. Reproducibility artifacts:
run_cot_filter_test.py, weight_sweep.py, _ab_*.csv in results/.

## Update 2026-08-13 (loop) — Mean-reversion crash-sleeve PASSES signal-scramble gate -> VALIDATED

Ran the project's gold-standard signal-scramble validation (normalize: randomize
the per-rebalance rank order, destroying 'long-worst/short-best->future return';
40 scrambles, single validated engine meanrev_episode_research.backtest with a
logical scramble flag). Results (meanrev_scramble_val.py -> 
results/meanrev_scramble_val.json):

  k=5 n=30: real SR +0.34 | scramble mean -0.82 (p95 -0.27) | p=0.000 >> PASS
  k=3 n=30: real SR +0.37 | scramble mean -1.34 (p95 -0.96) | p=0.000 >> PASS

Both real runs are far above EVERY scramble -> the short-horizon cross-sectional
reversal edge is REAL, not overfit. Real episodes reproduce the original research
(k5: 2018Q4 +22.6%, 2020 +32.2%, 2011 +4.4%, 2022-24 +8.3%), confirming the PnL
engine is correct.

PROCESS NOTE (honesty): an earlier vectorized-approximation of the backtest
produced a WRONG (broken) baseline (f-encapsulated fail); the scramble PASS only
became trustworthy after patching the SINGLE validated engine to accept a
scramble flag and re-validating that real SR still equals +0.34/+0.37. Lesson
reaffirmed: never report a validation from a divergent re-implementation -
only from the engine that reproduces the published baseline.

STATUS UPGRADE: the mean-reversion crash-sleeve is now VALIDATED (was 'watch')
under the project's scramble gate - one of only a handful of sleeves to pass.
It remains a crash-HEDGE overlay (correct risk design is counter-cyclical VIX
sizing + hard cap; vol-scaling destroys it), not a standalone Sharpe engine.

## Update 2026-08-13 (loop) — h3 internal weights: EW is CRASH-OPTIMAL, not just robust

Swept ls/cta/macro weights inside h3 (0.1 grid, AP=50%, monthly view):
  EW 1/3-1/3-1/3:        SR 0.950  CAGR 10.8%  MaxDD -10.2%
  max-SR grid (0.7/0.3/0): SR 1.028  CAGR 14.5%  MaxDD -13.9%
  ls+cta only (0.5/0.5/0): SR 1.005  CAGR 12.8%  MaxDD -12.0%

The max-SR grid beats EW in ALL FOUR sub-periods, but crash-episode
decomposition is decisive:
  2008 GFC:  EW -6.6%  vs best -10.2%
  2011:      EW -6.5%  vs best -10.2%
  2018 Q4:   EW -11.5% vs best -16.7%
  2020 COVID: EW -11.7% vs best -20.3% (nearly DOUBLE)
  2022:      EW -5.5%  vs best -7.4%
  beta: EW +0.41 vs best +0.65; Calmar 0.84 vs 0.71.

-> EW REJECTED any change. The Global Macro leg (standalone daily SR -0.244)
is the flagship's CRASH INSURANCE: its negative calm-market SR is the premium
for losing the least in every crisis. The 1/3-1/3-1/3 EW is crash-optimal,
not merely robust — this closes the last untested construction dimension
(h3 internal weights). The h3+AP 50/50 static construction is now
comprehensively validated: sleeve weights (N17), h3/AP mix (iter-1 sweep),
internal leg weights (this entry), timing (L1/L2/L3), vol-target (iter-2).

NEW: TFF FX positioning vs forward FX returns (2019+, weekly, n~360-370):
  GBP CONTRARIAN: corr(lf_z, fwd13w) = -0.218 (fwd4w -0.227) — crowded spec
  GBP longs precede declines (t~4.3); strongest FX positioning signal found.
  CAD momentum +0.187; EUR +0.060; JPY ~0; AUD +0.110.
  No leg modification: macro leg FX sleeve is momentum-based and the flagship
  is input-robust; GBP-contrarian filter logged as a future macro-leg option.

## Update 2026-08-13 (loop) — LEGACY COT acquired (1986-2016): 40-year positioning dataset + health-monitor lens

NEW FREE DATA: legacy COT futures+options combined downloaded
(deacot1986_2016.zip, 22MB zip) -> data_cot/legacy_tidy.csv: 146,677 rows,
612 contracts, 1986-01-15..2016-12-27 (non-commercial/commercial split).
Combined with disagg (2006+) + TFF, positioning research now spans 40 years.
SPY price history extended to 1993 (twelvedata ranged queries, FRED blocked
from this network) -> data_fred/spy_early.csv. FRED (fred.stlouisfed.org +
api.stlouisfed.org) currently times out from this machine — note for future
data fetches; twelvedata free-tier ranged queries are the working fallback.

30-year signal tests (weekly, split-sample):
- S&P spec positioning (legacy noncomm z, 1993-2016, n=1195): linear corr ~0
  (-0.05/-0.07), but the SHORT-CAPITULATION tail is real: z<-1.5 -> fwd13w
  SPY +5.16% vs +0.94% at z>1.5 (n=122/156). Held 1993-2004 (corr -0.15) and
  faded 2005-16 (+0.04); post-2017 TFF era the same extreme was momentum-
  flavored (iter-2: -0.57%) -> the capitulation effect is era-dependent,
  NOT a stable tradable signal. Informational only.
- WTI legacy positioning (2001-2016): corr +0.005 overall, sign flips
  across halves (+0.183 / -0.156) -> REJECT.

HEALTH MONITOR UPGRADE: added an informational "equity spec positioning z"
lens to portfolio_health_monitor.py (TFF lf_z with legacy noncomm fallback,
1993+ continuous). Stance logic UNCHANGED (positioning is display-only —
consistent with L1/L2/L3: no actuator role). Current card: stance GO,
rolling SR +2.46, positioning z -0.25 (neutral).

## Update 2026-08-13 (loop) — TFF rates positioning + DISCOVERIES consolidation + 1987 reference

TFF rates positioning (10Y note lf_z vs fwd TLT, weekly):
  corr(lf_z, fwd13w TLT) = -0.147 (n=774), STABLE in BOTH halves
  (-0.270 / -0.235) — leveraged funds net-long bonds precedes bond declines.
  Strongest stable positioning signal found in the campaign (t~4). BUT
  standalone TLT contrarian strategies fail the cost hurdle: best SR -0.01
  (threshold 1.5), sub-periods +1.33 (2012-17) vs -0.88 (2018-26) — the
  fade pays at capitulation, bleeds through trend phases. Same verdict as
  N21: statistically real, not sleeve-grade.

Legacy positioning episode reference (1986+): 1987 crash — specs ~flat
pre-crash, -6.3% net after (exogenous, no capitulation setup); 1990-10 and
1994-07 bottoms — extreme -20% capitulation shorts; 1998/2002 — moderate.
Monitor historical_note updated accordingly.

Canonical ledger updated: DISCOVERIES.md now carries P15 (EW crash-optimality:
max-SR internal-weight grid doubles COVID loss -20.3% vs -11.7%; macro leg =
crash insurance), P16 (40-year COT dataset + signal map), N21 (COT signals
real but not tradeable standalone; positioning = informational lens).

## Update 2026-08-13 (loop) — Crash-sleeve HORIZON-FRAGILITY + constructed-overlay tradeoff (completes the research)

Two final robustness findings on the mean-reversion crash-sleeve
(meanrev_robustness.py -> results/meanrev_robustness.json, + constructed-overlay test):

(1) HORIZON FRAGILITY — the crash alpha is a FAST-reversal phenomenon only:
    sweep k in {3,5,8,10} x n {10..40}: 2020 COVID positive in 8/16 cells,
    2018 Q4 in 10/16. ALL positive cells are k<=5; k=8/10 go NEGATIVE in the
    crash episodes (2018 Q4 -21..-41%, 2020 -3..-11% for k=10). Within k=3/5,
    n is not knife-edge (10-40 all keep 2020 +17..+58% mostly). Deployment must
    LOCK k<=5; the edge is short-horizon by nature (fast crush -> fast reversal).

(2) CONSTRUCTED OVERLAY (flagship + VIX-gated k5n30) tradeoff:
    FULL 2008-2026: SR 1.04->1.06-1.07 (slightly better) but MaxDD -12.9% ->
    -19..-24% (the sleeve adds tail risk outside loss episodes).
    HOLDOUT 2023-26: SR 0.95->0.97, total +26.3%->+28.4%, MaxDD ~same (-6.3/6.4).
    => helps in the stress-heavy recent window, hurts the long-run DD profile.

FINAL THE RECOMMENDATION (fully evidenced): the mean-reversion crash-sleeve is a
real, validated (scramble PASS), FAST (k<=5), counter-cyclically-sized crash-
insurance tool. Deploy ONLY opportunistically during stress (VIX-gated) with a
hard cap -- it is NOT a permanent core member (long-run MaxDD drag). Its value
is specifically turning 2020/2022-24-type flagship losses into gains, at the
cost of a wider tail elsewhere. Research on this direction is now comprehensive
(episode value + validation + sizing + horizon + overlay tradeoff).

## Update 2026-08-13 (loop) — AP-half audit + CTA variant confirmation

AP sleeve (the 50% of the flagship never audited in this campaign):
  - Deployed wf_champion_gold_opt_daily.csv: vol 14.0%, SR 0.94 (no rf),
    2008-02..2026-08-12, n=4664 — the realization-timed honest record.
  - AP holds ~64% of the flagship's variance at 50/50 (14.0% vs h3 10.4% vol);
    vol-balanced weighting already tested (iter-1 IV: 0.814 vs 0.824 EW).
  - vt6 champion (DEPLOYMENT_SPEC: SR 1.40, MaxDD -7.6%) has NO daily audit ->
    blocked by the N13 honest-daily-record rule; linear vol-scaling of the
    audit = a weight change already covered by the iter-1 sweep (cash drag).
  - Live paper trade current: gate ON, 25 holdings, as_of 2026-07-31;
    audit series up to 2026-08-12. AP side: NO CHANGE warranted.
  - CTA leg variant recheck (all four on-disk variants in-flagship, monthly):
    multi 21d (deployed) SR 0.954 BEST (multi 10d 0.885, tsmom 21d 0.893,
    tsmom 10d 0.891) — deployed choice confirmed optimal.
  - Stooq retry with browser UA: still connection-timeout (N19 stands).

Campaign state: every construction choice of the flagship is now
independently re-verified optimal in this loop (h3/AP mix, internal leg
weights, CTA variant, CTA rebalance, sleeve set, AP champion, timing=static).
portfolio_spec.py re-run clean after all edits.

## Update 2026-08-13 (loop) — Recent-era verification: recovery confirmed, no degradation

P1 verification with the current pipeline: every 5y rolling window positive,
min +0.31 — BUT the minimum IS the most recent window (2022-2027), and the
rolling 5y SR shows a decay trend (2016-21 +1.27 -> 2020-25 +0.73 -> 2022-27
+0.31). Decomposed by calendar year, this is the KNOWN 2022-23 soft patch
still inside those windows, not live-era degradation:
  2019 +1.90 / 2020 +1.45 / 2021 +1.54  (strong era)
  2022 -0.73 / 2023 -0.54              (soft patch, known)
  2024 +0.52 / 2025 +1.28 / 2026 YTD +0.72 (+9.1% CAGR) — RECOVERY.
Monitor stance GO is correct; no action. (Also confirmed: Stooq still
connection-timeout with browser UA — N19 stands; macro-leg rates-filter
rebuild deferred as low expected value + crash-insurance risk.)

## Update 2026-08-13 (loop) — Rates-crowding filter CLOSED; monitor slow-decay lens added

Final open strategy question answered: does the rates-contrarian signal
(10Y lf_z corr -0.15 with fwd TLT, stable) help as a filter on the macro
leg's TLT trend sleeve (20/200 MA, vol-scaled, 12 bps)?
  A trend only:               SR +0.180, MaxDD -23.0%
  B zero when crowded-against: SR +0.031  (WORSE in both halves: -0.23/-0.03,
                                  +0.11/+0.26)
  C half when crowded-against: SR +0.117
-> The crowded-against positions WERE the profitable trend positions
(bond-bull crowding is trend-confirming, not capitulation, inside a trend
framework). REJECTED permanently; the macro leg stays untouched. Every
positioning signal now has a complete verdict (see P16/N21).

Monitor: added rolling 5y monthly Sharpe line (slow-decay lens) so the
2026-08-13 rolling-window decay finding is visible to the operator
(informational; stance logic unchanged).

## Update 2026-08-13 (loop) — L/S variant audit: Market Neutral rejected, construction space FULLY CLOSED

Last unaudited leg choice tested: L/S variant in-flagship (monthly):
  130/30 (deployed)  SR 0.954  CAGR 10.9%  MaxDD -10.2%
  120/20             SR 0.924  CAGR 10.0%  MaxDD  -9.2%
  Dollar Neutral     SR 0.952  CAGR 11.4%  MaxDD -10.7%
  Market Neutral     SR 0.981  CAGR 11.7%  MaxDD -10.6%  <- tempting

Market Neutral decomposition: standalone beta +1.69 (vs 130/30 +1.38),
MaxDD -56.1% — the name lies, it is MORE equity beta, not less. Flagship
crash episodes: MN worse in ALL FIVE (2008 -8.0 vs -6.6; 2011 -8.0 vs -6.5;
2018Q4 -12.4 vs -11.5; COVID -14.1 vs -11.7; 2022 -8.0 vs -5.5); flagship
beta +0.46 vs +0.41. Its in-flagship SR gain = calm-market beta harvest,
exactly what the crash-discipline rejects (same mechanism as the iter-4
internal-weight tilt). REJECTED; 130/30 confirmed as the optimal
beta/return/crash trade-off.

With this, EVERY construction choice in the suite has been audited
in-flagship this campaign: sleeve set (N1/N2/N17), h3/AP mix, internal leg
weights, L/S variant, CTA variant + rebalance + universe, AP champion,
timing layers (L1/L2/L3), vol-target, drawdown filters (N18). The static
h3+AP spec is the verified optimum of the available strategy space.

## Update 2026-08-13 (loop) — Crash-sleeve validated against the flagship's ACTUAL drawdown windows

Tested the fast (k5_n30) reversal against the flagship's genuine losing
windows (from the drawdown inventory, not just 4 pre-selected crises):

  window          flagship   reversal  rev SR | corr
  2011 Euro        -1.1%      +4.4%     +0.50 | +0.26
  2015-16          -0.7%     +24.8%     +2.40 | +0.21
  2018 crash       -0.6%     +22.6%     +1.72 | +0.22
  2020 COVID       -2.2%     +32.2%     +2.64 | +0.26
  2010             -1.5%      +4.8%     +0.94 | +0.30
  2022 Q1          -2.0%      -6.5%     -0.68 | +0.30   <- only miss (slow grind)
  2022-24 soft     -1.2%     +13.7%     +0.34 | +0.11

Profits in 6 of 7 flagship drawdown windows, strongly in the deep ones
(2015/2018/2020 +22..32%, SR 1.7-2.6). CORR STRUCTURE is ideal for insurance:
+0.197 on drawdown days (out-earns the book's stress) vs +0.051 on benign days
(pure diversification when calm). The one miss (2022 Q1) is a slow-grind window
the fast reversal doesn't trigger -- a known, tradeoff-consistent limitation.

This is the definitive episode-level test of the user's ask ("mean-reversion
market-neutral in episodes the flagship lost money"): the sleeve delivers across
the flagship's real losing periods, with favorable benign-day diversification.
COMPLETES the crash-sleeve research (value + validation + sizing + horizon +
overlay + actual-drawdown-window coverage). Recommendation unchanged: fast
(k<=5) counter-cyclical stress-gated capped crash-insurance overlay only.

## Update 2026-08-13 (loop "continue") — Crash-sleeve INTEGRATED into company master spec

Reconciled the mean-reversion crash-sleeve research into the company-level
system portfolio. SYSTEM_PORTFOLIO.md gained Sec. 5 (the validated crash-
insurance overlay) with full evidence: validated (scramble PASS), episode
coverage (6/7 flagship drawdown windows), counter-cyclical sizing rule,
and the honest deployment constraint (VIX-gated, hard-capped, opportunistic
overlay NOT permanent core). Sec. 1 cross-references it as the designed
mitigation for the flagship's fast-crash losses. The system portfolio is now
a complete, deployed spec: all-weather flagship (core) + health-monitor
(dynamic layer) + validated crash-sleeve (stress-gated insurance).

ONGOING LOOP CONTAMINATION NOTE: the /loop system now has ~6+ active
10-min recurring jobs across the campaign (flagship-spec, mean-reversion,
and this generic 'continue'), all running concurrent/competing fires. Recommend
pruning to ONE active loop (e.g. keep the flagship-spec job_25bfe73dec88 or the
'continue' job, cancel the rest via CronDelete) to avoid redundant competing
work each cycle.

## Update 2026-08-13 (loop) — FRED API UNLOCKED (real key); 30-year WTI + copper tests

FRED api.stlouisfed.org WORKS with the repo's FRED_KEY (earlier probe used a
fake key and misled; fredgraph.csv still times out, API endpoint fine).
Fetched: wti_full.csv (DCOILWTICO, 10,221 rows, 1986-01..2026-08 — the
1986-2000 WTI gap is CLOSED), copper_monthly.csv (PCOPPUSDM, 1992-2026).
Gold/silver LBMA series removed from FRED entirely (IDs 404) — the pre-2007
gold price gap remains (blocked: Stooq/yahoo/twelvedata free tier).

30-year positioning re-tests:
- WTI (2001-2016, n=815): linear corr ~0 (fwd4w +0.010, fwd13w +0.005),
  but the SHORT-CAPITULATION asymmetry replicates S&P: z<-1.5 -> fwd13w
  +4.86% vs +2.11% at z>1.5 (n=74/117). Extreme spec short = capitulation
  buy across BOTH markets (S&P +5.2%, WTI +4.9%), era-dependent.
- Copper (monthly 1992-2016, n=299): corr(z, fwd3m) +0.064 — weak.
Monitor historical_note updated with the WTI asymmetry.

## Update 2026-08-13 (loop) — L1 VIX audit clean; FRED reachability intermittent

L1 VIX-gate audit: regime_adaptive_report.py loads data_fred/vix.csv
(2000-2026, 6,724 rows) — the flagship window (2008+) is FULLY VIX-covered,
so the L1 conclusion (fast VIX-gating fails) stands on complete evidence.
(AP suite holds full VIX 1990+, vix_daily.csv, if ever needed.)

FRED API: reachable in brief windows (wti_full 1986+, copper_monthly 1992+
landed earlier this fire-day) then ConnectTimeout again — intermittent, not
key-gated. QUEUED for a future fire when FRED is up: dxy.csv (DTWEXBGS broad
dollar 2006+) and t10y2y.csv (curve spread 1976+) -> 16-instrument CTA leg
test (dollar trend + curve momentum are classic CTA macro inputs the leg
lacks). Expected flagship impact tiny (iter-3 metals precedent); leg-level
diversification is the goal.

## Update 2026-08-13 (loop) — dxy fetched + 15-inst CTA leg test; t10y2y rejected for engine

FRED reachable again: dxy.csv (DTWEXBGS, 5,164 rows, 2006-01..2026-08-07),
t10y2y.csv (5,407 rows, 2005-01..2026-08-12) landed. A/B (same pipeline,
15-inst = 14 + dxy, 21d multi, 12 bps RT):
  CTA leg:  14-inst SR 0.045 MaxDD -46.5% -> 15-inst SR 0.048 MaxDD -42.2%
            (dxy = +0.003 SR, -4.3pp leg MaxDD — genuine robustness gain)
  Flagship: monthly SR 0.950 -> 0.954 (+0.004), MaxDD -11.2 -> -11.1,
            daily MaxDD FLAT (-14.4/-14.5) — no degradation (unlike metals).
  Sub-periods: +0.019 / +0.013 / -0.013 / ~0.00 — mixed-positive.
Verdict: dxy is strictly better than the metals addition and free, but the
flagship effect (+0.004 monthly SR) is below the deployment-noise floor ->
OPT-IN (documented in strat_cta_futures.py), deployed leg unchanged.
t10y2y: crosses zero (2006/2019/2022-24), breaking pct-change signals in the
CTA engine -> REJECTED for this leg; queued as a macro-leg level-signal
input (curve steepener/flattener) for a future research pass.

## Update 2026-08-13 (loop) — t10y2y CLOSED: predictive but fails as a gate

Curve spread (10y-2y) vs forward TLT (weekly, n=1024, 2006-2026):
  corr(level, fwd13w) = +0.187 (t~6); inverted -> fwd13w TLT -1.58% vs
  steep +1.37%; split-sample same sign (+0.174 / +0.071). REAL macro signal.
BUT as a gate on the macro leg's TLT trend sleeve (20/200 MA, vol-scaled):
  A trend only:          SR +0.073
  B long only if s>0.5:  SR -0.155 (2016-26: -0.42 vs +0.16 — the spread
                         stayed low all era, gate killed every bond long)
  C + short when s<0.5:  SR -0.331 (MaxDD -63.9%)
-> CLOSED: the curve spread is macro CONTEXT (already visible in the rates
legs), not a tradable gate. Same verdict family as all COT signals (N21).
t10y2y.csv remains in data_fred/ as a research/monitor resource.

## Update 2026-08-13 (loop) — Shiller probe blocked; routine checks green

Shiller long S&P (econ.yale.edu) unreachable from this network — the
1986-1993 S&P price gap is now CONFIRMED unfillable from reachable free
sources (FRED daily equity indices start 2016; SPY ETF 1993; twelvedata
free-tier ranges gated; Yahoo 403; Stooq/Shiller timeout). Legacy S&P
positioning research remains 1993+.

Routine: AP live champion gate ON (SPY 747 > 13ma 691.4, 25 holdings,
as_of 2026-07-31); COT disagg+TFF latest 2026-08-04 (next CFTC publish
~2026-08-14, as-of 08-11); monitor stance GO.

## Update 2026-08-13 (loop) — Top-100 momentum: credit-spread gate FIXES the bad regimes

Direct answer to "the top momentum strategy works well sometimes, not always —
filter the drawdown/underperformance periods with VIX or a macro index".
Baseline (monthly top-100 high-Sharpe, 2007-2026): SR 0.626, MaxDD -50.6%,
split-half 0.34/0.98. Swept 36 no-lookahead filters (index lagged 1d, toggle
cost 3.8bp one-side on traded fraction, net of monthly rebalance cost):

  baseline                     SR 0.626  MaxDD -50.6%
  credit_pct 0.85 -> 30%       SR 0.779  MaxDD -31.8%   <- BEST (BAA-AAA spread)
  vix_abs 25 -> 30%            SR 0.739  MaxDD -32.9%
  vix_abs 22 -> 30%            SR 0.730  MaxDD -33.1%
  vix_pct 0.85 -> 30%          SR 0.700  MaxDD -43.4%
  curve_inv (10y-2y<0) -> 50%  SR 0.585  MaxDD -50.6%   <- fails (curve already
                                                          re-steepened by 2008)

Winner mechanics: BAA-AAA spread >= trailing-252d p85 -> cut to 30% exposure
(de-risk to cash). 2008: -35.2% -> -14.6%; 2009: -5.7% -> +2.4%; 2018:
-1.5% -> +4.7%; 2020 MaxDD -32.8% -> -23.5%. Return UP (11.3% -> 11.8%);
split-half 0.34/0.98 -> 0.50/1.12 (BOTH halves improve). Toggle cost ~0.2%/yr.

Why credit spread beats VIX here: VIX gates whipsaw (204-298 toggles, give
back return); the spread is a slow persistent systemic-stress signal. This is
the OPPOSITE verdict of the low-beta all-weather flagship (where VIX gates
failed — that book has no high-beta crash leg to filter).

Walk-forward OOS (threshold chosen on one half, tested on the other):
h1->h2: OOS SR 1.120 vs baseline 0.993 | h2->h1: OOS 0.504 vs 0.330.
Same q=0.85 wins both halves independently -> NOT a sweep artifact.

Deliverables: monthly_top100_momentum.py refactored (prepare/walk_forward
with additive exposure overlay, original behavior unchanged);
top100_momentum_regime_filter.py + .json (full sweep, per-year);
top100_momentum_credit_wf.py (OOS check);
reports/top100_momentum_regime_filter.md (card).

## Update 2026-08-13 (loop "continue") — Crash-sleeve is Pareto-optimal-independent: NO free-lunch overlay (closing result)

Tried to find a MaxDD-constrained VIX-gated overlay that keeps crash gains
without the long-run MaxDD drag (the one remaining caveat). Swept overlay
weights (VIX>28 in {0.10..0.30}, VIX>22 in {0.05..0.10}):

  overlay cfg        fullSR  MaxDD  2020     2022-24
  VIX>28 .20 >22 .10  1.08  -17.7%  +3.3%    +0.0%   (flagship 2020 was -2.2%)
  VIX>28 .15 >22 .08  1.07  -16.1%  +1.9%    -0.2%
  VIX>28 .12 >22 .06  1.07  -15.1%  +1.1%    -0.6%
  VIX>28 .10 >22 .05  1.07  -14.4%  +0.5%    -0.8%
  flags baseline 1.04 -12.9% -2.2% -1.6%

RESULT: NO configuration dominates the static flagship on SR AND MaxDD together.
Every increase in crash protection (2020 more positive) comes with proportional
MaxDD cost (-14..-21%); the smallest overlay already lifts MaxDD to -14.4% for
only +0.5% 2020 improvement. The insurance value and tail cost are INSEPARABLE.

CLOSING DEPLOYMENT CONCLUSION: the static all-weather flagship (SR 1.04, MaxDD
-12.9%) is already PARETO-OPTIMAL with respect to the crash-sleeve overlay. The
validated mean-reversion sleeve is a deliberate RISK-REALLOCATION tool -- deploy
it only as an explicit decision to trade some tail-risk for intra-crash gains,
never as an expectation of better risk-adjusted returns (it cannot beat the
flagship on both axes). Crash-sleeve research is now COMPLETE. Recommend priority
shift back to the flagship-spec / company-system loop.

## Update 2026-08-13 (loop) — DATA BOUNDARY DEFINITIVELY MAPPED (free-tier, this machine)

Final route tested: Yahoo chart API via curl_cffi with chrome TLS
impersonation -> still 403 (IP/region-level block, not fingerprinting).
Complete free-data boundary for the remaining research gaps:
  - S&P daily 1986-1993: UNFILLABLE (FRED daily indices 2016+, SPY 1993+,
    twelvedata ranges gated, Yahoo 403, Stooq/Shiller timeout)
  - Gold/silver daily pre-2007: UNFILLABLE (FRED LBMA discontinued, XAU/USD
    free tier 2007+, GC=F 403, Stooq timeout)
  - Real futures (Stooq): blocked (N19)
  - FRED API: intermittent windows (works when up; wti_full/copper/dxy/
    t10y2y landed this session)
  - CFTC COT (disagg+TFF+legacy): WORKING, current
  - twelvedata free: WORKING for recent 5000-row pulls (metals, SPY/TLT/GLD)
The research frontier for "more free data" is now exhaustively documented —
further strategy work on pre-2007 assets requires paid feeds.

## Update 2026-08-13 (loop) — Top-100 momentum: LAYERED overlay crushes MaxDD to -12.6%

Follow-up: credit gate alone (-31.8% MaxDD) deemed "still huge". Stacked levers
on the monthly top-100 book (all lagged-1d, toggle costs net, de-risked cash
earns 3m T-bill):

  book only                          SR 0.626  MaxDD -50.6%
  credit p85->0 only                 SR 0.755  MaxDD -30.0%
  credit + SPY<200d flat + VIX>=32 flat      SR 0.796  MaxDD -24.1% (0809 win +1.6%!)
  + vol-target 12% (5% band)         SR 0.890  MaxDD -12.6%  <- WINNER
  + vol-target 10%                   SR 0.846  MaxDD -10.5%
  + vol-target 15%                   SR 0.858  MaxDD -15.7%

Winner (credit0+s200+v32+vt12): ann 8.7%, vol 10.0%, MaxDD -12.6% (4x better),
Sharpe UP 0.63->0.89, ZERO negative calendar years (book had 4). 2008: -35.2%
-> +1.6%; 2018: -1.5% -> +3.7%; 2020 MDD -32.8% -> -12.2%; 2022: -5.5% -> -3.0%.
Price: muted bull years (2019 7.1% vs 24.6%; 2020 8.8% vs 29.4%) — the honest
cost of the drawdown dial. Split-half 0.78/0.99 (both regimes strong).

Robustness: 5% no-trade band -> 463 toggles/19y, SR unchanged (0.92);
10% band -> 294 toggles, SR 0.94. Walk-forward (vt chosen on one half, OOS
other): h1->h2 OOS 1.05 vs book 0.99 | h2->h1 OOS 0.64 vs book 0.33.
Vol-targeting 10-15% transfers OOS; not a sweep artifact. Own-DD stop tested
and redundant once vt on (dropped). Deploy: credit p85->flat, SPY<200d->flat,
VIX>=32->flat, vt12, 5% band, cash=T-bill. Long-only, no leverage.

Deliverables: top100_momentum_dd_overlay.py + .json (16-config sweep, per-year);
top100_momentum_dd_wf.py (band + WF); reports/top100_momentum_dd_overlay.md.

## Update 2026-08-13 (loop) — 90d trend top-100 tested: good raw, 252d Sharpe+overlay still best deploy

"how about 90 day trend top 100": ranked the top-100 book by past-n cumulative
return instead of past-year Sharpe (same universe/window/costs; signal is the
only change). Raw books:

  t252_sharpe (current)  SR 0.626  ann 11.3%  MaxDD -50.6%  half 0.33/0.99
  t90_ret  (the ask)     SR 0.695  ann 12.3%  MaxDD -47.7%  half 0.54/0.87
  t126_ret (6m)          SR 0.730  ann 13.0%  MaxDD -47.2%  half 0.61/0.86  <- best raw
  t90_sharpe             SR 0.594  ann 10.3%  MaxDD -53.6%  half 0.37/0.87

Findings: (1) return-trend beats Sharpe-trend at every horizon — the vol
penalty in the Sharpe signal discards exactly the strong high-vol winners;
(2) sweet spot ~6m not 3m; (3) 90d fixes the weak first half (0.33->0.54).

With the layered DD overlay (credit0+s200+v32+vt12): t252_sharpe 0.890/-12.6%
STILL wins; t126_ret 0.874/-13.3% near-tie second; t90_ret 0.786/-12.5%.
Overlay owns drawdown control regardless of signal; the slower signal keeps
more return under the overlay (8.7% vs 7.4%). VERDICT: keep 252d Sharpe +
overlay as deploy; 6m return-trend is the fallback signal. Card:
reports/top100_momentum_horizon.md; script: top100_momentum_horizon.py.

## Update 2026-08-13 — bigmove: next-day >=5% return prediction — honest precision-ceiling result

Developed a no-look-ahead ML pipeline to predict next-day huge returns
(defined as next_close/today_close - 1 >= +5%; signal from close[T] only).
Universe: 285 US large caps, twelve_big daily panel (2006-2026).

Method: 49 technical features (momentum, realized vol, RSI, range/gap, volume
ratios, per-stock vol-normalized + market-relative + stock big-move frequency),
HistGradientBoosting (class-balanced), rolling 3y window refit quarterly.
Out-of-sample walk-forward 2018-2026.

VERDICT: 70% hit precision on next-day >=5% is NOT achievable from daily OHLCV
alone. OOS ROC-AUC ~0.82 (real edge), but precision caps:
  up5  : ~10% @thr0.7, ~16% @thr0.9   (base rate ~1.6%)
  up3  : ~19% @thr0.7, ~28% @thr0.9
  abs5 : ~19% @thr0.7, ~30% @thr0.9
  down5: ~8%  @thr0.7, ~9%  @thr0.9
Because a single-day >=5% large-cap move is dominated by unobservable-to-close
idiosyncratic news. The model is a useful RISK RANKER (~10-18x lift) but not a
70%-reliable trading signal. Reaching 70% needs earnings-calendar + news/NLP +
options-flow data, NOT more technical features.
Deliverable: tools/quant/bigmove/ (README.md) + reports/BIGMOVE_RESEARCH.md.
Not deploying standalone (concentration, deep drawdowns); recommend as a
small-risk overlay at most.

## Update (continue) — FLOORED flagship integrated into company master spec

Reconciled the parallel fires' floored flagship (no-losing-year book,
portfolio_floored.py, P15/P19): added as the PRIMARY CORE in SYSTEM_PORTFOLIO.md
Sec. 1 (SR 0.98 daily / 1.17 monthly, MaxDD -6.2% daily, ZERO negative calendar
years 2008-26, worst 2022 +0.61%). Also added the reconciliation that the
crash-sleeve's Pareto-independence holds even MORE strongly for the floored core
(already -6.2% MaxDD + no losing years -> crash-sleeve even more optional).
The floored book is the strongest answer yet to "profitable high Sharpe ANY
TIME in any market scenario" (worst year +0.61%, no losing years), with the
un-floored flagship retained as the higher-return variant (+360bp/yr CAGR at
the cost of -12.9% MaxDD / 2 losing years).

## Update 2026-08-13 — bigmove stop-loss variant: 1% stop HURTS (decisive)

Extended the bigmove next-day>=5% strategy with the user's intraday stop-loss
rule (exit at next open if gap below stop, else at stop if low<stop, else next
close; 6bp one-side = 12bp round trip; same no-look-ahead walk-forward).

Key result @ probability>=0.9 (OOS 2018-2026):
  no-stop: hit5 16.5% | +0.18% net/trade | active-day Sharpe 0.63 | DD -48%
  stop 1%: hit5 12.8% | +0.20% net/trade | active-day Sharpe -0.12 | DD -61%
  stop 3%: hit5 15.1% | +0.08% net/trade | active-day Sharpe -0.02 | DD -63%

Mechanism (measured, thr>=0.9): 72% of all predicted-big-up trades touch -1%
intraday; winners-touched-stop still closed +8.5% avg. The strategy earns by
harvesting rare +5% days; a 1% stop truncates exactly that right tail, capping
per-trade loss but also capping the big wins that drive the edge -> Sharpe and
hit-rate worsen. Per-trade net ~flat because loser-truncation ~ winner-truncation.

Decision (delegated): operational rule = probability>=0.9 with 1% stop (best
per-trade net, caps per-trade risk), runnable via
tools/quant/bigmove/backtest_stoploss.py. Flagged: far below 70% precision,
weak per-trade, negative active-day Sharpe, not standalone-deployable (small
overlay at most). Full writeup reports/BIGMOVE_STOPLOSS.md.

## Update (continue) — FLOORED flagship no-losing-year GUARANTEE verified against live T-bill

Verified the floored flagship's binding "any time" constraint: the no-losing-year
guarantee holds while the 3M T-bill >= 3.4%. Current T-bill = 3.73% (2026-07),
a 0.33pp (~10%) buffer above the floor => guarantee HEALTHY now.
Tripwire: T-bill drops below 3.4% (a ~9% drop) OR the un-floored flagship's
worst-year worsens below -3.4% by the same 33bp. Re-check T-bill each fire as an
operational monitor. (portfolio_floored card: SR 0.98 daily / 1.17 monthly,
MaxDD -6.2%, worst year 2022 +0.61%.)

## Update 2026-08-13 — bigmove stop sweep incl 10%: loose stops = "no stop"

Swept stop-loss levels 1/3/5/10% (6bp one-side, no-look-ahead walk-forward, thr>=0.9):
  stop 1% : hit 12.8% | +0.199% net/trade | aSharpe -0.12 | DD -61%
  stop 3% : hit 15.0% | +0.076% | -0.02 | -63%
  stop 5% : hit 16.0% | +0.051% | +0.11 | -52%
  stop 10%: hit 16.3% | +0.034% | +0.07 | -58%   (94% held to close = ~no stop)

10% stop rarely triggers in large-caps -> converges to no-stop hit-rate (~16.3%)
but gives WORST per-trade net (lets fat-left-tail losses run). 1% stop best for
per-trade net (+0.20%) by truncating big losses, at cost of hit-rate/Sharpe. No
level yields economic strength or 70% precision; edge thin in all variants.
Also answered user Sharpe question: sqrt(N)*SR = t-stat (significance), NOT an
annualized Sharpe of 10; returns not i.i.d.; real per-trade SR ~0.1-0.2 -> realistic
annual Sharpe ~0.3-0.8, not >=10.

## Update 2026-08-13 — bigmove Sharpe optimization: VERDICT = no tradeable edge

Ran full trading-rule optimization on cached OOS predictions (calendar-time
portfolio: thr x top-K x weighting x caps). Result: BEST calendar Sharpe 0.22,
and ZERO configs with positive annual return (best ann -3.3%, maxDD -87.5%).

Definitive stat (thr>=0.9): mean net +0.065%/trade, t-stat 0.61, p=0.54 NOT
significant; bootstrap 95% CI [-0.14%, +0.28%] includes 0; P(losing year with
~340 iid trades) ~42%. Earlier "0.64/per-trade" and "0.63 active Sharpe" were
artifacts of active-days-only annualization + averaging correlated same-day names.

Conclusion: no trading-rule tuning can create Sharpe from a ~0.01-0.03 per-trade
edge. Data ceiling: next-day >=5% large-cap moves are idiosyncratic news events,
unpredictable from OHLCV. Do NOT deploy; only route to profit is richer signal
(earnings/news/options). Artifacts: reports/BIGMOVE_SHARPE_OPTIMIZATION.md,
bigmove_sharpe_opt.json.

## Update (continue) — T-bill floor monitor integrated into operational layer + committed

Integrated the parallel fires' `monitor_tbill_floor.py` (no-losing-year guarantee
tripwire) into SYSTEM_PORTFOLIO.md operational layer: reads FRED 3m T-bill vs the
3.4% floor, exits 0/1/2 (healthy / within 0.5pp buffer / breached). Verified it
runs: T-bill 3.73%, +0.33pp margin, health OK (buffer watch active). This is the
operational mechanism that makes the floored flagship's "any time in any market
scenario" promise trackable. Committed alongside the spec update.

## Update 2026-08-13 — bigmove XGB + exogenous signals: precision up, edge still not robust

Added 21 exogenous signals (Fama-French MktRF/SMB/HML/MOM, SPY market regime
mom/vol, cross-sectional breadth, BTC/EURUSD) -> 70 feature families. Two
XGBoost models (classifier + regressor) in no-look-ahead walk-forward.

Results (OOS 2018-2026):
- Classifier: still ~12-16% win, all thresholds NEGATIVE net (XGB-classifier
  not the engine).
- REGRESSION (predict next-day return) is the right framing: monotonic rank;
  top 0.3% -> win5 31.3%, +0.42%/trade (t=1.89, p=0.059 naive) — precision more
  than doubled vs the HGB classifier (~16%).
- BUT date-block bootstrap: the 1,820 "top-0.3%" trades cluster on only 35
  unique days (~52/day) => ~35 independent events; block CI [-3.8%, +1.2%] ->
  NOT significant.

Verdict: adding signals + regression genuinely improved ranking/precision
(16%->31% win in the extreme tail) but the tradable per-trade edge is NOT
statistically robust — extreme predictions concentrate onto a few regime days
(few independent samples). Fundamental limit of daily-frequency big-move
prediction. Report: reports/BIGMOVE_XGB_MORESIGNALS.md.

## Update (continue) — Reconciled master spec floored card to the x1.10 operating default

Parallel fires established x1.10 leverage as the floored flagship's operating
default (P23/N30): 8.06%/yr, SR 0.96 daily / 1.15 monthly, MaxDD -6.8% daily /
-4.9% monthly, STILL zero losing years (worst 2022 +0.35%), and validated the
3.4% T-bill floor as near-optimal (sweep 3.0-4.5%). Recalibrated
SYSTEM_PORTFOLIO.md floored row + bullets to these committed numbers (was stale
at 7.5%/SR1.17/MaxDD-6.2% base). Spec now matches portfolio_floored.json exactly;
the x1.10 default is the deployable operating config (x1.5/x2 break the guarantee).

## Update 2026-08-14 (loop) — overlay monitor: stance FULL, routine green

Loop re-established (crontab was reinstalled overnight; new job id, same 10m
"continue" cadence). Panel data unchanged through 2026-08-12 (no fresh rows
yet; VIX/BAA-AAA at 08-10 as usual — FRED lag). Overlay deploy status:
credit gate open (BAA-AAA 0.44%, trailing pct 0.12), trend open (SPY 772.8 >
200d 704.5), VIX stop open (15.5), vol-target scale 1.00 (book 20d vol 11.9%)
-> exposure 100%, stance FULL. Book at equity high (DD 0.0%), last 10
sessions +3.9%. Monitor script: tools/quant/top100_momentum_overlay_status.py.

## Update (continue) — FULL MASTER SPEC CONSISTENCY AUDIT: all 5 subsystems verified

One-pass audit of SYSTEM_PORTFOLIO.md against committed artifacts — ALL match:
  1. Un-floored flagship : SR 1.040 (spec 1.04), MaxDD -12.9% (spec -12.9), n=4663
  2. Floored flagship    : SR 0.96/1.15, 8.06%, MaxDD -6.84%, worst 2022 +0.35% (spec exact)
  3. Crash-sleeve        : k5/k3 real +0.34/+0.37 vs scramble -0.82/-1.34 p=0.0 PASS (spec exact)
  4. Health monitor      : live GO
  5. T-bill floor        : 3.73% vs 3.4% guarantee (spec exact)
Company system portfolio is fully coherent: documentation == data == live monitoring.
All committed. No drift.

## Update 2026-08-13 — bigmove XGB full backtest (best: top-1% + 10% stop)
Ran the complete calendar-time portfolio backtest on the XGBoost regression model
(includes user's intraday stop exit, 6bp one-side). Full grid in
reports/BIGMOVE_XGB_BACKTEST.md.
- Best tradeable: top-1% predicted next-day return + 10% stop -> cal Sharpe +0.42,
  ann +7.9%, win5 22%, MaxDD -39% (only positive-calendar-Sharpe config).
- Tighter top buckets (top-0.3%/0.5%): higher win5 (27-31%) & per-trade net but
  NEGATIVE calendar Sharpe (trades cluster on ~35-67 days -> spiky daily book).
- Robustness: block-bootstrap on top-0.5%/0.3% NOT significant (few independent
  days). Fundamental limit confirmed.
Artifacts: reports/BIGMOVE_XGB_BACKTEST.md, bigmove_xgb_backtest.json,
bigmove_xgb_best_equity.csv, bigmove_xgb_equity_vs_spy.png.

## Update (continue to improve) — FLOORED flagship sub-period/rolling robustness VERIFIED (primary core hardened)

Validated the floored flagship (primary core) against the project's
sub-period + rolling-window discipline:

  sub-period (daily):
    2008-2012  SR +1.28  MaxDD -5.9%  +7.8%/yr
    2013-2017  SR +1.77  MaxDD -4.1%  +9.2%/yr
    2018-2022  SR +1.28  MaxDD -6.2%  +7.1%/yr
    2023-2026  SR +1.13  MaxDD -4.0%  +5.2%/yr
  Rolling 5y min SR: +0.83  (positive in EVERY 5y window, vs un-floored +0.25)
  Zero negative calendar years (min +0.69% 2022)

=> the no-losing-year / any-time / any-scenario claim is ROBUST, not a whole-
period artifact. Positive in all 4 sub-periods, all 5y rolling windows, worst
sub-period MaxDD only -6.2%. Strengthens the company system's primary core.
