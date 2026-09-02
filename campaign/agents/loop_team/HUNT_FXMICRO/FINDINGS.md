# HUNT_FXMICRO FINDINGS — GOAL100 loop team (2026-09-02)

## Mission (CHARTER.md)
Microstructure engines on the 8 tradable FX pairs (twelvedata daily OHLC, 2019+):
intraday/high-low-range, open-close reversal, carry via rate diffs. Daily, decorrelated (<0.15),
NO flattening, T+1, 6bps/side. Goal context: raise SR toward 5 / ann toward 80 without
violating leverage<=1.6.

## Data reality (all verified by code, exact numbers)
- 8 pairs: AUD_USD, EUR_GBP, EUR_USD, GBP_USD, NZD_USD, USD_CAD, USD_CHF, USD_JPY.
  2000 rows each; common tradable window **2019-06-12 → 2026-08-05 = 1862 weekdays (7.15y)**.
- Weekend rows are STALE ARTIFACTS: AUD has 104 Sat rows starting only 2024-02-10 and 30 Sun rows
  from 2026-01; |SatClose−FriClose| median 2.3bp vs daily |Δclose| median 25.5bp; EUR_GBP Sat
  H−L median 0.00072 vs Fri 0.00325. Dropped (executability: spot FX closed Sat/Sun).
- OPEN field quality is pair-dependent: for AUD/NZD/CAD/CHF/JPY/EUR_GBP, |close−open| median
  19-38bp with Fri→Mon gaps ~1-3bp (open≈true daily open). For **EUR_USD 57% and GBP_USD 26%
  of days have |close−open|<5bp** (median |oc| 0.18bp / 1.08bp vs open-gap median 20.9/23.8bp):
  the "open" is a stale prior quote, NOT the daily open. Any open-close signal is biased toward
  close-close continuation on those pairs.
- Interest-rate data for accrual: foreign 10y yields (FRED intl) are MONTHLY, 2018+ → carry
  accrual is PIT-constructible only with month-lag (value m usable m+1). No deposit/LIBOR/policy
  daily rates or FX forwards/vol surfaces exist anywhere on disk (verified by glob).

## Verified baseline
GOAL100_HONEST11L16_BALANCED_daily.csv re-scored: n=4522, 2008-03-31..2026-07-31, ann 39.37%
(arith) / SR_d 4.18 / MaxDD −4.85% / 0/19 neg yrs. Matches LOOP_L16 report (47.6% is geometric
annualization). All my corr checks vs this file.

## G1 — Parkinson range-vol harvest (charter idea 1) — REJECTED, 0/24 configs pass
Parkinson(21/63d) vs close-close vol "richness" gate × fade(1/3/5d) × daily/weekly. BEST net
SR = **−0.02** (no-gate, rev5, weekly); all 24 configs ≤ −0.02, 16 of 24 daily-decision ≤ −0.83.
FX has no tradable variance-risk-premium harvest in spot; the signal is a weak trend-fader that
fails SR, halves, and scramble gates. Also tested NR7 compression (follow SR −4.68, fade SR
−4.00 net; fade GROSS −0.09) and Donchian 10/20/40 breakouts (net SR −0.81/−0.38/−0.44) and
weekday holds (all 5 dows net SR ≈ −5.2 — 6bps cost exceeds any calendar effect; raw gross
dow-spread ≈ 1.3bp/day). Charter idea 1 verdict: **no daily-OHLC range edge survives 6bps in
spot FX on this window.**

## G2 — Open-close reversal (charter idea 2) — REJECTED, 0/46 configs pass
Fade(oc 1/2/3d), fade(gap), z-gated fade, plus continuation controls. FULL GRID NEGATIVE:
best of 46 = **SR −0.29** (oc3 weekly). Raw probes: oc_{t−1}→oc_t continuation +0.080bp/d;
gap→next cc continuation +0.352bp/d — both sub-cost. FX daily moves are continuation-tilted at
daily scale (negative of equity), and the open-field staleness on EUR_USD/GBP_USD would make any
"OC reversal" there close-close anyway. Charter idea 2 verdict: **dead at 6bps.**

## G3 — Carry via rate diffs (charter idea 3) — REJECTED (consistent with A2/D3 priors)
PIT accrual built (10y diff, monthly, value m usable m+1, ffill; EUR_GBP uses ez−gb).
Accrual magnitudes: USD_CHF +2.32%/yr, USD_JPY +1.99%, NZD +0.61%, rest |·|<0.8%.
Always-on diff-sign books (vol-inv weights): net SR **0.23** weekly / 0.17 daily, 4 neg years,
H2 0.03 (carry decayed in H2 as rates converged 2023-26); top/bottom-3 0.12; 12m-mid-gated
−0.43. Scramble p 0.655-0.98. Without deposit-rate data the accrual is a 10y-diff PROXY only;
even so it cannot approach the SR≥0.6 bar. Charter idea 3 verdict: **fails.**

