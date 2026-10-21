# J1_goldterrain — GOLD TERRAIN PREMIUM (daily gold 1968+)

## VERDICT: **REJECT** — FAIL SR gate on BOTH required windows. NOT a new terrain; this is a CONFIRMATION/RESAMPLE of the existing dead verdict on gold momentum. The 1968+ extension does NOT change the verdict — it exposes that all gold-momentum edge is concentrated in 1971-1980 (post-Bretton-Woods one-off), while the 2008+ spot window mirrors the dead-idea futures window (SR 0.18-0.62 << 1.0). No J1_sleeve.csv written (gate not met).

## Gates (direction-specified)
| Gate | Requirement | Best achieved | Result |
|---|---|---|---|
| SR full 1968+ | >= 1.5 | **0.693** (B2_TERRAIN_VT15_cap2) | **FAIL** (-0.807) |
| SR 2008+ | >= 1.5 | **0.623** (B1d/B1_TERRAIN_LF; B2 0.610) | **FAIL** (-0.877) |
| corr vs champion | < 0.5 | 0.091-0.139 (all) | pass (moot) |
| T+1 causal / no lookahead | required | lag+1d never improves SR (below) | pass |
| Costs | 6bps full \|dW\| + 4.5%/yr margin on (gross-1) + 0.5%/yr borrow on shorts | applied in engine | applied |

## Data (offline, tools/quant/data/newdata2/gold_pm.csv)
LBMA PM fixing USD, 1968-04-01..2026-09-04, n=14,676. Clean: 0 dups, 0 NaN, 0 nonpositive, max calendar gap 7d. Era vols: 1968-71 8.8% (77 zero-return days, fixed-price era), 1971-80 23.9%, 1980-00 20.4%, 2000-08 16.0%, 2008-26 17.4%. Extreme days |ret| up to 13.3% (Jan-1980 bubble).

## Method (pre-registered grid, T+1 causal)
Signal at close t -> weight W_t held on day t+1: r_strat = W.shift(1)*ret - 6e-4*|dW|.shift(1) - 0.045*max(|W|-1,0)/252 - 0.005*max(-W,0)/252. Momentum: mom = P.shift(21)/P.shift(252)-1 (12-1) and P/P.shift(252)-1 (12m). Terrain: trend = mom12m>0; vol regime = 63d realized ann vol vs its trailing-756d median (HIGH >1.25x, LOW <0.75x). Carry state: gold carry = 0 proxy -> carry gate is a pass-through constant (null, not a filter) as directed. Math per campaign standard: ann=(1+r).prod()**(252/n)-1; SR=r.mean()/r.std()*sqrt(252); MaxDD = min of (1+r).cumprod() drawdown (negative).

## Results (full 1968+ / 2008-09+ = champion window)
| Signal | SR 68+ | SR 08+ | ann% 68+ | ann% 08+ | MaxDD% 68+ | neg yrs/57 | turn/yr | corr champ |
|---|---|---|---|---|---|---|---|---|
| A1 TSMOM12m L/F (w=mom) | 0.278 | 0.353 | 2.76 | 1.69 | -72.18 | 29 | 2.49 | 0.116 |
| A2 TSMOM12-1 L/F (w=mom) | 0.270 | 0.467 | 2.31 | 2.00 | -62.21 | 25 | 2.43 | 0.112 |
| A3 TSMOM12m L/S | 0.460 | 0.181 | 7.25 | 1.65 | -61.34 | 26 | 10.36 | 0.112 |
| A4 TSMOM12-1 L/S | 0.495 | 0.282 | 7.98 | 3.49 | -55.76 | 24 | 10.87 | 0.096 |
| B1 TERRAIN L/F benign-bull | 0.516 | 0.623 | 4.73 | 5.91 | -31.45 | 22 | 5.32 | 0.114 |
| B2 TERRAIN vol-target 15% cap2 | 0.693 | 0.610 | 8.20 | 7.35 | -46.55 | 24 | 7.59 | 0.139 |
| B3 TERRAIN L/S stand-down hivol | 0.384 | 0.327 | 4.33 | 3.36 | -54.05 | 26 | 9.89 | 0.091 |
| B0 ALWAYS-LONG (baseline) | 0.509 | 0.613 | 8.28 | 9.76 | -70.26 | 20 | 0.02 | 0.111 |
| A1d discrete 1/0 | 0.578 | 0.480 | 8.45 | 6.22 | — | — | — | — |
| A4d discrete ±1 | 0.463 | 0.181 | 7.37 | 1.65 | — | — | — | — |
Champion verified from campaign/results/GOAL100_CHAMPION_daily.csv: SR 5.182, ann 61.67%, MaxDD -7.31%, n=4696 (matches brief ~5.18/~61%).

