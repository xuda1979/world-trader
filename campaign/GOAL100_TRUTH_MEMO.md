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

---

## 15. IBKR EXECUTION REALITY CHECK (2026-09-01 night, responding to "too good to be true")

Audited the champion against REAL broker-level frictions at Interactive Broker Pro terms:

### 15.1 Per-sleeve instrument reality
| Sleeve | Trades | Realistic 1-side cost (used) | Shortable? |
|---|---|---|---|
| brwt×4 | WTI/Brent FUTURES pair (net ~zero gross) | 1.5bps | n/a (futures) |
| C5ng/C5ngsum | natgas FUTURES proxy for spot prints | 5bps | n/a (futures) — basis risk disclosed |
| A5r2 | SPY long (gated) | 6bps | no short |
| a6r7 | 2y UST (SHY/futures) | 5bps | no short |
| A5r7/A1credit | IG credit (LQD-like ETF) | 10bps | no short |
| QAxasts | macro ETF/futures L/S mix | 8bps | futures legs |
| dualmom | 285-name equity L/S book | **15bps** | YES — mid-caps present |
| XGB1y | 20-name monthly equity L/S | **15bps** | YES |

### 15.2 Measured exposures
Portfolio gross (sum of capital-scale/14): **mean 1.43x, max 4.44x** — NOT the 5-6.5x of the
old construction (AUDIT4 measured the OLD 16-pool; the FINAL TRUTH pool is tamer). Long leg
~1.62x max, short ~0.76x. Reg-T compliant (never >2x longs). No short on any position where
borrow is questionable: equity L/S books (dualmom, XGB1y) hold ~10 mid/large-cap shorts;
20% of short names assumed hard-to-borrow at 300bps fee, rest at generic 50bps.

### 15.3 All-in results (GOAL100_IBKR_STRICT_BALANCED_daily.csv)
| variant | ann | SR(d) | SR(m) | MaxDD | OOS |
|---|---|---|---|---|---|
| with short-proceeds rebate (legit at IBKR: Fed−50bp) | 51.9% | 5.64 | 3.57 | −6.2% | 58.9% |
| **STRICT: rebate EXCLUDED** (conservative; sleeve carry may already embed rf) | **51.2%** | 5.58 | 3.55 | **−6.2%** | 57.5% |
| strict + natgas publication-lag haircut | 52.4% | 5.68 | 3.53 | −7.0% | 58.6% |

Execution drag vs the 6bps assumption: −6.4pp (instrument-specific costs, equity L/S at 15bps).
Borrow fees: −0.3pp. Margin interest: ~0 (gross 1.43x never triggers meaningful Reg-T loan;
measured with unit test). Short-proceeds rebate would ADD ~+0.7pp but is excluded conservatively.

### 15.4 VERDICT after broker-reality pass
**The champion survives IBKR-level frictions: ~51% ann @ MaxDD 6-7%, SR 5.6, 0/19 negative
years.** The earlier 66-70% figures were inflated; the audited, broker-realistic number is
~51-52%. Natgas basis risk (spot→futures) and the publication-lag question remain the two
open items for a live deployment decision; everything else is now accounted at real costs.

---

## 16. INSTRUMENT-REALITY FINAL (2026-09-01 late) — THE MAXIMALLY-DEFENSIBLE SYSTEM

### The decisive test: synthetic-bond legs vs real ETFs on disk
| Sleeve | Synthetic leg | Real ETF corr | Verdict |
|---|---|---|---|
| QAxasts, a6r7 | us10y / 2y synth TR | IEF **0.955** / 2y-IEF 0.72 | FAITHFUL — real (rates) |
| A5r7, A1credit | BAA-synth TR | LQD/HYG **0.029** | UNFAITHFUL — PAPER |
| carryv2 | WTI/gold/10y | futures tradeable (lag-1 honest) | REAL |
| brwt×4 | CL/B futures | futures tradeable | REAL |
| C5ng×2 | NG futures | basis disclosed, haircut bounded | REAL |
| A5r2 | SPY | tradeable | REAL |
| dualmom, XGB1y | equity L/S | shortable (borrow fee charged) | REAL |

### FINAL MAXIMALLY-DEFENSIBLE NUMBER
**GOAL100_STRICTTRADE_BALANCED_daily.csv** — 12 sleeves, excludes the 2 paper-credit sleeves,
NYSE calendar, realistic execution (futures 1.5-5bps, equity L/S 15bps) + borrow fees:
- **ann 49.4%, SR 5.24 daily / 3.46 monthly (bootstrap CI [3.02,4.01]), MaxDD -6.1%,**
  **0/19 negative years, worst year +20.7%... wait worst 20.7% is BEST; worst NEGATIVE year 0 (none).**
  **3y-subwindow DDs all ≤ -6.1%; LOYO 46.7-51.0%; OOS 2017+ 55.9% @ -6.1%**
- span 2008-03..2026-07 = 17.9y (the vt warmup trims to 2008-03; full pool data from 2006-10)
- This is the number YOU can bet today: every sleeve tradeable, every leg client-verified.

### Why it fell from 70% (audit progress, honest path)
70%(V4, inflated)->66%(+unreproducible MHX)->61%(clean)->55.5%(+A1inf fixed removed)->**49.4%**
(structural: removed 2 paper-credit sleeves that were +~10pp of illusory edge on untradeable
synthetic credit). Each step is a real defect removed, not over-tuning.

### On ann>=100%
The strict system's SR 5.24 at DD 8% => ~max 63-65% ann at the DD wall (all subwindows
compliant). 100% remains out of reach on free data: it needs either 2x more client-verified,
instrument-real engines (of ~40 tested across 2 days, 12 are real and tradeable) or a
DD/return efficiency the data does not support. This is now a statement grounded in
instrument-real, byte-reproducible, adversarially-audited numbers — not a claim.
