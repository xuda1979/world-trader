# B2_highfreq FINDINGS — Round 1

All strategies: T+1 execution, 6bps/side costs (8/10/20bps sensitivity tested), free data only, no lookahead.
Vol-target ~10% ann using only trailing expanding-window data (min 60d), scale cap 3x.

## Idea 1 — Short-horizon cross-sectional reversal, equity panel (twelve_big, 298 names)
- Long losers/short winners ranked by 1-10d past return, equal-weight, T+1.
- Numbers: gross SR only ~0.76; after 6bps + high daily turnover (~0.55 $/nav/day) best net SR=0.51 (L=7,k=20), trailing-vt best SR 0.51.
- Verdict: FAIL. FULL SR=0.51 < 0.6 gate; per-unit-turnover alpha too thin at 6bps on a broad 298-name book. Not saved.

## Idea 2 — Volume-shock reversal, equity panel
- Reversal on extreme-volume days (volume z-score trigger) + past-return cross-section.
- Numbers: GrossSR~0.6 but net SR negative (~ -0.7) — volume-shocked names are high-turnover, cost grind dominates.
- Verdict: FAIL. Not saved.

## Idea 5 — Cross-asset short-horizon reversal (rates/commodity/FX/VIX), 13-asset universe
- 13-name liquid cross-asset universe (US10y, US2y, DXY, XAU, WTI, Brent, VIX, EUR/GBP/JPY/CHF/CAD/AUD). Rank by past L-day return, long 2 worst / short 2 best, T+1, name returns clipped +/-18% to tame VIX shock tails.
- Same-universe momentum is strongly negative (SR~-1.2) confirming reversal direction.
- Numbers: FULL SR=1.17, ann=13.0%, vol=11.1%, MaxDD=-32.1%, H1=1.42/H2=1.00, negY=2/19 (2025 -4.6%, 2026 -2.1%) worst -4.59%, signal-scramble p=0.0000, plateau L6-10 ridge (0.85-1.19), cost SR 1.13@8bps/1.08@10bps/1.03@12bps.
- Verdict: PASS — SAVED as sleeves/crossasset_rev_L8.csv (SR=1.17).

## Idea 3 — Pair/stat-arb reversion on cointegrated pairs
- Tested XAU/SLV, EUR/DXY, US10y-2y curve, and Brent/WTI log-spreads with z-score mean-reversion trigger.
- XAU_SLV SR=-0.2 to -0.6 (FAIL, momentum-like spread), EUR_DXY SR=-1.2 to -2.4 (FAIL), T10_T2 curve SR 0.48-0.77 (weak, H2 ok but worst yrs -6 to -14%, marginal).
- BRENT/WTI: outstanding — log-spread mean-reversion, ALL 19 years positive.
- Numbers: FULL SR=2.50, ann=22.0%, vol=8.8%, MaxDD=-6.56%, H1=2.83/H2=2.24, negY=0/19 worst +5.78%, signal-scramble p=0.0000, plateau lb10-30&bz1-2 SR 1.66-3.05, cost SR 2.47@8/2.43@10/2.26@20bps (economically robust); monthly P&L positive every year 2008-2026 (0.13-1.2 gross/yr).
- Verdict: PASS — SAVED as sleeves/brwt_spread_rev15.csv (SR=2.50). Corr to cross-rev sleeve = 0.068.

---

## NUMBERED ROUND-1 SUMMARY
1. Equity cross-sectional reversal (Idea 1): best SR 0.51 after costs/vt — FAIL (full-SR gate). Not saved.
2. Volume-shock equity reversal (Idea 2): net SR negative after costs — FAIL. Not saved.
3. Cross-asset reversal, 13 names (Idea 5): SR=1.17, H1/H2 1.42/1.00, 2 neg yr worst -4.6%, scramble p<0.001 — PASS. SAVED crossasset_rev_L8.csv.
4. Brent-WTI spread stat-arb (Idea 3): SR=2.50, 0 neg yr worst +5.8%, MaxDD -6.6%, scramble p<0.001 — PASS. SAVED brwt_spread_rev15.csv.
5. Pair-scrubbed losers: XAU/SLV, EUR/USD-vs-DXY, US10y-2y — all FAIL (negative or weak SR, bad worst-years). Logged, not saved.
DELIVERABLES: 2 validated sleeves, mean pairwise |corr|=0.068 (target<0.15), both SR>=0.6 both halves positive; repro scripts in campaign/scripts/.

ROUND 1 DONE
