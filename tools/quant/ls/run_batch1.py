import sys, os, time, numpy as np
sys.path.insert(0, ".")
from tools.quant.ls.run_research_v3 import base_cfg, run_one

tests = [
    ("v3_base_d2_n200", dict(use_v2=True, bypass_ic_screen=True, gbrt_max_depth=2, gbrt_n_estimators=200)),
    ("v3_nov2_d2_n200", dict(use_v2=False, bypass_ic_screen=True, gbrt_max_depth=2, gbrt_n_estimators=200)),
    ("v3_screen_d2_n200", dict(use_v2=True, bypass_ic_screen=False, icir_threshold=0.08, ic_mean_threshold=0.005, ic_bonferroni=False, gbrt_max_depth=2, gbrt_n_estimators=200)),
    ("v3_d1_n500", dict(use_v2=True, bypass_ic_screen=True, gbrt_max_depth=1, gbrt_n_estimators=500)),
    ("v3_d3_n500", dict(use_v2=True, bypass_ic_screen=True, gbrt_max_depth=3, gbrt_n_estimators=500)),
    ("v3_huber_d2", dict(use_v2=True, bypass_ic_screen=True, gbrt_max_depth=2, gbrt_n_estimators=200, gbrt_loss="huber", gbrt_alpha=0.9)),
]

results = []
for name, kw in tests:
    cfg = base_cfg(name, use_v2=kw.pop("use_v2", True))
    cfg.set(**kw)
    print("Running: " + name)
    t0 = time.time()
    try:
        b = run_one(cfg)
        dt = time.time() - t0
        m = b["metrics"]; v = b["verdict"]
        r = dict(name=name, sharpe=m.get("sharpe",np.nan), ann_ret=m.get("annual_return",np.nan), ann_vol=m.get("annual_volatility",np.nan), max_dd=m.get("max_drawdown",np.nan), sortino=m.get("sortino",np.nan), calmar=m.get("calmar",np.nan), turnover=m.get("annual_turnover",np.nan), verdict=v["assessment"], n_flags=v["n_flags"], n_kept=len(b["kept"]))
        results.append(r)
        print("  S=%.3f  Ret=%.4f  DD=%.4f  TO=%.1f  nF=%d  %s(%df) dt=%ds" % (r["sharpe"], r["ann_ret"], r["max_dd"], r["turnover"], r["n_kept"], r["verdict"], r["n_flags"], int(dt)))
    except Exception as e:
        import traceback; traceback.print_exc()
        results.append(dict(name=name, error=str(e)[:200]))

print("=== SUMMARY ===")
ok = sorted([r for r in results if isinstance(r.get("sharpe"), (int,float)) and np.isfinite(r["sharpe"])], key=lambda r: r["sharpe"], reverse=True)
for i, r in enumerate(ok):
    print("%d. %-30s S=%.3f  ret=%.4f  dd=%.4f  to=%.1f  nF=%d  %s(%df)" % (i+1, r["name"], r["sharpe"], r["ann_ret"], r["max_dd"], r["turnover"], r["n_kept"], r["verdict"], r["n_flags"]))
import pandas as pd
pd.DataFrame(results).to_csv("tools/quant/ls/results/focused_batch1.csv", index=False)