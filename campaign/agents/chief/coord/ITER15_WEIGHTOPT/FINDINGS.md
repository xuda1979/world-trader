# ITER15 — WEIGHTOPT: a correlation-aware IS weight fit beats the champion's SR^P rule

**Status: ADOPTED — the champion of record now carries this change.**
Date: 2026-09-11. Agent: coordinator (ITER15), work dir `work/`.

> **ADOPTION LOG (2026-09-11).** Applied to the champion of record:
> * `campaign/scripts/rawew13v2_build.py` — `relw` now comes from `fit_relw()` (the
>   correlation-aware IS max-Sharpe fit); `P` retained for provenance only.
> * champion CSV + weights CSV re-emitted in place (the weights filename
>   `RAWEW13v2_IS_SR_weights.csv` is now a LEGACY NAME — its content is the new fit).
> * pre-ITER15 bytes archived first (nothing was destroyed):
>   `results/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER15_minsharpe_ann37.49.csv`
>   (sha `8d7e711e6d05a2b1`) and `results/archive_RAWEW13v2_IS_SR_weights_SUPERSEDED_by_ITER15_minsharpe.csv`
>   (sha `8c19ef227cf9b7b0`). Both still verify 7/7 under `verify_champion.py --rule srp`.
> * `CHAMPION_CARD.md` regenerated (now 38.11%).
> * `bt/verify_champion.py` gained `--rule {minsharpe,srp}` (default `minsharpe`), with the
>   max-Sharpe fit mirrored in the tool's OWN algebra — independent of the builder, since the
>   new `weights_repro` agrees with the committed weights to 9.37e-17.
> * New champion shas: daily `ee03f5c096aabb6d`, weights `745bc5f1d2037dc8`.
> * Post-adoption battery: builder `--verify` IDENTICAL (1.0e-16); card byte-reproducible
>   across runs; `verify_champion_r3_cmd.sh` **exit 0, 7/7**; pytest **15 failed / 429 passed**
>   vs the **22 failed / 422 passed** baseline inherited at session start (see "Test re-pins").

## Bottom line

`RAWEW16_IS_MINSHARPE` — the champion's 13 sleeves, same construction, same costs, same 1.6x
gross — with slot weights fitted by a **correlation-aware long-only max-Sharpe** on the IS
window instead of the champion's `max(IS_SR,0)^0.55` heuristic.

| metric | champion (RAWEW15) | **candidate (RAWEW16)** | delta |
|---|---|---|---|
| ann (geo, FULL) | 37.4923% | **38.1145%** | **+0.6222pp** |
| SR (daily, FULL) | 3.1951 | **3.2358** | **+0.0406** |
| MaxDD (FULL) | −6.6922% | **−6.5620%** | **+0.1302pp** (better) |
| negative years | 0/19 | 0/19 | — |
| OOS ann | 41.2328% | **41.6920%** | **+0.4592pp** |
| OOS SR | 3.0617 | **3.0916** | **+0.0299** |
| gross | 1.6 exact | 1.6 exact | 0 days > 1.6 |
| turnover | 5.2734 bp/yr | 5.3030 bp/yr | +0.03 bp/yr |
| worst year | +7.3104% | +6.9528% | −0.36pp (still positive) |

The candidate **strictly dominates the champion on ann, SR and MDD simultaneously**, which is
what makes it interesting: a pure weight change cannot buy ann with risk here because gross is
pinned at 1.6 by §8e.

## Why this was unexplored

`rawew13v2_build.py:68` sets `relw = np.maximum(SR, 0.0) ** P`. That is a function of each
sleeve's **own** SR only — it never reads the covariance matrix. The pool is not uncorrelated:

- the 4 `brwt*` Brent-WTI trend sleeves are **+0.62..+0.84** mutually correlated and hold
  **46.9%** of relw — one bet expressed four times;
- `C5ng`/`C5ngsum` +0.57; `A5r2`/`dualmom` +0.56;
- `QAxasts`, `carryv2`, `diescrack`, `a6r7` are ≈0-correlated to everything and hold only
  4.3–6.4% each.

For a zero-correlation asset the max-Sharpe identity `SR_new = sqrt(SR_p^2 + IR^2)` says a
positive-SR decorrelated sleeve *must* earn weight. The SR^P rule cannot see this. ITER14's
"all on-disk sleeves cannot raise Sharpe" conclusion (and the DEAD_IDEAS rows citing it) was
measured **under the SR^P heuristic**; this round shows the limitation was the *rule*, not the
sleeves.

## Method (IS-only discipline, identical to the champion's)

1. Load the 13 canonical sleeves, window `2008-03-31..2026-08-28`, IS = `< 2017-01-01`.
   CFX4 has zero IS coverage (starts 2019) so it stays relw=0, exactly as in the champion.
2. IS mean/covariance → long-only max-Sharpe, `w >= 0`, `w <= 2x` equal-weight,
   covariance shrunk toward its diagonal with factor `d`.
