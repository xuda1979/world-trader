# HUNT_H1_TAILFACTOR R1 — work_r1 record (engine + coverage audit + countersign)

Written AFTER the charter was sealed (58df590f, 2026-10-17 18:52 CST) and BEFORE
any forward return of any panel symbol was computed against any panel factor
value (the real panel never reaches the grid — span guard §Scope-3 fail-closed;
the only grid executions are on deterministic SYNTHETIC fixtures, see below).
This file countersigns the charter (../CHARTER.md IS the pre-registration per
§Scope-1) and records the engine that will mechanically implement it at
evaluation time (≥60 panel dates / ≥3 calendar months, ~early Dec 2026).

## What exists in work_r1 (as of 2026-10-17)

| artifact | role |
|---|---|
| `r1_engine.py` | mechanical implementation of the charter: Stage 0 coverage audit, Stage 1 span guard (fail-closed), Stage 2 gated exhaustive-grid evaluation. Never judges — verdicts ADOPT/REJECT/UNJUDGEABLE are adjudicated by the chief in FINDINGS.md against GATES_CONTRACT_V2. |
| `test_r1_engine.py` | regression tests (19 checks, all PASS, pytest 3 + standalone 19) proving the fail-closed machinery BEFORE the real panel matures. |
| `r1_results.json` | REAL-panel run artifact (2026-10-17): pin PIN-OK, coverage audit, span guard verdict **PROTOCOL-HOLD** (13/60 dates, 2/3 months). NO grid — the engine exits before Stage 2 per §Scope-2 quarantine. |
| `r1_results_synthetic.json` | SYNTHETIC-fixture run artifact: exercises the FULL pipeline (stages 0–2, all 30 grid cells) on a deterministic synthetic panel so the evaluation machinery itself is validated pre-maturity. NOT the live panel; carries no evidential weight for adoption. |
| `WORK.md` | this file. |

## Engine protocol (what run_round does, in order)

1. **Pin guard** (`pin_prefix_guard`): the charter-sealed snapshot
   (sha256 `cae23d09649b1917a77d978e1fbfcac49b52b88961479bdece1a576384339fd1`,
   114 rows / 13 dates / 9 symbols) must remain a byte-identical PREFIX of the
   live `H1_tailfactor_panel.csv`. Append-only scheduled accrual passes;
   mutation / deletion / reordering / truncation of sealed rows →
   **PROTOCOL-VIOLATION**, no grid evaluation, fail-closed.
2. **Stage 0 coverage audit** (diagnostics ONLY, allowed on the fragment per
   §Scope-2): rows/dates/symbols/months, per-date holes, duplicate rows, value
   sanity (p20∈[0,1), var99≤var95<0 monotone, no NaN factors), file sha256.
3. **Stage 1 span guard** (§Scope-3): ≥60 distinct dates AND ≥3 calendar months
   required to reach EVALUATE; otherwise **PROTOCOL-HOLD**, engine exits,
   nothing downstream executes.
4. **Stage 2 grid evaluation** (only on EVALUATE): the §Scope-4 exhaustive
   30-cell grid (per-symbol factor × z-window {21,63} × threshold {1.0,1.5,2.0}
   × 3 families a/b/c), T+1 execution, harness costs 6.4bps one-side |dW| +
   4.5%/yr margin on (gross−1) + 0.5%/yr borrow on short notional, metrics
   per campaign/bt/metrics.py. The WHOLE grid is reported. Pre-committed
   primary: `a_tail_risk_off|p20_30d|L63|t1.5` (SPY long/flat).

## Regression tests — 19/19 PASS (pytest 3 passed; standalone 19 passed, 0 failed)

1. **Pin guard, fail-closed** (7 checks): live panel PIN-OK; appended accrual
   stays PIN-OK; sealed-row mutation blocked; sealed-row deletion blocked;
   truncated panel blocked; sealed-row reordering blocked; byte-identical copy
   PIN-OK.
2. **Span guard on the real 13-date panel** (4 checks): real run exit 0;
   verdict PROTOCOL-HOLD with hold_reason; NO grid key in the real artifact
   (quarantine mechanically enforced); pin_check PIN-OK.
