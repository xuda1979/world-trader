# CHARTER: HUNT_H1_TAILFACTOR — pre-registered hunt round on the live H1 tail-factor panel

## Why
The H1 option-tail state-estimation deliverable (campaign/agents/H1_optiontail_results/,
verdict PASS as STATE-ESTIMATION, explicitly NOT a backtest) now accrues a LIVE panel:
`tools/quant/data/cboe_options/H1_tailfactor_panel.csv` — 114 data rows (header +
114), columns `date,symbol,p20_30d,var95,var99,skew,kurt`, 9 symbols
(AAPL, GLD, IWM, MSFT, NVDA, QQQ, SPY, TLT, TSLA), first archived day 2026-09-08,
panel current through 2026-10-16, scheduler healthy (campaign/logs/h1_status.json:
last_run 2026-10-17T18:20:08, consecutive_failures 0). ~13 accrued trading days
exist and ZERO evaluation has been done on them. This is the methodologically ideal
moment to SEAL the evaluation protocol BEFORE any forward-return outcome data is
inspected — the panel is outcome-blind as of charter signing.

Differentiation from dead ideas (frontier-closure legality, GATES_CONTRACT_V2
ratified 2026-09-08/09):
- DEAD_IDEAS row 58 / HUNT_VOL2 (167 variants): VVIX/SKEW/VIX-TS/GVZ/OVX INDEX-level
  vol-surface gates. The H1 panel is NOT an index statistic — it is a per-symbol,
  SVI-slice-implied RISK-NEUTRAL DENSITY product (p20_30d = P^Q(S_T < 0.8·S₀) from
  the fitted pdf, var95/var99 quantiles, skew/kurt moments of X=ln(S_T/S₀)). The
  measured object (cross-sectional dispersion and dynamics of tail-pricing state
  per UNDERLYING) was never tested in HUNT_VOL2, which had no per-asset implied
  density at all.
- HUNT_CBOE_IV R8 C1/C2/C3 (all REJECT, work_r8/FINDINGS_R8.md): CBOE INDEX
  statistics (VIX-family term structure, VRP, cross-asset implied-vol dispersion).
  None used option-implied densities of individual equities/ETFs; none had p20/var/
  skew/kurt of the risk-neutral distribution as inputs. R8's dead corners do not
  cover this panel's information set.
- Row 23 / HUNT_VOLOVERLAY, row 44 / HUNT_VXV_TERM: champion-overlay vol timing from
  index-level series — again no per-symbol density state.

## Scope
1. THIS CHARTER IS THE PRE-REGISTRATION. It is written and committed BEFORE any
   forward-return of any panel symbol is computed against any panel factor value.
   The ~13 accrued days are quarantined under §9b (see Non-goals) — no gate
   evaluation on the fragment, ever.
2. Evaluation window is FORWARD: the hunt may only evaluate once the panel accrues
   the pre-committed minimum span below. The accrued 2026-09-08..2026-10-16 fragment
   will be used ONLY for data-integrity diagnostics (row counts, hole detection,
   value sanity), never for return measurement or gate decisions.
3. Pre-committed minimum span: **no gate evaluation until ≥ 60 panel trading dates
   (post 2026-09-08) AND ≥ 3 distinct calendar months have accrued.** Until then the
   round reports PROTOCOL-HOLD. Grounding: GATES_CONTRACT_V2 §9b — materially-short
   spans are judged as such (unjudgeable, fail closed); ~13 accrued trading dates is
   materially short by any reading, so the fragment is quarantined and this charter
   sets a CONCRETE 60-date floor (stricter than the contract, which charters may do)
   so "long enough" is not adjudicated post-hoc after results are seen.
