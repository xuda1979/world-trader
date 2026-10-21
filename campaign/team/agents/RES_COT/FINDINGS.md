# RES_COT FINDINGS — COT positioning as a champion-improvement lever (honest, numbers-backed)
> Date: 2026-09-09. Verdict: honest **REJECT** as a standalone champion sleeve — but the data
> family is now **correctly built** into the engine (fixes + canonical panel + TDD), and the
> finding itself pinpoints WHY (data-coverage + standalone-SR constraint, not decorrelation).

## Bottom line
The COT (Commitments of Traders) positioning family — the project's top-ranked "new uncorrelated
data" candidate — is **genuinely decorrelated** to the champion (|corr| <= 0.08 across all 60
grid configs) and its engine is **causally clean** (leak gate PASS on every config). BUT no
configuration clears the champion-eligible **SR >= 1.0** bar. Consistent with the project's
repeated finding: the binding constraint is **standalone SR>2 edge in a new economic family**,
not decorrelation. COT is not that edge.

## What was built (comprehensive data-engine work)
| artifact | file | purpose |
|---|---|---|
| Canonical COT→price panel | `cot_panel.py` | 33-market daily tradeable price panel + coverage MANIFEST |
| Fix: silent missing-proxy defect | `cot_panel.py` | sp500_emini/nasdaq_emini had BLANK px (lookups missed twelvedata/SPY, more_etf/QQQ); FX used wrong src; now override-resolved + FAIL-LOUD |
| Honest COT engine | `cot_engine.py` | gate-native: single sig on EW basket; causal COT-release timing; full-|dW| 6.4bps + 0.5%/yr borrow |
| TDD suite (7 tests) | `test_res_cot.py` | no-interior-null, sane ranges, causal-contract invariant, costs, honest-verdict pin |

## Data-coverage correction (was WRONG in DATA_COVERAGE.md)
The clean `more_cot` panel (`<mkt>_cot.csv`, cols date/net_noncomm/net_noncomm_pct_oi/
open_interest) starts **2010**, NOT 1971+ as previously documented. 105 series exist (36 clean
`_cot.csv` + `tff_*`/`cit_*` breakdowns + `_jpy_proxy`), but the **tradeable clean positioning
panel is 2010+**. Consequences for champion improvement:
- The champion backtest starts 2008-03-31; a COT sleeve starts ~2010-2011 (after 52-wk z warmup).
- Its IS window (~2010-2017) COULD earn weight (unlike CFX4's 2019+), but only if standalone
  SR>=1.0; the honest grid shows it does NOT (all configs SR < 0.3).

## Honest battery results (representative; full grid = 60 configs via `cot_engine.py`)
Causal timing: COT report as-of Tuesday is released Friday; signal trades the business days in
(release_friday, +7]. Leak gate `leak_ok=True` on ALL configs — no lookahead.

| family | best SR | corr-to-champ | verdict |
|---|---|---|---|
| commod (dz8) | ~0.02-0.35 | -0.01..+0.02 | REJECT SR<1 |
| rates (dz8) | ~0.03-0.05 | -0.06..+0.08 | REJECT SR<1 |
| currencies (lvl) | 0.29 | -0.007 | REJECT SR<1 |
| eq/vol | -0.12..+0.10 | -0.05..+0.05 | REJECT SR<1 |
| all | -0.26..+0.09 | -0.02..+0.02 | REJECT SR<1 |

Best standalone non-negative: `COT_cies_lvl_follow` SR 0.29 (currencies — position LEVEL, follow).
No config passes `v2pass` (SR/halves/neg/ac1/uniq/corr/scramble/leak/beats-passive composite).

## Engine details and honest specifics
- Position signal = sign(EW z-score across markets) of either `net_noncomm_pct_oi` level
  (`lvl`) or its `lb`-day change (`dz`), z-scored over trailing 52wk (min 26), FOLLOW and FADE,
  lb in {4,8,13}.
- Markets restricted to DIRECT proxies (skip DBA multi-commodity bucket that smears single-commodity
  positioning). SUBBASKETS: commod(8), rates(4), currencies(3), eqvol(4), all(19).
- Daily book = position (weekly-fixed) x EW per-unit daily underlying return; net of full-|dW|
  6.4bps turnover + 0.5%/yr borrow.

## Relationship to the champion
- COT corr to the champion (SR 3.18 NAV-drift book) is tiny (|corr|<=0.08) — decorrelation is NOT
  the blocker.
- With no config clearing SR>=1.0, the `relw = max(IS_SR,0)^0.55` champion weighting would
  assign COT ~0 weight in the blend — adding it would neither help nor hurt (dilutes slightly).
- Consistent with ITER14 synthesis: raising the champion Sharpe needs a NEW genuinely-decorrelated
  **SR>2** honest sleeve; COT across level/delta/follow/fade and 4 sub-baskets is NOT it.

## Honest path forward (if COT is to be re-examined, not recommended as-is)
1. The raw CFTC zips in `more_cot/_raw/` only begin 2010; extending COT history pre-2010 needs a
   NEW historically-complete COT pull (CFTC archives back to 1986+ for legacy COT, 2006+
   disaggregated) — a genuine data acquisition task, not an engine fix.
2. Only after a 2008+ COT history exists does the IS<2017 solver get a real chance to earn COT
   weight. With 2010+ data the honest answer is already in and it is REJECT.

## Deliverables
- `cot_panel.py` (fixed, canonical 33-market price panel + MANIFEST.csv)
- `cot_net_weekly.csv` / `cot_pct_weekly.csv` / `MANIFEST.csv` (regenerated, all proxies resolved)
- `cot_engine.py` (honest battery; 60-config grid)
- `team/tests/test_res_cot.py` (7 TDD tests, all GREEN)
- `DATA_COVERAGE.md` update (see below): COT clean panel is 2010+, not 1971+.

RES_COT DONE — honest REJECT with numbers; data family now correctly built and covered.
