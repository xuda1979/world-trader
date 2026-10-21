# HUNT_CIT_AG — FINDINGS (iter8, 2026-09-03) — NEW-DATA HUNT #1

**VERDICT: NEGATIVE — no champion-eligible engine. Best economically-coherent variant
(lean_hogs noncomm z -> DBA/MOO family cluster) tops out at SR 0.18-0.21 with 5-8 neg years.
The screen's single SR>=0.6 row (lean_hogs noncomm -> SOYB, 0.705) is a CROSS-COMPLEX ARTIFACT:
hog positioning has no economic claim on soybean prices; it collapses under coherent mapping
(SR 0.24 on DBA, 0.21 on MOO) and fails yearly gates everywhere (3 neg yrs own-span, worst
-7.4%; fails 0-neg bar). PCPS spot-momentum tops at 0.465 (soy 21d) — below the 0.6 bar with
6 neg years. Nothing reaches even the near-miss bar.**

## TDD
- tests/test_cit_ag.py written FIRST, observed 5 FAILED (module missing). cit_ag.py -> 5 GREEN.
- Fixture-bug fixes only (signal semantics locked: hysteresis exit without same-row flip;
  cot_lag = index-shift preserving values). bt framework regression: 28 passed (untouched).

## Data honesty
- NEW ETF tradables acquired (twelvedata, 5000-bar): DBA(2007+) CORN(2010+) WEAT/SOYB/CANE(2011+)
  MOO(2007+) QQQ/DIA(2006+) UUP(2007+) — fail-closed lint (dupes=0, maxgap<=5d, closes>0).
  EWA deduped (vendor dual-vintage artifact, 3 material conflicts <=1e-2, keep-last).
  COW/NIB/BAL/SUGA/JJA blocked by twelvedata tier (documented).
- Signals: more_cot cit_*.csv (13 NEW CIT series), *_cot.csv noncomm, more_fred P*.csv (PCPS).

## Screen (156 variants, full honesty stack: COT 3d lag + T+1 + 6.4bps + borrow + margin + cap1.6)
- sr>=0.6: 1 (the artifact above) | sr>=0.3: 11 | sr>0: 56/156.
- Coherent-mapping re-test: best = lean_hogs-cit->DBA 0.181 (5 neg). CIT family itself: ALL NEGATIVE
  or sub-0.2 (soybeans-cit->SOYB -0.575; wheat -0.577). CIT long-only-index-flow premise is
  ALREADY PRICED in ETF space — consistent with the CIT program's public, delayed reporting.
- PCPS spot-momentum own-ETF: best PSOYBUSDM/SOYB 21d = 0.465 (6 neg yrs); neighborhood-degenerate.

## Scramble (top artifact variant): p=0.005 real-baseline — passes scramble, FAILS yearly + coherence.
## Param neighborhood (artifact): 0.44..0.58 — no cliff, just uniformly gate-failing.

## Gates scoreboard (all variants)
ann80 NO | SR5 NO | DD7 NO | 1.6x YES(construction) | 0-neg NO

## Decision
DEAD_IDEAS.csv += "CIT/noncomm ags z on ag-ETFs (coherent mapping)", dead,
"best 0.21 SR, 5+ neg yrs; cross-complex 0.705 artifact rejected"; PCPS mom dead at 0.465/6neg.
Do not re-run: ag z-scores entry 1.0-2.0, exit 0-1.0 on DBA/CORN/WEAT/SOYB/CANE/MOO.
HUNT_CIT_AG DONE
