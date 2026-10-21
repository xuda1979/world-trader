---
name: ai-trader
description: >-
  Multi-agent trading system that orchestrates a structured debate (5
  analysts -> bull/bear researchers -> 3-way risk debate -> research
  manager -> risk manager -> trader -> reflector) over a candidate
  ticker, ending in a concrete, defined-risk trade ticket. Use when the
  user asks for a "deep agent analysis", "multi-agent debate", "full
  trade plan", or wants the AI agent to decide on a specific ticker.
  For a fast scan without the LLM debate, use --scan-only.
---

# ai-trader — multi-agent debate -> trade ticket

A LangGraph-free, stdlib-only multi-agent system inspired by
TauricResearch/TradingAgents, HKUDS/AI-Trader, HKUDS/Vibe-Trading,
The-Swarm-Corporation/AutoHedge, and FinMem-LLM-StockTrading. See
`tools/wt/agent/RESEARCH_NOTES.md` for the full citation list.

## When to use

- "Run the agent on AAPL"
- "Give me a full multi-agent debate on BTC-USD"
- "What does the AI trading agent think of 600519.SS?"
- "Produce a trade ticket with entry/stop/target/size"

Do NOT use for:
- A fast scan of the whole market (use the `trade-scout` skill instead).
- Live order execution (this is research only; nothing places orders).
- Backtesting a custom strategy (use the existing `wt/analysis.py`).

## How to run

```bash
# Full multi-agent debate on the top scan candidate
python tools/agent_cli.py

# Focus on a specific ticker
python tools/agent_cli.py --sym AAPL
python tools/agent_cli.py --sym 600519.SS
python tools/agent_cli.py --sym BTC-USD

# Skip the LLM debate (fast; useful when no LLM key is configured)
python tools/agent_cli.py --scan-only

# Equity RESEARCH REPORT (agent debate -> sell-side-style report, not a ticket)
python tools/agent_cli.py --report MU
python tools/agent_cli.py --watchlist MU,INTC,DELL --force   # batch, regenerate
# Reports land in results/equity_research/<SYM>_<date>.md (+ .json)

# Include the cross-arb probe (delta-neutral carry trades)
python tools/agent_cli.py --sym BTC-USD

# Machine-readable JSON output (for piping to other tools)
python tools/agent_cli.py --sym AAPL --json

# Self-check (providers, tools, wt module imports)
python tools/agent_cli.py --doctor
```

## Environment

The agent uses the same provider priority as the rest of the project:
  1. xAI Grok       — `XAI_API_KEY` (preferred; cheap + fast)
  2. Anthropic      — `ANTHROPIC_API_KEY` (fallback)

It also respects the Huanxin local proxy env vars:
  - `ANTHROPIC_BASE_URL` (default: https://api.anthropic.com/v1/messages)
  - `ANTHROPIC_MODEL` / `ANTHROPIC_SMALL_FAST_MODEL`
  - `ANTHROPIC_DEFAULT_SONNET_MODEL` / `ANTHROPIC_DEFAULT_OPUS_MODEL` / `ANTHROPIC_DEFAULT_HAIKU_MODEL`
  - `WT_XAI_MODEL`, `WT_ANTHROPIC_FAST_MODEL`, `WT_ANTHROPIC_STRONG_MODEL` (override everything)
  - `WT_LLM_TIMEOUT` (default 40s) — raise for slow reasoning models

## Architecture

```
                   +-----------+
                   | scan_markets tool  (wt.report full pipeline)
                   +-----+-----+
                         |
                         v
            +------------+------------+
            | 5 analysts (fast LLM)  |
            |  market / fundamentals |
            |  news / sentiment      |
            |  social                |
            +------------+------------+
                         |
            +------------+------------+
            | 2 researchers (strong LLM)
            |  bull    |    bear      |
            +------------+------------+
                         |
            +------------+------------+
            | 3-way risk debate       |
            | aggressive / conservative / neutral
            +------------+------------+
                         |
                         v
            +------------+------------+
            | research manager -> plan
            +------------+------------+
                         |
                         v
            +------------+------------+
            | risk manager -> veto / size
            +------------+------------+
                         |
                         v
            +------------+------------+
            | trader -> TICKET        |
            | (entry/stop/target/size)
            +------------+------------+
                         |
                         v
            +------------+------------+
            | reflector -> long-term memory
            +-------------------------+
```

## Tool registry (10 tools, all backed by existing `wt` modules)

- `scan_markets` — full global opportunity scan (US+CN+crypto+FX+futures)
- `deep_dive` — per-ticker valuation/growth/quality/peers/catalysts/IV
- `breaking_news` — last N hours of market-moving news
- `llm_sentiment` — LLM judge of headlines (xAI -> Anthropic fallback)
- `list_arb_setups` — probe all 13 arb modules at once
- `market_sessions` — which markets are OPEN right now
- `country_crisis` — country-level crisis signals
- `hyperliquid_funding` — Hyperliquid perp funding rates
- `sharpe_ranked_setups` — re-rank the scan by **cost-adjusted per-trade
  Sharpe** (the high-Sharpe objective for a small retail account; nets
  IBKR commission + spread). Use when the user wants quality edges, not
  fat R:R with low win rate.
- `kelly_position_size` — **small-capital position sizer**. Converts a
  setup's (p_win, rr) + account equity into a HALF-Kelly dollar ticket
  capped at 20% of equity, with the retail commission bite reported.
  Use after picking a setup to size the trade for our small account.

The tool registry is the integration surface: adding a new tool is a
single `_register(...)` call in `tools/wt/agent/tools_registry.py`.

## Memory

- **Short-term**: the current run's state dict (analysts -> ... -> trader)
- **Long-term**: `logs/agent_memory/long_term.jsonl` — append-only log of
  reflector outputs, fed into future runs as `prior_lessons`.
- **Portfolio**: `logs/agent_memory/portfolio.json` — existing positions
  for the risk manager's veto (currently a stub; wire to the broker API).

## Files

- `tools/wt/agent/__init__.py` — package exports
- `tools/wt/agent/orchestrator.py` — the graph (plain Python)
- `tools/wt/agent/prompts.py` — every agent role's prompt template
- `tools/wt/agent/llm_chat.py` — generic LLM chat (xAI/Anthropic)
- `tools/wt/agent/tools_registry.py` — tool registry
- `tools/wt/agent/memory.py` — short/long/portfolio memory
- `tools/wt/agent/RESEARCH_NOTES.md` — citations to integrated repos
- `tools/agent_cli.py` — CLI entry point

## Hard rules (inherited from `trade-scout`)

1. Cite sources for every factual claim.
2. Every thesis must end with a defined-risk trade (entry, stop, target, R:R).
3. R:R must be >= 2.0 to be actionable.
4. Never promise profit or use "safe" / "guaranteed".
5. If data is missing or stale, say so and lower confidence.
6. Research only, not financial advice. Verify live before acting.
