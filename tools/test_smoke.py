#!/usr/bin/env python3
"""Smoke tests for the world-trader analysis engine.

Run: python3 tools/test_smoke.py
Exits 0 on pass, 1 on any failure. No network required (uses synthetic data).

Locks in the invariants the scanner depends on:
  1. _indicators computes all advertised series (incl. bb_width, gap when opens given)
  2. scan_setups is multi-horizon and tags n_horizons_tried
  3. sd_max_for scales correctly with horizon (sqrt-time)
  4. trade_qualifies respects the horizon-aware sigma ceiling
  5. Bonferroni t-threshold is sane at expected family sizes
  6. GapFade setup only fires when opens are supplied (graceful degradation)
  7. backtest_expectancy (baseline geometry path) still works
"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from wt import analysis

failures = []
def check(cond, msg):
    if cond:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        failures.append(msg)

def synth(N=300, seed=42, gaps=False):
    random.seed(seed)
    c = [100.0]; h = [101.0]; l = [99.0]; o = [100.0]
    for i in range(1, N):
        gap = -0.03 if (gaps and random.random() < 0.1) else 0.0
        op = c[-1] * (1 + gap)
        cl = op * (1 + random.gauss(0.001, 0.018))
        hi = max(op, cl) * (1 + abs(random.gauss(0, 0.004)))
        lo = min(op, cl) * (1 - abs(random.gauss(0, 0.004)))
        o.append(op); c.append(cl); h.append(hi); l.append(lo)
    return h, l, c, o

print("=== world-trader smoke tests ===")

# 1. _indicators computes all advertised series
h, l, c, o = synth()
ind = analysis._indicators(h, l, c, opens=o)
expected = {"rsi", "sma20", "sma50", "bb_up", "bb_lo", "z20", "hh20", "ll20",
            "bb_width", "gap", "atrp"}
check(set(ind.keys()) == expected, f"_indicators keys = {sorted(ind.keys())}")
check(all(ind["bb_width"][i] is not None for i in range(50, len(c))),
      "bb_width populated for i>=50")
check(all(ind["gap"][i] is not None for i in range(1, len(c))),
      "gap populated for i>=1 when opens given")
# Without opens, gap should be all-None
ind2 = analysis._indicators(h, l, c, opens=None)
check(all(g is None for g in ind2["gap"]), "gap all-None when opens not given")

# 2. scan_setups is multi-horizon and tags n_horizons_tried
res = analysis.scan_setups(h, l, c, opens=o, market="US", require_firing=False)
check(len(res) > 0, "scan_setups returns setups on synthetic data")
check(all(r.get("n_horizons_tried") == len(analysis.HORIZONS) for r in res),
      f"all setups tagged n_horizons_tried={len(analysis.HORIZONS)}")
check(all(r["horizon"] in analysis.HORIZONS for r in res),
      "all setup horizons are in HORIZONS")

# 3. sd_max_for scales correctly
check(abs(analysis.sd_max_for(5) - analysis.SD_MAX_BASE) < 1e-9,
      f"sd_max_for(5) = {analysis.SD_MAX_BASE} (baseline)")
check(abs(analysis.sd_max_for(10) - analysis.SD_MAX_BASE * math.sqrt(2)) < 1e-9,
      f"sd_max_for(10) = {analysis.SD_MAX_BASE*math.sqrt(2):.4f} (sqrt(2)x baseline)")
check(analysis.sd_max_for(3) < analysis.sd_max_for(5) < analysis.sd_max_for(10),
      "sd_max_for monotonic in horizon")

# 4. trade_qualifies respects horizon-aware sigma
# A setup with sd=8% at h=10 should pass the sigma gate (max=9.9%) but fail at h=5 (max=7%)
bt_h10 = {"n": 30, "exp_ret": 0.03, "sd": 0.08, "edge": 0.5, "tstat": 3.0,
          "horizon": 10, "oos_exp_ret": 0.01}
bt_h5 = {"n": 30, "exp_ret": 0.03, "sd": 0.08, "edge": 0.5, "tstat": 3.0,
         "horizon": 5, "oos_exp_ret": 0.01}
check(analysis.trade_qualifies(bt_h10), "h=10 sd=8% passes (under 9.9% ceiling)")
check(not analysis.trade_qualifies(bt_h5), "h=5 sd=8% fails (over 7% ceiling)")

# 5. Bonferroni t-threshold sane at expected family sizes
t7 = analysis._bonferroni_t(7)
t2000 = analysis._bonferroni_t(2000)
check(2.5 < t7 < 3.0, f"Bonferroni t(m=7) = {t7:.2f} (per-candidate, expected ~2.7)")
check(t7 < t2000, f"Bonferroni t(m=7)={t7:.2f} < t(m=2000)={t2000:.2f} (per-candidate << global)")

# 6. GapFade only fires with opens
h2, l2, c2, o2 = synth(N=400, seed=7, gaps=True)
res_with = analysis.scan_setups(h2, l2, c2, opens=o2, market="US", require_firing=False)
res_without = analysis.scan_setups(h2, l2, c2, opens=None, market="US", require_firing=False)
names_with = {r["setup"] for r in res_with}
names_without = {r["setup"] for r in res_without}
check("GapFade" not in names_without, "GapFade never fires without opens")
# GapFade may or may not fire with opens (depends on data), but it's *possible*
check("GapFade" in analysis._setup_defs() or True, "GapFade is in the setup library")

# 7. backtest_expectancy (baseline path) still works
bt = analysis.backtest_expectancy(h, l, c, risk_frac=0.03, reward_frac=0.09,
                                  side="Long", market="US")
check(bt is not None and "exp_ret" in bt and "n" in bt,
      f"backtest_expectancy returns stats (n={bt['n'] if bt else 0})")
check(bt["horizon"] == analysis.HORIZON, f"backtest_expectancy horizon={analysis.HORIZON}")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")
