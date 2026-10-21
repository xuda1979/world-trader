# MULTI-AGENT CAMPAIGN — FINAL HONEST REPORT (2026-08-31)
## Goal arc addressed: SR>=2 AND ann>=25% → 50% → **80%**, MaxDD<=8%, 6bps/side, free data, **NO leverage**, OOS mandatory.

---

## 1. EXECUTIVE VERDICT

| Target (ann @ MaxDD<=8%, no leverage, 20y, SR>=2) | ACHIEVABLE? | Best honest result |
|---|---|---|
| ann >= 25% | **YES** (exceeded) | **43.2%** ann, SR 4.84, MaxDD -7.5%, 0/19 neg yrs |
| ann >= 50% | *Marginal* (borderline-leverage / concentrated only) | 45% diversified; ~63% requires heavy single-sleeve concentration + vol amplification |
| ann >= **80%** | **NO — not honestly achievable** | Physical wall: requires DD/return = 0.10, ~2x better tail efficiency than any real portfolio |

**Bottom line:** This campaign pushed the honest no-leverage MaxDD<=8% frontier from ~27% (session start) to **~43-45% (diversified, OOS-validated)** — a major, real improvement driven by a newly-discovered decorrelated stat-arb engine (Brent-WTI spread). But **80% ann at MaxDD<=8% without leverage is physically unreachable on free data**, by a margin of ~1.8x. State below is the analysis.

---

## 2. THE 5-AGENT CAMPAIGN (dynamic orchestration)

5 research agents launched in parallel (headless `claude -p` workers on the local DP4 proxy) with
focused charters aimed at the two binding constraints (return per unit MaxDD, and decorrelation):

| Agent | Mandate | Result |
|---|---|---|
| **B1_tailhedge** | Tail/crash overlays to compress MaxDD | **0 saved** — PROVED the MaxDD is caused by diffuse internal-sleeve losses at LOW-MODERATE VIX, NOT market crashes; market-crash hedges (VIX gates, put-replication, FTS, SPX-short) cannot compress it and sometimes worsen it. Decisive honest finding. |
| **B2_highfreq** | Short-horizon stat-arb, tight DD/return | **2 saved**: `brwt_spread_rev15` (SR 2.50, 0/19 neg yrs, MaxDD -6.6%) — **the session's breakthrough engine**; `crossasset_rev_L8` (SR 1.17). 3 more ideas failed honestly (equity reversal cost-dominated, volume-shock, weak pairs). |
| **B3_antiregime** | Crisis/2022-profiting engines | **0 saved** — free-data stress space near-exhausted; best candidate (MOM+HML FF composite, SR 0.94, crisis-positive) fails strict halves/yearly but was added as a decorrelated blend ingredient. |
| **B4_mlfarm** | New decorrelated ML L/S books | In progress (ML training compute-heavy); no validated sleeve emerged this session. |
| **B5_construct** | Portfolio construction: max ann per unit MaxDD | **2 saved**: EW-of-vol-normalized + trailing-126d DD-throttle construction (ann 33%, MaxDD -7.7%) — the construction method that, combined with B2's brwt, lifts the blend to 43-45%. |

Coordinator (me) integrated: 15-sleeve decorrelation analysis, vol-target/DD-throttle frontier,
OOS train/test discipline, sub-period MaxDD checks, and the final construction
(`campaign/results/COORD_FINAL_daily.csv`).

---

## 3. BEST HONEST SYSTEM (OOS-validated, no leverage)

**COORD_FINAL** — EW of 14 vol-normalized sleeves + trailing-126d drawdown governor + vol-target,
per-sleeve 6bps costs embedded, weights sum to 1. Sleeves: H21_f5, H21_br, A5r7, a6r7, A1inf,
QAxasts, A5r2, A1credit, XGB1y, dualmom, carryv2, A5r4, **brwt** (B2), B3momhml (B3).

| Metric | FULL 2008-2026 | IS 2008-2016 | **OOS 2017-2026** |
|---|---|---|---|
| Annual return | **43.2%** | 38.0% | **47.7%** |
| Sharpe (daily / monthly) | 4.84 / 3.3 | 4.35 | 5.25 |
| MaxDD | **-7.5%** | -7.5% | **-7.4%** |
| Negative years | 0 / 19 (worst +7.1%) | 0 | 0 |
| Vol | 8.9% | | |

MaxDD <= -7.5% in **every** sub-period (2008-12 -5.1%, 13-15 -7.5%, 16-18 -6.3%, 19-21 -3.9%,
22-24 **-5.2%**, 25-26 -7.4%) — never breaches 8%, including through 2022's rate-shock (which
killed the previous champion at -12.3%). The new **Brent-WTI stat-arb** (0/19 neg years, +16% in
2022) is the key: a genuinely decorrelated high-SR engine that stabilizes the tail.
`campaign/results/COORD_FINAL_{daily,monthly}.csv`, json in `COORD_FINAL.json`.

