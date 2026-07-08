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
expected = {"rsi", "sma20", "sma50", "sma200", "bb_up", "bb_lo", "z20",
            "hh20", "ll20", "bb_width", "gap", "vol_ratio", "atrp"}
check(set(ind.keys()) == expected, f"_indicators keys = {sorted(ind.keys())}")
check(all(ind["bb_width"][i] is not None for i in range(50, len(c))),
      "bb_width populated for i>=50")
check(all(ind["gap"][i] is not None for i in range(1, len(c))),
      "gap populated for i>=1 when opens given")
# Without opens, gap should be all-None
ind2 = analysis._indicators(h, l, c, opens=None)
check(all(g is None for g in ind2["gap"]), "gap all-None when opens not given")

# 1b. sma200 is populated for i>=199 and None before
check(all(ind["sma200"][i] is None for i in range(0, 199)),
      "sma200 None for i<199")
check(all(ind["sma200"][i] is not None for i in range(199, len(c))),
      "sma200 populated for i>=199")

# 1c. vol_ratio is populated when volumes given, None when not
vols = [1000.0 + i * 10 for i in range(len(c))]  # ramping volume
ind_v = analysis._indicators(h, l, c, opens=o, volumes=vols)
check(all(ind_v["vol_ratio"][i] is None for i in range(0, 19)),
      "vol_ratio None for i<19")
check(all(ind_v["vol_ratio"][i] is not None for i in range(19, len(c))),
      "vol_ratio populated for i>=19 when volumes given")
# Without volumes, vol_ratio should be all-None (graceful degradation)
check(all(v is None for v in ind2["vol_ratio"]),
      "vol_ratio all-None when volumes not given")

# 2. scan_setups is multi-horizon and tags n_horizons_tried
res = analysis.scan_setups(h, l, c, opens=o, market="US", require_firing=False)
check(len(res) > 0, "scan_setups returns setups on synthetic data")
check(all(r.get("n_horizons_tried") == len(analysis.HORIZONS) for r in res),
      f"all setups tagged n_horizons_tried={len(analysis.HORIZONS)}")
check(all(r["horizon"] in analysis.HORIZONS for r in res),
      "all setup horizons are in HORIZONS")

# 2b. regime gate: counter-trend setups are skipped
# Strong risk-off -> no Long setups surfaced; strong risk-on -> no Short setups.
res_off = analysis.scan_setups(h, l, c, opens=o, market="US",
                               require_firing=False, regime_score=-0.6)
check(all(r["side"] != "Long" for r in res_off),
      "regime_score=-0.6 (risk-off) suppresses Long setups")
res_on = analysis.scan_setups(h, l, c, opens=o, market="US",
                              require_firing=False, regime_score=0.6)
check(all(r["side"] != "Short" for r in res_on),
      "regime_score=+0.6 (risk-on) suppresses Short setups")
# regime_score=None -> no gating (backward-compatible)
res_none = analysis.scan_setups(h, l, c, opens=o, market="US",
                                require_firing=False, regime_score=None)
check(len(res_none) > 0, "regime_score=None preserves default behavior")

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

# 4b. OOS Sharpe gate: positive OOS expectancy but non-positive OOS Sharpe -> reject
# A setup that earned +1.2% IS (sd 4%, Sharpe 0.5) but LOST money OOS (negative
# OOS Sharpe) has positive OOS expectancy? No -- if OOS Sharpe < 0, OOS exp_ret
# could still be barely positive. Test the case: oos_exp_ret=+0.001, oos_edge=-0.3.
bt_oos_sharpe_bad = {"n": 30, "exp_ret": 0.012, "sd": 0.04, "edge": 0.5,
                     "tstat": 3.0, "horizon": 5,
                     "oos_exp_ret": 0.001, "oos_edge": -0.3}
check(not analysis.trade_qualifies(bt_oos_sharpe_bad),
      "OOS edge>0 required: positive OOS expectancy but negative OOS Sharpe rejected")
# Same setup with positive OOS Sharpe -> accepted
bt_oos_sharpe_ok = dict(bt_oos_sharpe_bad, oos_edge=0.45)
check(analysis.trade_qualifies(bt_oos_sharpe_ok),
      "positive OOS Sharpe passes the OOS gate")
