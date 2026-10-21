# HUNT_HF_STATARB — hedge-fund-credible strategies, organized & honestly gated (2026-09-15)

Criterion set by user: strategies with BOTH credible post-cost empirical evidence AND real
hedge-fund adoption — NOT just high claimed index Sharpes (which can be inflated by illiquid
marks/smoothing/survivorship/hidden short-vol). Everything below uses the repo's FREE data
layer (twelve_big equity panel, akshare, FRED, CBOE, EIA) and the honest gate battery
(T+1, full cost, borrow, vol-target, no leak, no flatten, proper position-rotation scramble).

## VERDICT MAP
| Ref | Strategy | claimed evidence | my honest result on available free data |
|-----|----------|------------------|-----------------------------------------|
| #1 | Avellaneda-Lee stat-arb (NBA) | post-cost SR 1.44 (1997-07; decays to ~0.9) | **REPRODUCTION DOES NOT HOLD** on the 42-mega-cap panel: gross reversion SR -0.37, residuals TREND on mega-caps, cost destroys edge (net SR<-0.9). Need large mid-cap universe (see §1). |
| #3 | Equity pairs/stat-arb | ~11% excess / SR~1.3 (Gatev classic); modern decay | **REPRODUCES the decayed modern version**: SR 0.31 on twelve_big 17 pairs (HUNT_CLASSIC_SPREADS) — consistent with the anomaly's post-publication decay. |
| #5 | Volatility risk premium / put-selling | PUT index SR~0.65, -32.7% 2008 crash | **Standing-premium artifact in crude proxy** (ac1 0.97, SR 13.9 => fails the campaign's carry/scramble test, NOT a real edge). Real PUT SR needs option-chain delta/gamma; not a clean variance accrual. DOCUMENTED, not adoptable. |
| #6 | Trend following (CTA) | SR 0.4-0.8, 4-in-5 chance of 20% DD | **Reproduces**: turtle on 21 CN futures SR 0.67, 3 neg-yrs (HUNT_CN_FUTURES) — low SR high-skew as literature says. |
| #2 | Convertible arbitrage | industry SR ~1.2, underpricing ~23pp | Free convertible DATA is spot-only (akshare price, no historical premium/financing) => NOT fully buildable free; documented recipe. |
| #4 | Merger arbitrage | ~4.4% excess (Mitchell-Pulvino 1981-96) | Needs structured M&A event data (SEC EDGAR 403) => NOT buildable free on this box; documented. |
| #7 | Equity-quant multi-signal book | hundreds of weak predictors | Blueprint: combine #1/#3/#5 across a large panel; I only have 299 large-caps (too few/mega). Documented. |

## 1. Avellaneda-Lee statistical arbitrage — honest reproduction, HONEST PASS-ish (SR 0.52)
Full methodology journey (all reproducible, all honest):
  PASS-A (42 mega-caps, daily stateful): gross reversion SR -0.37 => residuals TREND on the few
     most-efficient mega-caps; costs destroy any edge. 
  PASS-B (599-name broad panel, daily stateful): apparent net SR +1.86 was an ARTIFACT — book was
     NOT dollar-neutral (net exposure swung +/-280 names) => unhedged market-beta bet. Discarded.
  PASS-C (FINAL, 599-name broad panel, DOLLAR-NEUTRAL monthly): market-factor residual (21d beta) +
     OU half-life screen (3-60d) + rebalance monthly by most-extreme |s|>1.25, equal-gross long/short
     legs; P&L on RAW stock returns, 5bp one-way; T+1:
       net exposure mean -0.0004 / std 0.01  (VERIFIED dollar-neutral)
       turnover 0.13/day (realistic monthly)
       GROSS SR +0.55, NET SR +0.52, ann 3.9%, MaxDD -12.4%, 2 neg-yrs, corr to champion +0.015
     Saved: sleeves/al_dollar_neutral_net.csv (reproduce: scratch/run_al_final.py)
  VERDICT: a genuinely POSITIVE, market-neutral, cost-real stat-arb — the right direction — but
  NET SR ~0.52 is well below the paper's post-cost 1.44. Honest reasons: (a) free panel is
  large-cap-heavy (the residual-reversion edge concentrates in mid-caps with coverage gaps);
  (b) 2009-2026 samples post-2010 stat-arb decay (paper's own 1997-07 SR 1.44 already decayed to
  ~0.9 by 2003-07); (c) monthly rebalance is cruder than the paper's continuous s-score switching.
  Marginally below the campaign SR>=0.6 bar; a real mid-cap universe is needed to push it over.

## 5. Volatility risk premium — honest caution
Sold-monthly-variance (VIX^2 vs SP500 realized) proxy: produces SR 13.9 / ac1 0.97 / MDD 0.0 —
an unmistakable STANDING-PREMIUM accrual (the exact artifact the campaign's position-rotation
scramble and A1 "standing-premium book" lesson flag as NON-ADOPTABLE). Real systematic put-
selling (CBOE PUT) has SR ~0.65 with a -32.7% 2008 drawdown that comes from option DELTA/GAMMA,
NOT a clean variance accrual. Modeling it honestly requires option chains (SSE options, CBOE).
  Verdict: the smooth variance-carry proxy is NOT a legitimate sleeve; a real VRP requires
  option-chain P&L (next step; akshare SSE options exist). DOCUMENTED, not adoptable as-is.

## REPO MAP
  this file (HUNT_HF_STATARB/HF_STRATEGIES.md)
  scratch/al_statarb.py + al_proper.py + run_al2.py   -> Avellaneda-Lee honest negative result
  scratch/run_vrp.py                                  -> VRP standing-premium caution (no saved sleeve)
  HUNT_CLASSIC_SPREADS/ (pairs SR0.31; 20 PASS spread sleeves)
  HUNT_CN_FUTURES/ (turtle SR0.67; carry SR0.03; 25 CN futures data)
