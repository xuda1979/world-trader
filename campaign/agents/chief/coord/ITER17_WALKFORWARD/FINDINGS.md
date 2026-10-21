# ITER17 — BUG CLEARING + WALK-FORWARD REFIT (built, measured, REJECTED) (2026-09-13)

> /goal: "improve the champion significantly by any means. Real time TDD is must and bugs
> must be cleared at first place."
>
> Champion of record: **UNCHANGED — ann 38.1145% | SR 3.2358 | MDD −6.5620% | 0/19 neg yrs |
> gross 1.6 exact | turnover 5.3030 bp/yr | n=4806 | sha `ee03f5c0`**. The walk-forward
> candidate was briefly adopted with the operator's approval and then **reverted** once it
> was attributed (§2). Suite: **455 passed, 0 failed**.

## 1. Bugs cleared FIRST (TDD: each test watched to fail before the fix)

| # | defect | why it mattered | test |
|---|--------|-----------------|------|
| 1 | `tools/floored_flagship_daily.sh:19` invoked the floor monitor with a path relative to the **caller's** cwd (the `cd "$ROOT"` is trapped in the `tee` subshell) | python exits 2 on "can't open file", which the `rc -ge 2` guard reports as **`!! FLOOR BREACH`**. The 2026-09-13 log carries that banner on a book whose own report says `floor health = OK` (T-bill 3.73%, 12-mo low 3.57% vs floor 3.40%). A fake alarm on a real guarantee. | `tools/test_floored_flagship_daily.py` — 2 tests (no false breach from a foreign cwd; a REAL breach still logged). Added `WT_TBILL_CSV` so both directions are hermetic. |
| 2 | `fit_relw`'s documented per-sleeve cap (`W_MAX = 2.0x` the EQUAL weight) was **INERT**: `bnds=[(0,W_MAX)]` against `sum(w)=1` can never bind | every doc (docstring, ITER15 FINDINGS, champion card) advertised a 2x-equal-weight cap the optimiser could not enforce; a fit could hold 100% in one sleeve. Inert for the champion only by luck (0.1457 < 2/13); it BINDS elsewhere — mean-shrunk fits drove a weight to 0.1667 > 2/12, and the ITER17 WF fit pinned a6r7 at exactly 2/13. | `campaign/bt/tests/test_iter17_wmax_cap.py` |
| 3 | `--emit` was **UNREACHABLE**: `mode = args[0] if not args[0].startswith('--') else '--verify'` sent every long flag to verify | `--emit` silently ran the verify path and wrote nothing — a documented re-emit after a sleeve refresh would no-op while printing a table that looks like success (the same silent-stale-artifact class as the D7 confusion). | `campaign/bt/tests/test_iter17_cli_modes.py` |
| 3b | *(added with #3)* now that `--emit` is reachable, `--emit --gear 1.75` (the RAWEW17 stray) or `--emit --shrink-d 0.8` would **overwrite the champion of record** | `check_emit_safe()` refuses such an emit unless `--force`; exits 2. Live-verified: `--emit --gear 1.75` -> rc=2, champion untouched. | `test_iter17_cli_modes.py` |

Fixes #2/#3 are champion-neutral by construction AND by measurement: `--verify` stays
**IDENTICAL (9.999e-17)**, and the suite went 444 -> **455 passed**.

## 2. THE HEADLINE: the walk-forward refit is NOT a gain — it is CFX4

The champion fits its 13 slot weights ONCE on `< 2017-01-01` and holds them. `wf_relw_frame()`
re-runs the SAME max-Sharpe fit at each annual refit date on `df[df.index < t]` (strictly past
data; causality proved by perturbing future returns — past weights are bit-identical).

On the full window it looked like a genuine win — ann AND SR up, all hard gates passing:

| metric | static champion | WF annual | delta |
|---|---|---|---|
| ann (FULL) | 38.1145% | 38.5030% | +0.3885pp |
| SR (FULL) | 3.2358 | 3.2603 | +0.0245 |
| MaxDD | −6.5620% | −6.6797% | −0.1177pp |
| IS ann | 34.275% | 33.899% | −0.376pp |
| OOS ann | 41.692% | 42.816% | +1.124pp |
| period split | — | — | +0.29 / +0.74 / +2.05pp in the 3 OOS windows |

**It is an artifact.** Once 2019+ enters the expanding window the refit loads **CFX4 at ~15%
of the book** — the sleeve whose twelvedata FX feed was discredited as a vendor artifact and
whose champion exposure is deliberately **ZERO**. Drop CFX4 from the pool entirely:

| pool | static | WF annual | delta |
|---|---|---|---|
| 13 sleeves (with CFX4) | 38.114% | 38.503% | **+0.389pp** |
| 12 sleeves (no CFX4) | 38.114% | 38.098% | **−0.016pp** |

The entire apparent gain is the discredited feed, and the biggest slice of it (+2.05pp) sits
in 2023-26, exactly where CFX4 has data. This is the CFX4-shaped hole in ITER16's frontier
table re-entering through a side door the static fit cannot open.

**Rejected, and pinned.** `test_iter17_walkforward::test_walkforward_edge_is_attributed_to_cfx4_and_rejected`
asserts both halves: the CFX4-driven gain reproduces (> +0.3pp) and it vanishes without CFX4
(< +0.2pp). The candidate bytes are kept at `campaign/results/RAWEW18_WF_YS_*` as an
artifact, NOT as a champion.

**Method note.** This was caught only by attributing the gain to its sleeves after the fact.
The identical trap applies to any adaptive-weight scheme here: a coverage-based fit will
silently load whatever sleeve becomes available, including one a prior audit discredited.

## 2b. Honest negative #2: ADDING a sleeve relaxes the binding rule — but only in-sample

The champion's rule is "max IS ann s.t. (IS SR >= 3.5) AND (IS MDD >= -6.0%) AND (0 neg yrs)".
Its IS SR is **3.5476 against the 3.5 floor**, so the SR floor is what binds — and a
decorrelated sleeve that lifts the attainable SR should therefore RELAX it, letting the rule
concentrate further. ITER16's candidate table, which measured candidates at frozen weights,
could not see this mechanism.

It is real. Re-running the whole rule (shrink re-selected, cap re-derived) with each validated
candidate added to the pool:

| pool (k) | rule-selected shrink | IS ann | IS SR | IS MDD | vs champion IS |
|---|---|---|---|---|---|
| champion (13) | 0.62 | 34.275% | 3.5476 | −5.9846% | — |
| +A5_r7_credit_composite | 0.80 | 32.408% | 3.5412 | −5.7040% | −1.867pp |
| +H21_fixed | 0.62 | 34.122% | 3.5643 | −5.8995% | −0.153pp |
| **+RB_hobr** | **0.90** | **34.799%** | 3.6601 | −5.9736% | **+0.524pp** |

The scan **independently reproduces ITER16's rejections** of the first two (−1.87pp vs its
−1.2..−2.0pp; −0.15pp vs −0.12..−1.4pp), which is what makes the RB_hobr delta credible.

