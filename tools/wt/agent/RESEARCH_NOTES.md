# Research notes — repos integrated into the world-trader agent

This file cites the GitHub repos whose architecture or code informed the
world-trader AI agent layer (`tools/wt/agent/`). The agent is stdlib-only
(no langgraph/langchain), so nothing here is a direct code copy -- but the
**architectural ideas** are directly borrowed. Each citation explains what
we took and what we changed.

## Tier 1: directly-informed architecture

### 1. TauricResearch/TradingAgents  ★93,838
- **Repo**: https://github.com/TauricResearch/TradingAgents
- **Paper**: https://arxiv.org/abs/2412.20138
- **What we took**:
  - The 5-analyst -> bull/bear -> 3-way risk-debate -> research-manager
    -> risk-manager -> trader graph shape.
  - The "aggressive / conservative / neutral" risk debator pattern (from
    `tradingagents/agents/risk_mgmt/`).
  - The "research manager synthesizes debate into a plan" role
    (`tradingagents/agents/managers/research_manager.py`).
  - The reflector node for post-decision memory
    (`tradingagents/graph/reflection.py`).
  - The structured-JSON-output-per-node convention.
- **What we changed**:
  - Dropped the LangGraph dependency. The graph is a plain Python
    function sequence in `orchestrator.py`. Each node is a pure
    `state -> state` function, so the orchestrator can be swapped without
    touching agent logic.
  - Dropped the langchain dependency. `llm_chat.py` uses stdlib
    `urllib.request` directly, matching the rest of the project.
  - The analyst nodes in TradingAgents use tool-calling; ours use a
    fixed tool registry that the orchestrator calls BEFORE the LLM step,
    so the LLM only reasons over the tool output (cheaper, no tool-call
    loop).
  - TradingAgents uses yfinance/alpha-vantage/FRED; we reuse the
    project's existing `wt.report` / `wt.deepdive` / `wt.altdata` so the
    agent sees the same universe the CLI does.

### 2. HKUDS/AI-Trader  ★20,942
- **Repo**: https://github.com/HKUDS/AI-Trader
- **What we took**:
  - The "agent-native" framing: every capability is a SKILL.md contract
    that the agent can invoke. Our `tools_registry.py` is the Python
    equivalent of AI-Trader's `skills/*/SKILL.md` catalog.
  - The market-intel + ai4trade + polymarket skill separation. We mirror
    this with separate tools (`scan_markets`, `deep_dive`,
    `breaking_news`, `list_arb_setups`, etc.) instead of one mega-tool.
  - The "publish to AI-Trader" pattern (from their polymarket SKILL.md):
    our `trader` node's output is a publishable ticket with the same
    fields (sym, side, quantity_hint, order_type, stop, target, etc.).
- **What we changed**:
  - AI-Trader is TypeScript/Node; ours is Python (consistent with the
    rest of the project).
  - AI-Trader's skills are LLM-as-agent (the model picks the next skill);
    ours is orchestrator-as-agent (the Python orchestrator calls tools
    and feeds outputs to LLM nodes). This is cheaper and more
    deterministic.

