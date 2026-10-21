# DIVERSIFICATION RESEARCH — Multi-Agent Sweep (2026-09-17)
**Goal:** make the champion MORE DIVERSIFIED with HIGHER SHARPE and LOWER MaxDD **without
lowering annual return**, via many submitted research agents over the existing 12-sleeve pool.

## Framing (from prior audit + this sweep)
The champion's edge and risk both live in the energy complex: the brwt triad (brwt5/7/10) is
~76% of gross and ~0.90 correlated to the champion; adding nat-gas (C5ng/C5ngsum) brings energy
to ~91% of gross. Every decorrelated sleeve has far lower per-gross return (IR ~0.8-1.9) than the
energy block (IR 2.8-3.0), so naive diversification costs annual return)Skip. The question is
whether a SMART (non-proportional) reallocation can improve SR/MaxDD at ~flat ann.

## Agents & results
- **Agent A (brwt de-concentration, proportional):** monotone frontier — more diversification
  steadily raises SR (to 3.46) and lowers MDD (to −5.6%) but costs ann (from +3.65 to −3.81pp).
  The max-Sharpe base sits at the ann-optimal endpoint. 45-55% brwt is the knee: SR 3.17-3.29,
  MDD −6.2..−6.7, ann ~±0.5pp.
- **Agent C (naive unconstrained linear-opt):** collapsed to single-sleeve; REJECTED (linear proxy
  misrepresents NAV-drift; produced SR 2.72 / MDD −11.9%). Lesson: must optimize actual mechanics.
- **Agent D (neutralize weakest energy brwt5 -> decorrelated):** SR +0.136, MDD +0.40 better at
  brwt5 fully removed, but ann −1.91pp monotone.
- **Agent E (substitute most-correlated energy brwt7 with EACH decorrelated):** only
  **C5ngsum (nat-gas summer-seasonal)** gives a strict-simultaneous improvement (SR↑, MDD↑, ann≈).
  All truly-non-energy sleeves (A5r2, QAxasts, dualmom, carryv2, diescrack, a6r7) fail — they cost
  too much ann per risk-unit on this pool.
- **Agent F (C5ngsum <-> brwt7 sweep, optimal):** monotone Pareto-improving family.
- **Agent G (IS/OOS robustness of candidate):** the SR/MDD gain holds and strengthens OOS.
- **Agent H (stack brwt7->C5ngsum + brwt5->A5r2):** SR 3.346/MDD −6.10 but ann −0.72pp; worse
  return-preservation than the single switch.

## Recommended DIVERSIFIED CHAMPION VARIANT (primary, strict improvements, ~flat ann)
**Swap ~35% of brwt7 weight into C5ngsum (natural-gas summer-seasonal).**
| | ann | SR | MaxDD | neg yrs | brwt gross-reliance |
|---|---|---|---|---|---|
| BASE (committed of record) | 39.50% | 3.218 | −6.52% | 0 | 76.1% |
| **CAND (35% brwt7→C5ngsum)** | **39.32%** | **3.327** | **−6.15%** | **0** | **71.0%** |

- ΔSR **+0.11**, ΔMDD **+0.38pp better**, Δann **−0.18pp** (within noise; 0 neg years).
- **Robust IS/OOS:** IS-SR 3.60 (vs 3.50), OOS-SR 3.22 (vs 3.08), OOS-ann 43.98% (vs 43.15%),
  0 neg years — the improvement is NOT OOS-only.
- Mechanic: C5ngsum (corr 0.166) is decorrelated from the crude-oil brwt block (brwt7 corr 0.926),
  so cutting the most-correlated oil leg into gas-adjacent seasonal alpha reduces crude dominance
  while keeping the energy edge.

**More-aggressive risk-reduction variants (if more return can be traded):**
| brwt7→C5ngsum frac | ann | SR | MDD |
|---|---|---|---|
| 45% | 39.26% | 3.355 | −6.03% |
| 60% | 39.18% | 3.391 | −5.84% |

## Honest conclusion
Within the existing 12-sleeve pool, **"diversify to raise Sharpe / lower MaxDD without any annual
return loss" is NOT strictly feasible** — every genuine risk gain costs some return. The
**C5ngsum-for-brwt7 reallocation is the closest to a free lunch** (SR+0.11, MDD+0.38pp at −0.18pp
ann, robust OOS) and is the recommended diversification step. Genuinely non-energy enrichment
(which would truly lower energy concentration) needs a NEW high-per-gross, low-correlation engine
— not found in existing data (see HUNT_FAMILY_FINDINGS).

## Files / status
- This memo. Champion-of-record CSV **unchanged** (byte-identical). The candidate is a
  reweighting proposal for operator review / adoption; can be materialized via the builder's
  `--emit-candidate` path if approved.

---
## PASS 2 (2026-09-17, loop iteration) — new-sleeve hunts + confirmed frontier
- **Hunt NEW-FX**: `fx_hist` (60-currency) cross-sectional momentum 21/63/126d -> SR **-0.40..-0.87**, no edge.
- **Hunt NEW-ETF**: commodity-ETF (BNO/CORN/CPER/COPX/WEAT/DBA/GLD/SLV/UNG/USO/DBC/GSG) cross-sectional
  mom -> SR **-0.25..0.00**, no edge.
=> No genuinely-new decorrelated daily engine exists in available data (consistent with the
   HUNT_FAMILY sweep). Diversification must be within-pool.
- **Multi-pair Pareto frontier search** (8 substitution pairs x fraction grid): the ONLY
  Pareto-improving moves are **energy -> C5ngsum** (nat-gas summer-seasonal). Non-gas targets
  (a6r7, QAxasts, dualmom, diescrack, carryv2) never achieve SR↑ & MDD↓ at flat ann.
- Confirmed frontier (brwt->C5ngsum):
  | frac | ann | SR | MDD | dSR | dMDD | dAnn |
  |---|---|---|---|---|---|---|
  | 20% | 39.40 | 3.282 | -6.31 | +0.06 | +0.21 | -0.10 |
  | **35% (recommend)** | 39.32 | **3.327** | **-6.15** | +0.11 | +0.38 | -0.18 |
  | 45% | 39.26 | 3.355 | -6.03 | +0.14 | +0.50 | -0.24 |
- **Recommendation (unchanged): adopt the 35% brwt7->C5ngsum reweight** as the diversified
  champion variant (highest SR & lowest MaxDD at minimal ann cost, robust IS/OOS). Champion of
  record CSV remains byte-identical pending operator adoption.

---
## PASS 3 (2026-09-17, loop iteration) — convergence check
- **Combined two-swap synthesis** (brwt7->C5ngsum + brwt5->diescrack): best combo SR 3.285 /
  MDD -6.31 — **worse** than the single 35% brwt7->C5ngsum switch (SR 3.327 / MDD -6.15). Stacking
  does not help.
- **Gas-family target split** (freed brwt7 weight split between C5ng & C5ngsum): no split beats
  the pure 35%->C5ngsum point.
- **Conclusion (converged): the 35% brwt7->C5ngsum reweight is the unique Pareto-optimal
  diversification within the existing 12-sleeve pool** — SR 3.33 (+0.11), MDD -6.15% (+0.38pp),
  ann 39.32% (-0.18pp), 0 neg yrs, robust IS/OOS. Champion-of-record CSV unchanged.
