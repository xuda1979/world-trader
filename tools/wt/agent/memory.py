"""Agent memory: persistent state across runs.

Layers (inspired by FinMem-LLM-StockTrading's layered memory):
  - short_term:  the current run's state (analysts -> ... -> trader)
  - long_term:   lessons from past reflector outputs
  - portfolio:   existing positions (for the risk manager's veto)

Storage: plain JSON files under <world-trader>/logs/agent_memory/.
We keep it stdlib-only and file-based -- no DB dependency.

Memory is an append-only log keyed by timestamp. The reflector writes to
long_term; the orchestrator reads long_term at the start of each run to
seed the prompts.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_MEMORY_DIR = Path(__file__).resolve().parents[2] / "logs" / "agent_memory"
_LONG_TERM_FILE = _MEMORY_DIR / "long_term.jsonl"
_PORTFOLIO_FILE = _MEMORY_DIR / "portfolio.json"


def _ensure_dir() -> None:
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Long-term memory (append-only JSONL of reflector outputs)
# ---------------------------------------------------------------------------

def append_long_term(entry: Dict[str, Any]) -> None:
    """Append a reflector entry to long-term memory. Adds timestamp."""
    _ensure_dir()
    entry = dict(entry)
    entry.setdefault("ts", now_iso())
    with open(_LONG_TERM_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def read_long_term(limit: int = 50) -> List[Dict[str, Any]]:
    """Return the most recent `limit` long-term entries."""
    if not _LONG_TERM_FILE.exists():
        return []
    out = []
    with open(_LONG_TERM_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out[-limit:]


def recent_lessons(limit: int = 10) -> str:
    """Return a compact string of recent lessons for prompt inclusion."""
    entries = read_long_term(limit=limit)
    if not entries:
        return "(no prior lessons -- first run)"
    lines = []
    for e in entries[-limit:]:
        lessons = e.get("lessons") or []
        cc = e.get("confidence_calibration") or ""
        ts = (e.get("ts") or "")[:19]
        for L in lessons:
            lines.append(f"[{ts}] {cc}: {L}")
    return "\n".join(lines) if lines else "(no prior lessons)"


# ---------------------------------------------------------------------------
# Portfolio memory (existing positions, for the risk manager)
# ---------------------------------------------------------------------------

def read_portfolio() -> Dict[str, Any]:
    """Return the current portfolio snapshot (empty if none)."""
    if not _PORTFOLIO_FILE.exists():
        return {"positions": [], "open_risk_pct": 0.0, "regime": "unknown"}
    try:
        with open(_PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"positions": [], "open_risk_pct": 0.0, "regime": "unknown"}


def write_portfolio(snapshot: Dict[str, Any]) -> None:
    _ensure_dir()
    with open(_PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Short-term memory (the current run state -- just a dict)
# ---------------------------------------------------------------------------

def new_short_term() -> Dict[str, Any]:
    return {
        "started_at": now_iso(),
        "analysts": {},        # name -> analyst output dict
        "bull": None,
        "bear": None,
        "risk_debate": {},     # aggressive/conservative/neutral
        "research_manager": None,
        "risk_manager": None,
        "trader": None,
        "reflector": None,
    }
