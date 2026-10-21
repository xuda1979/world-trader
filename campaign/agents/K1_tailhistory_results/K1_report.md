# K1 FAT-TAIL TREND — Direction 2 (leptokurtosis exploits)
Agent: K1_tai_trend | Date: 2026-09-16 | Script: campaign/scripts/K1_tail.py (reproducible, offline)

## VERDICT: REJECT — both directions fail. NO sleeve saved.
No candidate meets SR>=1.5 (best full-window net SR = 0.46 vs required 1.5; champion SR 5.18).
`K1_sleeve.csv` NOT written (gate unmet: SR>=1.5 AND corr<0.5 fails on SR for every candidate).
Fail-closed: every gate evaluated, numbers below; nothing hidden.

## (a) TREND x inverse-tail-kurtosis, CORN+QQQ (w=sign(12-1 mom)/(1+252d excess kurt), cross-sec normalized, gross=1, T+1, net 6bps |dW| + borrow)
Window 2011-06-10..2026-09-03 (CORN listing + 252d warmup), n=3831.
| variant | ann | SR | MaxDD | H1/H2 SR | negYr |
|---|---|---|---|---|---|
| A mom12-1 kurt252 (primary) | +2.70% | 0.26 | -33.2% | 0.16/0.34 | 7 |
| A vt10 (trailing lev<=2x, margin charged) | -0.81% | 0.11 | -55.3% | 0.02/0.19 | 7 |
| A plain trend (no kurt) | +5.37% | 0.43 | -31.6% | 0.21/0.63 | 4 |
| A kurt126 | +5.80% | 0.46 | -33.3% | 0.28/0.62 | 5 |
| A kurt378 | +3.26% | 0.29 | -24.8% | 0.36/0.25 | 8 |
| A mom9 / mom6 | +1.4%/+1.2% | 0.17/0.16 | -38.7%/-37.1% | neg H1 | 7/9 |
REJECT evidence:
- SR gate: best 0.46 << 1.5 (and < 0.6 library gate). Param plateau does not exist — neighbors 0.11..0.46 scattered, no peak.
- Scramble (200 perms, weights permuted vs returns, costs recomputed): real SR 0.255 < scrambled 95th pct 0.401 -> FAIL (no signal beyond noise).
- The prescribed inverse-tail-kurtosis scaling HURTS vs plain trend (0.26 vs 0.43): kurtosis is not informative for trend sizing here.
- corr vs champion 0.215 (<0.5 passes) — irrelevant given SR fail.

## (b) SHORT-variance harvest, VIX regime gate (T+1: gate/IV at t-1 close pays -r_t^2; net 6bps + 0.5%/yr borrow + 4.5%/yr margin if gross>1)
| variant | window | ann | SR | MaxDD | H1/H2 SR |
|---|---|---|---|---|---|
| B QQQ contango (VIX3M>VIX) | 1999-2026 | -0.71% | -2.08 | -18.0% | 0.12/-3.23 |
| B QQQ VIX<25 | 1999-2026 | -2.16% | -3.36 | -45.1% | -3.83/-3.16 |
| B SPY contango (same-index ctrl) | 2006-2026 | -0.00% | -0.01 | -4.9% | -0.27/0.20 |
| B SPY VIX<25 (ctrl) | 2006-2026 | -0.10% | -0.38 | -3.0% | -0.62/-0.12 |
| B QQQ cont vt2 | 1999-2026 | -5.33% | -4.16 | -77.7% | -5.52/-2.34 |
| B QQQ cont vt10 cap10 | 1999-2026 | -51.5% | -9.65 | -100.0% | -10.64/-8.75 |
REJECT evidence (cost stack is NOT the culprit — the edge is absent gross):
- GROSS (zero costs, w=1) QQQ contango: ann -4.73%, SR -3.64. Cross-index basis artifact: VIX (SPX implied) systematically understates QQQ variance -> shorting "QQQ vol" with VIX as strike bleeds.
- GROSS SPY contango control: ann -0.52%, SR -0.56. Even same-index, VIX^2/252 vs next-day realized variance nets ~zero-to-negative at daily granularity -> no harvestable VRP with this free-data proxy.
- Adding the mandated stack (borrow 0.5%/yr on short notional, 6bps on gate flips, margin 4.5%/yr on gross>1 when vol-targeting) turns ~0 into clearly negative: vt2 -5.3%/yr, vt10 -51.5%/yr (ruin; MaxDD -100%).
- Tail profile confirms penny-before-steamroller: net skew -5.7 (QQQ) / -3.9 (SPY), excess kurt 64/25, worst day -0.48%/-0.24% at w=1 (i.e. -48%/-24% per 100 notional units in a 1%-vol sleeve — any attempt to scale to useful vol breaches capital feasibility under the margin rule).

## Champion comparison (honest math)
- Champion @1x: n=4696, 2008-09..2026-08, ann +61.67%, SR 5.18, MaxDD -7.31%, halves 4.79/5.56, 0 neg years.
- Champion @1.6x (linear lev, margin 4.5% on 0.6 gross): ann +114.1%, SR 5.16, MaxDD -11.5%. (Brief's "SR~3.22 ann 39.5%" figure uses a different de-lever convention; under stated formulas it is SR 5.16 — either way ~10x any K1 candidate.)
- Best K1 candidate SR 0.46 (A_kurt126). Gap to champion: 4.72 SR. No synergy: AB_5050 SR 0.16, corr to champion 0.215.

## Cost-stack application (all variants)
6bps per FULL one-side |dW| turnover per asset; 4.5%/yr on (gross-1) for vol-targeted/levered variants; 0.5%/yr borrow on negative weights (conservatively applied to the variance-swap short as well). ann=(1+r).prod()**(252/n)-1; SR=mean/std*sqrt(252); MaxDD=(1+r).cumprod() drawdown (negative). T+1 throughout: weights/gates use data <= t-1 for day-t P&L. No lookahead paths.

## REJECT log (exact numbers)
- REJECT A_mom12-1_kurt252: SR 0.26 < 1.5; scramble FAIL (0.255 < 0.401); 7 neg years; H1 0.16 < 0.3.
- REJECT A_vt10: SR 0.11 < 1.5; MaxDD -55.3%; 7 neg years; H1 0.02.
- REJECT A_plain/A_kurt126/A_kurt378/A_mom9/A_mom6: SR 0.43/0.46/0.29/0.17/0.16 all < 1.5.
- REJECT B_qqq_cont: gross ann -4.73% (edge absent); net SR -2.08; H2 -3.23; 15 neg years.
- REJECT B_qqq_thr: net SR -3.36; 26 neg years; worst year 2000 -14.5%.
- REJECT B_spy_ctrl: gross ann -0.52% (no harvestable VRP); net SR -0.01/-0.38.
- REJECT B vol-targeted: vt2 SR -4.16; vt10 SR -9.65, MaxDD -100% (margin+borrow on negative-edge leverage).
- REJECT AB_5050: SR 0.16 < 1.5.

## Deliverable status
- K1_report.md: written (this file).
- K1_sleeve.csv: NOT written — condition (SR>=1.5 AND corr<0.5) unmet by every candidate (fail-closed).
DONE K1_tail
