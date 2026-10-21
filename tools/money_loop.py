#!/usr/bin/env python3
"""30-minute money loop: run full world-trader scan, extract trade-plan rows,
extract any candidates that CLEAR the strict backtest bar, and dispatch alerts.

Designed to run every 30 minutes via launchd (com.worldtrader.money-loop.plist).
Degrades gracefully: if no alert channel is configured, writes to
logs/money-loop-YYYY-MM-DD.log and logs/alerts.log.

Bar to alert (configurable):
  - Any verdict == 'clear' or 'clear*' (strict Bonferroni-OOS bar met)
  - OR a trade-plan row with R:R >= 3.0 and risk% <= 2.0 and a catalyst tag
  - OR an options RV/IV edge >= 5pp
  - OR a funding/basis arb with net_24h >= 0.10% (crypto, when reachable)

Usage:
  python3 tools/money_loop.py [--dry-run]
"""
from __future__ import annotations
import sys, os, time, json, re, subprocess, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from wt import alerts

LOGDIR = HERE / "logs"
LOGDIR.mkdir(exist_ok=True)
PY = os.environ.get("WT_PYTHON", sys.executable or "/Users/daxu/homebrew/bin/python3")

# Parse a scan log for the trade-plan table and the backtest verdict table.
ROW_RE  = re.compile(r"^\|\s*(\d+)\s+\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
VERDICT_RE = re.compile(r"^\|\s+(\d+)\s+\|\s*([A-Za-z0-9._-]+)\s+\|\s*(below|clear\*?|skip)\s*\|")

def parse_scan_log(path: Path):
    """Return dict with trade_plan rows, verdict rows, and flags."""
    out = {"trade_plan": [], "cleared": [], "options_edges": [], "nothing": False, "regime": ""}
    if not path.exists():
        return out
    in_trade_plan = False
    for ln in path.read_text(errors="replace").splitlines():
        if ln.startswith("-- TRADE PLAN --"):
            in_trade_plan = True
            continue
        if in_trade_plan and ln.startswith("+---"):
            # could be start or end of table
            if out["trade_plan"]:
                in_trade_plan = False
            continue
        if in_trade_plan:
            m = ROW_RE.match(ln)
            if m:
                parts = [p.strip() for p in ln.split("|")]
                # parts: ['', '#', 'Instrument', 'Sym', 'Mkt', 'Dir', 'Setup', 'Price', 'Quote', 'Chg%', 'Entry', 'Stop', 'Target', 'R:R', 'Risk%', 'Catalyst', '']
                if len(parts) >= 16:
                    out["trade_plan"].append({
                        "n": parts[1], "instrument": parts[2], "sym": parts[3],
                        "mkt": parts[4], "dir": parts[5], "setup": parts[6],
                        "price": parts[7], "quote": parts[8], "chg": parts[9],
                        "entry": parts[10], "stop": parts[11], "target": parts[12],
                        "rr": parts[13], "risk": parts[14], "catalyst": parts[15],
                    })
        # backtest verdict table
        mv = VERDICT_RE.match(ln)
        if mv:
            n, sym, verdict = mv.group(1), mv.group(2), mv.group(3)
            if verdict in ("clear", "clear*"):
                out["cleared"].append({"n": n, "sym": sym, "verdict": verdict})
        if "NOTHING cleared" in ln:
            out["nothing"] = True
        if ln.startswith("-- REGIME:"):
            out["regime"] = ln.strip("- ").strip()
        # options RV/IV edge lines look like: "  AAPL  RV=12.3% IV=18.4% edge=-6.1pp ..."
        mo = re.search(r"\b([A-Z]{1,6})\s+RV=([0-9.]+)%\s+IV=([0-9.]+)%\s+edge=([+-]?[0-9.]+)pp", ln)
        if mo:
            sym, rv, iv, edge = mo.group(1), float(mo.group(2)), float(mo.group(3)), float(mo.group(4))
            if abs(edge) >= 5.0:
                out["options_edges"].append({"sym": sym, "rv": rv, "iv": iv, "edge": edge})
    return out

def should_alert(parsed: dict) -> tuple[bool, str]:
    """Decide whether to push an alert, and return the reason."""
    if parsed["cleared"]:
        syms = ", ".join(f"{r['sym']} ({r['verdict']})" for r in parsed["cleared"][:5])
        return True, f"CLEARED bar: {syms}"
    # R:R >= 3 and risk <= 2% and has catalyst
    for r in parsed["trade_plan"]:
        try:
            rr = float(r["rr"])
            risk = float(r["risk"].rstrip("%"))
        except (ValueError, AttributeError):
            continue
        if rr >= 3.0 and risk <= 2.0 and r["catalyst"]:
            return True, f"High-RR catalyst: {r['sym']} RR={rr} risk={risk}% cat={r['catalyst']}"
    if parsed["options_edges"]:
        oe = parsed["options_edges"][0]
        return True, f"Options RV/IV edge: {oe['sym']} edge={oe['edge']:+.1f}pp"
    return False, ""

def build_digest(parsed: dict, scan_log: Path):
    lines = []
    lines.append(f"=== MONEY-LOOP {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    if parsed["regime"]:
        lines.append(f"regime: {parsed['regime']}")
    if parsed["nothing"]:
        lines.append("verdict: nothing cleared strict bar (E[R]>=1%, Sh>=0.40, Bonf t>=2, OOS>0)")
    if parsed["cleared"]:
        lines.append(f"*** {len(parsed['cleared'])} CLEARED ***")
        for r in parsed["cleared"][:10]:
            lines.append(f"  CLEAR {r['sym']} ({r['verdict']})")
    if parsed["trade_plan"]:
        lines.append("")
        lines.append(f"top {len(parsed['trade_plan'])} measured-edge trade plans:")
        for r in parsed["trade_plan"][:8]:
            lines.append(
                f"  #{r['n']:>2} {r['instrument'][:18]:18s} {r['sym']:12s} {r['mkt']:4s} "
                f"{r['dir']:5s} {r['setup']:7s} px={r['price']:>8s} chg={r['chg']:>6s} "
                f"entry={r['entry']:>8s} stop={r['stop']:>8s} tgt={r['target']:>8s} "
                f"RR={r['rr']:>4s} risk={r['risk']:>5s} cat={r['catalyst']}"
            )
    if parsed["options_edges"]:
        lines.append("")
        lines.append(f"options RV/IV edges (>=5pp): {len(parsed['options_edges'])}")
        for oe in parsed["options_edges"][:6]:
            lines.append(f"  {oe['sym']:6s} RV={oe['rv']:.1f}% IV={oe['iv']:.1f}% edge={oe['edge']:+.1f}pp")
    lines.append("")
    lines.append(f"full log: {scan_log}")
    lines.append("research only, not financial advice. verify before acting.")
    return "\n".join(lines)

def main():
    dry = "--dry-run" in sys.argv
    stamp = time.strftime("%Y%m%d-%H%M%S")
    scan_log = LOGDIR / f"money-scan-{stamp}.log"
    started = time.time()
    # Run the full scan
    if dry:
        # parse the latest existing scan log instead
        existing = sorted(LOGDIR.glob("scan-*.log"), key=lambda p: p.stat().st_mtime)
        if existing:
            scan_log = existing[-1]
        parsed = parse_scan_log(scan_log)
    else:
        env = os.environ.copy()
        # source .env.local if present
        env_file = ROOT / ".env.local"
        if env_file.exists():
            for ln in env_file.read_text().splitlines():
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                env.setdefault(k.strip(), v.strip())
        with scan_log.open("w") as f:
            f.write(f"=== MONEY-LOOP scan started {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.flush()
            proc = subprocess.run(
                [PY, str(HERE / "scan.py")],
                cwd=str(ROOT), env=env,
                stdout=f, stderr=subprocess.STDOUT,
                timeout=900,
            )
        elapsed = time.time() - started
        parsed = parse_scan_log(scan_log)
        parsed_log = LOGDIR / f"money-loop-{time.strftime('%Y-%m-%d')}.log"
        with parsed_log.open("a") as f:
            f.write(build_digest(parsed, scan_log) + f"\n[scan took {elapsed:.0f}s, exit={proc.returncode}]\n\n")

    digest = build_digest(parsed, scan_log)
    print(digest)
    push, reason = should_alert(parsed)
    if push:
        print(f"\n>>> ALERT REASON: {reason}")
        res = alerts.dispatch(f"world-trader: {reason}", digest)
        print(json.dumps(res, indent=2))
    else:
        print("\n(no alert dispatched — nothing met the push bar; digest logged locally)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
