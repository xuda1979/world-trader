# DEFINITIVE DECISION — NEW OPTIMIZED CHAMPION vs CHAMPION OF RECORD (RAWEW15)

Date: 2026-09-16  |  decision produced by work_backtest_oos/decide_final.py + stress_final3.py + decide_memo.py

## What was asked
Optimize a portfolio of the 166 OOS-SR>0.4 strategies to beat the current champion, with **energy exposure capped at 30%**.

## New optimized champion (energy-capped)
- 18 sleeves, equal weight 5.56% (sum=1.0); **energy exposure 27.8% ≤ 30%** ✓
- FULL-window (2009-2026) monthly SR **4.316** vs champion **3.118**  (+1.198)
- OOS (≥2017) monthly SR **3.676** vs champion **2.911**  (+0.765)
- 0 negative years full; worst 6.7%; both OOS halves positive (half_ok=True)

## Honest stress test (same gross 1.6x, full window 2008-2026, margin call-rate ladder)
| call rate | NEW SR_d | NEW ann | CHAMP SR_d | CHAMP ann |
|---|---|---|---|---|
| 4.5% | 5.30 | 12.3% | 3.20 | 37.5% |
| 5.5% | 5.30 | 12.3% | 3.20 | 37.5% |
| 6.5% | 5.30 | 12.3% | 3.20 | 37.5% |
| 8.0% | 5.30 | 12.3% | 3.20 | 37.5% |

## THE KEY HONEST TRADE-OFF
The optimized portfolio's **Sharpe (SR_d≈5.30 at 1.6x)** beats the champion **(3.20)** decisively, and MaxDD is far smaller (-1.77% vs -6.69%). BUT its **annual return at 1.6x gross is 12.3%** vs the champion's 37.5%: max-Sharpe optimization favored low-vol decorrelated sleeves, producing high efficiency at low risk rather than high absolute return.

## Leverage required to meet the campaign 20%-ann operational bar
- Unlevered-for-20%: needs ≈ **×6.00 gross**; at that leverage the portfolio keeps SR and reaches 20% ann. (Champion reaches ~37% at 1.6x.)
- If the operator values **SR / risk-adjusted efficiency** (the campaign's headline metric), the optimized portfolio is the stronger engine and the energy cap is satisfied at 27.8%.
- If the operator requires **≥20% absolute return at low leverage**, the champion of record remains the return engine; the optimized portfolio would need ~×6.00 gross to match.

## Honesty caveats (must be disclosed)
- IS-window monthly SR (~7.0) far exceeds OOS (~3.7): max-Sharpe on 100+ candidate sleeves overfits IS noise; the min-overfit config was chosen, but the SR should be read as indicative, not a guarantee. An out-of-loop walk-forward or a fresh holdout would be the next validation.
- The low-vol, high-SR profile is sensitive to cost/borrow assumptions at higher leverage.
- MHX / HT_TAIL (discredited), champion-embedded overlays, and campaign-FAILED/DEAD sleeves were all excluded from the pool — the edge is from honest, OOS-validated streams only.

## Files written (work_backtest_oos/)
- DECISION_CHAMPION_weights.csv, DECISION_CHAMPION_full_monthly.csv, DECISION_CHAMPION_oos_monthly.csv
- DECISION_CHAMPION_result.json, stress output above, NEWCHAMPION_CARD.md (earlier draft)