**RB_hobr fails the OOS reveal.** The +0.524pp is entirely in-sample:

| | IS | OOS | FULL |
|---|---|---|---|
| champion | 34.275% | 41.692% | 38.114% |
| +RB_hobr @0.90 | 34.799% | **40.301%** | **37.656%** |
| period split | +0.08 / +1.15pp (pre-2017) | **−0.72 / −1.36 / −1.92pp** (all 3 OOS windows) | — |

The relaxation buys concentration the IS window rewards and the future does not. Rejected, and
pinned by `test_iter17_sleeve_addition::test_rb_hobr_relaxes_the_is_rule_but_fails_the_oos_reveal`.

**Corollary worth recording:** the rule sits at a *risk corner* by construction (it maximises
return subject to a risk floor), so its IS optimum is systematically the most overfit point on
its frontier. Both of this session's "gains" were artifacts of that corner — the walk-forward
refit via a discredited sleeve, this one via constraint relaxation.

## 2c. Honest negative #3: a full-pool screen finds nothing that survives the rule

Rather than test candidates one at a time, every on-disk return sleeve was swept through the
rule (~368 `sleeves/*.csv`, filtered to genuine daily-return series — the raw list is full of
`_positions.csv` files whose "returns" are position sizes and which score absurd SR ~20).

**A fixed-weight IS proxy is not an admissibility test.** It ranked
`CMDT2_RatioCPERGLD_252d` first at +5.28pp IS, and at the FULL canonical build the candidate
does produce **+0.82pp FULL ann** — but it is *not admissible*: IS SR **3.4199 < the 3.5
floor**, IS MDD **−6.574%** breaches the −6.0% bound, and its FULL MDD of **−6.9911%** sits
**0.9bp from the −7% wall** — the entire risk buffer spent for +0.82pp. The proxy ignored the
NAV-drift, costs and margin the real book carries, so it was screening a book that does not
exist. Pinned by `test_cmdt2_screen_winner_fails_the_rule_at_full_build`.

