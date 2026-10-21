---
name: ai-devops
description: >-
  AI-DevOps discipline for orchestrating parallel research agents and
  operating the multi-agent quality/backtest pipeline. Use when (a) launching
  MANY headless agents at once, (b) running standup/status meetings, (c)
  applying TDD + verification-before-completion to backtests, (d) honoring
  trading-cost/shortability constraints in deployed systems. Encodes learned
  operational lessons (rate limits, concurrency, honesty gates).
---

# ai-devops — orchestrate & operate the multi-agent research pipeline

## When to use
- Launching 5+ headless research agents in parallel.
- Running a coordinator "standup" to track agent status.
- Changing ANY backtest/builder (TDD is not optional).
- Deploying any system that must honor trading costs / leverage / shortability.

## IRON RULE: never talk to yourself / never loop
Execute, then observe, then act. Do NOT restate intent without running a command.
If you catch yourself repeating "I'll run X" without invoking it, STOP and invoke it.
Bullshit (intent-without-execution) is unacceptable in this org.

## TDD (test-driven development) — superpowers skill, non-negotiable
- NO production code change without a FAILING test first.
- Write failing test -> watch RED -> write minimal code -> watch GREEN -> refactor.
- A reconciliation gate you never saw FAIL may test the wrong thing.

## Verification-before-completion
- No "PASS/DONE/0-neg" claim without fresh command output you actually read.
- Re-run builders yourself; do NOT trust an agent's own success report (caught real fraud: XGB1y).

## ORCHESTRATION: parallelism vs API rate limits (LEARNED, 2026-09-06)
- Headless agents run via:
  `claude -p --dangerously-skip-permissions --append-system-prompt "..." <charter>`
  with the model endpoint env vars exported in the SAME shell (ANTHROPIC_BASE_URL, _API_KEY,
  _AUTH_TOKEN, _MODEL). `claude` binary is at /Users/daxu/homebrew/bin/claude.
- WARNING (REAL FAILURE): launching all 20 agents at once against one API key hit
  HTTP 429 ("您的账户已达到速率限制" = rate limit exceeded) on 13/20. The GLM/Anthropic gateway
  caps CONCURRENT requests per key.
- CORRECT PATTERN — throttle concurrency & add retry/backoff:
  * Launch in BATCHES (e.g. 5 at a time) — do NOT fire 20 at t=0.
  * Add retry-with-backoff (e.g. retry on 429 after 30-90s exponential backoff) inside
    launch_agent_chief.sh (trap 429, sleep, retry).
  * Verify each batch's logs for "429/rate limit" before launching the next.
  * A headless agent that exits with code 0 may still have done NOTHING (API error at start);
    always grep its log for "API Error / 429" before trusting it.
- Each agent charter is SELF-CONTAINED (isolated context, no coordinator-context inheritance).
- Coordinator independently verifies every integration candidate (sleeve, bug fix) before accepting.

## STANDUP MEETINGS
- Coordinator runs a standup at a cadence: for each agent, is it RUNNING / DONE / note in FINDINGS.
- Detect "DONE" by grepping FINDINGS.md tail for "ROUND N DONE" (use exact marker).
- Detect "RUNNING" by ACTIVE PROCESS + growing log, NOT by charter-name in the cmdline
  (the claude -p cmdline is generic; name is not in it).
- A status tool that mis-labels RUNNING as NOT-STARTED is a tool bug — fix it, don't trust it.

## TRADING-OPERATIONS CONSTRAINTS (honor in every sleeve/backtest)
- One-side cost = 6.4 bps on FULL |dW| traded notional (TRADE_RECORD_STANDARD). NO 0.5 half-turn.
- IBKR call-rate margin: 4.5%/yr on (gross-1) charged daily.
- Borrow: fee on short notional (default 0.5%/yr; hard-to-borrow tiers higher).
- Shortability: single-name equity L/S MUST model non-shortable stocks (fraction of bottom names
  can't be shorted -> drop/reweight those legs); commodity/rates/fx/futures are fungible-short.
- Leverage cap applied on capital-real gross; no intraday overshoot.

## FAIL-CLOSED
- Any audit check that cannot be computed must count as FAIL, not pass.
- Missing long zero-runs, NaN totals, partial-coverage joins -> flag loudly.
