"""TDD RED tests for HUNT_LIQREV engine. Run BEFORE lib exists -> must FAIL (RED).
Exact-number reconciliation gates per SUPERPOWERS_RIGOR.md."""
import numpy as np, pandas as pd
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_LIQREV")
from liqrev_lib import simulate, vt_scale  # must exist

COST = 6.4e-4  # per side
BORROW = 0.5e-4 / 252  # per day on short notional

def test_T1_no_same_day_leak():
    # w decided at t (rows), earns r_{t+1}. r=[0.05,0.10,0], w=[1,1,1], w_prev0=0.
    idx = pd.date_range("2020-01-01", periods=3)
    r = pd.Series([0.05, 0.10, 0.0], index=idx)
    w = pd.Series([1.0, 1.0, 1.0], index=idx)
    net, parts = simulate(w, pd.DataFrame({"A": r}), borrow_daily=BORROW)
    # day0: gross must be ZERO (position from t=-1 = 0), cost = 6.4e-4*1
    assert abs(net.iloc[0] - (-COST*1.0)) < 1e-15, f"day0 net {net.iloc[0]} != {-COST} -> same-day leak or cost bug"
    # day1: gross = 1*0.10, turnover |w1-w0|=0, no cost
    assert abs(net.iloc[1] - 0.10) < 1e-15, f"day1 net {net.iloc[1]} != 0.10"
    assert abs(net.iloc[2] - 0.0) < 1e-15

def test_T2_cost_reconciles_to_turnover():
    rng = np.random.default_rng(7)
    idx = pd.date_range("2020-01-01", periods=250)
    w = pd.Series(rng.normal(0, 0.3, 250).clip(-1, 1), index=idx)
    r = pd.DataFrame(0.0, index=idx, columns=["A"])
    net, parts = simulate(w, pd.DataFrame({"A": 0.0}, index=idx), borrow_daily=BORROW)
    turn = w.diff().abs().fillna(w.abs().iloc[0]).sum()
    charged = parts["cost"].sum()
    assert abs(charged - COST * turn) < 1e-15, f"charged {charged} != {COST*turn}"

def test_T3_borrow_on_short_notional():
    idx = pd.date_range("2020-01-01", periods=3)
    r = pd.DataFrame(0.0, index=idx, columns=["A"])
    w = pd.Series([-0.5, -0.5, -0.5], index=idx)
    net, parts = simulate(w, pd.DataFrame({"A": 0.0}, index=idx), borrow_daily=BORROW)
    exp1 = -0.5 * BORROW  # day1: short held, zero turnover
    assert abs(net.iloc[1] - exp1) < 1e-18, f"day1 {net.iloc[1]} != {exp1}"
    exp0 = -COST*0.5  # entry cost at close of day0; borrow on the new short accrues from day1 (T+1)
    assert abs(net.iloc[0] - exp0) < 1e-18

def test_T4_vt_scale_no_lookahead():
    rng = np.random.default_rng(3)
    idx = pd.date_range("2020-01-01", periods=300)
    r = pd.Series(rng.normal(0, 0.01, 300), index=idx)
    s = vt_scale(r)  # scale_t uses ONLY r <= t-1 (expanding, min60, cap3)
    # perturb ONLY the last return r_t -> scale_t MUST NOT change (strict: excludes r_t)
    r2 = r.copy(); r2.iloc[-1] += 0.05
    s2 = vt_scale(r2)
    assert abs(s.iloc[-1] - s2.iloc[-1]) < 1e-15, "vt scale at t sees same-day return -> LOOKAHEAD"
    # perturb a FUTURE return (append) -> past scales unchanged
    r3 = pd.concat([r, pd.Series([0.07], index=[idx[-1] + pd.Timedelta(days=1)])])
    s3 = vt_scale(r3)
    assert abs(s3.iloc[:-1].values - s.values).max() < 1e-15, "future perturbation changed past scale"
    # exact value check at pos 100: scale_t = clip(0.10/std(r[0..99] ddof=1)*sqrt252, cap 3)
    rv100 = r.iloc[:100].std(ddof=1) * np.sqrt(252)
    exp = min(0.10 / rv100, 3.0)
    assert abs(s.iloc[100] - exp) < 1e-12, f"scale {s.iloc[100]} != {exp}"

def test_T5_endtoend_turnover_matches_charged():
    # mini synthetic panel through full engine path
    rng = np.random.default_rng(11)
    idx = pd.date_range("2020-01-01", periods=120)
    px = pd.DataFrame(rng.normal(100, 1, (120, 4)).cumsum(axis=0), index=idx,
                      columns=list("ABCD"))
    import liqrev_lib as L
    rets = px.pct_change()
    w = L.xs_weights(rets, lb=1, direction=-1, bucket="tercile")
    s = L.vt_scale_from_w(w, rets)
    ws = w.mul(s, axis=0)
    net, parts = L.run_book(w, rets, borrow_ann=0.5)
    turn = (ws - ws.shift(1).fillna(0.0)).abs().sum().sum()
    assert abs(parts["cost"].sum() - 6.4e-4 * turn) < 1e-12, "engine cost != 6.4bps*turnover"

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    nfail = 0
    for f in fns:
        try:
            f(); print(f"PASS {f.__name__}")
        except Exception as e:
            nfail += 1; print(f"FAIL {f.__name__}: {type(e).__name__}: {e}")
    print(f"RED/GREEN SUMMARY: {len(fns)-nfail}/{len(fns)} pass")
    sys.exit(0 if nfail == 0 else 1)