The screen's apparent champions are, without exception, the campaign's already-killed artifact
families — which is the real finding:

| apparent winner | why it is not a candidate |
|---|---|
| `MHX_multihorizon_xgb` (+15.4pp IS, SR 6.48) | the XGB overfit/flattening trap (`uniq_ratio` gate) |
| `C4_construct_v1/v2` (+10.2pp) | constructed portfolios, not sleeves — circular |
| `E1_CHAMPION20Y_BALANCED_uncost` (+7.8pp) | costs not charged |
| `HT_TAIL_L*/LEV16_*` (+7.2pp) | the half-turn@6.0 cost-undercharge artifact, *pre-levered 1.6x* |

## 2d. Honest negative #4: the EIA storage lead is tested — and the tradeable half has no edge

The one lead the ledger still marked UNTESTED ("the EIA regional/product storage cross-section")
was built and measured. `campaign/scripts/iter18_storage_sleeve.py`, TDD'd first
(`test_iter18_storage_sleeve.py`, 4 tests: future prices must not move past returns; a storage
value may earn nothing before its publication date; finite/covered; a surprise BUILD must lower
the position). Causality is explicit — EIA publishes the Friday figure the following Thursday,
so the value dated week w is usable only from w + 6 days, and the sleeve earns day t from the
position known at t-1.

**Aggregate storage surprise (US working gas vs Henry Hub, 1997-2026, 7731 days): no edge.**

| formulation | SR |
|---|---|
| change − 5yr same-week norm (shipped) | 0.055 |
| level − 5yr seasonal level norm | 0.002 |
| level − 10yr norm / 4wk-smoothed level | −0.040 / −0.005 |
| z-window 26 / 52 / 104 | 0.149 / 0.055 / 0.064 |
| unscaled surprise, clipped | 0.133 |

Nothing clears SR 0.3 against a book whose sleeves run at IR 2.8-3.0. The tradeable version of
the classic storage-report trade is the *immediate* 10:30 ET Thursday reaction, which needs
intraday prices; with daily closes and a conservative publication lag only the aftermath is
captured, and the aftermath is flat.

**The cross-sectional half is not tradeable with data on hand — a data gap, not a result.**
Regional storage exists (east/midwest/southsalt/southnonsalt/west/other/L48 weekly) but there is
exactly ONE gas price series in the repo (`natgas_HH_spot_daily.csv`). A storage cross-section
is expressed in regional basis (HH vs Chicago/Algonquin), which is not available. Recorded as
untestable-so-far rather than dead.

## 2e. Why every candidate fails the same way: the RULE is an overfitting machine

Three independent additions were tested — RB_hobr, the CMDT2 family, and finally all three
decorrelated sleeves TOGETHER (RB_hobr + CMDT2_RatioCPERGLD + H21_fixed, k=16). Every one
reproduces the identical signature:

| candidate | IS gain (rule-admissible) | OOS reveal |
|---|---|---|
| +RB_hobr | +0.524pp | −1.391pp |
| +CMDT2 (best admissible) | below champion at every admissible shrink | rule rejects |
| **+3 sleeves together** | **+0.340pp** (SR floor relaxes 3.55 → 4.03 at shrink 0.95) | **−0.832pp** |

The mechanism is now clear and general: the rule maximises IS ann *subject to a risk floor*, so
its optimum is by construction the **most overfit point on its own frontier**. Any expansion of
the feasible set — a new sleeve, a relaxed SR floor, another shrink step — is spent *in-sample*
first. The IS gain is therefore not evidence of anything; only the OOS reveal is, and it has
failed in every single case this session. The champion survives not because the rule is good
but because nothing has yet beaten it on the only test that counts.

*Method note (self-caught):* the admissibility label in the first variant of this scan compared
a fractional MDD against `-6.0`, which is always true — so only the `SR >= 3.5` half of the
filter was ever real there. Corrected; the conclusions above use the fixed comparison.

## 2f. The ceiling, measured: an ORACLE BOUND, and three causal methods that cannot reach it

To stop asserting and start proving, the maximum achievable ann was computed directly: trace the
**full-window** mean-variance frontier over long-only mixes of the 13 sleeves (cap 2xEW) and run
each point through the real construction, keeping the best that satisfies the contract gates.

