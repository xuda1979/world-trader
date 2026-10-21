"""TDD tests for wt.options_cboe (keyless CBOE delayed-quote chain analytics).

Run: python3 tools/test_options_cboe.py
Exits 0 on pass, 1 on any failure. Offline: synthetic chains verify parsing
and aggregation invariants only. No synthetic PnL claims (2026-07-26 policy).

Locks in:
  1. parse_contract: OCC symbol -> (root, expiry, right, strike)
  2. chain_analytics: put/call, ATM IV, 25d skew on a synthetic chain
  3. chain_url: index symbols get the underscore-prefixed URL form
  4. aggregate: multi-name rollup with breadth + per-name error isolation
  5. fail-closed on empty or malformed chains
  6. options_rviv: stooq-first history provider, dead yahoo path removed
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from wt import options_cboe as oc

failures = []


def check(cond, msg):
    if cond:
        print("  PASS " + msg)
    else:
        print("  FAIL " + msg)
        failures.append(msg)


def mk(root, cp, strike, vol=0.0, oi=0.0, iv=0.0, bid=0.0, ask=0.0, delta=None):
    sym = root + "260918" + cp + "{:08d}".format(int(round(strike * 1000)))
    d = dict(option=sym, volume=vol, open_interest=oi, iv=iv, bid=bid, ask=ask)
    if delta is not None:
        d["delta"] = delta
    return d


print("[1] parse_contract")
cases = [
    ("SPX260918C00200000", ("SPX", "260918", "C", 200.0)),
    ("SPXW260918P04500000", ("SPXW", "260918", "P", 4500.0)),
    ("TSLA260904C00050000", ("TSLA", "260904", "C", 50.0)),
    ("GME260911P00019000", ("GME", "260911", "P", 19.0)),
    ("BRK.B261218C00450000", ("BRK.B", "261218", "C", 450.0)),
]
for sym, want in cases:
    got = oc.parse_contract(sym)
    check(got == want, "parse " + sym + " -> " + repr(want) + ", got " + repr(got))

for bad in ["SPX", "SPX260918X00200000", "spx260918c00200000", ""]:
    try:
        oc.parse_contract(bad)
        check(False, "parse " + repr(bad) + " must raise")
    except Exception:
        check(True, "parse " + repr(bad) + " raises")

print("[2] chain_analytics")
chain = [
    mk("SPX", "C", 7700, vol=100, oi=2000, iv=0.058, bid=10.0, ask=10.4, delta=0.52),
    mk("SPX", "P", 7700, vol=200, oi=3000, iv=0.060, bid=10.0, ask=10.4, delta=-0.48),
    mk("SPX", "C", 7750, vol=30, oi=500, iv=0.056, bid=3.0, ask=3.2, delta=0.27),
    mk("SPX", "P", 7675, vol=60, oi=900, iv=0.067, bid=4.0, ask=4.3, delta=-0.25),
    mk("SPX", "C", 7850, vol=10, oi=100, iv=0.050, bid=0.5, ask=0.6, delta=0.09),
    mk("SPX", "P", 7600, vol=20, oi=200, iv=0.072, bid=1.0, ask=1.1, delta=-0.15),
]
spot = 7718.6
a = oc.chain_analytics(chain, spot=spot)
check(isinstance(a, dict), "returns dict")
check(abs(a["pc_vol"] - 280.0 / 140.0) < 1e-9, "pc_vol = 280/140 = 2.0")
check(abs(a["pc_oi"] - 4100.0 / 2600.0) < 1e-9, "pc_oi = 4100/2600")
check(abs(a["atm_iv_call"] - 0.058) < 1e-9, "atm_iv_call = strike nearest spot")
check(a["atm_iv_put"] > a["atm_iv_call"], "put ATM iv above call ATM iv")
check(a["skew_25d"] > 0, "skew_25d positive (25d put iv minus 25d call iv)")
check(a["total_volume"] == 420, "total_volume sums all contracts")
check(a["total_oi"] == 6700, "total_oi sums all contracts")
check(a["n_contracts"] == 6, "n_contracts counts parsed contracts")
check(abs(a["atm_iv"] - 0.059) < 1e-9, "atm_iv averages call and put ATM")

print("[3] chain_url")
check(oc.chain_url("SPX").endswith("/_SPX.json"), "index SPX gets underscore form")
check(oc.chain_url("VIX").endswith("/_VIX.json"), "index VIX gets underscore form")
check(oc.chain_url("AAPL").endswith("/AAPL.json"), "equity AAPL unprefixed")
check(oc.chain_url("SPX").startswith("https://cdn.cboe.com/"), "cdn host")

print("[4] aggregate")


def fetch_ok(sym):
    out = []
    for i in range(5):
        out.append(mk(sym, "C", 100 + i, vol=10, oi=100, iv=0.30, bid=1.0, ask=1.1, delta=0.4))
        out.append(mk(sym, "P", 100 + i, vol=30, oi=100, iv=0.34, bid=1.0, ask=1.1, delta=-0.4))
    return out


agg = oc.aggregate(["AAA", "BBB", "CCC"], fetch=fetch_ok)
check(agg["n_ok"] == 3 and agg["n_fail"] == 0, "all names ok")
check(agg["names"] == ["AAA", "BBB", "CCC"], "names preserves order")
check(all(v["pc_vol"] > 1.0 for v in agg["per_name"].values()), "per-name pc_vol above 1")
check(agg["breadth_pc_vol_gt1"] == 3, "breadth counts names with pc_vol above 1")
check(abs(agg["median_pc_vol"] - 3.0) < 1e-9, "median_pc_vol")


def fetch_bad(sym):
    if sym == "BAD":
        raise IOError("down")
    return fetch_ok(sym)


agg2 = oc.aggregate(["AAA", "BAD", "CCC"], fetch=fetch_bad)
check(agg2["n_ok"] == 2 and agg2["n_fail"] == 1, "failed name isolated")
check("BAD" in agg2["errors"], "error recorded per name")
check(agg2["names"] == ["AAA", "CCC"], "failed name dropped from names")

print("[5] fail-closed")
for bad_chain, msg in (([], "empty"), ([dict(option="GARBAGE", volume=1)], "malformed")):
    try:
        oc.chain_analytics(bad_chain, spot=100.0)
        check(False, msg + " chain must raise")
    except ValueError:
        check(True, msg + " chain raises ValueError")

print("[6] rviv current public API (refactored; dedicated suite in "
      "tools/quant/data/cboe_options/test_options_rviv_revival.py)")
import wt.options_rviv as rviv
# The pre-refactor API (HISTORY_PROVIDERS / yahoo_history / _parse_challenge /
# solve_pow / _nasdaq_rows) was REMOVED when rviv moved to wt.sources.nasdaq_history.
# This smoke block now verifies the CURRENT public surface; full behavior coverage
# lives in the revival test (8 checks).
check(callable(rviv.scan), "rviv.scan callable (iron-condor scanner entry point)")
check(callable(rviv.realized_vol), "rviv.realized_vol callable")
check(callable(rviv.atm_metrics), "rviv.atm_metrics callable")
check(callable(rviv._occ_parse), "rviv._occ_parse callable (OCC contract parser)")
check(not hasattr(rviv, "HISTORY_PROVIDERS"), "removed HISTORY_PROVIDERS (was in iter13 snapshot API)")
check(not hasattr(rviv, "yahoo_history"), "removed yahoo_history (dead provider)")
check(not hasattr(rviv, "_parse_challenge"), "removed stooq PoW _parse_challenge")
check(not hasattr(rviv, "solve_pow"), "removed stooq PoW solve_pow")
check(not hasattr(rviv, "_nasdaq_rows"), "removed _nasdaq_rows (inlined via wt.sources.nasdaq_history)")

print("")
if failures:
    print("FAILED " + str(len(failures)) + " checks")
    sys.exit(1)
print("ALL GREEN")
sys.exit(0)
