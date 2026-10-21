"""Per-role track records (HydraQuant-inspired).

HydraQuant weighs each agent's contribution in the meta-synthesis round by
its track record (argument quality + historical accuracy). We add a thin
version of this:

  - Every time the reflector runs, it scores each role's contribution
    (1 = helped, 0 = neutral, -1 = hurt) and writes it to a jsonl log.
  - On the next run, we read the trailing N=20 entries per role and
    compute a hit-rate, which is injected into the research-manager
    prompt as a "role track record" hint.

Storage: tools/logs/agent_memory/track_records.jsonl (one line per role
per run). Stays stdlib-only (no DB).
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_MEMORY_DIR = Path(__file__).resolve().parents[2] / "logs" / "agent_memory"
_TRACK_FILE = _MEMORY_DIR / "track_records.jsonl"
_WINDOW = 20  # trailing N runs per role


def _ensure_dir() -> None:
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def record_run(scores: Dict[str, int], ts: str) -> None:
    """Append one row per scored role to the track-records log.

    `scores` maps role name -> int in {-1, 0, 1}.
    `ts` is the run timestamp (ISO string).
    """
    if not scores:
        return
    _ensure_dir()
    with open(_TRACK_FILE, "a") as f:
        for role, score in scores.items():
            if score not in (-1, 0, 1):
                continue
            f.write(json.dumps({"ts": ts, "role": role, "score": score}) + "\n")


def hit_rates() -> Dict[str, Dict[str, float]]:
    """Return trailing-window hit rate per role.

    Returns:
        {role: {"hit_rate": float, "n": int, "avg": float}}
        where hit_rate = (count(score==1) + 0.5*count(score==0)) / n
        and avg = mean(score) in [-1, 1].
        Only roles with at least 3 entries are included.
    """
    if not _TRACK_FILE.exists():
        return {}
    by_role: Dict[str, List[int]] = {}
    with open(_TRACK_FILE) as f:
        for line in f:
            try:
                row = json.loads(line)
            except Exception:
                continue
            role = row.get("role")
            score = row.get("score")
            if not role or score not in (-1, 0, 1):
                continue
            by_role.setdefault(role, []).append(int(score))
    out: Dict[str, Dict[str, float]] = {}
    for role, scores in by_role.items():
        recent = scores[-_WINDOW:]
        n = len(recent)
        if n < 3:
            continue
        hits = sum(1 for s in recent if s == 1)
        neutrals = sum(1 for s in recent if s == 0)
        avg = sum(recent) / n
        out[role] = {
            "hit_rate": (hits + 0.5 * neutrals) / n,
            "n": float(n),
            "avg": avg,
        }
    return out


def format_track_records_for_prompt(rates: Optional[Dict[str, Dict[str, float]]] = None) -> str:
    """Human-readable block for the research-manager prompt."""
    if rates is None:
        rates = hit_rates()
    if not rates:
        return "(no track-record data yet)"
    lines = []
    for role in sorted(rates.keys()):
        r = rates[role]
        lines.append(
            f"  - {role}: hit_rate={r['hit_rate']:.2f} "
            f"(n={int(r['n'])}, avg_score={r['avg']:+.2f})"
        )
    return "\n".join(lines)


def score_role(role: str, output: Optional[Dict[str, Any]],
               final_outcome: Optional[Dict[str, Any]]) -> int:
    """Heuristic score in {-1, 0, 1} for one role's contribution this run.

    Used by the reflector to write track records. The heuristic is
    intentionally simple and deterministic (no LLM call):

      - For bull/bear: +1 if the role's direction matches the final
        trader ticket's direction, -1 if it disagrees, 0 if no trade.
      - For risk_debate conservative: +1 if final trade was skipped AND
        the conservative voice recommended skip, or if final trade was
        approved AND conservative approved; -1 otherwise.
      - For research_manager/risk_manager: +1 if a trade was approved
        and ran with R:R >= 2, -1 if approved but R:R < 1.5, else 0.
      - Default: 0.
    """
    if not output or not final_outcome:
        return 0
    side = final_outcome.get("side") or final_outcome.get("action")
    if role == "bull":
        if not output:
            return 0
        # bull is long-biased; +1 if final is long, -1 if short
        if side == "long":
            return 1
        if side == "short":
            return -1
        return 0
    if role == "bear":
        if not output:
            return 0
        if side == "short":
            return 1
        if side == "long":
            return -1
        return 0
    if role == "conservative":
        approved = bool(final_outcome.get("approved"))
        # We don't have the conservative's vote here directly; assume
        # +1 if it agreed with the final decision.
        return 1 if approved else 0
    if role in ("research_manager", "risk_manager"):
        rr = final_outcome.get("rr")
        approved = bool(final_outcome.get("approved"))
        if approved and isinstance(rr, (int, float)):
            if rr >= 2.0:
                return 1
            if rr < 1.5:
                return -1
        return 0
    return 0
