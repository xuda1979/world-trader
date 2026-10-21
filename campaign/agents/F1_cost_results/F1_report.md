# F1_cost_model — COST & CAPACITY AUDIT OF THE GOAL100 CHAMPION (2026-09-16)

## VERDICT (read first)

**TRUE FRONTIER @1.6x (champion of record, GEAR16, capital-real):**
| cost | ann (geo) | SR | MaxDD |
|---|---|---|---|
| **9 bps** | **39.47%** | **3.216** | **-6.52%** |
| **12 bps** | **39.44%** | **3.214** | **-6.52%** |

- **PASS (cost robustness):** the champion of record re-priced 6.4→12bps loses only **0.058pp ann / 0.004 SR** (turnover 0.745 turns/yr, cost drag 4.77bp/yr baseline). Cost risk on the live construction is immaterial.
- **REJECT (phantom frontier):** "SR ~5 / ann ~109%" @1.6x obtained by naively levering GOAL100_CHAMPION_daily.csv is **NOT capital-real** — the SAFE16 book carries **4.03x mean internal gross with ZERO financing charged** (champion_build.py "charged-free convention"). Honest 4.5% margin on 6.45x gross gives 68.15% ann @ **MaxDD -22.61%** and 6.45x gross > the 1.6x capital-real cap → inadmissible on both counts.
- **REJECT (brief anchor):** "6bps baseline = 0.90%ann" is wrong; measured drag = **1.077%/yr** (mean one-side turnover 7.123%/day × 6e-4 × 252). All scenario deltas below use the exact daily turnover series, not the 0.90% constant.
- **REJECT (reproducibility):** `champion_build.py --verify` **FAILS**: max|new-old| = **1.130e-03** (SAFE), 4.099e-03 (AGG), 2.069e-03 (BAL) vs committed CSVs — post-2026-09-07 costfix sleeve wave. Aggregate stats still match to 0.054pp (geo ann 61.673 vs 61.619, corr 0.999993, mean|d| 2.5e-06), so scenario conclusions are unaffected; the "byte-identical" claim in GOAL100_CHAMPION.md §8.1 is stale.

## 1. WHERE COST ENTERS; COMMISSION/SPREAD CONFLATION

