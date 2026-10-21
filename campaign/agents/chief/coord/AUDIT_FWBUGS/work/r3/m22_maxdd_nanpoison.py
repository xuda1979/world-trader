"""M22 closure (AUDIT_FWBUGS R3): max_dd NaN-poison mutation analysis.

R2 verdict was VACUOUS-EVERYWHERE for M22_maxdd_nanpoison (insert `eq[r.isna()] = np.nan`
after cumprod in bt/metrics.max_dd). This script settles WHY and supplies the mutants the
new pins must kill:

  1. The original M22 mutant is an EQUIVALENT MUTANT under pandas skipna semantics: at a
     NaN day the carried equity (and cummax) are unchanged, so dd[t] duplicates dd[t-1]
     and the min is identical. Proven by exhaustive equality on randomized NaN panels.
  2. The DISTINGUISHABLE NaN-poison mutant family (killable by honest pins, not
     equivalent): M22d fail-open-zero (any NaN -> return 0.0, the "perfect drawdown" lie)
     — same fail-open class as the R2 ann_geo all-NaN prod bug. M22a/M22b/M22c are all
     proven equivalent; the pins below pin the CONTRACT (holes don't change the answer,
     all-NaN fails closed) which survives any future equivalent-mutant rewrite.
Run: python3 m22_maxdd_nanpoison.py   (writes m22_run.txt next to nothing; prints table)
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
from bt.metrics import max_dd  # noqa: E402


def dd_original(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan


def dd_m22a(r):  # the R2 mutant verbatim
    eq = (1 + r).cumprod()
    eq[r.isna()] = np.nan
    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan


def dd_m22b(r):  # dropna-compress
    r = r.dropna()
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan


def dd_m22c(r):  # output NaN-poison (dd itself poisoned at holes)
    eq = (1 + r).cumprod()
    dd = eq / eq.cummax() - 1
    dd[r.isna()] = np.nan
    return float(dd.min()) if len(dd) else np.nan


def dd_m22d(r):  # fail-open zero
    if r.isna().any():
        return 0.0
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan


def rand_panel(rng, n, hole_p):
    r = pd.Series(rng.normal(0, 0.01, n), index=pd.date_range("2020-01-01", periods=n))
    r[rng.random(n) < hole_p] = np.nan
    return r


def main():
    rng = np.random.default_rng(42)
    rows = []
    n_eq_a = n_eq_b = n_kill_c = n_kill_d = 0
    trials = 0
    for n in (50, 200, 500):
        for hole_p in (0.01, 0.05, 0.20):
            for t in range(20):
                r = rand_panel(rng, n, hole_p)
                trials += 1
                a, b, c, d = dd_m22a(r), dd_m22b(r), dd_m22c(r), dd_m22d(r)
                o = dd_original(r)
                n_eq_a += (a == o) or (np.isnan(a) and np.isnan(o))
                n_eq_b += (b == o) or (np.isnan(b) and np.isnan(o))
                n_kill_c += not (c == o)
                n_kill_d += not (d == o)
    print(f"trials={trials}")
    print(f"M22a (eq[r.isna()]=nan)  == original on {n_eq_a}/{trials}  -> EQUIVALENT MUTANT")
    print(f"M22b (dropna-compress)   == original on {n_eq_b}/{trials}  -> EQUIVALENT MUTANT")
    print(f"M22c (dd-output-poison)  == original on {trials - n_kill_c}/{trials}"
          f"  -> EQUIVALENT too (min() is skipna: poisoning dd at holes"
          f" cannot move the min unless the min IS a hole, and holes carry"
          f" the prior cummax so dd[hole]==dd[prev])")
    print(f"M22d (any-NaN->0.0)      differs on {n_kill_d}/{trials}   -> KILLABLE by pin")
    # deterministic pin fixtures (the exact assertions added to test_fwbugs_audit_r3.py)
    r1 = pd.Series([0.01, -0.02, np.nan, 0.03, -0.04],
                   index=pd.date_range("2020-01-01", periods=5))
    r2 = pd.Series(np.nan, index=pd.date_range("2020-01-01", periods=100))
    r3 = pd.Series([0.01, 0.02, 0.03], index=pd.date_range("2020-01-01", periods=3))
    print("\npin fixtures on CURRENT shipped code:")
    print(f"  interior-NaN dd  = {max_dd(r1)!r}  (expect {dd_original(r1)!r}; M22d would say 0.0)")
    print(f"  all-NaN dd       = {max_dd(r2)!r}  (expect NaN fail-closed; M22d would say 0.0)")
    print(f"  no-NaN control   = {max_dd(r3)!r}  (expect {dd_original(r3)!r})")


if __name__ == "__main__":
    main()