3. **Hyper-parameter `d` selected by the champion's own PRE-COMMITTED rule**, quoted verbatim
   from the builder: *"the largest P maximizing IS annualized-return subject to (IS SR>=3.5)
   AND (IS MaxDD >= -6.0%) AND (IS 0 negative years)"*. Applied to `d` this selects **d=0.62**.
   Selection never touches OOS; OOS is revealed once, after.
4. Construction is the canonical machinery **verbatim**: NAV-drift weights × relw,
   row-normalised, gross exactly 1.6, FULL |dW| @ 6.4bps one-side, margin 4.5%/yr on (GEAR−1).

The rule's objective improves in-sample too: **IS ann 34.2753% vs the champion's 33.4836%
(+0.7917pp) under the same constraints.** So the correlation-aware family is not merely a
different risk point — it is *better on the champion's own IS objective*.

## Verification

`campaign/bt/verify_champion.py` (independent algebra) on the candidate: **6/7 PASS**.

| check | result |
|---|---|
| byte_repro | PASS, max_dev **1.010e-16** |
| cost_reconciliation | PASS, model `full_dw`, ratio 1.0000000000006 |
| causality | PASS, `nav.shift(1)`, truncation-invariant |
| gross | PASS, max 1.6000000000006, 0 days over |
| yearly | PASS, 0 negative years |
| mdd | PASS, −6.5620% vs −7% limit |
| **weights_repro** | **FAIL — by construction.** The check asserts `relw == max(IS_SR,0)^P`; any different weight rule fails it definitionally. It is a recipe-provenance check, not a correctness gate. |

