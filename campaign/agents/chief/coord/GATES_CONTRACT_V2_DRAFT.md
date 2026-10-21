# GATES_CONTRACT v2 — DRAFT (ADDITIVE) — AUDIT_GATES2 R3 2026-09-07

> **SUPERSEDE BANNER (2026-09-08, AUDIT_GATES2 R5, insert-only):** this DRAFT is
> superseded by `GATES_CONTRACT_V2.md` (RATIFIED 2026-09-08 03:1x CST) AND the Step-2
> flip has since EXECUTED (commit `539f50e`, leak_check DEFAULT-ON). Its line-14 phrase
> "opt-in flag pending ratification" is double-stale: ratification happened AND the
> default is now ON. Read this file as history only; never cite its gate states.

STATUS: DRAFT for coordinator ratification. Nothing here removes or weakens v1
(`GATES_CONTRACT.md`, which stays in force); sections 6-9 are ADDITIVE requirements and
every threshold cites campaign evidence that post-dates v1. Cross-refs: AUDIT_GATES2
FINDINGS R1-R3, `bt/gates.py`, `bt/leakcheck.py`, `bt/beats_passive.py`, `bt/blend.py`,
`bt/verify_champion.py`, DEAD_IDEAS.csv (107 rows).
R3 re-audit (AUDIT_GATES2, 2026-09-07 16:xx): every section's numbers reproduced or
corrected from the live tree — 6b now states the implemented leakcheck thresholds;
7's near-miss count corrected 8/15 -> 9/15 (full-tree sweep, r3c_full_results.json);
6a's activation condition is MET (bt.leakcheck.py exists; gates.run leak_check=True
wired, opt-in, fail-closed incl. sig=None per AUDIT_FWBUGS R3).

## 6. Mandatory leak-probe (`bt.leakcheck` exists — ACTIVE, opt-in flag pending ratification)

v1 item 1 (T+1/no-lookahead) is PROCEDURAL today: `gates.run()` does not certify it.
AUDIT_GATES2 R2 probe C — a `sig=sign(r)` contemporaneously-coupled book scores SR 20.85
with scramble p=0.000 and composite **pass=True** — proves the scramble certifies signal↔return
coupling, NOT T+1 alignment. The champion's own history shows the damage real leaks do:
the pre-AUDIT_CHAMP2 re-emit had corr(dW_t, r_t) = **0.78** (same-day leak, +0.99pp ann
phantom); the causal fix (nav.shift(1)) reads **−0.0120** on the same statistic.

- 6a. `bt.leakcheck` NOW EXISTS (AUDIT_FWBUGS R3): EVERY sleeve/blend submission MUST call
  `gates.run(..., leak_check=True, sig=...)` (or `bt.leakcheck.leak_probe` directly for a
  blend's wide weight frame) and publish the output in the .meta. Until ratification, keep
  the per-agent prefix-no-lookahead harness test as a second line of defense.
- 6b. Fail thresholds (fail-closed) as implemented in `bt.leakcheck` (MIN_ABS_CORR=0.20 +
  Fisher p<0.05 + lag-0-is-argmax of the lag scan; calibrated leaky=+0.789 vs causal
  -0.032 on the real champion — long panels make a tiny significant corr fire a bare
  threshold, so effect size AND peak-lag are required). Real-data pin: committed champion
  corr(dW_t, r_t) = -0.032, archived leak vintage +0.78, both detected correctly by
  AUDIT_FWBUGS-R3 tests. Same-day weight sensitivity: zeroing r_t must not move W_t
  (`verify_champion` truncation-probe semantics, TRUNC_TOL 1e-15).
- 6c. Extra-lag stability: re-run at extra lag 0..3 — metrics degrade GRACEFULLY (no cliff).
  Positive precedent: MACRO2 VIXsus21|T10Y2Y overlay dMDD +1.385/+2.330/+1.817/+2.540pp at
  lags 0-3. A metric that collapses at lag 1 is a timing artifact, not a signal.
- 6d. Never cite `gates.run(...)['pass']` as T+1 evidence (it is not; see 6a probe C).

## 7. Mandatory beats-passive (v1 item 3a is necessary but not sufficient)

Implemented in `bt/beats_passive.py`, opt-in today: `gates.run(..., beats_passive=True,
spy=..., ief=..., cta=...)` ANDs it into the composite. A sleeve whose whole complexity
loses to NOT TRADING on its own span is not champion-eligible:
- R2 INTL RS252_LS: SR 0.564 passed halves/yearly/decorrelation, but SPY B&H on the same
  span = **0.73** → the rotation bought nothing (beta, not alpha).
- R3c near-miss sweep: 9/15 library sleeves with SR 0.53-0.70 FAIL beats_passive on their
  own span (`candidate_sr_le_passive`: 8 of the inherited 11, plus COMP_invvol; A11 0.679
  vs SPY 0.754, INTL 0.564 vs 60/40 0.741, A_rs_ratio 0.534 vs 0.578) — the SR>=1.0 gate
  alone would have let a 0.65 book through without this check on shorter spans.
- 7a. Candidate net SR must EXCEED the best of {spy_bh, sixty_forty, cta_trend} computed on
  the CANDIDATE's matched span at campaign costs (ties fail; unmeasurable benchmarks fail
  closed; MIN_OBS=60 and >=50% span coverage enforced in-module).
