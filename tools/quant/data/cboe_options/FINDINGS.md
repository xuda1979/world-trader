# H1 Forward-Collection Harness — FINDINGS (2026-09-30)

**STATUS: PASS — harness LIVE; first archive day captured (20260929, 9/9 symbols);
launchd agent scheduled (04:20 + 05:20 CST daily); 12/12 tests green.**

## What was built

`h1_collect.py` — the daily CBOE EOD snapshot → H1 tail-factor forward-collection
harness specified by H1_report.md §7 (2026-09-16, campaign/agents/
H1_optiontail_results/), which until today existed only on paper:

1. **Fetch** all 9 symbols (SPY,QQQ,IWM,TLT,GLD,AAPL,MSFT,NVDA,TSLA) from the free
   keyless CBOE delayed-quotes API. NOTE: the endpoint now 307-redirects
   cdn.cboe.com → cdn-api.cboe.com (schema unchanged; urllib follows transparently).
2. **Archive write-once**: `archive/YYYYMMDD/{SYM}.csv` — same schema as `latest/`,
   full strike range, ALL expiries ≥ 7 DTE retained (term structure needs both 30d
   brackets; the 0.8S strikes carry the p20 signal). A second run for the same date
   raises FileExistsError and never touches archived files. `fetch_report.json`
   records fetch timestamp, per-symbol sha256, spot/iv30/contract counts, and the
   **trade date** (from the underlying's `last_trade_time`), keeping T+1 causality
   auditable.
3. **Factor recompute per date**: `H1_tailfactor_YYYYMMDD.csv` +
   `H1_diagnostics_YYYYMMDD.csv` — math identical to the committed
   H1_build_tailfactor.py (verified: all 9 reference rows reproduce to ≤1.5e-4
   relative; worst-case float noise from groupby/pivot ordering).
4. **Panel**: `H1_tailfactor_panel.csv` — all archived days, ascending by
   (date, symbol), rebuilt idempotently from the archive each run.
5. **Fail-closed**: symbol fetch/lint failures are logged and excluded; the day's
   factor file must carry ≥ 6 of 9 symbols or the run exits 1.

## Trade-date labelling (the pre-market subtlety)

The CBOE delayed payload serves the LAST COMPLETED session. A fetch before the US
open therefore prices the prior close: e.g. fetched 2026-09-30 03:25 ET, underlying
`last_trade_time` = 2026-09-29T15:59:59 → archived as **20260929**, not 0930. The
archive date is the majority trade date across symbols, so tau math (and therefore
p20/var95/var99) stays aligned to the priced session. Archiving by fetch date would
have corrupted every DTE by one day.

## First live day (2026-09-29 close, captured 2026-09-30 ~03:25 ET)

9/9 symbols, 0 rejects. Panel row count: 9. Headlines vs the 2026-09-08 vintage:

| symbol | p20_30d (09-08) | p20_30d (09-29) | var95 (09-29) |
|---|---|---|---|
| SPY | 0.00344 | 0.00405 | -0.0659 |
| QQQ | 0.00574 | 0.00898 | -0.0984 |
| TLT | 0.00005 | 0.00281 | -0.0986 |
| AAPL | 0.00549 | 0.01936 | -0.1422 |
| TSLA | 0.01821 | 0.04211 | -0.1912 |

Tail pricing moved materially in 3 weeks (TSLA p20 ×2.3, AAPL ×3.5, TLT ×50) —
exactly the cross-sectional state variation the future tail sleeve is meant to
harvest. This also retroactively validates H1's premise: the state is NOT static.

## Scheduling

launchd agent `com.worldtrader.h1collect` (~/Library/LaunchAgents/): 04:20 and
05:20 CST daily. 04:20 captures the US summer close (16:00 EDT = 04:00 CST + 20min
settle); 05:20 covers the winter close (16:00 EST = 05:00 CST) and doubles as a
retry for the summer slot. Write-once archiving makes the duplicate attempt a
harmless loud no-op (second run raises FileExistsError, logged, nothing touched).
`crontab` was NOT used: `crontab -` / `crontab <file>` hang in this environment.

**Interpreter PINNED (2026-09-30 hardening, same session)**: the plist invokes
`/Users/daxu/homebrew/bin/python3` (3.14.7, pandas 3.0.3 / scipy 1.18.0 /
numpy 2.4.6) — the stack that produced the committed canonicals. Verification
found system `/usr/bin/python3` (3.9.6, scipy 1.13.1) drifts the SVI fits by up
to 1.26e-4 (p20/var/skew) vs the committed archive and can fail the digital
cross-check gate on some symbols. A stack seam would have silently entered the
daily factor series if launchd had used the default PATH python.

**Bug found+fixed during the same hardening**: `recompute_day`'s input glob
previously matched its OWN output files (`H1_tailfactor_*.csv`,
`H1_diagnostics_*.csv`) when re-running on an already-computed day — the first
run was safe only because outputs didn't exist yet; a `--recompute` on any
archived day would try to parse its own outputs as chains. Fixed: inputs exclude
`H1_*` files (with test pin).

## Tests (12/12 green)

`test_h1_collect.py`: pin-parity vs the committed 2026-09-16 reference (SPY row +
all 9 rows, ≤2e-4 relative); DTE floor 7d gate; ≥6/9 fail-closed gate; synthetic
end-to-end smile (parity r≈q≈0 recovery, p20∈(0,0.5), var99≤var95<0, digital
cross-check ≤0.05); archive/20260929 existence + schema + sha256 + trade-date pins;
panel ordering pin; write-once enforcement (re-archive raises, file unchanged).

## What this unlocks (unchanged math, new time axis)

- ≥3y of daily factors → H1 sleeve construction per H1_report §7 (cross-sectional
  L/S on tail-pricing state vs subsequent realised tail; T+1; 6bps |dW| + margin
  on levered gross + 0.5% borrow). Until then the factors are monitoring-only.
- Free data cannot be backfilled — every day this harness now runs is a day the
  future sleeve can use. Daily capture STARTED 2026-09-29; days before that are
  lost except the single 2026-09-08 snapshot (kept in `latest/`).
- Backfill gap remains open (CBOE DataShop / ORATS / ivolatility / Polygon, ≥5y
  EOD chains preferred; 3y minimum) — a licensed-data decision, not free data.

---

# ADDENDUM 2026-10-01 — the 20260930 near-loss and the hardening it forced

**STATUS: PASS — trade-date 20260930 recovered pre-open (18:13 CST manual run,
9/9 symbols, 0 rejects, panel 18→27 rows, commit 9f70b649); harness hardened
(freshness guard + repair path + heartbeat + 10-slot retry ladder, commit
c44f7549); cboe_options suite 46/46 green.**

## What happened

Both 04:20/05:20 CST launchd runs failed ALL 9 symbol fetches with
`SSLCertVerificationError: self-signed certificate` (forensic preserved:
`campaign/logs/h1_collect_FAILURE_20261001_0420_0520.log` — the live log is
overwritten by launchd each run). Trade-date 20260930 went un-archived; the
CBOE delayed payload serves the last COMPLETED session only until the next
open, so the day would have been PERMANENTLY LOST at 09:30 ET. Diagnosed at
18:05 CST (pre-market, ~3.4h of margin): interactive-path fetch worked
(Let's Encrypt chain verifies fine), manual run archived the day cleanly.

## Root-cause picture (evidence, not conjecture)

- Night-path TLS presents a cert the homebrew `openssl@3/cert.pem` bundle
  does not trust ("self-signed" per python; curl via the macOS keychain
  verified a legit Let's Encrypt chain at 18:0x). A local PAC proxy
  (TrustAgentLauncher, 127.0.0.1:54021→54119) is active on this machine;
  unified log yielded nothing conclusive about the 04:20 window.
- Decision: do NOT weaken verification (no `certifi`-swap, no
  `SSL_CERT_FILE` pinning to a keychain-exported CA, no verify-off). Instead
  make the schedule resilient to ANY transient night-path failure mode
  (TLS, DNS, proxy): 10 retry slots spanning the 17h payload window, plus
  the freshness guard so post-success slots are free no-ops.

## Hardening (TDD: 15 new tests, 7 mutations all killed)

1. `expected_trade_date(now_et)` — zoneinfo/DST-proof ET trade date the
   payload serves (16:00 ET close boundary; NYSE full-holiday calendar
   2026-2028; weekend/holiday pre-market → prior session).
2. `is_fresh(expected)` — true iff archive/<d>/ holds ≥6/9 snapshots AND its
   `H1_tailfactor_<d>.csv`; fresh → `collect()` no-ops (fixes the
   `FileExistsError` crash class on scheduled duplicates — the old 05:20 run
   after a successful 04:20 run crashed loudly).
3. Repair path — snapshots archived but factor file missing (transient
   crash mid-run): recompute factors from the archive WITHOUT re-fetching
   (write-once data is irreplaceable; factors are pure functions of it).
4. `write_status()` heartbeat — `campaign/logs/h1_status.json` every run:
   last_run/last_success/last_archive_date/expected_archive_date/n_symbols/
   consecutive_failures. A silently-failing launchd agent is now visible
   with one `cat`.
5. launchd retry ladder — 04:20/05:20/06:20/07:20/08:20/10:20/12:20/14:20/
   16:20/18:20 CST; plist reloaded, 10 intervals verified via
   `launchctl print`; live end-to-end run verified (no-op, exit 0,
   heartbeat written).

## Residual risk

- If ALL 10 slots fail on a given day (sustained outage or a night-path cert
  that persists past ~18:20 CST), that trade date is lost; the heartbeat's
  `consecutive_failures` is the tripwire — check `h1_status.json` daily.
- The 04:20 failure mode (night-path TLS) may recur on any slot; the ladder
  exists precisely to outlive it. If logs show failures across the whole
  ladder on one day, escalate to a licensed-feed decision (the open backfill
  gap) rather than weakening TLS verification.

DONE H1_forward_collection
