#!/bin/bash
# Canonical verify_champion.py invocation for the COMMITTED champion of record.
# ITER20 (2026-09-18, operator objective Sharpe-max s.t. ann>=20% & gross<=1.6): the
# champion family is the minsharpe fit at shrink 0.70 THROUGH the brwt-block relw-share
# cap 0.30 (pro-rata redistribution; CFX4 pinned 0) -> --shrink 0.70 --brwt-cap 0.30.
# ITER49 (2026-09-19, session 29): third adoption - tsmom (QAxasts) harness vol-target vt=0.15
# (8/8 gates, G7 4/5 positive bins min -0.0092, FS SR 3.820357 = +0.0363) became the champion of
# record (canonical pair; canonical-vs-driver relw gap 3.249e-09 = the SLSQP landing class, disclosed).
# Prior pair (3c456aa53193eb89 / 8313bee1ad8a72fe) preserved under coord/ITER49_TSMOM_VT/
# prior_champion_backup/. Anti-dog-chase binding: LAST seal on the tsmom family (precommit
# dbf5406f3e40f356); the still-rising 0.15 grid edge is recorded, NOT chased.
# ITER47 (2026-09-19, session 27): second adoption - A5r2 VT upper-edge extension argmax VT=0.24
# (8/8 gates, G7 5/5 positive bins min +0.0111, FS SR 3.784099) became the champion of record
# (precommit 2aafd014c7521ebe; canonical pair weights_repro 8.327e-17). Prior pair (e67446186e269b88 /
# bde8612d0b295068) preserved under coord/ITER47_A5R2_VTEXT/prior_champion_backup/. Anti-dog-chase
# binding: LAST seal on the A5r2-VT family.
# ITER43 (2026-09-19, session 23): first adoption since ITER21 - the A5r2 VT-axis
# argmax (VT=0.15, 8/8 sealed gates + independent 7/7 gauntlet on the canonical pair)
# became the champion of record (sha16 e67446186e269b88 / weights bde8612d0b295068).
# The A5r2 canonical sleeve is now the vt015 variant (sha16 901eebdd3abef617, provenance
# in its .meta); --is-end 2017-01-01 pinned explicitly (inference is exact for the
# canonical weights but explicit is deterministic). Prior champion (8559fa55ee9a3417 /
# d2d11c92a98683df) preserved under coord/ITER43_A5R2_VT/prior_champion_backup/.
# D16 (2026-09-19, coordinator): the ITER21 gear swap moved the canonical GEAR to 1.0
# and this script went stale on the verifier DEFAULT_GEAR=1.6 -> the gauntlet failed-
# closed against the live champion (byte_repro/cost/causality/gross RED). --gear 1.0
# added; pinned to the builder canonical constants by
# campaign/bt/tests/test_verify_r3_cmd_canonical_pin.py (knobs must equal B.GEAR /
# B.SHRINK_D / B.W_BRWT_CAP, so the NEXT swap trips the test, not the record).
# ITER19 history (2026-09-13, operator-approved; pinned by test_iter19_prune_brwt15.py): brwt15 was
# PRUNED from the brwt block -> the champion is now a 12-sleeve pool. This sleeve map mirrors
# rawew13v2_build.PATHS EXACTLY (A5r2 lives under campaign/agents/A5_vol_cond; the older
# HUNT_BASIS1 path no longer exists). Supplying fewer than all 12 rows fails closed with
# "missing sleeve input(s) for weights rows". --rule minsharpe = the ITER15/ITER19 champion
# weight rule, named explicitly. Usage: bash verify_champion_r3_cmd.sh [out.json]
set -e
ROOT="/Users/daxu/software/world-trader"
OUT="${1:-$ROOT/campaign/agents/chief/coord/verify_champion_r3_last.json}"
exec python3 "$ROOT/campaign/bt/verify_champion.py" \
  --champion "$ROOT/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv" \
  --weights "$ROOT/campaign/results/RAWEW13v2_IS_SR_weights.csv" \
  --rule minsharpe \
  --shrink 0.70 \
  --brwt-cap 0.30 \
  --ng-cap 0.28 \
  --vintage-end 2026-08-28 \
  --c5ngsum-trunc 2026-08-24 \
  --gear 1.0 \
  --is-end 2017-01-01 \
  --sleeve brwt10="$ROOT/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv" \
  --sleeve brwt7="$ROOT/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv" \
  --sleeve brwt5="$ROOT/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv" \
  --sleeve C5ng="$ROOT/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv" \
  --sleeve C5ngsum="$ROOT/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv" \
  --sleeve A5r2="$ROOT/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock__vt024.csv" \
  --sleeve a6r7="$ROOT/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv" \
  --sleeve QAxasts="$ROOT/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv" \
  --sleeve carryv2="$ROOT/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv" \
  --sleeve dualmom="$ROOT/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv" \
  --sleeve diescrack="$ROOT/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv" \
  --sleeve CFX4="$ROOT/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv" \
  --json "$OUT"