3. **Synthetic determinism + artifact separation** (8 checks): consecutive
   synthetic runs byte-identical; synthetic run never touches the real
   artifact; synthetic span_guard reaches EVALUATE; 30 grid cells present;
   pre-registered primary cell present; real-mode rerun after synthetic still
   PROTOCOL-HOLD + PIN-OK; real artifact rewrite deterministic.

The synthetic grid run additionally demonstrates the machinery can separate
signal families on planted structure (best-sr cell `b_tail_harvest|p20_30d|L21|t2.0`
SR 1.56 vs primary 0.65 on planted fixtures) — a PIPELINE probe only; it says
nothing about the live panel and is treated as zero evidence per the charter's
anti-p-hack commitments.

## Coverage audit of the live panel (2026-10-17, diagnostics only)

- 114 rows, 13 dates (2026-09-08 → 2026-10-16), 9 symbols, 2 calendar months.
- Holes: 2026-10-08 (8 symbols missing), 2026-10-09 (7 missing) — the
  documented CBOE feed gap carried since accrual; noted, not actionable.
- dup_rows 0. Value sanity all TRUE (p20∈[0,1), var monotone negative, no NaN).
- File sha256 == charter pin (prefix check on the full 115-line file: exact
  match — the sealed snapshot IS the current file, accrual not yet past it at
  run time).
- Span guard: 13/60 dates, 2/3 months → **PROTOCOL-HOLD** (correct).

## Countersign

The charter's pre-registration is mechanically enforceable and now enforced:
every path the engine can take (PIN-OK/PIN-VIOLATION, HOLD/EVALUATE,
synthetic/real) has a regression test or a deterministic artifact on file.
No forward return of any panel symbol has been computed against any panel
factor value as of this writing. The round remains PROTOCOL-HOLD until the
panel accrues ≥60 dates and ≥3 months; the next session touching this hunt
should only need to re-run `python3 r1_engine.py` (no `--synthetic`) and
adjudicate in FINDINGS.md against GATES_CONTRACT_V2.

Round state: PROTOCOL-HOLD (by design). Champion of record untouched:
RAWEW13v2_WEIGHTED_GEAR16, sha16 a8ed233bd0f6fd5d.

---

## Addendum A — forward-return data-dependency audit (2026-10-17/18, §9b diagnostics)

Countersigned pre-outcome audit of the PRICE-SOURCE files that the sealed
engine's `load_returns()` will consume at December maturity. This is a
coverage/integrity audit only (GATES_CONTRACT_V2 §9b): NO forward return of
any panel symbol has been computed against any panel factor value; the grid
has never run on real data; the panel pin (cae23d09…) is untouched.

### A.1 Why this audit was required

`eval_cell` needs the T+1 forward return of every panel symbol for every panel
date. The engine reads prices from `tools/quant/data/cboe_hist/{SYM}.csv`
(fallback `tools/quant/data/twelvedata/{SYM}.csv`). The audit asked one
question: **will those files cover the panel's T+1 windows at the December
run?** Answer as of 2026-10-17: **no** — both sources are stale.

### A.2 Staleness findings (measured, not inferred)

| source | symbols covered | last bar | rows |
|---|---|---|---|
| twelvedata | all 9 panel syms | **2026-09-22** | 5028 (TSLA 4083); mtimes 2026-09-23 |
| cboe_hist | 5 ETFs only (GLD/IWM/QQQ/SPY/TLT) | **2026-09-09** | SPY 5709, GLD 5487, IWM 5704, QQQ 5708, TLT 5708 |
| cboe_hist single names | AAPL/MSFT/NVDA/TSLA | — | no files exist; single names are twelvedata-only in the sealed engine |

Panel last date is 2026-10-16 → gap ≥ 3.5 weeks (twelvedata) / 5+ weeks
(cboe_hist) and growing with each accrual. At maturity (~early Dec 2026) every
panel date after 2026-09-22 would lack forward returns on the primary path.

### A.3 Latent engine defects found by reading the sealed code (outcome-blind)

1. **No coverage-end guard in `load_returns()`**: it raises only if a symbol
   has no file or ≤1 row; it never checks that price coverage extends past
   the panel's last date. A silently stale file passes.