4. Candidate signal constructions from the 6 factor columns (transform registry,
   per GATES_CONTRACT_V2 §8-style pre-commit; the grid below is EXHAUSTIVE — any
   variant tried later that is not in the grid is a PROTOCOL VIOLATION, not a result):
   - Per-symbol transforms: x in {p20_30d, var95, var99, skew, kurt};
     z-scored over trailing L in {21, 63} panel dates; cross-sectional rank
     (9 symbols) of raw and z-scored values.
   - Cross-sectional aggregates: mean and cross-asset DISPERSION (std across 9
     symbols) of each transform; equally-weighted 9-symbol composite of each
     transform (this is the panel's own "index", distinct from CBOE index products).
   - Candidate signals: (a) tail-risk-off gate — composite p20_30d z > threshold
     t in {1.0, 1.5, 2.0} (risk-neutral crash probability elevated → de-risk);
     (b) tail-harvest — negative-exposure variant of (a); (c) dispersion timing —
     cross-asset p20 dispersion z as a regime gate on a long SPY baseline,
     thresholds same set; (d) skew/kurt state gate — composite skew or kurt z
     crossing same thresholds.
   - Pre-committed PRIMARY: (a) with L=63, t=1.5, applied to SPY instrument,
     long/flat, T+1 execution (signal from date T close drives position at T+1).
     All other cells are SECONDARY; the primary is the only cell that can ADOPT
     without a new charter.
5. Evaluation harness: campaign bt (campaign/engines/... per repo convention),
   leak_check=True (bt.leakcheck detects same-day leak; champion control
   corr(dW_t,r_t)=-0.032 → leak=False), cost basis 6bps per full |dW| turnover +
   4.5%/yr margin on (gross−1) + 0.5%/yr borrow on short notional, ann/SR/MaxDD
   exactly per campaign formulas. §9a inception-fail rule applies.
6. Champion of record for benchmarking (do not touch):
   `campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`,
   sha256 a8ed233bd0f6fd5dad4056fda8fbd4cdde10d87ca4886c104c25b93c8014fbf4,
   n=4806, span 2008-03-31..2026-08-28 (machine-generated headline via
   campaign/scripts/champion_card.py: T+1 causal, nav.shift(1) — any memo quoting
   a different headline is VOID). Whitening/correlation gates per GATES_CONTRACT_V2.
7. Deliverables: PRE_REGISTRATION.md (this charter, countersigned per-hunt with any
   numeric grid refinements BEFORE unblinding), work_r1/ engine + coverage audit,
   FINDINGS.md with honest verdicts (ADOPT / REJECT / UNJUDGEABLE / PROTOCOL-HOLD),
   DEAD_IDEAS row text for the coordinator, STANDUP entry.

## Non-goals (hard charter caps)
- NO gate evaluation, return measurement, or PASS/REJECT verdict on the accrued
  2026-09-08..2026-10-16 fragment (~13 trading dates — materially short,
  §9b-unjudgeable, quarantined). PROTOCOL-HOLD is the only allowed status until
  the §Scope-3 minimum span is met.
- NO change to the champion, its weights, manifests of record, LEDGER/LEDGER_AXES,
  or CHAMPION_CARD.md until a candidate passes the full GATES_CONTRACT_V2 gate set.
- NO modification of the H1 pipeline / scheduler / panel file (the panel is the
  INPUT; acquisition continues untouched under campaign/logs/h1_status.json).
- NO deletion of any existing CSV. NO new data acquisition in this round (panel
  extension accrues passively via the existing scheduler).

## Anti-p-hack commitments
- The grid in §Scope-4 is fixed; the WHOLE grid is reported, not just the best cell.
- The ~13-day fragment never gates anything (§Scope-3 quarantine, §9b fail-closed).
- A clean negative is a good result and will be written as such.
- If the panel is unmeasurable for span reasons at evaluation time, the verdict is
  UNJUDGEABLE or PROTOCOL-HOLD, never REJECT and never ADOPT.
- Panel pin at charter signing: sha256
  cae23d09649b1917a77d978e1fbfcac49b52b88961479bdece1a576384339fd1,
  114 data rows, 13 dates, 9 symbols. Any pre-unblinding panel mutation beyond
  scheduled accrual is a protocol violation.

Charter sealed (pre-outcome): HUNT_H1_TAILFACTOR, R1, 2026-10-17.