Weight provenance for the candidate is supplied instead by re-deriving the emitted weights
from the sleeve CSVs alone: **max|re-derived − emitted| = 2.776e-17**. (This shares the
optimiser code with the emitter, so it is a determinism check; the genuinely independent
structural check is `byte_repro`, which rebuilds the whole book from sleeves + weights in the
gate's own algebra.)

## Is the gain real? (adversarial checks)

- **Not overfit.** OOS SR +0.0299 and OOS ann +0.4592pp; the fit generalises.
- **Not selection luck.** Across the shrinkage family, **63/63 feasible members beat the
  champion's OOS SR** (min 3.0916 vs 3.0617). The shift is systemic, not a single lucky draw.
- **Statistically significant.** Daily difference `candidate − champion`: FULL +0.1801 bp/day,
  ann +0.4538%, **Newey–West (lag 10) t = +3.998, p ≈ 0.0001**; OOS +0.1290 bp/day, t = +2.330,
  p ≈ 0.0198. Block bootstrap (21d blocks) dSR: FULL +0.0378, 90% CI [+0.0158, +0.0584],
  **P(dSR>0) = 0.9967**; OOS P = 0.9387.
- **Broad-based, not one episode.** Top-10 |difference| days carry **−5.1%** of the net gain —
  the largest differences go *against* the candidate and the gain comes from the middle of the
  distribution. ex-2020 +0.4609%/yr; ex-2022 +0.4971%/yr.
- **Not the D7 tail artifact.** The champion has 12 materially-rewritten tail days carrying
  ≈+0.31pp (unexplained, highest-value open integrity item). Dropping the last 12/30/60/120
  days leaves dSR **+0.0403 / +0.0395 / +0.0386 / +0.0380** — the candidate's gain is orthogonal
  to that defect.
- **Tails no worse.** Worst day −4.483% vs champion −4.585%; lower skew (7.76 vs 8.01) and
  kurtosis (169.7 vs 178.6). Slightly worse worst-month (−2.65% vs −2.16%) and worst-63d
  (−3.35% vs −3.23%), while MDD improves 0.13pp.
- **Weight stability.** Block bootstrap (21d, 200 draws): every fitted weight sits inside its
  90% interval. Caveat: the brwt-block share is *not* robustly reduced (the fitted d=0.62 book
  holds 48.2% vs champion 46.9%) — the gain is a broad reallocation (up `C5ng` +2.2pp, `brwt5`
  +2.7pp, `diescrack` +1.5pp, `a6r7` +1.3pp; down `carryv2` −3.3pp, `dualmom` −2.0pp,
  `A5r2` −1.4pp), **not** a decorrelation play.

## Family scan: the champion's construction is confirmed optimal

Scanned the 2-parameter family (shrinkage `d`, NAV-drift mixer `rho`) that **nests the
champion** (`rho=1` is the canonical NAV-drift construction, `rho=0` is constant-mix):

- The **IS-rule winner over the whole (d, rho) family is d=0.62, rho=1.00** — the candidate.
  The canonical construction is confirmed best on the champion's own criterion.
- Only 4/30 members dominate the champion on both ann and SR, all at `rho=1`.
- `rho` is a clean frontier (rho=0: SR 3.6721 but ann 32.29%) — higher SR, lower ann. Not
  adopted: §8c requires dAnn > 0.
- A general mean-variance frontier family was also tested and has **no feasible member**
  (it never satisfies IS MDD >= −6.0%), so the shrinkage parameterisation is the right one.

Higher-SR alternatives that still dominate the champion (for coordinator choice; the
pre-committed rule picks d=0.62 by max IS ann):

| variant | FULL ann | FULL SR | FULL MDD |
|---|---|---|---|
| d=0.40 | 37.6616% | **3.2849** | −6.2573% |
| d=0.50 | 37.8592% | 3.2648 | −6.3949% |
| **d=0.62 (rule pick)** | **38.1145%** | 3.2358 | −6.5620% |

## Honest framing

- This does **not** close the GOAL100 gap (80% ann / SR 5 remain unmet; the book sits at the
  honest frontier). It is a +0.62pp ann / +0.041 SR improvement on the existing pool with no
  new data and no new sleeve.
- The leverage cap of 1.6 is the binding constraint on everything here. The high-SR/low-MDD
  books (rho≈0 variants, MDD −5.37%) would lever to ~2.09x and ~42% ann against the −7% wall,
  but §8e/1.6x forbids it. **The largest available lever remains the leverage cap, not alpha.**
- Weights are fitted on 2008–2016 only. Like the champion's own P=0.55, this is an IS-fitted
  constant re-applied OOS; no time-varying refit, no lookahead.

## Artifacts

```
campaign/agents/chief/coord/ITER15_WEIGHTOPT/
  RAWEW16_daily.csv                    candidate net series (n=4806)
  RAWEW16_IS_MINSHARPE_weights.csv     fitted slot weights
  emit_report.json                     stats + construction audit
  verify_candidate.json                bt/verify_champion.py report (6/7, weights_repro N/A)
  FINDINGS.md                          this file
  work/explore_is.py                   IS correlation / concentration
  work/weightopt.py                    first pass, shrinkage grid
  work/validate.py                     IS-rule selection + OOS reveal
  work/frontier.py                     full grid + MV family + bootstrap weights
  work/significance.py                 NW t-stat, block bootstrap, concentration, tails
  work/emit_candidate.py               deterministic emitter
  work/robustness.py                   provenance, tail-vintage, construction, window sensitivity
  work/mixing.py                       (d, rho) family scan
```

## Test re-pins performed at adoption

Changing the champion of record invalidates tests that pin its identity. These were
re-pinned to the new, legitimate facts (never weakened — where a decomposed identity was
pinned, the decomposition gained the new term rather than dropping it):

| test file | change |
|---|---|
| `test_verify_champion.py` | fixture calls now pass `rule="srp"` — the synthetic fixture is deliberately an IS-SR^P book; the tool's new default is `minsharpe`. 3 tests green. |
| `test_rawew13v2.py` | `test_weights_are_is_only_no_lookahead` rewritten: independently re-derives the max-Sharpe fit AND proves the IS-only handoff (fit must equal `fit_relw(IS)` and must DIFFER from `fit_relw(full)`, else the test is vacuous). |
| `test_audit_champ2_round2.py` | pin now decomposes over **three** sanctioned knobs: `c_prev − c_old` (costfix) + `c_old − l_old` (shift) + `c_new − c_prev` (weight rule). Each knob is separately asserted present and signed. 4 tests green. |
| `test_auditrecon_r2_lineage.py` | `_ports()` gained `rule=`; leak arm stays `srp`, causal arm uses the builder's `fit_relw`. |
| `test_auditrecon_r2_pin_mutations.py` | baseline rebuild uses `fit_relw`; the mutation guards are orthogonal to the rule. |
| `test_audit_champ2_round3.py` | `a4` headline pin → 38.114469; `STALE_HEADLINES` extended with the 37.49/37.195 generations (the lint's memory). |
| `test_audit_champ2_round4b.py` | fixture names the COMPUTED headline so it cannot go stale on a re-emit. |
| `test_camp_cost_r7_refresh.py` | the RAWEW15 refresh candidate was ADOPTED (2026-09-09) and is byte-identical to the archived pre-ITER15 champion, so the candidate-vs-champion comparisons are re-pointed at that archive; the obsolete "candidate EXTENDS champion" premise became "candidate covers the adopted generation". |
| `CAMP_COST/work_r3/turnover_attribution.py` | was recomputing the RETIRED `max(IS_SR,0)^P` inline instead of using `build()`'s relw — silently detached from production (total 5.274 vs champion 5.304). Now takes relw from `build()`; CSV regenerated. |
| gated docs | `GOAL100_CHAMPION.md`, `ITER10`, `ITER11`, `ITER14`, `FINAL_REPORT`, `FINAL_STATE`, `PROGRESS`, `TRUTH_MEMO` each gained an ADDITIVE supersede line naming the 38.11% headline. No history was deleted. |

Result: **15 failed / 429 passed**, vs the **22 failed / 422 passed** baseline inherited at
session start. The 15 remaining are all pre-existing stale pins (git-HEAD champion shas,
financing-stress scenario numbers keyed to the old book, round6/recon-lineage pins) that were
already red before this change and are largely downstream of **D7** (the champion of record is
still not committed, so anything comparing the working tree to git HEAD or to the `4358dfab`
pin cannot pass until it is).

## Recommended next step

The champion-of-record is still uncommitted (**D7**). Now that the book has changed, the
`4358dfab` pins scattered across the audit suite are stale on top of the pre-existing D7
stall. Committing the new champion (sha `ee03f5c096aabb6d`) and then re-pinning the remaining
15 tests against it is the natural next unit of work.