## Leak checks (all clean)
Extra +1 day signal lag does NOT improve SR for any candidate (A1 0.278->0.278; A2 0.270->0.270; A3 0.460->0.441; A4 0.495->0.465; B1 0.516->0.510; B2 0.693->0.660; B3 0.384->0.359). High same-period pos*ret corr on long-biased books (0.43-0.75) is always-long beta, not timing: B3 (direction-switching) same-period corr 0.068, and all lag tests flat/decaying. Engine is T+1: W.shift(1) on returns, turnover charged on the rebalance day.

## Why REJECT is robust (era decomposition, honest)
| Era | B2 SR | B0 always-long SR | A4 L/S SR |
|---|---|---|---|
| 1971-1980 | 1.689 | 1.118 | 1.144 |
| 1981-1999 | 0.097 | -0.136 | 0.238 |
| 2000-2007 | 0.945 | 0.908 | 0.682 |
| 2008-2015 | 0.454 | 0.250 | 0.308 |
| 2016-2026 | 0.673 | 0.914 | 0.245 |
Every candidate's 1968+ SR is carried by 1971-80 (Nixon-shock/inflation one-off, a non-repeatable monetary regime); the 20-year 1981-99 gold bear zeroes momentum (best SR 0.24), and the 2008+ spot window (SR 0.18-0.62) reproduces exactly the dead-idea futures-window verdict. Halves: H1(68-97) vs H2(97-26) never both near gate (best B2 0.747/0.644). Terrain (b) beats raw TSMOM (0.693 vs 0.278-0.495) and dodges the 1980 drawdown (MaxDD -31% vs -72%) but lands at ~1/2.2x the required SR and only matches/slightly trails the always-long baseline on 2008+ ann (7.35 vs 9.76%). This matches dead-ideas patterns: always-long gold baseline SR ~0.56 (D2_MACROREGIME, DEAD_IDEAS line 115) reproduced here at 0.509/0.613; pre-2010-concentrated edge = FAIL per ledger row-156 doctrine (EMFX TSMOM_252 +1.308 pre-2010 -> -0.169 post-2010).

## New terrain or resample artifact?
**RESAMPLE ARTIFACT / confirmation of a dead verdict.** The long 1968+ history does not add terrain premium; it (i) reproduces the futures-window dead result on the 2008+ subsample (independently, on spot fixings rather than futures), and (ii) shows the apparent momentum edge is a single-decade (1971-80) monetary-regime artifact that no longer exists in any later regime. Terrain conditioning (vol regime + trend) is the best gold wrapper found in this campaign so far (SR 0.69 vs 0.51 baseline) but is far below the 1.5 gate and does not survive era-slicing.

## FAIL-CLOSED log
All pre-registered cells computed; none hidden. 0 data-blocked cells. Gate FAIL numbers: max full-window SR 0.693 < 1.5; max 2008+ SR 0.623 < 1.5. J1_sleeve.csv NOT written (conditional deliverable, gate unmet). Ledger row appended to campaign/results/DEAD_IDEAS.csv (J1_GOLDTERRAIN-R1). Repro: campaign/agents/J1_goldterrain_results/j1_engine.py (single file, offline).

DONE J1_gold
