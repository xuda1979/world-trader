> **[ITER20 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER20
> SR-max book: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 36.41% / SR 3.4551 /
> MDD -5.93% / 0 neg years / gross 1.6 exact (sha16 766fc0ce9926d793). Operator objective
> 2026-09-18: Sharpe-max subject to ann>=20% and gross<=1.6; the prior ann-max vintage
> (39.50 / 3.2176, ITER19) is archived byte-exact as archive_*_SUPERSEDED_by_ITER20_srmax.csv.
> Every earlier headline quoted in this document (39.50, 38.11, 37.49, 37.195, 40.84,
> 55.5, 62.4, ...) is SUPERSEDED history kept for provenance — it WAS current once, it is
> not current now.

# GOAL100 PROGRESS REPORT (Round 2 complete) — 2026-09-01

> **[SUPERSEDE BANNER 2026-09-08 — THE "CURRENT champion" ROW BELOW IS STALE.]**
> The 48.2% 16-pool config billed "CURRENT champion" in the table below was the
> champion of record on 2026-09-01 only. The champion of record is now
> GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 37.195% / SR 3.181 / MDD -6.69% /
> 0 neg years (re-verified 2026-09-08 via campaign/bt/verify_champion_r3_cmd.sh, 7/7
> checks ok). Later generations (55.5% V1, 49.4% STRICTTRADE, 37.195% RAW-EW13v2) each
> removed construction defects (hidden leverage, same-day weight leak, half-turn cost
> undercharge); the ann drops are defect removals, not regressions. Current headline +
> lineage: campaign/CHAMPION_CARD.md. This banner is ADDITIVE — every original line
> below is preserved unmodified.
> (2026-09-11, ITER15 weight-rule re-emit ADOPTED): ann 39.50% | SR 3.2176 | MaxDD -6.52% | 0/19 neg years — CURRENT headline, see campaign/CHAMPION_CARD.md.

## Frontier movement
| Config | ann | SR | MaxDD | OOS(2017+) ann/DD | Status |
|---|---|---|---|---|---|
| GOAL80 COORD_FINAL (14 sleeves) | 43.2% | 4.84 | -7.5% | 47.7% / -7.4% | prior champion |
| + C5ng weekday + C5ngsum summer (16-pool, vt0.085) | **48.2%** | 5.13 | **-7.8%** | **52.8% / -7.8%** | CURRENT champion |
| 16-pool at vt0.095 (IS margin rule) | 53.8% | 5.16 | -9.2% | 58.7% / -9.2% | breaches DD cap OOS |
| 16-pool brute (vt0.10) | 56.7% | 5.18 | -9.9% | 62.0% / -9.9% | breaches |

Honest frontier @ MaxDD<=8%: **48.2% ann** (was 43.2% at GOAL80 end). Gap to 100%: 2.1x.

## New validated engines (GOAL100 rounds 1-2)
1. **C5_ng_summer_weekday (SR 2.19)** — natgas Apr-Oct weekday premium (storage-report economics).
   Per-year SR 0.7-4.1 (0 neg), even/odd split 2.04/2.44, weekday-map scramble p=0.015, corr to blend -0.01.
   ddt variant (MaxDD -8.8%) used in blend. C5 NEW-DOMAIN (cash-market calendar).
2. **C5_ng_weekday_prem (SR ~1.0 honest)** — all-year version; weaker but decorrelated (corr -0.02).
3. ~~C2_fly2AB_75~~ — **QUARANTINED round-2**: units bug (pct-pt fret vs decimal costs, 100x cost
   understatement). Honest net SR -2.04. Gross edge real (1.5) but 6bps kills it. Fly family infeasible.

## Coordinator honesty findings
- **gates.py scramble_pval is degenerate** (permuting returns preserves mean/std => p~1.0 always).
  All round-1 gates used signal-perm or calendar-scramble instead. Coordinator audits use
  calendar-scramble (circular shifts of raw input) — the proper test. Documented; agents informed.
- **T+1 lookahead demo**: KF OP/INV spread momentum shows SR 2.3-2.8 WITHOUT shift(1),
  0.1-1.7 with. Every quick test must shift. (Caught in my own sweep too.)
- **a6_r7_bond2y_trend + A1_credit_regime_mom re-audited clean** (decimal units, repro byte-consistent).
- Failed families this session (all honest, exact numbers in agents' FINDINGS): COT positioning (C3:
  0/7, harness bug found+fixed), KF industry mom/rev (C1: best 0.35), level z-reversion, crack
  spreads (MaxDD), EM-FX/broad-dollar momentum, NFCI/STLFSI4 (param spikes), equity calendars,
  rates flies at 6bps (gross 1.5 < costs 7-13%/yr), OP/INV spread momentum (T+1 artifact),
  ML on all domains (C6: no daily directional edge; meta-ML loses to EW OOS).

## Pool health (16 sleeves)
XGB1y is the keystone (drop => -10pp). brwt +3.5pp. A5r2/A5r4 are duplicates (corr 1.0) — kept
(redundant EW smooths the throttle). No other dedup warranted.

## Verdict on GOAL (100% ann @ MaxDD 8%, no leverage)
SR 5.1+ at vt 10.4% vol. 100% ann needs vol ~19% at this SR -> MaxDD ~11-12% (measured DD/vol
~0.62 for this pool). Still short by ~1.8x. Needs ~2x more decorrelated SR>=2 engines
(natgas-calendar-like) — continuing with rounds 3+ on remaining promising domains.
