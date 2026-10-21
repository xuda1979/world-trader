"""pipeline_guard.py — institutionalize 'one backtest path' + 'PASS means honest' (items 2/3).

Reusable CI checks the company runs so the honest rules are enforced in exactly one place:
  1. bt_only(): reject backtest logic written in bespoke heredocs/scripts that don't route
     through campaign/bt/ (they can silently drop the 6.4bps/T+1 contracts). Static scan:
     flags scripts that compute Sharpe/ann/MaxDD from raw returns instead of importing bt.
  2. champion_publish_gate(): before a new champion can be quoted/committed, the honest_verify
     gauntlet (byte-repro + full-|dW| cost + T+1 causal + flatten) MUST pass. Gives the
     "no number without reconciliation" guarantee (item 3).
  3. decorr_first(): a candidate sleeve must pass corr_gate (|corr|<0.15 to champion) before
     it is worth the full gate battery (item 2).
Fail-closed: any rule that can't be evaluated returns False (block), per ai-devops.
"""
import os
import re
import subprocess
import sys

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
# make `import lib` work whether run as a script or imported (CI entrypoint is `python3 .../lib/pipeline_guard.py`):
# add the PARENT of this file (campaign/team) so `lib` (the package holding __init__.py) resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, f"{ROOT}/campaign")  # for `import bt` in honest_gate


def bt_only(paths, since=None):
    """Return files computing return-metrics WITHOUT campaign/bt/.

    `since` (str, e.g. "2026-09-08") applies the one-backtest-path rule ONLY to files modified on
    or after that cutoff. Historical scripts stay as documented debt (not CI blockers); NEW backtest
    code must route through campaign/bt/ so the honesty contracts (T+1, 6.4bps/side) live in one place.
    """
    import datetime
    offenders = []
    bt_tokens = re.compile(r"from bt\.|import bt|campaign/bt/|bt\.metrics|bt\.gates|bt\.engine")
    metric_tokens = re.compile(r"sharpe|ann_geo|max_dd|neg_years|apply_cost|6\.4|6\.4e-4|bps")
    cutoff = datetime.datetime.fromisoformat(since) if since else None
    for p in paths:
        if not os.path.isfile(p):
            continue
        if cutoff is not None:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p))
            if mtime < cutoff:
                continue  # historical debt, not a new-code violation
        try:
            src = open(p).read()
        except Exception:
            offenders.append((p, "unreadable"))
            continue
        if metric_tokens.search(src) and not bt_tokens.search(src):
            offenders.append((p, "has return-metrics but not bt/"))
    return offenders


def champion_publish_gate():
    """Block a champion quote/publish unless the honesty gauntlet + flatten sweep passes."""
    from lib import honest_gate
    ok, rep = honest_gate.honest_verify()
    return ok, rep


def decorr_first(candidate_csv, corr_max=0.15):
    """Pass only if candidate is decorrelated to the champion blend (item 2)."""
    from lib import corr_gate
    df = pd.read_csv(candidate_csv)
    col = "ret" if "ret" in df.columns else df.columns[1]
    return corr_gate.gate(df[col].dropna().astype(float), corr_max=corr_max)


if __name__ == "__main__":
    # CI entrypoint: run the full company guard battery, fail-closed (new code only for BT-ONLY).
    from pathlib import Path
    todo = sys.argv[1:] if len(sys.argv) > 1 else []
    # support: `--since 2026-09-08` to scope BT-ONLY to new code after a cutover FIXME (default: today)
    since = "2026-09-08"
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]
    if not todo:
        todo = [str(p) for p in Path(ROOT + "/campaign/scripts").rglob("*.py")][:400]
        todo += [str(p) for p in Path(ROOT + "/campaign/team/agents").rglob("*.py")][:120]
    offenders = bt_only(todo, since=since)
    ok_gate, _ = champion_publish_gate()
    print(f"BT-ONLY (new code since {since}):",
          "PASS" if not offenders else f"FAIL {len(offenders)} new-code offenders")
    for p, why in offenders[:8]:
        print("   -", p, f"({why})")
    print("HONEST-GATE:", "PASS" if ok_gate else "FAIL")
    sys.exit(0 if (not offenders and ok_gate) else 1)