2. **`eval_cell` window mis-alignment** (lines ~259-260):
   `w = exposure.shift(1).fillna(0.0); w = w.reindex_like(px_ret).fillna(0.0)`
   — with real data `px_ret` spans 2006→last price date, so this
   (i) reindexes weights onto the FULL price history: ~20 years of
   zero-weight zero-return days enter `net`, inflating metric `n` to ~5000+
   and diluting SR/ann_geo (double distortion), and (ii) with stale prices,
   panel dates after the price last-date are silently DROPPED (absent from
   the `px_ret` index) rather than failing closed. Both distortions were
   invisible to the synthetic probe because `make_synthetic_returns` aligns
   its dates to the panel exactly. These would have corrupted the December
   run had the audit not caught them.

### A.4 Verified remediation paths (live probes, 2026-10-17)

- **TwelveData**: `TWELVEDATA_KEY` present in `.env.local`; live API probe
  (SPY, outputsize=5) returned status ok, newest bar 2026-10-16 — key valid,
  data current. Refresher: `tools/quant/refresh_panel.py` (writes
  date,open,high,low,close,vol CSVs; skip-if-mtime-today; 9s sleep between
  calls; URL api.twelvedata.com/time_series, interval=1day, outputsize=5000).
- **CBOE keyless**: `https://cdn.cboe.com/api/global/delayed_quotes/charts/
  historical/{SYM}.json` serves a 307 (redirect must be followed);
  `curl -sL` confirmed **all 9 panel symbols including single names** —
  SPY 5736 bars 2004-01-02→2026-10-15, AAPL 5734 bars →2026-10-15.
  Fetcher `tools/quant/data/cboe_hist/cboe_hist_dl.py` accepts ad-hoc CLI
  symbols (`main(argv)` overrides the sealed ETF-only SYMBOLS list), lints
  OHLC coherence, keyless. **Unverified**: whether its urllib follows the
  307 (sandbox blocked python DNS; curl -L worked) — must be verified on
  unsandboxed network before relying on it.
- **What is safe to touch**: refreshing PRICE-SOURCE files does not touch the
  pinned `H1_tailfactor_panel.csv` — permitted data hygiene. Re-verify the
  pin (prefix guard) after any refresh as a matter of course.

### A.5 Planned hardening (pre-outcome, fail-closed tightening)

Before the December run: (1) add a returns-coverage guard to the engine —
fail closed unless price coverage extends ≥1 trading day past the panel's
last date for every symbol; (2) align `eval_cell` to the panel's T+1 window
only (no full-history reindex; missing forward dates fail closed instead of
being dropped); (3) regression tests for both, re-run
`test_r1_engine.py` (19/19) and the synthetic probe to prove the guards fire.
These are outcome-blind tightenings; they will be countersigned here and
committed with pre-outcome framing before any real grid execution.

### A.6 Execution + verification log (2026-10-17, countersigned pre-outcome)

All A.5 hardening executed and proven before any real grid evaluation
(no forward return of any panel date has been computed — span guard still
holds the round in PROTOCOL-HOLD at 13/60 dates):

