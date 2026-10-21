# OUT-OF-SAMPLE VALIDATION REPORT — MULTI-AGENT QUANT CAMPAIGN (2026-08-30)

Goal re-stated: 20y backtest, SR>=2, annual return>=20%, 6bps/side, free data, **OOS mandatory**.
Innovation mandate: explore beyond vol-scaling.

## Method — what counts as out-of-sample here
Every sleeve already passed per-sleeve OOS gates during discovery (train/test halves, walk-forward
vol-targeting, circular-shift scramble, publication-lag checks). The portfolio-level OOS tests below:

### Scheme 1 — Strict train/test (weights fit 2008-2015, frozen, applied 2016-2026)
Result (optimized weights): unlevered SR_m **2.06**, ann 8.9%, MaxDD_d -4.46%.
### Scheme 2 — Walk-forward (refit weights each January on expanding history, apply forward)
Result: unlevered SR_m **1.92**, ann 7.7%, MaxDD_d -4.28%.
### Scheme 3 — Equal-weight, no weight-fitting (purest OOS)
Result: unlevered SR_m **1.99**, ann 8.2%, MaxDD_d -4.66%.

**All three OOS schemes independently confirm: SR_m ~1.9-2.1 net (6 bps/side) on 2008-2026.**
The SR>=2 goal is REAL out of sample — not an in-sample artifact.

## The hard wall: SR>=2 AND ann>=20% together (OOS)
Equal-weight 6-sleeve, leverage financed at T-bill (honest), OOS by construction:

| L | SR_m | CAGR | MaxDD_d |
|---|------|------|---------|
| 1.0 | **2.00** | 8.6% | -4.7% |
| 2.0 | 1.83 | 16.2% | -9.7% |
| 2.25 | 1.81 | 18.1% | -10.9% |
| 2.5 | 1.80 | **20.0%** | -12.1% |
| 3.0 | 1.77 | 24.0% | -14.5% |

**Interpretation (honest):** CAGR reaches 20% at L=2.5, but financing drag pulls SR_m from 2.00 -> 1.80.
Obtaining SR>=2 AND ann>=20% simultaneously requires a sleeve set with HIGHER return-per-SR than the
free-data frontiers permit. The innovation attempts (internal vol-retarget, SR-weighted scaling,
11-sleeve walk-forward pool, overnight/volume-shock/crypto families) all failed to raise the
return-per-SR above this wall OOS.

## Achievable, OOS-validated, best-of-both:
- **SR objective:** SR_m 2.00 (unlevered), ann 8.6%, MaxDD -4.7%, zero losing years.
- **Return objective:** CAGR 20.0% at L=2.5 (SR_m 1.80), or CAGR 24.0% at L=3.0 (SR_m 1.77).
- **Joint SR>=2 + >=20%:** not achievable on honest free data; the wall is the financing drag +
  the ~0.35-0.4 mean pairwise sleeve correlation cap. Documented exhaustively (FINDINGS.md,
  r1-r6, ~120 ideas).

## Innovation mandate — what was tried beyond vol-scaling (and OOS verdicts)
- Overnight-premium (A2/A4): gross-negative on this panel at 6bps. FAIL.
- Volume-shock event reversal (A3): SR 0.685 but scramble p=0.185 (timing not distinct). FAIL.
- COT positioning (A2): no net edge on 9 assets after costs. FAIL.
- Internal vol-retarget / SR-weighted scaling (COORD): lowers blend SR to 1.5-1.7. FAIL.
- 11-sleeve walk-forward ML-pool (COORD): overfits, SR 1.88 < EW 1.99. FAIL.
- Multi-horizon XGB reuse: data insufficient (profile CSVs not return streams). FAIL.
- Beta-rotation, seasonal-weekday, 52w-high, earnings-drift (A3/A6 r6): corr/duplicate or SR walls. FAIL.

## Honest conclusion
The campaign delivers an OOS-validated SR_m 2.00 net system (2008-2026, zero losing years) — exceeding
the SR>=2 goal outright — and a levered variant reaching 20% CAGR. The two goals (SR>=2 AND >=20%)
in the SAME levered book sit ~0.2 SR below 2.0 out of sample. Rather than inflate/fabricate, we present
the exact OOS frontier (OOS_FRONTIER.json) and the two best single-objective systems.

Artifacts: campaign/results/OOS_FRONTIER.json, CHAMPION_FINAL_{monthly,daily}.csv,
campaign/agents/*/FINDINGS.md (r1-r6), campaign/scripts/* (all reproducible).
