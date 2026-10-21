# HUNT_CLASSIC_SPREADS — research summary (8 classic strategy families)

Built under the honest-gate contract (T+1, 6.4bps full-cost, borrow, vol-target, no flatten,
proper position-rotation scramble, |corr|<0.15 to HONEST11FIX champion).

## Adoptable (PASS all gates, 16 sleeves)
| Family | #sleeves | SR | ann | MDD | neg-yr | corr(champ) |
|---|---|---|---|---|---|---|
| Crack Spread (裂解价差) | 8 | 0.79–1.02 | 6.9–9.1% | -9.9..-15.3% | 0–1 | +0.02..0.06 |
| Inter-Commodity (跨品种套利) | 5 | 0.79–1.94 | 5.7–14.6% | -7.2..-17.8% | 0–2 | +0.01..0.02 |
| Calendar Spread (日历价差, VIX term) | 5(win)+1 | 0.73–1.89 | 5.8–15.7% | -8.9..-13.3% | 0–1 | -0.02..-0.03 |

Flagship new engine: **inter_gasreg_nyh_gulf** (NYH–Gulf gasoline regional basis) SR 1.94,
ann 14.6%, 0/19 neg years, corr to champion +0.012 — an exceptionally clean, orthogonal sleeve
that was NOT in the champion pool.

## Built & rejected (honest FAIL)
| Family | result |
|---|---|
| Pairs / Stat-Arb | SR 0.31, ann 1.7%, 6 neg-yrs — FAIL (needs leverage/stronger signal) |
| Trend / CTA | SR -0.49…-1.02 on spot/ETF/FX proxies — FAIL (no roll-yield channel) |
| Vol-Arb | SR -0.16 via VIX-index proxy — FAIL (no VIX futures on box) |

## Not buildable (data scarcity, documented)
| Family | blocker |
|---|---|
| Merger Arb | M&A deal data; SEC EDGAR 403 this session |
| Convert-Arb | no free convertible-bond data |

## Free data fetched
CBOE VIX term-structure daily CSVs (VIX/VIX9D/VIX3M/VIX6M) power the calendar-spread engine.
Blocked: Stooq (JS-gate), Yahoo (403), CBOE futures (403), TwelveData free-tier (equities only),
SEC EDGAR (403).

Full detail: FINDINGS.md. Rebuild: scratch/verify_all_sleeves.py.

## Champion impact (adoption gate 8c) — HONEST verdict
I re-ran the canonical ITER15 max-Sharpe capital-real adoption test adding each new sleeve one at a
time. EVERY new sleeve PASSES standalone gates but LOWERS full-window annualized return at fixed
1.6x gross (gasreg dAnn -0.97pp, vixterm -1.28pp), even though they raise SR (3.27-3.30) and lower
MDD. Champion stays at the honest frontier: **ann 39.5% | SR 3.22 | MDD -6.5% | 0/19 neg-yrs**.
Energy-family weight does NOT drop: brwt block holds 51% of the book and stays 43-47% after each
candidate (the max-Sharpe fit keeps concentrating in the highest per-gross-IR energy sleeves).
So: these are strong decorrelated new engines for future work, but none is adoptable into the
fixed-leverage champion under the honest dAnn>0 rule. Reproduce: scratch/adoption_test.py.
