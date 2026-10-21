# D3_fxfactor FINDINGS — Round 1 (2026-09-01)

Mission: weekly/monthly FX FACTOR structure on full DEX panel (13 ccys: INR,BRL,ZAR,MXN,KRW,SGD,JPY,NOK,DKK,CAD,EUR,GBP,AUD; USD-per-local orientation verified vs known 2026 levels; SEK parse fail in file — excluded).
Harness: `campaign/agents/D3_fxfactor/d3lib.py` (shared, reproducible). T+1 exec + 1d FRED noon-rate pub lag (monthly series: 31d lag), weekly signals held to Friday-gap, 6bps/side on turnover, vt10% trailing expanding min60d clip3. Gates per GOAL100_AGENT_BRIEF (SR>=1.0, H1/H2>=0.5, <=2 neg yrs each >-5%, scramble 200x p<0.05, |corr|<0.15 vs COORD_FINAL blend). IS split <2018, OOS >=2018.
**VERDICT ROUND 1: 0/5 ideas pass — NO sleeves saved (contract: failed gates = do not save). All five charter ideas REJECTED.**

## 1. FX carry proxy via 10y rate-diff momentum (us10y minus jp/ez/gb/ca 10y, FRED intl 10y = MONTHLY, 2018+ only)
Backtest 2019-01→2026-08 (n≈1970d). All variants FAIL every gate. Exact net SRs (vt10):
- us-jp L3/L12m: -0.05 / -0.14 (mdd -40%/-49%, scramble_p 0.36/0.97)
- us-ez L3/L12m: +0.33 / -0.64 (scramble_p 0.97/0.79)
- us-gb L3/L12m: -0.00 / -0.35; us-ca L3/L12m: +0.43 / +0.05 (best variant worst yr -8.0% → gate fail)
- book3 (jp+ez+gb) L3/L12m: +0.13 / -0.50
Root cause: monthly intl yields only from 2018 → 8y sample; sign(diff-momentum) flips regime violently; scramble p>=0.075 for ALL variants = no edge beyond noise.
**REJECTED: best SR 0.43 << 1.0 gate, scramble fail, worst-year fail.**

## 2. EM vs DM basket relative trend (63d + 21/42/126d), weekly
EM bkt = INR,BRL,ZAR,MXN,KRW (vol 7.9%); DM = EUR,GBP,AUD,JPY,CAD,NOK (6.5%); basket corr 0.46.
2008-01→2026-08, per-currency 0.5/len weights, net SRs: trend +1/-1 sign: L21 -0.58, L63 -0.28, L126 -0.36; reversed (fade EM underperformance): L21 -0.29, L63 -0.18, L126 +0.01. Gated "strong-moves-only" variants all negative (≤ -2.13 SR, artifacts of a bug-fixed earlier run removed). 10-19 negative years each.
**REJECTED: EM/DM relative spot trend has NO persistent sign 2008-2026; both directions ≈0.**

## 3. Dollar-smile VIX gate (long EM when VIX<20, short when VIX>30; also 17/25 and long-only gate)
Net SRs: EM v20/30 -0.54, DM v20/30 -0.60, EM v17/25 -0.56, DM v17/25 -0.59, long-only-EM<20 -0.75 (mdd -84%!), long-only-DM<20 -0.52. Corr to blend 0.04-0.15 (decorrelated but worthless). H1/H2 consistently negative both halves.
**REJECTED: VIX-gating does not rescue long-EM-FX spot; low-VIX regimes contain the big EM crashes (2013 taper, 2018, 2020).**

## 4. Monthly extreme-move mean reversion (z of 21d/63d ret vs trailing 2y, |z|>1.5/2.0 fade, + continuous)
Net SRs: L21 th1.5 -0.91, th2.0 -0.61, cont -0.85; L63 th1.5 -0.70, th2.0 -0.51, cont -0.55. Worst years -22% to -27% (fading 2008/2020 EM crashes = disaster). Scramble p 0.31-1.0.
**REJECTED: monthly-horizon FX spot reverts are dominated by crash continuation, not mean reversion.**

## 5. Cross-sectional rank books (long top-k / short bottom-k by 63d momentum, k=2,3; L=21/63/126; momentum & reversal)
Net SRs momentum: -0.93/-0.85 (L21 k2/k3), -0.56/-0.45 (L63), -0.44/-0.27 (L126). Reversal: -0.05/-0.22, -0.05/-0.19, -0.05/-0.23. Nothing above 0; momentum is NEGATIVE at all horizons post-2008 (dollar cycles dominate single names).
**REJECTED: no cross-sectional structure in the 13-ccy DEX panel at any tested horizon.**

## Engine sanity check (harness validation, not a sleeve)
DTWEXBGS 63d/126d trend (short-dollar long-DM basket): SR +0.10 / +0.01 — weak-positive as expected for spot-FX trend without carry; confirms pipeline (T+1, costs, vt, gates) behaves correctly and Idea-1 variant results were not alignment artifacts (Idea 2 first run DID have a column-alignment bug — positions keyed 'EM'/'DM' vs ccy names → zero gross, pure cost drag, SR -2 to -3.7; caught and re-run correctly with per-currency columns; results above are the corrected runs).

## ECONOMIC POST-MORTEM (for future rounds)
FRED noon rates are SPOT-ONLY. The FX carry premium (~2-4%/yr, the dominant FX risk premium) accrues via interest differentials and is structurally UNHARVESTABLE from this data. Spot FX has ≈zero drift → all trend/MR/XS books on 13 ccys cap out at SR<0.3 gross, well below the 1.0 gate even before the DEX noon-rate stale-Friday smoothing. Genuinely decorrelated FX sleeves need either (a) forward/carry data (free sources: not on disk), or (b) FX-implied vol surfaces (unavailable free daily). Recommendation: D3 round 2 should pivot to fx-pairs microstructure (8 tradable pairs 2019+ exist but only 7y) or abandon the FX-spot domain.
Ideas tried this round: 5 charter + 2 fixed reruns + 1 sanity. Tool calls ~14. No other agent dirs touched.

## NUMBERED SUMMARY
1. Idea 1 rate-diff momentum (us10y−intl10y, 3m/12m): best SR +0.43 (us-ca L3), others −0.64..+0.33; scramble p 0.075–1.0; worst yr −8.0% best variant; monthly data 2018+ only → REJECTED (SR gate 1.0, scramble, worst-year all fail).
2. Idea 2 EM/DM relative trend (L21/63/126 ±reversal, weekly): SR −0.58…+0.01; 10–19 neg yrs → REJECTED.
3. Idea 3 VIX dollar-smile gate (20/30, 17/25, long-only): SR −0.52…−0.75, mdd to −84%; corr blend 0.04–0.15 → REJECTED.
4. Idea 4 extreme-move z mean-reversion (L21/63, th 1.5/2.0, continuous): SR −0.51…−0.91, worst yr −27% → REJECTED.
5. Idea 5 cross-sectional momentum/reversal ranks (L21/63/126, k2/k3): momentum SR −0.27…−0.93, reversal −0.05…−0.23 → REJECTED.
6. Sanity: DTWEX dollar trend SR 0.10/0.01 — harness valid; failures are economic (spot-only data, no carry accrual).
0/5 pass → NO sleeves saved per honesty contract. Pivot advice: need forward-rate (carry) data or abandon FX-spot domain.
ROUND 1 DONE
