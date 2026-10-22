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
- To restore a stable paper gateway, use real IBKR **paper-trading account**
  credentials (the paper account that ships with a funded account) in
  `~/ibc/config.ini` — still paper mode, port 4002, zero real-money exposure.
  Demo credentials should be considered deprecated for auto-restart setups.

## Paper-Only Guarantees (unchanged)
- `campaign/ibkr_v7_engine.py`: port 4002 only; `--dry-run` default.
- `tools/wt/alpaca_paper.py`: hardcoded `https://paper-api.alpaca.markets`.
- No live endpoint or live credential exists anywhere in the repo.
- Real-account statement PDF gitignored ("Stock Accounts Information .pdf").