| mix | ann | SR | MDD | gate |
|---|---|---|---|---|
| oracle, lambda = 0.1 (max mean) | 40.850% | 3.1906 | −7.4737% | MDD breach |
| **oracle, lambda = 6.58 (best admissible)** | **40.564%** | 3.2273 | **−6.8688%** | **PASS** |
| champion (committed) | 38.114% | 3.2358 | −6.5620% | PASS |

**The ceiling is 40.564%; the champion is 2.450pp below it.** That magnitude is real but it is
bought with FULL-WINDOW hindsight (μ and Σ fitted on the very data being scored). The question
that decides everything is whether a causal method can capture it. Three were tested:

| causal method | FULL delta vs champion |
|---|---|
| walk-forward refit, fixed shrink (max-Sharpe on trailing data) | ~0 (−0.016pp once CFX4 is out) |
| **rule walk-forward** (re-run the WHOLE rule each year, shrink re-selected on trailing data) | **−3.961pp** — it re-selects a far more conservative book (IS ann 27.0% vs 34.3%) |
| mean-vector shrinkage (Jorion-style) | −2.2pp at λ=0.25, worse thereafter |

None captures it. **The headroom is estimation error, not a discoverable edge** — it is exactly
the quantity that has produced every false positive this session (+0.52pp RB_hobr, +0.34pp
3-sleeve, +2.45pp oracle: each shrinks or inverts out of sample). A bound being reachable only
with hindsight is a statement about the bound, not about a missing method.

## 2g. Honest negative #5: the unwired data families carry nothing near the bar

The repo holds ~90 series landed in batches 8-9 (`cboe_hist`, `bund_daily`, `em_rates`,
`wb_commodity`, `dm_rates`) that are wired into **no** sleeve. Family-level screening had been
done; **sleeve construction had not** — so it was done here: every daily yield/FX series in
`bund_daily`/`dm_rates`/`em_rates` (the families at this book's frequency; `wb_commodity` is
monthly and would trip the >=20 zero-run gate) was run through four canonical causal signals
(252d and 63d trend, 21d reversal, 252d z-score), with the long-bond return proxy -dy.

| |SR| | series | signal | what it actually is |
|---|---|---|---|
| 1.200 | `aud_interbank_overnight` | z52 | a **policy-rate step function** — degenerate |
| 1.170 | `aud_cash_rate_target` | z52 | ditto |
| 0.969 | `nok_policy_rate` | mom63 | ditto |
| 0.653 | `aud_govt_2y` | mom252 | the first *tradeable* instrument on the list |
| 0.620 | `aud_govt_2y` | z52 | — |

**Best tradeable |SR| = 0.65; best overall = 1.20 on step-function policy rates.** The champion's
sleeves run at IR 2.8-3.0, and the adoption bar is that the sleeve must not *lower* the book's
per-gross return. Nothing here is within a factor of four. The frontier doc's earlier finding
(credit/FX/value/international all at IR 1.3-1.5) is confirmed on genuinely new data.

**This closes the analysis side.** Every route reachable from data already in the repo is now
tested. What remains is not analysis: new data (a purchase) or the leverage mandate (declined).

## 2h-bis. The regional cross-section is TESTED — no predictive edge (this closes the lead)

Before treating regional prices as the blocker, the obvious was checked: **a predictor test needs
no regional prices.** The 7 regional storage series were turned into cross-sectional features and
used to time aggregate Henry Hub (weekly, publication-lagged):

| feature | \|SR\| |
|---|---|
| South Central salt vs rest (`sc_vs_rest`) | 0.411 |
| regional dispersion / max−min | 0.395 |
| salt share of total | 0.110 |
| production (SC salt) − demand (East) | 0.158 |
| aggregate total (reference) | 0.225 |

Best of 6 features × 2 directions over 724 weeks = **0.411, i.e. t≈1.5 across 12 tries — noise.**
So the lead is not "blocked on data": **the regional storage cross-section carries no usable
signal.** Regional prices remain an ID lookup away, but they would only matter for a *basis*
trade, and there is no evidence here that the cross-section predicts anything. **The EIA lead is
closed in both halves.**

## 2h. The regional cross-section: blocked on an ID lookup, not on money

Following 2d, the blocker on the one remaining lead was pinned down rather than assumed. The
repo's own keyless route (`eia_dl.py` → `dnav/hist_xls/<ID>.xls`) is live — controls
`RNGWHHDd` (7451 obs) and `RBRTEd` (9973 obs) both fetch cleanly — so this is not a
connectivity artifact. But:

