"""AUDIT_FWBUGS R2(b): mutation harness for round-1 test files.

Applies deliberate code mutations (from a registry of *real* bugs we want the tests to
catch) to campaign/bt/, runs the specified test files, and reports any mutation that
SURVIVES (all tests pass) => vacuous coverage.
Usage: python3 mutate.py            # all mutations
       python3 mutate.py <id>       # one mutation, verbose pytest output
"""
import os, subprocess, sys, shutil, re

ROOT = "/Users/daxu/software/world-trader"
BT = f"{ROOT}/campaign/bt"
TESTS = f"{BT}/tests"

# (id, file, old, new)
MUTATIONS = [
    # ---- engine.py ----
    ("E1|day1-entry-charge removed", "engine.py",
     "    prev = w.shift(1)\n    prev.iloc[0] = 0.0\n    one_side = (w - prev).abs().sum(axis=1)",
     "    one_side = w.diff().abs().sum(axis=1)"),
    ("E2|cap_leverage eps removed", "engine.py",
     "max_lev * (1.0 - 1e-12) / g", "max_lev / g"),
    ("E3|borrow on longs too", "engine.py",
     "    shorts = -weights.clip(upper=0.0)\n    return shorts.sum(axis=1) * short_fraction * borrow_frac / ANN",
     "    return weights.abs().sum(axis=1) * short_fraction * borrow_frac / ANN"),
    ("E4|margin on full gross", "engine.py",
     "    lev = (gross - 1.0).clip(lower=0.0)\n    return lev * rate / ANN",
     "    return gross * rate / ANN"),
    # ---- metrics.py ----
    ("M1|neg_years NaN fail-open (R1 bug reinserted)", "metrics.py",
     "    yr = yr.where(np.isfinite(yr), -1.0)\n", ""),
    ("M2|max_dd NaN-poisoned", "metrics.py",
     "    eq = (1 + r).cumprod()\n", "    eq = (1 + r).cumprod()\n    return float('nan') if r.isna().any() else "),
    ("M3|sharpe constant -> NaN not 0", "metrics.py",
     "    if not s or not np.isfinite(s) or s < 1e-12:\n        return 0.0\n    return float(r.mean() / s * np.sqrt(ANN))",
     "    return float(r.mean() / s * np.sqrt(ANN))"),
    ("M4|half_split off-by-one", "metrics.py",
     "    k = len(r) // 2", "    k = (len(r) + 1) // 2"),
    # ---- gates.py ----
    ("G1|corr fail-open ref=None (R1 bug reinserted)", "gates.py",
     "corr_ok=(bool(abs(corr_to(ref, r)) < p['corr_max']) if ref is not None else False)",
     "corr_ok=(bool(abs(corr_to(ref, r)) < p['corr_max']) if ref is not None else True)"),
    ("G2|plateau neighbor_frac semantics restored (one-sided cliff passes)", "gates.py",
     "    ok = bool(nb) and len(good) == len(nb)",
     "    ok = bool(nb) and len(good) >= 1"),
    ("G3|run() ignores halves gate", "gates.py",
     "res['pass'] = all(res[k + '_ok'] for k in ['sr', 'halves', 'neg', 'ac1', 'uniq', 'corr'])",
     "res['pass'] = all(res[k + '_ok'] for k in ['sr', 'neg', 'ac1', 'uniq', 'corr'])"),
    ("G4|plateau nonpositive-peak guard removed", "gates.py",
     "    if peak <= 0:\n        return (False, dict(reason='nonpositive_peak', peak=peak))\n", ""),
    ("G5|scramble baseline = raw return SR (VERIFY_BEST 4c reinserted)", "gates.py",
     "    real_sr = sharpe_d(pd.Series(sig * r))",
     "    real_sr = sharpe_d(pd.Series(pd.Series(r).fillna(0.0)))"),
    # ---- reconcile.py ----
    ("R1|turnover day-1 recon drop (R1 bug reinserted)", "reconcile.py",
     "    prev = pos_path.shift(1)\n    prev.iloc[0] = 0.0\n    pos = (pos_path - prev).abs().sum(axis=0)",
     "    pos = pos_path.diff().abs().sum(axis=0)"),
    ("R2|ledgers coverage hole ignored", "reconcile.py",
     "    if len(j) != len(champion):", "    if False:"),
    ("R3|max_abs_diff NaN fail-open", "reconcile.py",
     "    if j.isna().any().any():\n        return np.inf\n", ""),
    ("R4|turnover zero-pos-nonzero-ledger guard removed", "reconcile.py",
     "    pos_zero_nled_nonzero = (j.pos == 0) & (j.led != 0)\n    if pos_zero_nled_nonzero.any():\n        return dict(ok=False, max_rel=float('inf'), n=len(j))\n", ""),
    # ---- shortability.py ----
    ("S1|NONE tier drops longs too (longs touched)", "shortability.py",
     "        w[c] = w[c].clip(lower=0.0)   # drop the short leg only",
     "        w[c] = 0.0"),
    ("S2|tiered borrow flattened to EASY", "shortability.py",
     "        borrow = borrow + shorts * TIERS[t] / ANN",
     "        borrow = borrow + shorts * TIERS['EASY'] / ANN"),
    ("S3|unknown tier fail-open", "shortability.py",
     "        if t not in TIERS:\n            raise ValueError(f\"unknown tier {t} for {c}\")\n", ""),
    # ---- backtest.py ----
    ("B1|backtest.book same-day weights (no lag)", "backtest.py",
     "    w = weights.reindex(returns.index).fillna(0.0).shift(1).fillna(0.0)",
     "    w = weights.reindex(returns.index).fillna(0.0)"),
    ("B2|backtest.sleeve no shift", "backtest.py",
     "    pos = lag_signal(sig)", "    pos = sig"),
]


