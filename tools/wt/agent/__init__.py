"""world-trader AI agent layer.

Multi-agent trading system that orchestrates the existing `wt` scan engine
through a structured debate (analysts -> bull/bear researchers -> risk
debate -> research manager -> risk manager -> trader -> reflector).

Architectural inspirations (see RESEARCH_NOTES.md for full citations):
  - TauricResearch/TradingAgents   (93k*): LangGraph multi-agent debate
  - HKUDS/AI-Trader                (21k*): agent-native skill composition
  - HKUDS/Vibe-Trading             (26k*): tool registry + MCP
  - The-Swarm-Corporation/AutoHedge (4k*): swarm-of-tools pattern
  - FinMem-LLM-StockTrading         (928*): layered memory + reflection

Design choices:
  - Stdlib-only, no langgraph/langchain dependency (consistent with the rest
    of the project). The graph is a plain Python orchestrator.
  - Every agent is a pure function (state -> state) so the orchestrator can
    be replaced/augmented without touching agent logic.
  - Every agent call goes through wt.llm with the existing xAI->Anthropic
    fallback, so the agent works with whatever keys are already configured.
  - The existing scan engine (wt.report, wt.deepdive, wt.breaking, etc.) is
    exposed as a TOOL REGISTRY, so the agents call the same battle-tested
    code paths the CLI uses -- no duplicated data fetching.
"""
from .orchestrator import run_agent, AgentResult  # noqa: F401
from .tools_registry import TOOLS, call_tool, list_tools  # noqa: F401
from . import regime_router, track_record, signal_processor  # noqa: F401

__all__ = [
    "run_agent", "AgentResult", "TOOLS", "call_tool", "list_tools",
    "regime_router", "track_record", "signal_processor",
]
