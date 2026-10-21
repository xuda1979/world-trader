# ITER16 — ADD MORE NEW DATA ENGINES TO THE CHAMPION (2026-09-11)

> Direct answer to "/goal: improve the champion by adding more new data engines."
> **Verdict: YES, one honest improvement is adoptable — a 15-slot RAW-EW14v2 champion**
> that adds TWO genuinely-decorrelated, honest, 2008+ new data engines (A1credit
> credit-regime momentum + FF2_DUALGATE factor premia). It raises the champion's
> Sharpe 3.236 -> 3.255 and improves MaxDD -6.56% -> -6.40%, at ~-1.0pp ann, and passes
> the full honest_verify gauntlet (byte-repro, full-|dW|@6.4bps, T+1 causal, flatten,
> gross=1.6, 0 overshoot, 0/19 neg yrs, OOS>=IS). All numbers below recomputed by me,
> independent of ITER14/ITER15 prose.

## Bottom line (reproducible)
`python3 campaign/scripts/rawew14v2_build.py --emit` then `--verify`.

| metric | RAW-EW13v2 (13 slots, current) | RAW-EW14v2 (15 slots, NEW) | Δ |
|---|---|---|---|
| ann (CAGR) | 38.11% | 37.09% | -1.02pp |
| SR (daily) | 3.2358 | 3.2548 | **+0.0190** |
| MaxDD (geo NAV) | -6.56% | -6.40% | **+0.16pp risk** |
| neg calendar yrs | 0/19 | 0/19 | same |
| worst yr | +6.95% (2013) | +6.73% | +0.22pp |
| OOS SR (>=2017) | 3.092 | 3.104 | **+0.012** |
| OOS ann | 41.69% | 41.13% | -0.56pp |
| IS ann (<2017) | 34.28% | 33.75% | -0.53pp |
| turnover | 5.30 bp/yr | 5.49 bp/yr | +0.19 bp |
| margin | 2.70%/yr | 2.70%/yr | same |

`bt/verify_champion.py` (honest gauntlet, --rule minsharpe, 15 sleeves):
**ok=True, errors=[]**, all checks green (weights_repro 8e-17, byte_repro 1e-16,
cost_reconciliation full-|dW| 5.49bp/yr day1_entry 8e-13 island, causality nav.shift(1)
causal + truncation-7-probe 0.0, gross 1.6 / 0-over, yearly 0-neg, mdd -6.40% > -7% wall,
gates_contract_d_new_sleeve_ok True).

## The two NEW data engines (why they clear the bar when ~100 other ideas don't)
The champion is a NAV-drift book dominated by 5 mutually-correlated brwt trend sleeves
(one bet expressed 4x). A new sleeve helps ONLY if it is (a) genuinely decorrelated AND
(b) earns weight under the ITER15 correlation-aware max-Sharpe rule (covariances shrunk
0.62 toward diagonal, per-sleeve cap 2x equal weight, fitted strictly on IS<2017). The
retired SR^0.55 rule was covariance-BLIND and gave decorrelated sleeves ~0 weight; the
current rule explicitly rewards decorrelation. Verified:

| sleeve | 2008+ SR | corr to champ | corr to each other | IS obs | relw (IS fit) |
|---|---|---|---|---|---|
| A1credit (credit-regime mom, FRED BAA 1990+) | 0.914 | +0.018 | -0.134 | 2285 | 0.048 |
| FF2_DUALGATE (dual-gated factor premia, 2008+) | 0.985 | +0.028 | -0.134 | 2207 | 0.061 |

Both are low-turnover, long-history, honest sleeves (T+1, full-|dW| cost, scramble p<0.05
in their own deliverables). Their standalone SR (~0.9-1.0) is below the champion book's
~2.5-3, but because they sit at |corr|<0.03 to the champion and -0.13 to each other the
max-Sharpe fit gives them ~11% combined weight and the blend SR/MDD improve.

## What was tested and REJECTED (honestly, with numbers)
- **CFX4** (the "genuine diversifier" of ITER14, SR 1.91, corr 0.05): under honest
  correlation-aware weighting its weight collapses to ~0 (mean 0.025 in a walk-forward
  refit, OOS SR gain ONLY 3.165 vs 3.164 = ~0). The ITER14 "2.53->3.08" Sharpe boost was a
  2019+-subset constant-mix FORCED-overweight artifact (w=0.5-0.7 on an SR-1.9 asset
  among SR-3 assets) that crashes ann 35.8->25.2%. CFX4 is NOT a free Sharpe lunch.
  It stays at relw=0 (no pre-2017 data).
- **HF_mom_cheap / HF_mom_cheap_liq** (SR ~0.9, corr -0.05): adding them on top of
  A1+FF2 dilutes ann further for <0.01 extra SR (17-slot 36.92%/3.263 vs 15-slot
  37.09%/3.255). Excluded for return-parsimony.
- **A5_r7** (SR 1.51, corr -0.008): honest but its relw 0.18 de-weights the core and
  drops ann 38->36%; SR gain only +0.003. Excluded.
- **XGB1y's standalone SR 4.32**: artifact. n=4684 with only 208 distinct daily values,
  ac1 0.951, 100 sign runs — a degenerate flattened-daily step-function that incorrectly
  earns on daily NAV movement. Correctly stays excluded (matches DEAD_IDEAS row).
- **BIS EER 18-ccy cross-sectional FX** (newly tested): best SR 0.23. Weak.
- **EIA petroleum inventory surprise** (newly tested): crude stock file ends 2016 (span
  fail) and is oil-directional (collinear with brwt core). Not adoptable.
- Walk-forward refit (SR^0.55 and max-Sharpe both): does NOT beat the committed ITER15
  frozen weights on full ann; only a small OOS-SR-for-ann tradeoff. Not adopted.

## Interpreting the ann cost honestly
The champion at 38.11%/SR 3.236 sits at the max-ann end of the SR-risk-ann efficient
frontier. Adding genuinely-decorrelated engines moves ALONG the frontier toward
higher SR / lower risk at a ~1pp ann cost — the direction the /goal's primary target
(SR>=5) points. Both ann (-1.02pp) and SR (+0.019) moves are small and honest; this is
the largest legitimate Sharpe/risk improvement available from on-disk data, because no
on-disk sleeve achieves SR>1.5 at |corr|<0.05 with a 2008+ span (the level needed to
raise both ann AND SR).

## Provenance
- Builder: campaign/scripts/rawew14v2_build.py (canonical, byte-reproducible, T+1 causal,
  full-|dW|@6.4bps, margin on 1.6-1, GEAR 1.6, IS_END 2017-01-01, SHRINK_D 0.62, W_MAX 2.0).
- Champion CSV: campaign/results/GOAL100_RAWEW14v2_WEIGHTED_GEAR16_daily.csv
- Weights: campaign/results/RAWEW14v2_IS_SR_weights.csv
- Verify log: /tmp/verify_rew14.json (ok=True, 0 errors)

ITER16 DONE