KNOWN_BROKEN = {  # other agents' live-module tests, pre-existing at R2 baseline
    "test_treasfut_r2.py::test_net_of_no_phantom_window",
    "test_treasfut_r2.py::test_net_of_subset_columns_zeroed",
    "test_treasfut_r2.py::test_combined_mom_weights_not_all_nan",
}

def run_mutation(mid, verbose=False):
    m = next(x for x in MUTATIONS if x[0].split("|")[0] == mid)
    name, fname, old, new = m[0].split("|", 1)[1], m[1], m[2], m[3]
    src_path = f"{BT}/{fname}"
    orig = open(src_path).read()
    if old not in orig:
        return (name, "MUTATION-ANCHOR-NOT-FOUND", None)
    mutated = orig.replace(old, new, 1)
    open(src_path, "w").write(mutated)
    # touch __init__ timestamp so pycache refreshes
    try:
        os.remove(f"{BT}/__pycache__/engine.cpython-*.pyc")
    except Exception:
        pass
    try:
        res = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
                              "-rf", f"{TESTS}"],
                             capture_output=True, text=True, timeout=900)
        out = res.stdout
        failed = set()
        for ln in out.splitlines():
            if ln.startswith("FAILED "):
                path = ln.split("FAILED ", 1)[1].split()[0]
                if "::" in path:
                    f, t = path.rsplit("::", 1)
                    failed.add(f.rsplit("/", 1)[-1] + "::" + t)
        new_fails = sorted(failed - KNOWN_BROKEN)
        verdict = "KILLED" if new_fails else "VACUOUS-SURVIVED"
        return (name, verdict, new_fails)
    finally:
        open(src_path, "w").write(orig)


if __name__ == "__main__":
    os.chdir(ROOT)
    ids = sys.argv[1:] or [m[0].split("|")[0] for m in MUTATIONS]
    for mid in ids:
        name, verdict, nfail = run_mutation(mid)
        print(f"{verdict:16s} {name}", flush=True)
        if isinstance(nfail, list):
            for t in nfail:
                print(f"                  -> {t}", flush=True)