- 18 guessed regional-hub series IDs all returned nothing;
- the IDs could not be read from the source: WebFetch is blocked for `eia.gov`, the NG
  spot-price table pages `ng_pri_spt_s1_d.htm` / `ng_pri_spt_s1_a.htm` return 404, and
  `ng_pri_top.asp` (217 B) / `naturalgas/data.php` contain no `hist_xls` links.

**So the storage cross-section is OPEN, blocked only on reading EIA's citygate series IDs from
a browser — an identifier lookup, not a data purchase.** Anyone with a browser can unblock it
in a minute; it is recorded here so the next iteration does not mis-file it as "needs paid
data" (and does not re-run the aggregate version, which has no edge — §2d).

## 2i. Audit: the champion is NOT carrying a cost undercharge (stale-meta trap, pinned)

The pool takes costfix variants for brwt10/7/5 but the legacy path for brwt15, and
`E1_brwt_spread_rev15_2000.csv.meta` advertises **"6bps half-turn"** — the convention
`brwt_ens_build.py` calls *"the undercharge defect"*, and the gate test that would catch it
covers **"brwt10/7/5 ONLY"**. It looked like an open 1%-class integrity defect in the champion.

**It is not — measured, not assumed.** Rebuilding from the same generator, parameters and
vintage, differing only in the cost convention, on the daily mean return:

| | %/yr |
|---|---|
| committed − `convention="full", bps=6.4` | **+0.0000** (exact) |
| committed − `convention="half", bps=6.0` | −1.0564 |

The committed bytes ARE the full-cost series; **the `.meta` prose is stale**. Two things follow.
(1) The champion is charged in full — no headline correction is owed. (2) Acting on the meta
text would have been a real error: subtracting the half-vs-full delta **double-charges** an
already-paying sleeve and costs 0.064pp of headline for nothing (measured). Pinned by
`test_iter19_brwt15_cost_convention.py` so neither mistake can recur. Champion unchanged.

## 2j. A previously-unknown construction quirk, quantified — and it is a WASH, not a gain

The builder hard-codes `df.index >= '2008-03-31'`, but **`A5r2` does not start until
2009-09-18** (~385 trading days later) and its fitted weight is 4.25% of the book. `build()`
fills the missing returns with 0 while still allocating the slot its full weight, so for the
first 1.5 years the book holds ~4.25% of gross in a sleeve that does not yet exist — silent
dead weight. The fit itself does not have this problem (`isr[have].dropna()` starts 2009-09-18);
only the construction does.

Masking the slot to 0 before each sleeve's INCEPTION (an ex-ante fact; no lookahead — a naive
per-day `notna()` mask churns daily on interior gaps and blows turnover to **435 bp/yr**, which
is how the first attempt was caught and discarded):

| | ann | SR | MDD | turnover |
|---|---|---|---|---|
| as-built | 38.114% | 3.2358 | −6.5620% | 5.3030 bp/yr |
| inception-masked, same weights | **38.322%** | 3.2361 | −6.5620% | 5.3341 bp/yr (+0.03bp) |

+0.21pp at fixed weights — but that is not the rule's question. The mask deepens the IS
drawdown (−5.9846% → −6.1677%), which BREAKS the rule's `IS MDD >= -6.0%` bound, so the rule
re-selects shrink 0.62 → 0.50:

| rule-selected book | ann | SR | MDD |
|---|---|---|---|
| champion (as-built, 0.62) | **38.114%** | 3.2358 | −6.5620% |
| corrected construction (0.50) | 38.071% | **3.2654** | **−6.3949%** |