- 7b. Publish the per-benchmark SRs in the .meta (module returns them; no extra work).
- 7c. Passive-benchmark data is a shared dependency (twelvedata SPY, more_etf IEF,
  sleeve_library CTA_15vol) — keep those three files pinned; if one is re-fetched,
  re-run the gate on open submissions.

## 8. Champion-BLEND gate (overlays and w<=15% NAV sleeves)

For any candidate submitted as an overlay/addition to the committed champion (not a
standalone sleeve), ALL of:

- 8a. Blend yearly: **0 negative years** on the blended book (champion bar, not the
  contract-d bar; `verify_champion.checks.yearly` semantics).
- 8b. Blend MDD: **> −7%** (goal line; report dMDD vs current champion).
- 8c. Blend dAnn > 0 (HARD). Evidence this bites: HUNT_VOL2-R3 blend lane — of 6 published
  decorrelated sleeves, **0/6 had dAnn>0 at any w** (best −0.69pp at w=2.5%); CRYPTO2-R3:
  dSR +0.149 real for 4/6 books but dAnn negative at every rung (best −0.77pp) → fail-closed
  on the ann arm, correctly.
- 8d. Blend dSR >= 0 AND dH2 (second-half delta) >= 0. dH2 evidence: CRYPTO2-R3 blend dH2
  negative at every rung (−0.003..−0.072) — diversification that borrows from the future
  half is not adoption-grade.
- 8e. Blend gross <= 1.6 (leverage/cost gate unchanged, full |dW| @ 6.4bps one-side).
- 8f. Halves-consistency of the DELTA: the improvement must not be single-half luck
  (report dSR_H1 and dSR_H2 separately).
- 8g. w-plateau: the accepted w must sit on a plateau across the rung grid (e.g. w ∈
  {2.5,5,7.5,10,12.5,15}%: dAnn(dSR) not a single-point spike; plateau_ok logic applies to
  the rung grid, not a price-grid). Relever-to-cap variants need the same ladder disclosure
  (CRYPTO2-R3: 0/5 relever rungs passed).
- 8h. Vol/corr-matched placebo (anti-diversification-artifact): a matched null — random
  sleeve with the same vol and same corr-to-champion, 200 draws — must NOT reproduce the
  claimed delta. Evidence: VOL2-R3 dSR "+0.149 real for 4/6" was 2/6 pure diversification
  artifact (frac_pos=1.000); SECTOR2-R3 A11 dSR +0.141@15% was "100% reproduced by matched
  nulls". A delta the placebo reproduces is arithmetic, not alpha.
- 8i. **Single-episode exclusion test on dMDD** (coordinator precedent, STANDUP_LOG
  2026-09-07 04:xx): recompute dMDD excluding the dominant dd episode window; relief must
  stay >= +0.5pp. T10Y2Y overlay: +1.161pp full → **+0.319pp excl 2018-05..07** (72%
  one-episode lottery) → REJECTED. JOINT overlay: +1.495 → +0.653 (broad-based, kept alive
  on the test but not adopted on the ann trade-off). Crypto dMDD passers died the same way
  (0/38 pass excl 2018-06).