1. **CBOE 307-follow verified live** (closes A.4's open item): unsandboxed
   python urllib via `cboe_hist_dl.fetch('SPY')` returned 5736 bars
   2004-01-02..2026-10-15. No code change needed.
2. **Price sources refreshed** (the A.2 staleness, operational only —
   `tools/quant/data/` is git-ignored and regenerable; the pinned panel was
   never touched):
   - twelvedata: all 9 panel symbols re-fetched via the A.4 refresher
     (4101–5000 rows each), last bar 2026-10-16 (mtimes 2026-10-17).
   - cboe_hist: 5 panel ETFs (GLD/IWM/QQQ/SPY/TLT) re-fetched via the sealed
     ad-hoc CLI path after removing their 5 manifest rows; 5513–5735 bars
     each, last bar 2026-10-15.
3. **A.5(1) staleness guard proven in both directions live**:
   - fail: `load_returns` on the real panel raises (twelvedata AAPL last bar
     2026-10-16 ≤ panel last date 2026-10-16 — the last panel date's T+1
     genuinely does not exist yet; correct live fail-closed behavior).
   - pass: on a panel truncated to 2026-10-14 (probe only, in-memory, no
     artifact written), the guard passes and every symbol's T+1 forward
     return is computable from the refreshed sources (cboe_hist for the 5
     ETFs, twelvedata for the 4 single names; T+1 = 2026-10-15 bar present
     for all 9).
4. **A.5(2) window alignment diff audit**: `r1_results_synthetic.json` diff
   vs HEAD is exactly the exposure-window correction — metric `n` 71→70 per
   cell (the old artifact had evaluated the full synthetic price span);
   consecutive runs byte-identical (test [3] of the battery).
5. **Full battery re-run**: `test_r1_engine.py` 19/19 GREEN; real engine run
   deterministic PROTOCOL-HOLD (13/60 dates, 2/3 months, no grid, pin
   PIN-OK sha cae23d09649b1917/114rows sealed-prefix intact).

Residual operational note: price files go stale again by ~1 trading day per
panel accrual day. See Addendum B for the corrected refresh runbook — the
A.6-draft wording ("refresh both sources same-day") is superseded: CBOE
delayed-quotes lags ≥1 trading day, so same-day dual refresh is infeasible
for cboe_hist. The engine itself needs no further change.

---

## Addendum B — price-feed refresh runbook correction (2026-10-18, post-A.6, pre-outcome)

§9b operational follow-through on the A.6 residual note. No engine code, no
grid, no forward returns — documentation + live probe only. Round state
unchanged: PROTOCOL-HOLD 13/60 dates, 2/3 months.

### B.1 A.6 runbook sentence was infeasible for CBOE — corrected

The A.6 residual note drafted "refresh both sources same-day (paths in A.4)
before the December maturity run". Live probe (Sat 2026-10-17 14:05 ET = Sun
2026-10-18 02:05 +0800, 22h after the Friday 2026-10-16 close): the CBOE
delayed-quotes historical feed still ends 2026-10-15. SPY: 5736 raw bars
2004-01-02→2026-10-15, 5735 unique, dup ['2024-12-31'] — disk proven
current-to-feed (5736 = 5735 unique + 1 dup). GLD probe similar: 5514 raw /
5513 unique, last 2026-10-15. Probe JSONs: /tmp/cboe_probe_spy_20261018.json,
/tmp/cboe_probe_gld_20261018.json. Conclusion: the CBOE delayed feed lags
≥1 trading day behind close; same-day same-feed refresh cannot make cboe_hist
reach the panel's last date. The A.6 wording is superseded by this Addendum.

### B.2 Verified source state (disk, 2026-10-18)

- twelvedata: current through Friday 2026-10-16 for all 9 panel syms (SPY,
  QQQ, TLT, GLD, IWM, AAPL, MSFT, NVDA, TSLA). Refresh mtimes 2026-10-18
  01:26–01:28 +0800. twelvedata/manifest.csv is old (mtime 2026-09-08) — it
  is bookkeeping only, not used by the engine.
- cboe_hist: all 5 ETF files last bar 2026-10-15 (= feed max, per B.1), mtimes
  2026-10-18 01:28 +0800. Disk state is current-to-feed on both sources.

### B.3 Corrected December runbook (supersedes the A.6 sentence)

1. Post-close twelvedata refresh (all 9 panel syms) — reaches same-evening.
2. cboe_hist refresh on the NEXT trading day's post-close window (feed lags
   ≥1 trading day; per B.1 it cannot be same-day).
3. Then run r1_engine.py real mode. Either source covering T+1 of the panel's
   last date is sufficient per-symbol: engine preference order (r1_engine.py
   ~line 431) is cboe_hist first, twelvedata fallback per symbol, and the
   fail-closed span guard (lines ~456–462) raises RuntimeError if the chosen
   source does not extend ≥1 trading day past the panel's last date. So
   option (2) is belt-and-suspenders: even with cboe_hist one day behind,
   twelvedata coverage carries the 5 ETFs' T+1 and the guard passes.

### B.4 Partial-bar hazard (date-only guard) — operational rule

The A.5 staleness guard is DATE-ONLY: it checks that a bar exists at/after
T+1 but does not verify bar completeness. An intraday refresh during ET
market hours could ingest an in-progress partial bar (open/high/low stale or
mid-stream, close/volume not final) that passes the date guard. Rule:
refresh price sources only when the ET market is closed (after ~16:15 ET or
before ~09:25 ET on trading days; weekends freely). The 2026-10-18 01:26–01:28
+0800 refreshes = Sat 2026-10-17 ~13:26–13:28 ET, market closed — compliant.
All planned refresh waves must hold this rule.

Probe integrity note: zero null-OHLC bars in the B.1 SPY feed probe (5736
bars checked); feed first 2004-01-02, last 2026-10-15.
