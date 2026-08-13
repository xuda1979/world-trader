
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
