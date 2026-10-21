#!/usr/bin/env python3
"""Probe: does widening the champion's factor universe reduce fragility?

The champion (n10_r14, polygon) keeps exactly the 5-factor polygon set
[liq_turnover, mom_12_1m, range_vol_60d, resid_mom_6m, vol_60d], and the
08-13 diag found ALL measurable factors DECAYED in the second half — the
edge is carried by adaptation, not stable factor strength. If the screen
universe dries up below ~3 factors the strategy degrades. This probe asks
whether the unused factor families (OHLC-based, v2 academic alpha) add
candidates that (a) pass the ICIR screen, (b) hold SR, (c) improve the
second-half (OOS) half — i.e. headroom for the fragility failure mode.

Variants (on the deployed champion config, loaded from
results/live_signal_polygon/config.json):
  base      — as-deployed
  +ohlc     — use_ohlc_factors=True   (OHLC-based factors, orthogonal family)
  +v2       — use_v2_factors=True     (ivol, MAX, beta-arb, trend-eff, ...)
  +ohlc+v2  — both
Each exports to results/verify/factor_uni_*; metrics + kept factors + half
Sharpe printed as a table.

Usage: python -m tools.quant.ls.probe_factor_universe
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from tools.quant.ls.config import Config
from tools.quant.ls import runner

TD = 252

def half_sharpe(r: pd.Series) -> str:
    r = r.dropna()
    n = len(r)
    h1, h2 = r.iloc[:n // 2], r.iloc[n // 2:]
    s = lambda x: (x.mean() / x.std()) * np.sqrt(TD) if len(x) > 30 and x.std() > 0 else np.nan
    return f"{s(h1):.2f}/{s(h2):.2f}"

def main() -> int:
    champ = json.load(open(os.path.join(
        ROOT, "tools/quant/ls/results/live_signal_polygon/config.json")))
    variants = [
        ("base",     {}),
        ("+ohlc",    {"use_ohlc_factors": True}),
        ("+v2",      {"use_v2_factors": True}),
        ("+ohlc+v2", {"use_ohlc_factors": True, "use_v2_factors": True}),
    ]
    rows = []
    for tag, over in variants:
        cfg = Config.from_dict(champ).set(
            name=f"factor_uni_{tag.strip('+').replace('+', '_')}",
            out_dir=f"tools/quant/ls/results/verify/factor_uni_{tag.strip('+').replace('+', '_')}",
            plot=False, verbose=False, **over)
        print(f"\n=== variant {tag}: {over or '(as deployed)'} ===", flush=True)
        res = runner.run(cfg)
        m = res["metrics"]
        n_factors = len(res.get("processed_factors", {}))
        kept = res.get("kept_factors", [])
        daily = res["result"]["daily_returns"]
        rows.append({
            "variant": tag, "SR": m.get("sharpe"), "ret": m.get("annual_return"),
            "DD": m.get("max_drawdown"), "TO": m.get("annual_turnover"),
            "n_factors": n_factors, "n_kept": len(kept), "kept": ",".join(kept),
            "halfSR": half_sharpe(daily),
        })
    print("\n=== SUMMARY ===")
    hdr = f"{'variant':<10} {'SR':>6} {'ret%':>7} {'DD%':>7} {'TO':>5} {'univ':>5} {'kept':>4}  halfSR(1st/2nd)  kept-factors"
    print(hdr)
    for r in rows:
        print(f"{r['variant']:<10} {r['SR']:>6.3f} {r['ret']*100:>7.2f} {r['DD']*100:>7.2f} "
              f"{r['TO']:>5.2f} {r['n_factors']:>5d} {r['n_kept']:>4d}  {r['halfSR']:>13}  {r['kept'][:80]}")
    json.dump(rows, open(os.path.join(
        ROOT, "tools/quant/ls/results/verify/factor_uni_summary.json"), "w"), indent=1)
    print("\nsaved: results/verify/factor_uni_summary.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
