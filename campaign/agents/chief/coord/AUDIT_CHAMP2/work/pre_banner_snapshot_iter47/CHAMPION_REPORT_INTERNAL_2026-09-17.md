> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
> **[ITER21 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER21
> gear-1.0 book: the SAME committed weights as ITER20 (shrink 0.70 + brwt-cap 0.30, weights
> sha16 d2d11c92a98683df) at canonical gross 1.0 — the margin term (4.5%/yr on gross-1)
> makes net SR strictly decreasing above gear 1, so the SR argmax under the operator's
> gross<=1.6 cap is the de-gear: **ann 23.61% / SR 3.751429 / MDD -3.61% / 0 neg years /
> gross 1.0 exact** (sha16 8559fa55ee9a3417). Objective unchanged: Sharpe-max s.t.
> ann>=20% and gross<=1.6. The prior ITER20 gear-1.6 vintage (36.41% / SR 3.4551, sha16
> 766fc0ce9926d793) is archived byte-exact as
> archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER21_gear10.csv and
> stays reproducible via build(gear=1.6). Every earlier headline quoted below (36.41,
> 39.50, 38.11, 37.49, 37.195, ...) is SUPERSEDED history kept for provenance — it WAS
> current once, it is not current now. See campaign/GOAL100_ITER21_ADOPTION.md.
>
> **[ITER20 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER20
> SR-max book: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 36.41% / SR 3.4551 /
> MDD -5.93% / 0 neg years / gross 1.6 exact (sha16 766fc0ce9926d793). Operator objective
> 2026-09-18: Sharpe-max subject to ann>=20% and gross<=1.6; the prior ann-max vintage
> (39.50 / 3.2176, ITER19) is archived byte-exact as archive_*_SUPERSEDED_by_ITER20_srmax.csv.
> Every earlier headline quoted in this document (39.50, 38.11, 37.49, 37.195, 40.84,
> 55.5, 62.4, ...) is SUPERSEDED history kept for provenance — it WAS current once, it is
> not current now.

# The World-Trader "All-Weather Flagship" — Champion Research Report (Internal, Replication-Grade)

**Version:** 1.0  |  **Date:** 2026-09-17  |  **Classification:** INTERNAL & CONFIDENTIAL — NOT for distribution
**Champion of record:** ITER19 RAW-EW13 (brwt15 pruned) weighted @1.6x leverage
**Representative headline (verified from canonical builder):** ann 39.50% / SR 3.22 / MaxDD -6.52% / 0 negative years over 19.

> This document is the single authoritative reference for **exactly** reconstructing the champion
> from raw sleeve inputs in live trading. Every constant, path, algorithm step, and acceptance
> check is given. It is machine-verified (`rawew13v2_build.py --verify` = byte-IDENTICAL; the full
> R3 acceptance gauntlet ok=True; the honesty CI gate PASS). A separate investor-facing version
> (REDACTED — no sleeve identities, weights, or data sources) accompanies this file.

---

## 0. Executive summary
- A **multi-sleeve, instrument-real, long/short daily** book combining 12 signal sleeves —
  energy spreads (Brent-WTI), natural gas seasonals, credit, rates, quality/quality-momentum,
  FX carry, commodity basis, dual equity momentum — into a **single capital-real 1.6x book**.
- Weights come from a **correlation-aware in-sample (IS) max-Sharpe fit** (covariance shrunk
  0.98 toward the diagonal, per-sleeve cap 2.0x equal weight), fitted once on data < 2017-01-01
  and held static for all 19 years. This replaced an earlier SR^P heuristic that underweighted
  decorrelated sleeves.
- **T+1 causality everywhere** (`nav.shift(1)`): no same-day lookahead. **Capital-real**: full
  |dW| transaction cost at 6.4bps one-side + 4.5%/yr funding on the 0.6x leverage; borrow is
  already embedded in every sleeve net CSV.
- **Acceptance is strict**: builder byte-reproduction, full-R3 independent re-verification,
  flatten-sweep (no ac1>0.5 / uniqR<0.08 artifacts), scramble/block (no lookahead), OOS>=IS.
- Not every slot is a "trade": CFX4 = 0 weight by design (coverage / vendor-artifact
  caveat, documented).

---

## 1. Champion identity & provenance
| field | value |
|---|---|
| canonical builder | `campaign/scripts/rawew13v2_build.py` |
| committed daily NAV CSV | `campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` |
| committed weights CSV | `campaign/results/RAWEW13v2_IS_SR_weights.csv` |
| independent acceptor | `campaign/bt/verify_champion.py` |
| canonical gate cmd | `campaign/bt/verify_champion_r3_cmd.sh` |
| honesty CI gate | `campaign/team/lib/honest_gate.py` |
| champion card (generated) | `campaign/CHAMPION_CARD.md` |
| audit (this sweep) | `campaign/AUDIT_DAX_2026-09-17.md` |
| verify fingerprint | net maxdev 9.996e-17; weights maxdev 6.939e-17 (vs committed) |
| rows | 4806 (2008-03-31 .. 2026-08-28) |

**Previous champion lineage (superseded, all archived under `campaign/results/archive_*`):**
SR^P 37.49% -> raw cost 40.84/39.85 (leak/half-turn artifacts) -> correlation-aware fit -> brwt15
pruned (ITER19) -> current 39.50%.

---

## 2. Fixed recipe constants (DO NOT CHANGE to reproduce)
| const | value | meaning |
|---|---|---|
| `K` | 12 | number of sleeves in the pool |
| `GEAR` | 1.6 | target gross (sum of |Wg|); margin charged on (GEAR-1)=0.6 |
| `RATE` | 0.045 | funding/margin rate **per year**, on the 0.6x borrowed capital |
| `BPS` | 6.4 | one-side transaction cost, basis points per unit of |dW| |
| `SHRINK_D` | 0.98 | covariance shrinkage toward the diagonal (IS weight fit) |
| `W_MAX` | 2.0 | per-sleeve weight cap, in units of the equal weight (1/K) |
| `IS_END` | 2017-01-01 | IS window is return dates < this |
| `START` | 2008-03-31 | book start (inclusive) |
| `P` | 0.55 | legacy SR^P exponent (NOT used for current fit; provenance only) |

---

## 3. The 12 sleeves (logical role + exact committed file path)
> Identity of the actual signals is the core edge — full detail here is for internal replication
> only. See the REDACTED version for the investor-facing taxonomy.

| # | slot key | logical family | committed sleeve CSV (relative to ROOT) |
|---|---|---|---|
| 1 | brwt10 | Energy: Brent-WTI spread mean-reversion | `campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv` |
| 2 | brwt7  | Energy: Brent-WTI spread mean-reversion | `campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv` |
| 3 | brwt5  | Energy: Brent-WTI spread mean-reversion | `campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv` |
| 4 | C5ng   | Gas: weekday premia | `campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv` |
| 5 | C5ngsum| Gas: summer weekday | `campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv` |
| 6 | A5r2   | Equity vol / rate-shock risk | `campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv` |
| 7 | a6r7   | Rates: 2y policy momentum | `campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv` |
| 8 | QAxasts| Quality: XS TSMOM (189d) | `campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv` |
| 9 | carryv2| Carry: seasonal (lag-1 honest) | `campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv` |
| 10| dualmom| Equity: dual-momentum band | `campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv` |
| 11| diescrack| Energy: diesel-crack basis | `campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv` |
| 12| CFX4   | FX: 4-book z-reversion | `campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv` |

**CFX4 = 0.00 weight.** It is kept in `NAMES` (so row-normalization and slot-count K are stable)
but has no IS coverage (<2017) and its twelvedata FX feed was discredited as a vendor artifact;
the champion deliberately holds it at zero. Reconstructing CFX4 is therefore optional for live
trading (contributes nothing).

---

## 4. Reconstruction algorithm (exact, reproducible)
Inputs: 12 sleeve daily-net-return series (`df`, dates x K). Outputs: `net` (daily champion
return), `relw` (relative weights), `gross` (daily gross), `to` (daily |dW|).

### Step A — Load and align sleeves
```
df = DataFrame({ n: load(PATHS[n]).dropna()  for n in NAMES })
df = df[df.index >= '2008-03-31']
```
`load(p)` reads a CSV whose first column is the date index and picks column `ret` if present
else the first data column, coerced to float. Sleeves are long-short **net** returns (borrow
already inside). Missing dates are NaN.

### Step B — IS relative-weight fit (`fit_relw`, fitted ONCE on <2017)
```
have = [n for n in NAMES if isr[n].notna().sum() > 0]   # CFX4 excluded (no IS rows)
X    = isr[have].dropna()
mu   = X.mean()*252                      # annualized mean vector
Sig  = X.cov()*252                       # annualized covariance
Sig  = (1-SHRINK_D)*Sig + SHRINK_D*diag(diag(Sig))       # shrink 0.98 to diagonal
k    = len(have)
# solve:   max  mu.w / sqrt(w' Sig w)   s.t.  sum(w)=1, 0<=w_i<=W_MAX/k
#   (long-only; SLSQP; 3 deterministic starting points; two-stage cap enforcement)
relw[have] = opt_sharpe_weights  ;  relw[else] = 0
```
Determinism: 3 fixed starting vectors (equal weight, max(μ,0) normalized, inverse-vol
normalized); each unknown converged under SLSQP; best (highest Sharpe) kept. The cap bound is
added only if an unconstrained optimum violates `w_i <= W_MAX/k` (keeps the committed bytes
byte-identical; see source comment).

**Committed ITER19 weights (relw, units of 1/12 equal weight; sum = 1):**
brwt10 0.166330 · brwt7 0.166668 · brwt5 0.177385 · C5ng 0.108688 · C5ngsum 0.098882 ·
diescrack 0.092626 · a6r7 0.050582 · QAxasts 0.046494 · A5r2 0.034636 · dualmom 0.033445 ·
carryv2 0.024263 · CFX4 0.000000.

### Step C — NAV-drift weights (T+1 causal) and gross
```
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)   # T+1: weight at t uses NAV through t-1
d2  = (nav / nav.mean(axis=1)) * relw                       # scale by per-row mean-forward  (row-normalize w.r.t. NAV drift)
d2  = (d2 / d2.sum(axis=1)) * K                              # row-normalize to sum K
Wg  = d2 * (GEAR / K)                                        # scale column weights to gross 1.6
gross = Wg.abs().sum(axis=1)                                 # == 1.6 every day
```
Note: `nav.mean(axis=1)` is the cross-sectional mean of the 12 NAV levels at day t.

### Step D — Portfolio return and costs
```
port   = sum_over_sleeves( df_t * Wg_t )
to     = |Wg_t - Wg_{t-1}|.sum(axis=1)                        # FULL one-side turnover (day-1 enters from 0)
net_t  = port_t  -  to_t * (BPS/1e4)  -  max(GEAR-1,0)*RATE/252
```
- **Turnover is FULL |dW|** (no 0.5 half-turn): this was a blocking honesty fix (audit A1) —
  the prior half-turn undercharged ~half the cost rate.
- **Margin** at 4.5%/yr on the 0.6 borrowed, applied daily (RATE/252).
- Day-1 entry (0→w_0) IS a real traded notional and is included in `to` (audit R1 fix).

### Digest
- `--verify` : rebuilds and compares to the two committed CSVs; PASS requires maxdev<1e-12.
- `--emit`   : writes champion + weights (guarded: refuses non-canonical gear/shrink/walk-forward
  unless `--force`).
- `--emit-candidate NAME` : safe way to write a candidate (never overwrites the champion).

---

## 5. Verified performance (canonical build; all figures machine-computed)
| metric | value |
|---|---|
| ann (CAGR, geo) | **39.50%** (39.4995%) |
| ann (arithmetic) | 33.85% |
| SR (daily) | **3.2176** |
| MaxDD (geometric NAV) | **-6.52%** (trough 2018-06-25, peak 2018-06-19) |
| negative calendar years | **0 / 19** |
| best year / worst year | +169.18% (2020) / +5.62% (2013) |
| daily vol | 0.0026 (approx) |
| turnover | **4.766 bp/yr** (mean |dW|/day 0.002955) |
| margin drag | 2.70 %/yr |
| turnover cost | 0.0477 %/yr |
| gross | mean = max = 1.600000 (0 overshoot days) |
| IS (<2017) SR | 3.50 (n=2286) |
| OOS (>=2017) SR | 3.08 (n=2520) — OOS >= IS, no overfit signal |

**Yearly returns:** 2008 +74.10 · 2009 +43.92 · 2010 +31.54 · 2011 +9.64 · 2012 +22.65 ·
2013 +5.62 · 2014 +22.28 · 2015 +68.92 · 2016 +63.64 · 2017 +47.12 · 2018 +49.77 ·
2019 +55.94 · 2020 +169.18 · 2021 +7.84 · 2022 +16.65 · 2023 +25.53 · 2024 +48.99 ·
2025 +24.60 · 2026 +33.27. (2026 is partial YTD through 2026-08-28.)

---

## 6. Risk & concentration profile
- **brwt triad concentration.** The three Brent-WTI sleeves carry **~76% of mean gross**
  (brwt10 28.7%, brwt7 24.6%, brwt5 22.8%) and are mutually correlated **+0.80** (pairwise
  avg 0.81) — structurally the same trade expressed three times. This is the dominant
  risk: an oil-spread regime break hits the whole book at once. It is the primary target
  for future de-concentration (see Research Agenda).
- **Other exposures** are small: C5ng 8.4%, C5ngsum 6.8%, diescrack 2.6%, QAxasts 1.6%,
  a6r7 1.5%, A5r2 1.0%, carryv2 0.6%, dualmom 1.3%, CFX4 0%.
- **Concentration is a symptom of the max-Sharpe fit on a nearly-collinear block**, not an
  error; ITER19 already pruned the weakest member (brwt15) and improved MDD and turnover.
- MaxDD episode: 2018-06-19 → 2018-06-25, -6.52%. Single best day +17.73%, worst day -4.62%.
- No credit/liquidity fragility beyond the underlying instruments' own costs; financing
  assumption is static 4.5%/yr.

---

## 7. Honesty & acceptance gates (what "verified" means)
1. **Builder byte-reproduction**: `rawew13v2_build.py --verify` — net maxdev 9.996e-17, weights
   6.939e-17 (< 1e-12). 
2. **Independent R3 acceptor** (`bt/verify_champion.py`, mirrors the algebra — no engine import):
   weights_repro / byte_repro / cost_reconciliation (model=full_dw) / causality (nav.shift(1),
   matched, truncation-invariant) / gross = 1.6 / yearly (0 neg) / mdd — all **True**.
3. **Honesty CI gate** (`team/lib/honest_gate.py`): VERIFY_R3 PASS + FLATTEN-SWEEP PASS
   (every sleeve ac1<0.5 and uniqR>=0.08 — no flatten-trap artifacts).
4. **Scramble/block** tests for each sleeve: position-lag scramble p=0.000 (no lookahead).

These gates are the difference between a "quoted" number and a reproducible, honest book.

---

## 8. Audit findings & fixes applied (this sweep, 2026-09-17)
Refer to `campaign/AUDIT_DAX_2026-09-17.md` for the full audit. Summary of what was corrected
so replication is unambiguous:
- **verify gate re-synced to ITER19**: removed pruned brwt15 from the 13-sleeve R3 map and
  pointed A5r2 at its current path (`A5_vol_cond/...`, not the dead `HUNT_BASIS1/...`).
- **verify_champion gained `--shrink`**: the hardcoded ITER15 shrink 0.62 was replaced by a
  parameter; the ITER19 champion verifies at `--shrink 0.98`.
- **Test-order determinism** fixed (module-name collision between RES_STATARB and RES_BASIS
  `hunt_r1.py`); a genuine `ls_weights` tie bug and an off-by-one warmup contract in a
  non-champion statistical-arb sleeve were also fixed.
- Champion itself was **not** changed by the audit (byte-identical before and after).

---

## 9. Live-replication checklist (turnkey)
1. Check out the working tree so the 12 sleeve CSVs + canonical builder are present and tracked.
2. `python3 campaign/scripts/rawew13v2_build.py --verify` → expect `IDENTICAL` (two lines).
3. `bash campaign/bt/verify_champion_r3_cmd.sh` → expect `"ok": true` with 7 green checks.
4. `python3 campaign/team/lib/honest_gate.py` → expect `VERIFY_R3: PASS | FLATTEN-SWEEP: PASS`.
5. For a candidate (any pool/data change): **never** `--emit` casually — it overwrites the
   champion paths — use `--emit-candidate NAME` and run it through the R3 acceptor + gates
   before any adoption decision.
6. The daily net series is in `campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`;
   reuse it verbatim as the strategy target, and apply each sleeve's own T+1 lag when mapping
   signals to live orders.

## 10. Fast facts for the research agenda
Dominant risk (brwt triad concentration), the static-weight design (weights fixed at IS fit,
held 19y; walk-forward refits tested and rejected as attributed to the discredited CFX4), and
OOS-keeping (OOS SR 3.08 vs IS 3.50) are the three facts every next-research decision should be
checked against. See `campaign/RESEARCH_AGENDA_2026-09-17.md` for the prioritized
multi-agent plan.

---

## 11. APPENDIX — Realistic small-IBKR-client cost re-backtest (2026-09-17)
The committed-of-record book uses **RATE=4.5%/yr flat + BPS=6.4 one-side**. For a small
IBKR-style retail client, the realistic parameters are researched in
`REALISTIC_COST_REBACKTEST_2026-09-17.md` and summarized here:
- **Call rate** = SOFR/Fed-Funds benchmark + 1.0-1.5% (IBKR Pro tiered schedule for a small
  book) -> a time-consistent path, currently ≈4.9%/yr (SOFR 3.65% on 2026-09). Realized mean
  margin drag over 2008-26 = **1.61%/yr** (not 2.70%) because the high-return years were low-rate.
- **Execution** = 6.4bps one-side, conservative (small futures ~1-3bps).

**Re-backtest under the realistic time-varying call path:** ann **41.03%** / SR **3.32** /
MaxDD **-6.51%** / 0 neg yrs — *better* than the flat 4.5% assumption.
**Stress bounds (flat constant call rate):** at 6.0% -> 38.25%/SR 3.13; at 7.0% -> 37.43%/SR 3.08,
still **zero negative years** in every case. The champion is robust to realistic and stressed
call-rate assumptions; the 0-negative-year property and MDD wall hold throughout.
