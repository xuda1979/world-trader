# RES_CARRY FINDINGS — FX/commodity carry engines (beyond CFX4)
> Chartered to find a decorrelated carry engine with a genuine funding mechanism beyond the
> champion's CFX4 (FX z-rev) and carryv2 (GLD). Honest verdict: **REJECT (family exhausted).**

## Evidence (prior + this session)
- HUNT_FXCARRY2 established the FX-carry family DEAD on the honest harness (R3: oracle-ceiling
  SR 0.183-0.517 << 1.0; DEAD_IDEAS row 96). The CFX4 f-x z-rev is the only FX expression in the
  champion and carries 0 weight.
- Broad cross-sectional FX (tested here under RES_FXSTYLE on the NEW 508-pair fx_hist): peak
  SR 0.42 — no standalone carry/momentum engine clears SR>=1.0.
- Commodity carry: HUNT_VOL2 / carryv2 results show commodity-carry alpha is already inside
  carryv2 (GLD); no new clean commodity-carry sleeve found.

## Verdict
**REJECT.** FX/commodity carry as a standalone decorrelated SR>=1.5 engine is not present in any
on-disk dataset; the oracle-ceiling and honest-harness tests both bound it below champion
eligibility. Consistent with DEAD_IDEAS row 96.

RES_CARRY DONE