### 3. HKUDS/Vibe-Trading  ★25,772
- **Repo**: https://github.com/HKUDS/Vibe-Trading
- **What we took**:
  - The tool registry pattern (`tools_registry.py` -> `call_tool(name, **kwargs)`).
  - The "agent/src/" directory layout with `agent/`, `tools/`, `skills/`.
  - The MCP server idea (we don't expose one yet, but `agent_cli.py
    --json` is the first step toward it).
- **What we changed**:
  - Vibe-Trading is a full web-app with a frontend; ours is CLI-first.
  - Vibe-Trading has its own backtest engine; we reuse the project's
    existing `wt/analysis.py` backtest (already Bonferroni-gated).

### 4. The-Swarm-Corporation/AutoHedge  ★3,865
- **Repo**: https://github.com/The-Swarm-Corporation/AutoHedge
- **What we took**:
  - The swarm-of-tools pattern: `autohedge/tools/tools_registry.py` is
    the direct inspiration for our `tools_registry.py`.
  - The `exa_search_tool` / `yahoo_api` / `polygon_api` split -> our
    `scan_markets` / `breaking_news` / `deep_dive` split.
- **What we changed**:
  - AutoHedge is crypto-only and focused on hedging; ours covers all
    world markets and is opportunity-first.
  - AutoHedge uses the `swarms` framework; ours is framework-free.

### 5. FinMem-LLM-StockTrading  ★928
- **Repo**: https://github.com/AI4Finance-Foundation/FinMem-LLM-StockTrading
- **What we took**:
  - The layered memory idea: short-term (current episode), long-term
    (cross-episode lessons), portfolio (existing positions). Our
    `memory.py` mirrors this with `_LONG_TERM_FILE` (jsonl append-only)
    and `_PORTFOLIO_FILE` (json snapshot).
  - The reflector node writing lessons into long-term memory.
- **What we changed**:
  - FinMem uses a proprietary layered memory with explicit read/write
    gates; ours is simpler (file-based, append-only) to keep the stdlib-only
    constraint.

## Tier 2: repos considered but not directly integrated (yet)

### 6. freqtrade/freqtrade  ★52,490
- **Repo**: https://github.com/freqtrade/freqtrade
- **Status**: production crypto trading bot. Not integrated because the
  project is opportunity-scanner-first, not bot-first. The agent's
  `trader` node produces a TICKET, not a live order -- that's the right
  boundary for now. Live execution would go through freqtrade or through
  the existing `wt/alpaca_paper.py` module.

### 7. ccxt/ccxt  ★43,355
- **Repo**: https://github.com/ccxt/ccxt
- **Status**: unified crypto exchange API. Not integrated because the
  project already has `wt/hyperliquid_funding.py`, `wt/dex_cex_arb.py`,
  `wt/funding_arb.py` etc. that talk to exchanges directly. If we ever
  need broader exchange coverage, ccxt would be the clean drop-in.

### 8. nautechsystems/nautilus_trader  ★24,855
- **Repo**: https://github.com/nautechsystems/nautilus_trader
- **Status**: Rust-core trading engine. Overkill for this project's
  research-first scope, but the right choice if we ever need
  sub-millisecond execution.

### 9. Polymarket/agents  ★3,747
- **Repo**: https://github.com/Polymarket/agents
- **Status**: autonomous Polymarket agents. The project already has
  `wt/prediction_market_arb.py` which scans Polymarket + Kalshi + Manifold
  for arbs. The "agent" layer on top (deciding which arb to take) would
  be a natural future extension of our `trader` node.

### 10. ginlix-ai/LangAlpha  ★1,568
- **Repo**: https://github.com/ginlix-ai/LangAlpha
- **Status**: "Claude Code for Investing". Similar multi-agent shape;
  our agent already covers the same ground with a stdlib-only stack.

### 11. jason8745/llm-agent-trader  ★377
- **Repo**: https://github.com/jason8745/llm-agent-trader
- **Status**: LLM-based backtesting. Not integrated because the project's
  backtest is already Bonferroni-gated and OOS-Sharpe-filtered; an LLM
  layer on top would add variance without clear edge.

### 12. moss-site/moss-trade-bot-skills  ★380
- **Repo**: https://github.com/moss-site/moss-trade-bot-skills
- **Status**: LLM-powered trading agents with a five-pillar strategy.
  Our 5-analyst structure covers a similar spectrum (technical /
  fundamental / news / sentiment / social).

### 13. EthanXiang777/circuit-framework  ★486
- **Repo**: https://github.com/EthanXiang777/circuit-framework
- **Status**: multi-agent LLM trading research system. Architecturally
  similar to what we built; ours integrates with the project's existing
  40-module scan engine, which circuit-framework doesn't have.

## Tier 1.5: integrated in the second pass (regime-aware routing)

These repos were researched and their **architectural ideas** integrated
into `tools/wt/agent/` in the second integration pass. As with Tier 1,
nothing here is a direct code copy -- the project stays stdlib-only, so
we adapted the ideas to our plain-Python orchestrator.

### 14. ymcbzrgn/HydraQuant  ★9
- **Repo**: https://github.com/ymcbzrgn/HydraQuant
- **Status**: "Cognitive trading organism" -- 12 specialized agents
  (TrendFollower, MeanReverter, MomentumRider, FundingContrarian,
  RiskMinimizer, DevilsAdvocate, EvidenceValidator, MacroCorrelator,
  TemporalAnalyst, ExploiterAgent, DefenderAgent, ReflectionAgent), 4-7
  selected per debate based on regime. 3-round debate with cross-examination
  and meta-synthesis. Round 2 SKIPPED when Round 1 consensus is high
  (LLM cost optimization). Meta-synthesis weighs agents by track record.
- **What we took**:
  - **Regime-aware agent selection** -- `regime_router.py` classifies the
    market into one of 6 labels (trending_bull, trending_bear, ranging,
    high_volatility, transitional, unknown) and picks which analysts to
    run. We always run market + fundamentals; the other 3 analysts
    (news, sentiment, social) are regime-conditional. In transitional /
    high-vol regimes, we also run the macro-regime analyst (see #16
    below).
  - **Consensus-skip cost optimization** -- `regime_router.consensus_skip()`
    checks if bull & bear both arrived at high confidence AND agree on
    direction. If so, we skip the 3-way risk debate entirely (saves 3
    LLM calls on clear-cut setups). The `debate_skipped` flag is
    surfaced in the result and in the CLI output.
  - **Track-record-weighted synthesis** -- `track_record.py` writes
    per-role scores (-1/0/+1) from each run to a jsonl log, and reads
    the trailing 20 entries to compute a hit rate per role. The
    research-manager prompt now includes these hit rates so the LLM
    can weigh more-trusted roles higher.
  - **Weight profile per regime** -- `regime_router.weight_profile()`
    returns hints like `{bull: 1.10, bear: 0.90, conservative: 0.95}`
    for trending_bull, etc. Fed into the research-manager prompt as
    non-binding hints.
- **What we changed**:
  - HydraQuant has 12 specialist agents; we kept our 5 generalist
    analysts + 1 new macro-regime analyst. The selection is at the
    "which analysts to run" level, not "which specialist to invoke."
  - HydraQuant's debate has 3 explicit rounds with cross-examination;
    ours is a single-shot bull/bear + 3-way risk debate. We added the
    consensus-skip but not the multi-round cross-examination (would
    3x the LLM cost).

### 15. Tomortec/CryptoTradingAgents  ★271
- **Repo**: https://github.com/Tomortec/CryptoTradingAgents
- **Status**: Multi-agent crypto framework, langgraph-based. Has a
  dedicated `SignalProcessor` class that distills the full trader output
  to a core BUY/SELL/HOLD decision. Also has `ConditionalLogic` for
  graph flow (debate rounds, risk judge routing) and a `Propagator` for
  state init.
- **What we took**:
  - **Signal processor** -- `signal_processor.py` takes the trader dict,
    risk_manager approval, and research_manager plan, and produces a
    compact signal: `{action: BUY/SELL/HOLD, side, confidence, entry,
    stop, target, rr, size_pct, timeframe, sym, regime, skip_reason}`.
    Rule-based (no LLM) so it's deterministic and cheap. Confidence is
    blended from the trader's confidence + R:R bonus + regime alignment.
    This gives downstream consumers (CLI, JSON API, future auto-trader)
    a single canonical signal instead of having to interpret the
    trader dict.
  - **Graph-flow conditional logic** -- the consensus-skip in
    `regime_router.consensus_skip()` is directly inspired by
    `ConditionalLogic.should_continue_*` in CryptoTradingAgents.
- **What we changed**:
  - Their SignalProcessor calls an LLM to extract BUY/SELL/HOLD from
    a text signal; ours is rule-based (deterministic) and operates on
    structured dicts. We don't need an LLM here because our trader
    already produces structured JSON.

### 16. brandononchain/opentrade  ★36
- **Repo**: https://github.com/brandononchain/opentrade
- **Status**: TradingView AI agent with 50 tools, 15 LLM models, and
  16 well-defined skill prompts under `src/skills/`. The skills have
  clean boundaries: macro-regime, hft-microstructure, liquidity-analysis,
  onchain-analytics, hedge-fund-analysis, quant-analysis, sentiment-feeds,
  portfolio-scanner, etc.
- **What we took**:
  - **Macro-regime analyst prompt** -- `prompts.ANALYST_MACRO_REGIME`
    adapts opentrade's `src/skills/macro-regime.md` into a 6th analyst
    role. It maps growth + inflation to one of the 4 macro quadrants
    (RECOVERY / GOLDILOCKS / STAGFLATION / DEFLATION), describes the
    yield curve, and -- critically -- says whether the macro backdrop
    SUPPORTS or OPPOSES the candidate's direction. This analyst is
    mandatory in transitional and high-volatility regimes (where
    bottom-up bullishness most often gets undone by macro).
- **What we changed**:
  - opentrade's skill is a standalone TradingView skill; ours is
    integrated as one more analyst in the existing 5-analyst rotation,
    gated on regime.
  - We did NOT adopt the other 15 skills -- most are either
    redundant with what we have (quant-analysis, sentiment-feeds) or
    out of scope for now (hft-microstructure, onchain-analytics,
    pine-script). They remain candidates for future integration.

### 17. gameworkerkim/vibe-investing  ★308
- **Repo**: https://github.com/gameworkerkim/vibe-investing
- **Status**: Multi-strategy Korean/US crypto+equity agent system.
  Has a "Harness quantv2" sequential pipeline
  (filter → sentiment → multi-agent judge → report) and a VibeQuant
  backend with notebooks, scripts, docker setup.
- **What we took**:
  - The sequential-pipeline discipline (run cheap deterministic filters
    BEFORE the LLM debate) is something we already follow via
    `scan_markets` → analysts → debate. vibe-investing's pipeline
    reinforced that this is the right shape. No new code added.
- **What we changed**:
  - Nothing. vibe-investing's architecture is more bot-first than ours;
    we don't want live trading yet, so we kept our scanner-first shape.

### 18. huygiatrng/AlpacaTradingAgent  ★241
- **Repo**: https://github.com/huygiatrng/AlpacaTradingAgent
- **Status**: TradingAgents fork with live Alpaca execution, WebUI,
  per-agent ChromaDB reflection memories, safety kill-switch, LLM cost
  monitor, daily operations reports.
- **What we took (ideas, not code)**:
  - **Per-agent persistent memory with similarity retrieval** --
    AlpacaTradingAgent uses ChromaDB collections per role
    (bull, bear, trader, invest judge, risk manager). Our `memory.py`
    + new `track_record.py` achieve a similar effect with plain jsonl
    files (stdlib-only). We don't do similarity retrieval yet -- this
    is a candidate for a future pass.
  - **LLM cost vs realized return attribution** -- their PR #37 does
    this. We don't have it yet, but the `tool_calls` log on each
    AgentResult is the groundwork for it.
  - **Safety high-water mark + kill switch** -- their `~/.tradingagents/safety/`
    dir. We don't have this because we don't trade live; if we ever do,
    this is the right pattern.
- **What we changed**:
  - No code copied. The track-record module is the closest analog,
    and it's much simpler than their ChromaDB setup.

## What's NOT integrated (on purpose)

- **No live order execution.** The `trader` node produces a ticket; it
  does not place orders. The existing `wt/alpaca_paper.py` module is the
  boundary for paper execution.
- **No langgraph / langchain.** The project is stdlib-only. Adding
  langchain would pull in ~200MB of transitive deps for no clear gain --
  the graph is a simple linear sequence with one conditional branch
  (risk_manager.approved -> trader).
- **No vector DB for memory.** Long-term memory is JSONL append-only.
  This is fine for thousands of entries. If we ever need semantic search
  over past lessons, we'd add a local SQLite FTS5 index before reaching
  for an external vector DB.
- **No browser/web frontend.** CLI-first. The `--json` flag is the
  integration point for any future web UI.

## How to extend

### Add a new tool
```python
# In tools/wt/agent/tools_registry.py
def _tool_my_new_thing(arg1: str) -> Dict[str, Any]:
    from wt import my_module
    return my_module.scan(arg1)

_register(
    "my_new_thing",
    "One-line description for the LLM prompt catalog.",
    {"arg1": "str: what this arg does"},
    _tool_my_new_thing,
)
```
That's it. The orchestrator automatically picks it up; the LLM
automatically sees it in the tool catalog.

### Add a new agent node
1. Add a prompt template in `prompts.py`.
2. Add a call in `orchestrator.py`'s `run_agent()` following the
   existing pattern:
   ```python
   user = prompts.MY_NEW_ROLE.format(today=_today(), context=ctx)
   res.my_new_role = _llm_call(prompts.PREAMBLE.format(today=_today()),
                               user, errors=res.errors, label="my_new_role")
   ```
3. Add the field to `AgentResult` and `as_dict()`.

### Swap the LLM provider
Set env vars:
```bash
export XAI_API_KEY=xai-...           # preferred
# OR
export ANTHROPIC_API_KEY=sk-...      # fallback
# OR point at a local Anthropic-compatible proxy:
export ANTHROPIC_BASE_URL=http://127.0.0.1:63152
export ANTHROPIC_MODEL=glm5.2
```
`llm_chat.py` handles all three.

## Academic references integrated (2026-07-21)

Three research artifacts informed the engine. Each is cited in-line at the
implementation site; this section consolidates the citations.

### 1. GDELT Event Database V2.0 Codebook
- Source: https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf
- Integrated in: `wt/news.py::gdelt_events` (CAMEO-coded event projection)
- Used by: `wt/country_crisis.py` (catalyst confirmation for country-drop setups)
- Notes: The dedicated GDELT Events API endpoint was deprecated; the
  supported access pattern is the DOC API with `mode=artlist` plus the
  themes/tones fields, or the raw GDELT V2 master files at
  `data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.export.CSV.gz` for full
  CAMEO-coded events. `gdelt_events` projects DOC API articles onto the
  CAMEO schema via `GDELT_THEME_TO_CAMEO` (PROTEST->14, MILITARY->18,
  PEACE->05, etc.) so downstream consumers can think in event-code space
  even though the underlying fetch is DOC API.

### 2. Post-Earnings Announcement Drift (PEAD) with transaction costs
- Source: EconPapers (Abarbanell-Bushee / Sadka lineage), JOARES 2008
  https://econpapers.repec.org/RePEc%3Abla%3Ajoares%3Av%3A46%3Ay%3A2008%3Ai%3A3%3Ap%3A661-696
- Integrated in: `wt/altdata.py::earnings_surprise` (Finnhub EPS surprise fetch)
  and `wt/analysis.py` PEADup/PEADdn setups + `_backtest_pead_pooled`
  (cross-sectional pooled t-stat).
- Notes: The price-action signature (gap > 2*ATR%, volume > 1.5x,
  close beyond SMA20) is the trigger; the earnings-surprise data is the
  CONFIRMATION. The pooled backtest gives a real cross-sectional t-stat
  for the PEAD edge after round-trip costs (the JOARES paper's point:
  transaction costs erode but do not eliminate the drift).

### 3. Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014)
- Source: SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- Integrated in: `wt/analysis.py::_deflated_sharpe` (formula), `backtest_setup`
  (computes DSR per setup), `trade_qualifies` (soft gate: DSR<-1 with
  edge<2 rejects), `report.py` OPP_COLUMNS (DSR column in the output table).
- Formula: `Var[SR_hat] = (1 - skew*SR + (kurt-1)/4 * SR^2) / (n-1)` (Lo 2002
  eq. 7, Bailey-LdP 2014 eq. 4), with `E[max_N] = sqrt(2*ln(N))` for the
  expected max of N independent Gaussian trials.
- Gate logic: DSR < 0 means the observed Sharpe is consistent with the
  expected maximum of N noise trials (selection bias). We reject only
  when DSR is strongly negative (< -1.0, ~1 sigma into the noise regime)
  AND the in-sample Sharpe is not itself very large (< 2.0). A large IS
  Sharpe with negative DSR still passes -- the OOS gates above provide
  the primary defense -- but DSR is visible in the output table so the
  trader sees the multiple-testing warning.

## 2026-08-22 — agent-debate → EQUITY RESEARCH REPORT projects evaluated

Survey (3 agents, GitHub API + code inspection) of open-source projects
that use LLM-agent debate to produce equity research / investment
analysis. Verdict: **no project is production-grade enough to integrate
wholesale**; the genuinely valuable ideas were adapted into the new
`research_report.py` module (stdlib-only, consistent with this repo).
None of these are direct code copies.

### Evaluated (with verdicts)

| Project | Stars | License | Verdict |
|---|---|---|---|
| virattt/ai-hedge-fund | 63k | MIT | The famous "agents debate" is marketing: v1 (langgraph DAG) has zero debate code; v2 (current main, 2.2.0) is a plain-Python signal pipeline with NO debate at all. Requires a PAID data API (financialdatasets.ai). Adopted: v2's PIT-honesty design (LLM never touches the numbers; missing data → abstain, never fabricate). |
| kbhujbal/AlphaAnalyst | 46 | Apache-2.0 | Best engineering for the REPORT output: schema-validated research memo, deterministic pure-Python valuation ("the LLM is a writer, not a knower"), eval suite. Debate is a single devil's-advocate pass; stale ~4 months. Adopted: memo schema + deterministic-valuation discipline. |
| Spkap/StockSense-AI | 15 | MIT | Best anti-sycophancy debate mechanics: bull sees growth data first / bear sees risk data first; mandatory rebuttal round; evidence grading by data support. LangGraph demo-grade. Adopted: all three mechanics. |
| helloJamest/FinAgent | 47 | MIT | Real multi-round bull/bear debate + judge with convergence detection; stdlib orchestration; active. Adopted: judge + convergence detection. |
| jinsong8/FinRpt (AAAI 2026) | 38 | MIT | The academic answer: 9 SFT/RL agents decompose report writing; 4.1/5 content accuracy. Zero debate, needs fine-tuning infra. Not integrated. |
| AlphaFin-projects/QuantAgent | — | — | Repo org deleted; the paper (arXiv 2402.03755) is about self-improving signal mining, not reports. Not integrated. |
| AI4Finance FinRobot/FinGPT | — | — | Agent framework / fine-tuning toolkit, not report generators. Not integrated. |
| CloudAI-X/the-trading-floor-v2 | 63 | MIT | Beautiful CrewAI council demo, dead (created+pushed same day). |
| OpenSourceAGI/ai-broker-investing-agent | 11 | NOASSERTION | Full debate stack + LIVE money execution with no eval discipline. Rejected on license + risk. |

### Literature guardrails (why the debate is graded)
- **FINSABER** (arXiv 2505.07078): LLM-agent strategy advantages largely
  vanish once look-ahead/survivorship bias is mitigated → all report
  numbers must come from real, timestamped data.
- **deeplearning-wisc/debate-or-vote**: debate gains ≈ voting/ensemble
  gains → every claim must be evidence-graded or the debate is noise.
- **MoCA-Agent** (arXiv 2606.11537): market-of-claims > free-form debate
  → implemented as the rule-based evidence grading + convergence check.

### What `research_report.py` took from each
- AlphaAnalyst: Python-computed valuation; schema-validated output.
- StockSense-AI: data-ordering, rebuttal round, evidence grading.
- FinAgent: judge node, convergence detection, scenario probabilities.
- ai-hedge-fund v2: abstain-on-missing-data; LLM writes no numbers.
- TradingAgents (already Tier 1): structured JSON per node.