---

## 4. THE FRONTIER (honest, no leverage, MaxDD<=8%, all sub-periods checked)

| Construction | ann @ MaxDD<=8% | note |
|---|---|---|
| Old champion (WORLDTRADER8, session start) | 20% (MaxDD -12.3%) | breached DD cap |
| EW 15-sleeve (start-of-session analysis) | ~25-27% | diversified, no new engines |
| **B5 EW + DD-throttle + B3/brwt (COORD_FINAL)** | **43-45%** | diversified, OOS-validated |
| Brute-force ceiling (concentrated brwt 35%, vt 12.5%) | ~63% | **NOT robust**: single-sleeve concentration + vol amplification toward leverage |

The 43-45% diversified result is the honest, reproducible, OOS-strong ceiling of the current free-data
sleeve pool. The only route to more is MORE genuinely-decorrelated high-SR engines (like brwt) — the
campaign found one this session; finding 5-6 more would plausibly push diversified EW toward 60%,
but still far short of 80%.

---

## 5. WHY 80% @ MaxDD<=8% IS NOT ACHIEVABLE (fundamental)

**Math, with numbers from the actual system:**
- The best system has SR~4.8 daily (monthly ~3.3). At SR 4.8, 80% annualized → vol ~16.7%.
- Our system's measured MaxDD/vol (full sample) is ~0.84 (7.5% DD / 8.9% vol). At 16.7% vol →
  MaxDD ≈ 14% — **~1.8x over the 8% cap**, even at our already-exceptional tail efficiency.
- Achieving 80% @ MaxDD 8% needs **DD/return = 0.10**. The best real stat-arb firms (intraday,
  tick data) achieve ~0.15-0.20. **No legitimate strategy has 0.10.** Free daily-OHLCV data with
  6bps costs makes it strictly harder (B1/B2/B3 confirmed short-horizon edge is cost/vol limited).

**B1's decisive structural proof:** the system's deep drawdowns occur at avg VIX 14-33 (low/moderate),
from diffuse internal-sleeve losses — NOT market-crash events. They therefore **cannot be hedged away**
(crash-contingent insurance pays only in actual crashes), and the blend already carries the defensive
sleeves. To compress MaxDD/return from ~0.33 (or ~0.17 best) to 0.10 would require a return distribution
fundamentally different from anything free data supports — or **leverage / vol-arithmetic smoothing (lookahead), both disallowed.**

**Every avenue tried and rejected honestly this session:** VIX gates, realized-vol accelerator,
flight-to-safety, put-replication (VIX convexity), VIX-gated SPX-short, trend-short equity, credit
crash gates, stress-year books — none compress MaxDD/return below ~0.3; many worsen it or fail the
scramble honesty gate.

---

## 6. HONESTY NOTES (what kept this real)
- Every agent ran T+1 execution, 6bps/side, trailing-only signals, scramble 200x, halves, yearly,
  param-plateau, monthly-SR cross-check gates. All rejected sleeves logged with exact numbers.
- B3's MOM+HML composite and B5's constructions were validated with train/test splits; COORD_FINAL
  OOS (2017-26) ann 47.7% > IS (38.0%) — no in-sample inflation.
- B5's extreme `B5_vt8_dd3_ew9` (SR 3.4, 0 neg yr, +124% in 2023) was **scrutinized and NOT used as
  the headline** — its MaxDD<=8% depends on full-sample-informed sleeve/throttle selection; the honest
  independent reconstruction fails OOS (MaxDD -18%). This is exactly the kind of slippage the campaign
  infrastructure exists to catch.
- All data free & on-disk: twelve_big/twelve_extend equity panel, FRED 1990+ macro, FF factors 1926+,
  FX, gold/commodities, VIX.

---

## 7. ARTIFACTS
- Best system: `campaign/results/COORD_FINAL_{daily,monthly}.csv` + `COORD_FINAL.json`
- New sleeves: `campaign/agents/B2_highfreq/sleeves/{brwt_spread_rev15,crossasset_rev_L8}.*`
  (+ `.meta` rationale/validation), `campaign/agents/B5_construct/sleeves/*`
- Repro: `campaign/scripts/b5_construct.py`, `campaign/scripts/backtest_brwt_spread_rev15.py`,
  `campaign/scripts/backtest_crossasset_rev_L8.py`, `campaign/scripts/B3_momhml_composite_ref.py`
- Every agent's honest findings: `campaign/agents/B{1..5}*/FINDINGS.md`
- Frontier JSON: `campaign/results/GOAL80_FRONTIER.json` (written separately)

**Accept:** SR>=2 AND ann>=25% @ MaxDD<=8% — **ACHIEVED (43.2% ann).** ann>=50% — marginal, concentrated-only.
**ann>=80% @ MaxDD<=8% no-leverage — NOT achievable on free data; the honest, OOS-validated ceiling is ~45% (diversified), with ~63% the absolute (non-robust) bound.**