**champion_build.py (16-sleeve SAFE/AGG/BAL, the @1x benchmark file):**
- Cost enters **once, at portfolio level** (`construct()`, lines 76–85): `tot = 0.5*Σ_i |dW_i|` (per-sleeve turnover-accounting weights, cross-sectionally summed) `+ 0.5*|d(throttle)|`, then `ret_net = b − tot*6e-4`. There is **no per-sleeve cost line** — a sleeve's own file is already net of 6bps per its validation convention, and the build then charges AGAIN on the blend's weight turnover. Double-charge is avoided only because sleeve files are sleeve-level nets; the portfolio charge covers reallocation between sleeves + throttle switches.
- **Commission + spread + (missing) impact are conflated** into one flat 6bps one-side. No separation, no size dependence, no borrow line (documented as "inside sleeve net files"), and **no margin line** despite 4.03x mean internal gross (p90 6.22x, max 7.75x; measured from the S/W matrices, warmup-ffilled).
- **Convention defect:** champion_build charges `0.5*Σ|dW|` (half-leg). The campaign standard since audit A1 / TRADE_RECORD_STANDARD is **FULL |dW|** (each leg's position change is a trade; the GEAR16 builder does this at 6.4bps). At 6bps FULL the SAFE16 book undercharges by exactly **1.73pp/yr ann** (61.673% → 59.945%, rows `SAFE16_at_1x_FULLdW`), i.e. the committed @1x headline embeds a ~1.7pp convention subsidy. Against the current 6.4bps FULL standard the gap is ~1.85pp.
- Turnover concentrates on **holiday Mondays** (top days: 2024-01-15 110%, 2012-05-28 107%, 2010-04-05 94% of NAV one-side — brwt-family reversion around calendar gaps): the flat-bps assumption is weakest exactly there (wider spreads, thin books).

**rawew13v2_build.py (champion of record GEAR16):** cost enters per-portfolio as `to = Σ_i |dWg_i|` FULL, charged `to*6.4e-4`, plus explicit margin `0.6*4.5%/252`; gross pinned to exactly 1.6x (0 overshoot days, verified); borrow inside sleeve files. This is the cleanest cost treatment in the repo and reproduces byte-identical (maxdev 9.996e-17).

**T+1/no-lookahead:** both builders causal — SAFE16 turnover uses `W.shift(1)`, throttle peak `shift(1)`; GEAR16 weights use `nav.shift(1)`. Re-pricing here only adds/subtracts cost series derived from these same causal objects; **no lookahead introduced**.

## 2. RE-PRICING AT 3/6/9/12 BPS (@1x, per brief)

Method: `ret_net(c) = ret_committed + tot*(6−c)/1e4` — exact daily proportional scaling of the turnover-cost series (per-day cost ∝ bps; strictly tighter than a constant-drag approximation), c ∈ {3,6,9,12}, baseline committed file. Full table incl. @1.6x variants in **F1_cost_scenarios.csv**.

| cost_bps | ann % | SR | MaxDD % | dAnn vs 6bps (pp) |
|---|---|---|---|---|
| 3 | 62.544 | 5.238 | -7.21 | +0.871 |
| 6 (baseline) | 61.673 | 5.182 | -7.31 | 0 |
| 9 | 60.807 | 5.125 | -7.41 | -0.866 |
| 12 | 59.945 | 5.068 | -7.52 | -1.728 |

Sensitivity ≈ **-0.29pp ann per +1bp** at 1x (log-drag 0.179pp/bp × 1.617 compounding level at 61.7% ann). Cross-checks: rebuilt series ann 61.619/SR 5.178 (-0.05pp vs committed) — conclusions robust to the verify DIFF. Under the FULL|dW| rules convention the same table shifts to 59.945/58.235/56.542 @ 6/9/12.

## 3. PROPOSED ADDITIVE + SQRT MARKET-IMPACT MODEL

Replace flat bps with, per one-side trade in leg i at day t (all in bps):

    c_i,t = κ_comm + s_i/2 + λ · σ_i,t · sqrt( f_i,t ),   f_i,t = q_i,t / ADV_i

- `q_i,t = |dW_i,t| · G · NAV` = traded $ (G = book gross); `σ_i,t` = trailing daily vol of leg i (decimal); `s_i` = full spread; `κ_comm` = commission; `λ ≈ 0.85` square-root-law coefficient (lit. range 0.4–1.5); participation `f` capped by policy at ρ* (e.g. 10% of ADV).
- Portfolio: `cost_t = Σ_i |dW_i,t| · G · c_i,t / 1e4` (turnover-weighted, additive across legs; sqrt term makes it concave in size, so per-slot aggregation is safe — no cross-leg impact interaction assumed).
- Calibration (illustrative, no network): κ_comm 0–0.15bp (IBKR tiered, $0.35 min); s/2: SPY/TLT ~0.5–1bp, sector/commodity ETF 1–3bp, USO/UNG 2–6bp, CL/NG futures 0.2–0.5bp all-in.
- Worked example (GEAR16, worst slot brwt10 at 6.02bp/day of NAV): NAV $50M → q = $30k/day; ADV(BNO/USO) ≈ $100–300M → f ≈ 1–3e-4; σ ≈ 1.8%/day; λ=0.85 → impact ≈ **2.7bp**; +spread 2bp +comm 0.15 → **≈4.8bp one-side**: the 6.4bps assumption is **defensible at $50M AUM**. At $500M: f ≈ 1–3e-3 → impact ≈ 8.4bp → c ≈ **10.5bp one-side**: the true cost roughly doubles. Break-even where 6.4→12bps honest: **≈ $300–350M AUM** for the brwt block at those ADV/vol assumptions. The flat-bps champion is cost-honest at family-office size, not at institutional size.
- Model upgrades over flat 6bps: (a) separates the conflated commission/spread/impact; (b) charges the holiday-Monday turnover spikes at stressed spreads; (c) gives AUM a first-class input so "capacity" and "cost" are one curve (below).

## 4. ADV → COST/CAPACITY MAPPING; PER-GROSS IR ≈ 2.8 GATE

- **Capacity law:** per-leg participation `f_i,t = G·|dW_i,t|·NAV / ADV_i ≤ ρ*` ⇒ `NAV_max,i = ρ*·ADV_i/(G·|dW_i|)`. GEAR16 binding leg brwt10 (|dW|=6.02bp/day, G=1.6 ⇒ G·|dW|=9.63e-4): at ρ*=10%, NAV_max = 0.10/9.63e-4 = **104×ADV** → e.g. ADV $100M ⇒ ~$10.4B book: raw participation is never the binding constraint on liquid ETF/futures legs at any realistic AUM. **Cost creep (§3), not participation, is the binding capacity constraint** — capacity = the AUM at which c_eff hits the cost budget (12bps ⇒ ~$300–350M for brwt block; C5ng/natgas legs carry futures-basis and holiday-spread risk that flat bps does not price at any size).
- **Per-gross IR gate (why ~2.8):** for a zero-correlation additive sleeve, `SR_new = sqrt(SR_p² + IR²)`. Champion of record SR_p = 3.2176 @1.6x ⇒
  IR 1.0 → 3.368 (+0.15); IR 2.0 → 3.786 (+0.57); **IR 2.8 → 4.265 (+1.05)**; IR 3.83 → 5.00 (GOAL).
  So "~2.8 per-gross IR to add a sleeve" ≈ the bar for a **+1.0 SR lift** on the champion of record — no validated sleeve is close (best family-level IS SR ≈ 3.6 before costs/diversification haircuts). On the SAFE16 @1x book (SR 5.182) the same IR 2.8 lifts only to 5.89 (+0.71). At capacity-limited weight φ (fraction of the full max-Sharpe allocation), the realized lift scales ≈ φ²·IR²/2SR_p — a sleeve that can only run at 30% weight because of ADV/cost creep delivers ~1/10th of its headline IR contribution. **Capacity and the IR gate must be evaluated jointly**: IR ≥ 2.8 AND NAV_max ≥ target AUM at c_eff ≤ 12bps.
- Interaction with the verdict: because GEAR16 turnover is 0.745 turns/yr, its cost curve is nearly flat in bps — the champion of record's frontier is limited by **alpha (SR 3.22 ≪ 5 goal), not by costs or capacity**, under any cost assumption in 3–12bps.

## FAIL-CLOSED LOG (all checks with exact numbers)

| check | result |
|---|---|
| `champion_build.py --verify` | **FAIL — REJECT**: max\|new-old\| 1.130e-03 / 4.099e-03 / 2.069e-03 (SAFE/AGG/BAL), n=4696. Aggregate stats match to 0.054pp; scenarios anchored to committed CSV + rebuilt turnover. |
| `rawew13v2_build.py --verify` | PASS: maxdev 9.996e-17 IDENTICAL; gross mean/max 1.600000, 0 days >1.6. |
| brief anchor "6bps = 0.90%ann" | **REJECT**: measured 1.077%/yr (mean one-side turnover 7.123%/day SAFE16; B config 7.346%/day → 1.111%/yr). Exact series used. |
| brief anchor @1x SR~5.18 ann~61% | PASS: 5.182 / 61.673% (geo). |
| brief anchor @1.6x SR~3.22 ann~39.5% | PASS: 3.2176 / 39.4995% (= champion of record GEAR16; note it is a DIFFERENT construction than the @1x file — 12 NAV-drift-weighted slots vs 16 EW throttled slots). |
| turnover-series integrity | PASS: reconstruction == construct() to 1.7e-18; tot1==tot2 maxdiff 0; index unique/monotonic, no dups. |
| FULL\|dW\| convention on SAFE16 | **REJECT (convention)**: committed file uses 0.5·Σ\|dW\|; at rules-FULL 6bps ann drops 61.673→59.945 (−1.73pp/yr undercharge). GEAR16 already FULL. |
| financing on internal gross (SAFE16) | **REJECT (not capital-real)**: gross 4.028x mean (p90 6.217, max 7.748) uncharged. Honest 4.5%: @1x 61.7→41.11% ann, MaxDD −7.31→−13.53; naive 1.6x lever (gross 6.45x) 109.00% is phantom; honest 68.15% @ MaxDD −22.61%, breaches 1.6x cap + all DD gates. |
| borrow 0.5%/yr on shorts | N/A at portfolio level: both builders document borrow as already inside sleeve net files (TRADE_RECORD_STANDARD); not re-charged (would double-count). Short notional not decomposable from net sleeve files — disclosed, not hidden. |
| offline | PASS: only campaign/results + campaign/agents sleeve CSVs + committed builders read; zero network. |

**Bottom line:** the TRUE capital-real @1.6x frontier is the champion of record's — **39.47% ann / SR 3.216 @9bps; 39.44% / 3.214 @12bps; MaxDD −6.52% at both** — and it is cost-invariant to 12bps. Every frontier number above ~40% @1.6x found in legacy docs (55.5%/61%/109% families) is either arithmetic-annualized, half-turn-undercharged, or financing-phantom; this report's REJECT log itemizes each with numbers.

DONE F1_cost