**−0.043pp ann for +0.030 SR and a shallower MDD — a frontier trade, not a gain. NOT adopted.**
(The difference is confined to 386 days; after 2009-09-18 the two books are identical, so this
changes the backtest's early history only, never the live strategy.) Recorded because "fix the
dead weight" looks like a free +0.21pp and is not — the rule's own risk bound gives it back.

## 2k. Honest negative #6: a grid-selected sleeve PASSES gate 8c and is still an artifact

The brwt family holds 48% of the book and its generator (`brwt_ens_build.py`) can build ANY
(lookback, band) parameterisation — but the campaign had only ever tested variants that already
existed on disk. Scanning the grid (8 lookbacks x 4 bands, full-cost convention) finds a cell
that is NOT in the pool: **(lb=15, zb=1.0), IS SR 3.814**, above every incumbent (brwt10 3.614,
brwt7 3.726 / 3.090, brwt15 2.937). Added to the pool it re-runs the rule to shrink 0.50 and:

| gate | candidate | limit | verdict |
|---|---|---|---|
| IS ann | 36.530% (champ 34.275%) | — | +2.255pp |
| **FULL ann** | **39.232%** (champ 38.114%) | — | **+1.118pp** |
| SR / MDD | 3.2249 / −6.6706% | MDD ≥ −7% | PASS |
| neg years / gross / turnover | 0 / 1.6 exact / 5.3028 bp | 0 / ≤1.6 / ≤6.4 | PASS |
| OOS ≥ IS | 41.729 ≥ 36.530 | — | PASS |
| **gate 8c (dAnn>0)** | **+1.118pp** | — | **PASS** |

**It is still an artifact, and the operator rejected it as in-sample.** The cell is the MAXIMUM
of a 32-point IS grid, so its IS edge is upward-biased by construction, and it shows the WORST
IS→OOS degradation in its own family — the signature of exactly that bias:

| sleeve | IS SR | OOS SR | drop |
|---|---|---|---|
| **brwt(15,1.0)** | **3.814** | **2.223** | **−1.59** |
| brwt10 | 3.614 | 2.638 | −0.98 |
| brwt7 | 3.726 | 2.949 | −0.78 |
| brwt15 | 2.937 | 2.163 | −0.77 |

IS +2.255pp but OOS **+0.037pp**, with OOS windows +0.87 / +1.14 / **−1.41pp** (the most recent
negative). **Gate 8c is a portfolio-construction test, not an out-of-sample test** — a candidate
can pass it purely by fitting the IS window harder. Pinned by
`test_iter19_brwt15_cost_convention::test_is_best_brwt_grid_cell_is_not_oos_supported`.

## 3. The weight/alpha frontier is CLOSED — independently re-measured

~20 parameter points across three families, all measured on the canonical construction:

| family | result |
|---|---|
| covariance shrink 0.0 -> 0.95 | IS ann rises monotonically (32.7 -> 36.0) but IS SR/MDD bind at **shrink=0.62**: champion IS MDD −5.9846% vs the −6.0% bound, IS SR 3.5476 vs the >=3.5 bound — it IS the return-max admissible point. |
| mean-vector shrinkage (Jorion-style) | strictly LOWERS IS ann: 34.275 -> 30.480 -> 27.044 -> 25.297 (lambda 0/0.25/0.5/0.75) |
| blend toward the max-mean mix | MDD blows through the wall immediately: t=0.25 -> IS MDD −7.80%, FULL −8.13%, SR 3.24 -> 3.01 |
| per-sleeve cap 1.0/1.5/2.0/3.0 | 2.0 and 3.0 byte-identical (interior optimum); 1.0 and 1.5 cost return |

At fixed gross 1.6, raising ann requires raising per-gross return (alpha). Every decorrelated
family found so far runs at ann/vol IR 1.3-1.5 against the energy core's 2.8-3.0.

## 3b. The leverage lever, quantified and DECLINED (operator decision, 2026-09-13)

The only change that delivers a significant gain is spending the risk budget the contract's own
−7% MDD wall allows. Computed exactly on the current champion:

| gear | ann | SR | MDD | wall |
|---|---|---|---|---|
| 1.600 (contract) | 38.114% | 3.2358 | −6.5620% | PASS |
| 1.650 | 39.297% | 3.2223 | −6.7647% | PASS |
| **1.705** | **40.608%** | 3.2084 | **−6.9875%** | PASS |
| 1.710 | 40.727% | 3.2072 | −7.0077% | **BREACH** |

+2.49pp ann, 0/19 neg years, costs 6.38bp vs the 6.4 limit, OOS >= IS — failing only
"leverage <= 1.6". Put to the operator twice; **the answer was "keep 1.6 — close it out."**
The champion therefore stays at 38.1145% and this iteration closes with no adoption.

## 4. Status

- champion/bt suite: **455 passed, 0 failed** (was 444; +11 new tests, all bug/negative pins).
- `rawew13v2_build.py --verify`: **IDENTICAL (1e-16)**; card regenerated and byte-reproducible.
- Adoption of the WF book: attempted with operator approval, **reverted** on the CFX4 finding.
- The operator has kept the 1.6x gross cap binding, so the leverage lever identified in
  standup #103 remains off the table: within the cap, no honest change from this iteration
  raises the champion. **The honest frontier is unchanged at 38.1145% / SR 3.2358.**
