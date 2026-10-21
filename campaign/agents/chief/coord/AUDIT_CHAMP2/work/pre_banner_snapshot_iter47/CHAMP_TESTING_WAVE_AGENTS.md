> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
> **[ITER21 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER21
> gear-1.0 book: the SAME committed weights as ITER20 (shrink 0.70 + brwt-cap 0.30, weights
> sha16 d2d11c92a98683df) at canonical gross 1.0 — the margin term (4.5%/yr on gross-1)
> makes net SR strictly decreasing above gear 1, so the SR argmax under the operator's
> gross<=1.6 cap is the de-gear: **ann 23.61% / SR 3.751429 / MDD -3.61% / 0 neg years /
> gross 1.0 exact** (sha16 8559fa55ee9a3417). Objective unchanged: Sharpe-max s.t.
> ann>=20% and gross<=1.6. The prior ITER20 gear-1.6 vintage (36.41% / SR 3.4551, sha16
> 766fc0ce9926d793) is archived byte-exact as
> archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER21_gear10.csv and
> stays reproducible via build(gear=1.6). Every earlier headline quoted below (36.41,
> 39.50, 38.11, 37.49, 37.195, ...) is SUPERSEDED history kept for provenance — it WAS
> current once, it is not current now. See campaign/GOAL100_ITER21_ADOPTION.md.
>
> **[ITER20 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER20
> SR-max book: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 36.41% / SR 3.4551 /
> MDD -5.93% / 0 neg years / gross 1.6 exact (sha16 766fc0ce9926d793). Operator objective
> 2026-09-18: Sharpe-max subject to ann>=20% and gross<=1.6; the prior ann-max vintage
> (39.50 / 3.2176, ITER19) is archived byte-exact as archive_*_SUPERSEDED_by_ITER20_srmax.csv.
> Every earlier headline quoted in this document (39.50, 38.11, 37.49, 37.195, 40.84,
> 55.5, 62.4, ...) is SUPERSEDED history kept for provenance — it WAS current once, it is
> not current now.

# CHAMPION COMPREHENSIVE TESTING WAVE — multi-agent results (2026-09-14)

Coordinator directive: "do comprehensive testing using many agents on the champion again."
Launched 5 autonomous research agents in parallel (campaign/agents/CHAMP_*), each with a fresh,
independent, rigorous mission against the champion of record (RAWEW13v2 WEIGHTED, 12-sleeve).

Champion of record: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann(geo) 39.50% | SR 3.2176 | MaxDD -6.52% | 0/19 neg | capital-real gross EXACTLY 1.6 |
full-|dW|@6.4bps + 2.70%/yr margin | T+1 causal | ITER19 12-sleeve IS-fitted weights.

## Agent 1 — CHAMP_AUDIT_LEAK (adversarial causality re-audit) — **PASS**
- Recompute matches committed to 9.996e-17; gross exactly 1.600000000000 all 4806 days.
- Same-day-leak forensics: pooled corr(dW_t, r_t) = **-0.0100** (full span). DETECTOR POWER
  confirmed: rebuilding the OLD leaked (nav w/o shift) construction gives +0.5902 and +0.94pp
  ann — so a leak WOULD be caught; the committed book shows none. Weakest per-sleeve brwt10
  corr -0.1229 (antipersistent, cost-reducing, NOT leak-signal). CONTROL corr(dW_t, r_{t-1})
  = +0.5903 (NAV-drift correctly chases yesterday, never today).
- Extra-lag probe (+1 day on all sleeves): ann 39.50->39.50%, SR unchanged, MDD unchanged
  (book has no day-level timing to destroy; turnover 4.77bp/yr near-static).
- Zero-run forensics: every interior zero-run is strategy-by-design (band/gates/weekday/
  seasonal/long-flat); NO missing-data zeros (missing = NaN, dropped).
- VERDICT: PASS — the champion is causally clean.

## Agent 2 — CHAMP_AUDIT_METRICS (statistical robustness) — **PASS**
- Block-bootstrap SR (3000 draws, 12m blocks): SR 3.2176, 95% CI **[2.757, 3.942]**,
  P(SR<2.0)=0.0000; CI lower bound above the prior generation's upper (2.53). Robust.
- Sub-windows all pass: 2008-15 SR 3.33, 2016-19 SR 4.49, 2020-23 SR 2.45, 2024-26 SR 3.45.
- 0 negative years / 19 (worst 2013 +5.62%); worst 252d rolling +0.92% (2014); worst month
  -2.46% (2022-08). Leverage/cost audit: gross exactly 1.6, margin 2.70%/yr, turnover
  4.766bp/yr; all honest.
- SKEPTIC FLAG: SR NOT tail-carried (dropping top-20 days RAISES SR to 3.44); but the brwt
  complex holds median 78% of gross (one Brent-WTI reversion expressed ~3x), effective
  #sleeves ~4.4 -> real concentration risk to monitor (capacity/regime).
- NOTE (convention): arithmetic-ann is 33.85%; geometric (the champion's stated convention)
  is 39.50%. Both honest; SR 3.22 identical.

## Agent 3 — CHAMP_HUNT_CONSTRUCTION (spec + weight refinement) — **PASS / no in-spec gain**
- SPEC-COMPLIANCE PASS: gross 1.600000000000 (0 overshoot), MaxDD -6.52% >= -7% wall, 0 neg
  yrs, full-|dW| cost reconstruction exact (0.0 err), IS-only weights (OOS-perturbation
  leaves relw bit-identical -> no OOS leak), T+1 causal (mid-date perturb leaves prior
  weights bit-identical).
- WEIGHT-SENSITIVITY (shrink_d 0.90/0.95/0.98/0.995, all IS-only<2017): OOS ann spread ONLY
  0.05pp; NO variant materially improves. Committed 0.98 fit = in-spec optimum confirmed.
- COST-HONESTY: clean. Per-gross returns: energy core (brwt,C5ng,C5ngsum,A5r2,diescrack;
  1.52/1.6 gross) ~21.8%/yr per gross; decorrelated adds (QAxasts,dualmom,a6r7,carryv2;
  0.081 gross) ~7%/yr per gross. Confirms the frontier gap.
- VERDICT: champion at the in-spec construction optimum; no weight improvement available.

## Agent 4 — CHAMP_DATA_FRESH (freshness/coverage/regression) — **fresh+warn**
- REGRESSION: build still IDENTICAL (9.996e-17); disk self-consistent. GOV NOTE: disk holds
  ITER19 12-sleeve champion but git HEAD still has ITER15 13-sleeve (uncommitted) ->
  coordinator should COMMIT the current disk state.
- FRESHNESS: every sleeve's last row is 2026-08-03..08-28 vs 2026-09-12 (gap 15-40d).
  81% of relw (brwt 51% + C5ng 21% + diescrack 9%) is extendable on-disk to 2026-09-01;
  16.5% at its on-disk bound; CFX4 absent/unrefreshable (held at 0 anyway).
- Coverage: all sleeves except CFX4 have ample <2017 rows for the IS fit. Zeros are design.
- VERDICT: freshness refresh is possible on-disk (small, +2-6 td tail) — worth a follow-up
  but historically moves the champion only ~0.05pp. No coverage threat to the champion.

## Agent 5 — CHAMP_HUNT_FUND (new decorrelated equity-quality engine) — **REJECT**
Built the honest T+1 cross-sectional equity-quality long-short sleeve (ROE+ROOA rank at month
M -> earn TOP-minus-BOTTOM quintile spread of next-month return, shift-1, no same-month leak):
ann 27.95%, monthly SR 0.92, stable halves (29.7%/26.2%), corr to champion 0.020. BUT at the
dAnn>0 adoption gate it DILUTES: blend 5/10/15% gives dAnn -0.61/-1.26/-1.95pp (champion 44.95%
-> 44.34/43.69/43.00%). per-gross IR ~0.92 << energy core. REJECTED with numbers -
the one untested family does not raise the champion.

## COORDINATOR SYNTHESIS — ALL 5 AGENTS COMPLETE
The champion (ann 39.50% geo / SR 3.22 / MaxDD -6.52% / 0-neg / gross exactly 1.6) survives
EVERY independent, adversarial audit in this wave:
1. **Causally clean** (Agent 1): corr(dW_t,r_t) = -0.0100 pooled; leak-detector power proven
   (+0.59 on a deliberately leaked book); extra-lag invariant; zero-runs are all design.
2. **Statistically robust** (Agent 2): bootstrap CI [2.76, 3.94], P(SR<2)=0; all sub-windows;
   0/19 neg years; costs/leverage honestly and exactly charged.
3. **In-spec optimal on weights** (Agent 3): shrink_d grid OOS spread only 0.05pp; no material
   improvement; IS-only + T+1 causal bit-level proven.
4. **Data-fresh-with-governance-note** (Agent 4): build IDENTICAL; 81% of weight is on-disk
   refreshable by +2-6 td (small, historically ~0.05pp); MUST COMMIT the current ITER19 disk
   state (git HEAD still ITER15).
5. **No new engine** (Agent 5): the one untested family (equity-quality) is REJECTED at the
   dAnn>0 gate (dilutes ann -0.6 to -2.0pp); corr 0.02 but per-gross IR too low.
CONCLUSION: the champion is robustly at the honest frontier. Rigorous leverage (1.6 capital-real,
exactly) and MaxDD (-7% wall) are spec-fixed. The one UNTESTED-until-now lever (#1: PIT-clean
cross-sectional equity quality/profitability) has now been tested with the real 503-stock SEC EDGAR
XBRL PIT cache (filed-date as-of, 2010-2026) — and REJECTED: the PIT-clean quality/margin premium
is negative or SR<=0.66, no adoption. The remaining legitimate follow-ups are (a) refresh the
extensible 81% of weight on-disk by a few trading days (small), and (b) commit the current disk
champion to version control (governance). No in-spec data/strategy/weight lever raises ann
significantly in a way that clears the dAnn>0 gate at the fixed rigorous 1.6 leverage.