- 8j. Correlation expectations differ by lane: the 0.15/0.35 decorrelation gate (v1 3f) is
  for NEW sleeves. A champion overlay will legitimately read corr 0.94-0.98 (MACRO2 JOINT
  overlay: 0.9839; CRYPTO2 overlay: 0.9465) — for overlays, report corr but do not fail on
  it; the blend gates 8a-8i are the acceptance path. Do NOT file corr_ok=False as the
  rejection reason for an overlay (and do not accept one for lacking it).

## 9. span_class discipline (data admission is part of gate honesty)

Implemented in DATA_ETF_MORE `work_r3/manifest_r3.py` (+ `retest_r3.classify`); every
post-R2 data unlock is admitted under the coordinator 2007-waiver with per-file disclosure.

- 9a. Every new data series carries `span_class ∈ {pre2007, 2007plus, inception_fail}`
  (bounds: 2007-01-01 / 2013-01-01) in its manifest row, and every sleeve built on it
  states the class in its .meta. inception_fail series are NOT hunt-eligible.
- 9b. A sleeve whose evaluable span is materially shorter than the charter intent (~19y)
  must be judged as such (disclose n + span; "unjudgeable" is a valid fail verdict —
  CREDIT2-R3 EM-HY OAS: n=753 from 2023-09, still failed closed).
- 9c. 2007-waiver series may support satellite/blend evidence but a champion-eligible NEW
  sleeve must demonstrate its gate battery on >= its own admitted span with the span_class
  printed next to every gate number in the .meta (no mixing spans silently between rows
  of a results table).
- 9d. Data revisions rotate results (CMDT2-R3: GLD history extension 2006-10→2004-11
  rotated hold-3 rebalance phase, SR 0.35→0.17): a sleeve's .meta pins the manifest vintage
  (sha or mtime) of every price file it consumed.

## 10. Artifact verifiability (audit requirement, R3c finding)

- 10a. Every .meta gate number must be reproducible from published artifacts. R3c sweep:
  13/15 near-miss metas cite a scramble p-value that CANNOT be recomputed because
  positions were never published (sleeve CSVs are [date,ret] only). Either publish
  positions (or the signal series) alongside the sleeve, or mark scramble claims
  "agent-run, not artifact-verifiable".
- 10b. Champion-vintage pinning: corr_to_champion is vintage-sensitive (R3c full sweep,
  git-reconstructed pre-costfix vintage sha e6d8b9c0 SR 3.2964 vs current 4358dfab SR
  3.1810: the re-emit moved ALL 15/15 measured corrs, max |old-new| = 0.0042). Metas must
  name the champion file + sha prefix used. None of the 13 corr-bearing near-miss metas
  was a mis-statement — all 13 matched the pre-costfix champion within ±0.0020 (tol
  0.0055) — but the audit could only prove that by reconstructing the old vintage from
  git. Pin it going forward.
- 10c. Scale lock: metas using the retired SR>=0.6 scale (e.g. SEC3 "SR 0.667 (>=0.6 PASS)")
  must be re-labeled when re-read: that CSV is also the known 3.0bps/side undercharged
  vintage (honest 6.4bps ⇒ 0.18-0.26). The contract scale is SR >= 1.0.

## 11. Composition-preserving scramble = DIAGNOSTIC, never a gate

`r3/r3b_composition_scramble.py` (this round): alpha-preserving common-lag of the weight
matrix. Calibrated on the current champion (SR 3.1810, byte-repro dev < 1e-12): p=**0.775**
(real 3.181 vs null 3.248±0.072) — consistent with R2's 0.83 reading on the pre-costfix
vintage; NOT flagged. 200 static-composition noise books: flag rate **9/200 = 4.5%**
(nominal). DETECT fixture (trailing-momentum composition on 13 persistent-alpha slots,
phi=0.99/alpha 0.30): real 8.10 vs null −0.398, p=**0.010** DETECTED; static-weight control
on the same slots p=1.000 (not flagged) — the diagnostic isolates COMPOSITION TIMING.
Per-slot independent lags are documented as a NEGATIVE result (champion p degenerates to
1.000; null vol 0.00377 vs real 0.00636 — it probes cross-slot SYNCHRONY, not timing, and
must not be used as a "composition" scramble on correlated-slot books). It stays OUT of
`gates.run` by design: the champion is a composition book and would fail a gate it should
not be judged by; use it to UNDERSTAND a candidate's timing source, not to accept/reject.
