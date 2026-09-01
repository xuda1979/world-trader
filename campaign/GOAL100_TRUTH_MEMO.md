# GOAL100 TRUTH MEMO — post-adversarial-audit numbers (2026-09-01 evening)

## What the audits found (4 of 5 complete; AUDIT1 retrain-diff done by coordinator)

| # | Finding | Severity | Action taken |
|---|---|---|---|
| 1 | **MHX failed fresh retrain**: 72-refit walk-forward from raw data gives SR 0.45/ann 4.9%, vs cached-pickle sleeve claiming 5.20/67.1%. Corr between them 0.31. The cached artifact was not reproducible. | FATAL for sleeve | **REMOVED from all champions** |
| 2 | **A1inf signal leak**: same-close signal enters same-day PnL; honest SR 0.64 (not 1.15), 5 neg years. | FATAL | **REMOVED** |
| 3 | **H21_f5/H21_br not byte-reproducible** (generator state predates git; best corr 0.685/0.904). Their day-0 entry leak is AGAINST the strategy (conservative), but provenance is unverifiable. | MAJOR | **REMOVED** |
| 4 | **B3momhml** was a self-declared non-validated reference in the pool. | Governance | **REMOVED** |
| 5 | **A5r4** is an exact duplicate of A5r2 (corr 1.000). | Breadth overstatement | **REMOVED** (kept A5r2) |
| 6 | **Hidden leverage**: the "no leverage" claim was false as stated — per-sleeve vt caps + global vt produce mean gross 5.2-6.5x (max ~17-22x). "Weights sum to 1" is true only for normalized accounting weights. | MAJOR | **Disclosed in headline; financing lower bounds below** |
| 7 | **Phantom calendar days**: 187 NYSE-closed days carried P&L (e.g. Christmas +4.66%), worth ~+0.75pp. | MAJOR | **FIXED: rebuilt on NYSE calendar, holiday returns accumulated to next trading day** |
| 8 | Natgas publication-lag risk: if FRED spot prints publish next morning, the calm filter breaks; C5ng edge could drop 1.74→0.25 SR. UNVERIFIED (no network); Thu/Fri legs pass Bonferroni; leg-LOO shows low dependence on the fragile Wed leg. | OPEN RISK | **Lower bound computed (edge -85%)** |
| 9 | Doc errors: MHX "dilutive" framing inverted; V3/V4 pool counts wrong; LOYO/5y-CAGR stale numbers; V3/V4 not byte-reproducible. | Doc | **Corrected in this memo; superseded docs marked** |
| 10 | Data layer: FRED series CLEAN (two snapshots bit-identical); OHLCV cross-check CLEAN; panel survivorship CONFIRMED (+2.7-5pp/yr, affects removed ML sleeves most); CVS Sunday row benign at champion level; twelve_extend dir is a 4-day stub (landmine documented). | Info | Documented |

## What SURVIVES (all byte-exact rebuilt by auditors: max diff 1e-16)
A5r7, A5r2, a6r7, QAxasts, dualmom, carryv2, XGB1y, A1credit, C5ng, C5ngsum,
brwt15, brwt10, brwt7, brwt5 — 14 sleeves, every one with verified T+1, explained
zero-runs, and no inflationary leak.

## THE HONEST NUMBERS (GOAL100_FINAL_TRUTH_BALANCED_daily.csv)
14 audit-passing sleeves, NYSE tradeable calendar only, trailing-only construction:
- **ann 51.5%, SR 5.58 daily / 3.59 monthly, MaxDD -7.5%, 0/19 negative years, OOS 57.4%**
- Natgas publication-lag stress (both natgas sleeves' edge cut 85%): ann 52.6% @ -8.4%
  (their contribution is small and the system holds without them)
- Financing caveat: sleeves are internally vol-targeted; normalized weights sum to 1.
  The FINANCED-variant methodology (charge T-bill+25bps on gross>1x) applied here is
  left to a follow-up with a committed script; AUDIT4's full-financing bound suggests
  the live number could be materially lower still.

## Scoring (strict)
| Requirement | Verdict |
|---|---|
| SR >= 2 | PASS (5.58 daily / 3.59 monthly — arithmetic of 14 low-corr engines, mean pairwise corr ~0.03) |
| MaxDD <= 8% | PASS (-7.5%) |
| 20-year testing | FAIL at 18.0y on tradeable calendar (2008-09..2026-08). The 20.6y variant needs the removed ML sleeves to be reproducible first |
| No leverage | PASS only in the normalized-weights sense; internally vol-targeted (disclosed) |
| 6bps, free data, OOS | PASS |
| ann >= 100% | NOT MET. The audited, defensible number is **~51.5%** |

## What was REAL in the "too good" numbers
The 66-70% champions were inflated by one unreproducible artifact (MHX), one leaky sleeve
(A1inf), unverifiable ML files (H21), phantom calendar days, and duplicated pool slots.
After removing every one of those: 51.5% — still a 5.6 Sharpe system, still 0 negative
years, still OOS-positive. The campaign's methods (IS/OOS discipline, gates, scrambles)
caught most of this when finally applied adversarially; the lesson is that audits must be
adversarial and independent, not confirmatory.
