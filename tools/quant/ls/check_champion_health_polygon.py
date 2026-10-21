"""Polygon champion health monitor (operationalizes the 2026-08-13 rule).

Runs the champion (n10_r14_lev3, ~40s) and reports:
  1. full-window SR vs baseline (1.68)
  2. ACTIVE-period SR (2025-08+, post warm-up) vs baseline (2.23)
  3. kept factor set vs baseline 5
  4. ICIR decay flags for the kept factors (the watch-verdict risk)
Warnings (per RESEARCH_LOG 2026-08-13):
  - fallback keeps < 3 factors            -> WARN (factor universe drying)
  - active SR < ~1.0                       -> WARN (edge degrading)
  - > 3 kept factors flagged decayed      -> WARN (fragile edge)
Usage: python -m tools.quant.ls.check_champion_health_polygon
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner


def main() -> int:
    import dataclasses
    d = json.load(open(os.path.join(ROOT, "tools/quant/ls/results/champion_n10_r14_lev3/config.json")))
    valid = {f.name for f in dataclasses.fields(Config)}
    d = {k: v for k, v in d.items() if k in valid}
    cfg = Config(**{**d, "name": "health_check", "diag_window_sweep": (),
                    "plot": False, "verbose": False})
    res = runner.run(cfg)
    m = res["metrics"]
    sr = m["sharpe"]
    kept = list(res.get("kept_factors", []))

    # active-period SR from the daily returns
    r = res["result"]["daily_returns"]
    act = r[r.index >= "2025-08-01"]
    act_sr = float(act.mean() / act.std() * (252 ** 0.5)) if len(act) > 60 else float("nan")

    # ICIR decay flags for kept factors (diagnostics holds a DataFrame)
    decay_df = res.get("diagnostics", {}).get("icir_decay")
    decay_map = {}
    if decay_df is not None and not decay_df.empty:
        for f, row in decay_df.iterrows():
            decay_map[f] = dict(row)
    decayed = [f for f in kept if decay_map.get(f, {}).get("flag") == "decayed"]

    warns = []
    if len(kept) < 3:
        warns.append(f"factor universe drying: only {len(kept)} kept factors")
    if act_sr < 1.0:
        warns.append(f"active SR {act_sr:.2f} below 1.0")
    if len(decayed) > 3:
        warns.append(f"{len(decayed)}/{len(kept)} kept factors flagged decayed: {decayed}")

    print(f"=== POLYGON CHAMPION HEALTH (as of {r.index[-1].date()}) ===")
    print(f"Full-window SR : {sr:.3f} (baseline 1.68)")
    print(f"Active SR      : {act_sr:.3f} (baseline 2.23, 2025-08+)")
    print(f"Kept factors   : {kept} ({len(kept)})")
    print(f"Decay flags    : {decayed if decayed else 'none'}")
    if warns:
        print("  !! " + " | ".join(warns))
        return 2
    print("  HEALTH OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