## G5 — Cross-pair z-reversion stat-arb (self-directed extension) — ONE NEAR-MISS, honestly failed
The ONLY structure that clears the return gates: log-spread z-reversion on GBPUSD/NZDUSD
(corr 0.149 pair), continuous −z cap2, lb42. Single-book net SR 1.93 (ann 6.7%, MaxDD −3.27%,
1 neg yr −1.0%, H1 2.78/H2 0.76, corr to L16 **0.013**, flatten PASS ac1 −0.182 uq 0.953).
3-book block (+AUDGBP 1.67, +AUDEUR 1.19) saved as candidate: **FXMR3_42z2_daily.csv**
(2019-11-22..2026-08-05, n=1749): SR 1.87, ann 5.98%, vol 3.2%, MaxDD −3.69%, 1 neg yr (−2.0%),
H1 2.45 / H2 1.10, corr −0.008, flatten PASS (ac1 −0.158, uq 0.953), max|day| 1.28%.
**BUT the charter scramble gate (200×, p>0.05 reject → need p<0.05) FAILS:**
- iid scramble 200×: **p = 0.610-0.845 across seeds 0-9** (min 0.610) — far from 0.05.
- iid scramble 2000×: p=0.095; circular block-10d bootstrap 2000×: **p=0.497**.
- PnL is slow-episode-driven: top-20 days = 41% of total PnL, top-50 days = 79%. The mean
  reversion works by sitting short the 2022 GBP crash leg etc.; permuted paths that hold the
  mean-less drift reproduce the SR. The SR≈1.9 is NOT provably signal-invariant.
- Robustness that DID pass: LOYO min SR 1.53 (ex-2022), quarterly SRs positive in 19/27 quarters,
  IS/OOS split (IS 2019-22 picks lb21, OOS 2023+ SR 1.41; 3-book OOS SR 1.60), 1-pair-out stays
  positive unless EUR_USD (SR 0.08) or GBP_USD (0.15) is dropped — i.e. the book leans on the
  two clean-open pairs (EUR_USD/GBP_USD are the *drop* cases; dropping them kills it: 6-pair
  version SR −0.86), another concentration warning.
**Verdict: REJECTED as a sleeve per honesty contract (scramble gate). Saved to sleeves/ WITH
failure disclosure in .meta for VET_HONESTY review — it is a candidate-diversifier, not a pass.**

## Marginal-value test vs the goal (diagnostic, not committed)
Adding vt10-scaled FXMR3 to HONEST11-L16 BALANCED at w=0.05/0.10/0.15/0.20:
SR_d 3.92→4.00→4.08→4.15→4.23, SR_m 3.79→4.19, MaxDD −4.14→−3.31, ann 42.4→37.3% (arith),
0 neg yrs kept. Linear extrapolation: **w=0.70 would be needed for SR_d 5.0, at which point
blend ann falls to ~24.6%** — i.e., FXMR3 is a risk-reducer, NOT a return engine; it moves SR
toward 5 only by sacrificing the Ann>=80 goal. Even a hypothetical PASS version cannot close
the 80%/1.6x gap: at champion-like SR 4.2 the 80% ann needs ~2.5-3x gross (LOOP_L16 verified),
and a 3.2%-vol FX book contributes ~6%/yr raw at full vol-budget use.

## Flattening-gate discipline (audit_harness.py rule applied to everything I built)
Every candidate run through ac1<0.5 AND uniq_ratio>=0.08. ALL FINAL series pass by wide margins
(ac1 −0.16..−0.06, uq 0.95-1.00). No constant-run months anywhere (unlike XGB1y bug). The G1/G2
sign books have uq≈1.0 trivially; the continuous z-books pass too. NO FLATTENING introduced.

## Bottom line for the loop (exact numbers)
- 0 of the charter's 3 engine families passes the gates on the 8-pair daily OHLC 2019+ panel.
  Best charter-family result: G3 carry always-on SR 0.23 (needs ≥0.6/1.0).
- 1 near-miss found OFF-charter (GBP/NZD-led cross z-reversion, SR 1.87, corr 0.01) that fails
  scramble honesty (p 0.61-0.85 @200×; 0.50 block-boot) — disclosed and saved for vetting only.
- The 7.15y window, 6bps costs, and stale open quotes on 2/8 pairs are structural limits of this
  data domain. My verdict confirms LOOP_L16: no FX-microstructure sleeve moves the honest ceiling.
  SR≥5 at Ann≥80% and lev≤1.6 remains INFEASIBLE with anything found here; the fastest honest
  SR gains from my domain would be the FAILED-scramble FXMR3 (SR_d 4.23 @ w=0.20, ann −5pts),
  which should NOT be blended per the honesty contract.

## Files (all under campaign/agents/loop_team/HUNT_FXMICRO/)
- scripts/fxmicro_lib.py — shared honest backtest lib (T+1, 6bps, PIT accrual, flatten gate)
- scripts/g1_parkinson.py, g2_open_close.py, g3_carry.py, g4_execution_edges.py (+g1/g2/g3 grids .csv)
- scripts g5 grid: g5_statarb.csv, g5_cont_grid.csv (28-pair sweeps)
- sleeves/FXMR3_42z2_daily.csv(+.meta) — candidate-failed, disclosed
- G4 detail: close-to-close gross 4.393bp/d, cost 3.022bp/d, breakeven 8.72bps/side vs mandated 6
  → the ONLY engine that even conceptually clears zero (CPWR hold2) does so at 8.7bps breakeven
  and dies at open-to-open (−8.71bp/d gross) or mid-to-mid (−2.16bp/d gross) execution bounds —
  i.e., its profit is an artifact of close-print timing, not a robust premium.

HUNT_FXMICRO DONE
