# IB Gateway Paper Login — Status 2026-10-22

## Context
- Setup per `campaign/work_backtest_oos/V7_REPLICATION_SPEC.md` §7 (IBKR PAPER runbook):
  IB Gateway 10.50 standalone + IBC 3.24.2, launched via
  `/Users/daxu/software/ibc/scripts/ibcstart.sh 10.50 -g ... --mode=paper`.
- Config: `/Users/daxu/ibc/config.ini` (`TradingMode=paper`,
  `OverrideTwsApiPort=4002`).
- Engine side ready and paper-locked: `campaign/ibkr_v7_engine.py` connects
  127.0.0.1:4002 only (IBKR paper API port; live is 4001), defaults to
  `--dry-run` (no connection).

## 2026-10-21 (Wednesday) — SUCCESS
- Login OK with demo credentials (`edemo`/`demouser`, paper mode).
- "Paper Account Notice" dialog detected and closed automatically (21:08).
- Clean session end (exit 143, ~21:40). IBC log:
  `~/ibc/logs/ibc-3.24.2_GATEWAY-10.50_Wednesday.txt`.
- Screenshot of live gateway state kept transiently (`.tmp/gateway_state.png`,
  22:09); `.tmp/` is gitignored.

## 2026-10-22 (Thursday) 09:10 +0800 — FAILED
- Auto-relaunch attempted; IBKR auth server rejected the login:
  - `DISCONNECT_AUTHORIZATION_FAILED, FailReason: 1` from `ndc1.ibllc.com:4001`
  - server message includes "the login is possible beginning the day after
    account approval" — the demo credentials are not (or no longer) accepted.
- `~/Jts/loginFailFrequency.txt`: 9 consecutive failures.
- Gateway process exited; port 4002 never opened. No trading impact —
  engine was not running (dry-run default; nothing connects on failure).

## Impact & Next Steps
- No data, orders, or account state affected. Pure login-layer failure.
- Demo (`edemo`) logins are unreliable — yesterday worked, today rejected.
- ~~To restore a stable paper gateway, use real IBKR paper-trading account
  credentials in `~/ibc/config.ini`.~~ → **Done / updated**: real paper
  credentials (`aatsy6164`) are now in `~/ibc/config.ini`, but the login
  requires first-time web-portal activation (see 13:00 section above).

## 2026-10-22 13:00–13:30 +0800 — All four credential paths tested; root cause identified
- Systematic test of every credential available for this machine (one attempt each,
  spaced out; rate-limit event at 15 consecutive failures occurred 12:56–13:14 and
  was waited out; `loginFailFrequency.txt` peaked at 19):
  | Login | Type | Result |
  |---|---|---|
  | `edemo`/`demouser` | demo | Authenticated 10-21 21:08; **rejected 13:18 today** ("Unrecognized Username or Password") |
  | `aatsy785` | advisor | Auth OK → `NO_PAPER_MAPPING` (no paper account attached) |
  | `fengx199` | individual | Auth OK → `NO_PAPER_MAPPING` ("no paper user configured") |
  | `aatsy6164` | paper user for DF3354047 | `INVALID_USERNAME_OR_BAD_IP` — before *and* after ET midnight |
- Root cause: the paper account **DF3354047 exists but its login (`aatsy6164`) was
  never activated**. IBKR requires the account holder to complete a first-time web
  portal login (https://ndcdyn.interactivebrokers.com — usually with a forced
  password change) before gateway/API logins work. This is a human step; all
  retries were stopped to avoid escalating failure counters toward lockout.
- Retry automation: `tools/wt/gateway_login_retry.sh` (single attempt per call,
  fast-exits if port 4002 already listening) scheduled via launchd
  `com.worldtrader.gatewayretry` — every 2h at :23 (odd minute), 1 attempt max per
  run, logging to `~/ibc/logs/launchd-gateway-retry.log`. The gateway will come up
  automatically once the paper login is activated in the web portal.
  (crontab installs are TCC-blocked in this environment; launchd used instead.)
- `~/ibc/config.ini` updated to the real paper credentials (login `aatsy6164`,
  password per the account statement PDF; paper mode, port 4002 unchanged), so the
  launchd retry logs in with the correct account as soon as it is activated.
- Action needed from account holder (human): first-time web login for
  `aatsy6164` at https://ndcdyn.interactivebrokers.com → accept/complete password
  reset → confirm paper account DF3354047 is listed. After that, the next launchd
  tick (within 2h) restores the gateway, or run manually:
  `bash tools/wt/gateway_login_retry.sh 300`.

## Paper-Only Guarantees (unchanged)
- `campaign/ibkr_v7_engine.py`: port 4002 only; `--dry-run` default.
- `tools/wt/alpaca_paper.py`: hardcoded `https://paper-api.alpaca.markets`.
- No live endpoint or live credential exists anywhere in the repo.
- Real-account statement PDF gitignored ("Stock Accounts Information .pdf").
