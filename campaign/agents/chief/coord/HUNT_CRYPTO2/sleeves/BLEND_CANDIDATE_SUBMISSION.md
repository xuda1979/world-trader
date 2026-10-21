BLEND_CANDIDATE_SUBMISSION — HUNT_CRYPTO2 -> HUNT_VOL2 blend lane (round 3, 2026-09-07)
========================================================================================
candidate:    CRYPTO_VolX_10-30_EW12_audit (crypto VOL-SCALED weekly crossover 10/30, EW-12 basket)
csv:          campaign/agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_10-30_EW12_audit.csv
csv sha256:   36e15c356755a741bbcf56b31d36b5c9434120b15be22c7cfa118920e86a16cd
provenance:   AS-IS from round 1 (NO re-fit; sha-identical to work_r3/sleeves_r1_snapshot/).
              Reproducer: campaign/scripts/HUNT_CRYPTO2_round1.py; meta in .csv.meta
              (cost=6.4bps_full_dW + borrow0.5% + margin4.5%(gross-1), vt=10% trailing
              clip3, T+1; caveat binance_perp_funding_not_modeled).

HONEST OWN-SPAN STATS (recomputed THIS session from the CSV alone by
campaign/agents/chief/coord/HUNT_CRYPTO2/work_r3/r3lib.py — independent
re-implementation, not bt.*; pinned by work_r3/test_r3_verify.py):
  n=3272  span 2017-09-19..2026-09-03
  SR      = 0.910           (FAILS the campaign SR>=1.0 champion gate — submitted anyway
                             per charter b2: "it may die in HUNT_VOL2's gates - fine")
  ann     = 11.32% geo (11.52% arith), vol 12.7%
  halves  = H1 1.35 / H2 0.24          -> FAIL halves (H2<0.5); decay = adoption drift
  negyr   = 2/10, worst year -2.54%    -> PASSES yearly gate
  MDD     = -22.6%
  corr vs HEAD champion (git blob, SR 3.2964) = -0.0263  -> PASSES |corr|<0.15
  yearly: 2017 +63.5 | 2018 +8.9 | 2019 +9.7 | 2020 +18.7 | 2021 +52.3 | 2022 +3.2 |
          2023 -0.5 | 2024 +5.6 | 2025 +7.9 | 2026 -2.5

MEASURED BLEND FACTS (already computed by HUNT_VOL2 round 3 on this exact CSV,
work_r3/blend_table.csv rows CRX1030; restated here for the submission record):
  best dSR +0.149 at w=0.15 (SURVIVES their 200-null adversarial control, frac_pos 0.000)
  but dAnn NEGATIVE at every rung (best -0.77pp at w=0.025) -> FAILS their dAnn gate
  dH2 negative at every rung (-0.003..-0.072) -> FAILS both-halves
  +10%/yr perp-funding stress = -5.28pp ann on sleeve notional (their honest disclosure)
  => VERDICT at their gates: DIES (as charter anticipated).

submission_status: SUBMITTED_AS_IS  (verdict at my gates R1: FAIL_SR|FAIL_HALVES;
                                    verdict at HUNT_VOL2 blend gates: FAIL_DANN|FAIL_DHALVES)
