> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER25 — CREDIT RE-ADJUDICATION (2026-09-19, session #7)

**Operator objective (unchanged, 4th verbatim issue):** keep improving; leverage <= 1.6;
maximize Sharpe; annual return >= 20%.

**Champion of record: UNCHANGED.** ITER21 gear-1.0 book — `GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
sha16 `8559fa55ee9a3417`, weights `d2d11c92a98683df` — ann 23.6054% (CAGR) / SR 3.751429 /
MDD −3.6130% / 0 negative years / gross 1.0 exact. Fresh canonical gauntlet 7/7 this session
(byte-repro 1.0e-16, causality clean, costs 4.03 bp/yr).

## Why this iteration exists (audit finding)

The ITER16 new-engine rejections leaned on gate 8c ("blend dAnn > 0, HARD") — a gate whose
recorded evidence was certified against champions superseded twice since (ann-39.5% era,
then the 1.6-gross pin). The operator's actual constraint is a floor (ann >= 20%), not
zero-dilution. RB_hobr was the only 8c-era reject ever re-adjudicated under the current
objective (#114: died on OOS honesty). The strongest documented 8c-only reject —
**A5_r7_credit_composite** (SR 1.51 standalone, scramble p=0.000, corr-to-library 0.13,
1990-2026 FRED, full .meta provenance) — never was. ITER25 re-adjudicated it under the
current champion with the ITER24-verbatim pool-fit protocol, pre-committed before any
computation (`coord/ITER25_CREDIT_READJ/FINDINGS_PRECOMMIT.md`, sha16 `d176f7cb8f2f11f5`).

## Result: honest negative — blocked by the concentration invariant, not by returns

| quantity | value | verdict |
|---|---|---|
| fit allocation to credit | **19.03%** (largest ever earned by any candidate; bund_02y got 9.93%) | fit WANTS it |
| 13-pool IS-SR | **4.2575** vs incumbent 4.198632 | **PASS** (+0.059) |
| IS-MDD | −2.52% (vs ≥ −6% bar) | PASS |
| IS negative years | 0/9 | PASS |
| **Wmax (max share × 13)** | **2.4745× vs ≤ 2.0×** | **FAIL → NO-ADMISSION** |

Per the sealed stop rule the FS reveal never fired. Champion bytes pre == post (asserted).
The house cap function was re-verified against `rawew13v2_build.apply_brwt_cap` — the
breach is a genuine property of the frozen method (pro-rata redistribution has no
post-clamp), not a driver artifact.

## What this means

1. **The 8c misalignment is real as documentation but moot as selection.** The modern
   selector rejects credit before any return-dilution question arises. Two eras, two
   mechanisms, one verdict — the frontier statement survives adversarial re-audit.
2. **The campaign's binding wall now has a name and a price tag.** The fit wants a
   19% credit allocation worth +0.059 IS-SR, and the only thing between IS and the OOS
   police is the max-share ≤ 2× equal-weight invariant. This is the same wall that closed
   ITER23's grid edges (there: +0.024 FS-SR at the edge). **OPERATOR-DECISION ITEM (no
   action taken, per #109/#116 precedent):** sanction or decline "relax Wmax 2.0×".
   Declining costs nothing; the book stays at its verified corner.
3. **Every admission path is now catalogued by its binding constraint:** EM-FX/energy —
   dead at IS screen (no SR edge, Wmax breach); bund/cad — admitted, died at 5-bin OOS
   (ITER17 law); credit — passes IS-SR/MDD, blocked by the concentration invariant;
   vol complex — not capital-real; seliccary — passed FS-SR + dAnn, died OOS 3/5 bins.

## Scope exclusions (pre-reveal, recorded): H21_fixed (no .meta — fail-closed), VOL2-R3 /
CRYPTO2 (standalone-bar fails independent of 8c), CFX4 (dead vendor artifact), RB_hobr
(already re-adjudicated #114). With those, **the 8c-era rejection ledger is fully
re-adjudicated or affirmed — no standing rejection rests on the misaligned gate alone.**

## Deliverables
- `campaign/agents/chief/coord/ITER25_CREDIT_READJ/`: FINDINGS_PRECOMMIT.md (sealed 02:44,
  before any computation), FINDINGS.md, driver_2026-09-19.py + .log (audit trail),
  candidate_A5r7credit_weights.csv + _daily.csv (for the record only).
- `campaign/bt/tests/test_iter25_credit_readj.py`: 4 reality-pins, mutation-checked
  RED → restored → GREEN (asserts on artifacts, not exit codes).
- Suite after landing: see STANDUP_LOG (expected 499 + 4 = 503 passed).