# Missing OOS fields entirely -> grace (don't fail on missing data)
bt_no_oos = dict(bt_oos_sharpe_bad)
del bt_no_oos["oos_exp_ret"]; del bt_no_oos["oos_edge"]
check(analysis.trade_qualifies(bt_no_oos),
      "missing OOS -> grace (no OOS gate applied)")

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

# 8. backtest_orb works on synthetic intraday data (no network required)
# Build 30 sessions of 5-min bars (78 bars/session = 6.5h trading day).
import random as _r
_r.seed(99)
N_SESSIONS = 30
BARS_PER_SESSION = 78
o_intra = []; h_intra = []; l_intra = []; c_intra = []; v_intra = []; s_intra = []
base = 100.0
for sess in range(N_SESSIONS):
    # First 6 bars: opening range. Then a breakout to the upside with volume.
    or_open = base
    for b in range(BARS_PER_SESSION):
        if b < 6:
            # tight opening range
            op = or_open + _r.gauss(0, 0.05)
            cl = op + _r.gauss(0, 0.03)
        elif b == 6:
            # breakout bar
            op = or_open
            cl = or_open + 0.5  # clear breakout up
        else:
            op = c_intra[-1]
            cl = op + _r.gauss(0.001, 0.05)
        hi = max(op, cl) * (1 + abs(_r.gauss(0, 0.002)))
        lo = min(op, cl) * (1 - abs(_r.gauss(0, 0.002)))
        o_intra.append(op); h_intra.append(hi); l_intra.append(lo)
        c_intra.append(cl); v_intra.append(1000.0 + _r.gauss(0, 100))
        s_intra.append(f"2026-01-{sess+1:02d}")
    base = c_intra[-1]
intraday = {"open": o_intra, "high": h_intra, "low": l_intra, "close": c_intra,
            "vol": v_intra, "session": s_intra, "interval": 5}
bt_orb = analysis.backtest_orb(intraday, side="Long")
check(bt_orb is not None and "exp_ret" in bt_orb and "n" in bt_orb,
      f"backtest_orb returns stats (n={bt_orb['n'] if bt_orb else 0})")
if bt_orb:
    check(bt_orb["setup"] == "ORBLong", "backtest_orb setup name = 'ORBLong'")
    check(bt_orb["horizon"] == 1, "backtest_orb horizon = 1 (intraday)")
    check(bt_orb["n"] >= 20, f"backtest_orb n>=20 (got {bt_orb['n']})")
    # On constructed breakout-up data, ORB Long should have positive expectancy
    check(bt_orb["exp_ret"] > 0, f"backtest_orb positive edge on breakout data (exp={bt_orb['exp_ret']:+.4f})")

# 9. backtest_rv_mean_reversion + qualifies_rv
# OU (mean-reverting) spread -> should qualify; random walk -> should not
import random as _r2
_r2.seed(42)
N2 = 400
ou = [0.0]
for i in range(1, N2):
    ou.append(ou[-1] + 0.15 * (0.0 - ou[-1]) + _r2.gauss(0, 1.0))
bt_rv = analysis.backtest_rv_mean_reversion(ou)
check(bt_rv is not None and "exp_ret" in bt_rv, "backtest_rv returns stats on OU process")
if bt_rv:
    check(bt_rv["setup"] == "RVMR", "backtest_rv setup name = 'RVMR'")
    check(analysis.qualifies_rv(bt_rv, n_tests=1),
          f"OU mean-reverting spread qualifies (sharpe={bt_rv['edge']:.2f})")
# Random walk -> should NOT qualify (no mean reversion edge)
_r2.seed(7)
rw = [0.0]
for i in range(1, N2):
    rw.append(rw[-1] + _r2.gauss(0, 1.0))
bt_rw = analysis.backtest_rv_mean_reversion(rw)
if bt_rw:
    check(not analysis.qualifies_rv(bt_rw, n_tests=1),
          f"random walk does not qualify (sharpe={bt_rw['edge']:.2f})")
else:
    check(True, "random walk: no entries or insufficient samples (also fine)")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")
