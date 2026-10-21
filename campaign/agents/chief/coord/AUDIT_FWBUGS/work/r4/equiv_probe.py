"""AUDIT_FWBUGS R4: machine-check EQUIVALENCE of the unkillable M22 mutants.

R3 asserted M22a/M22b/M22c "identical on 180/180 randomized NaN panels" by hand-run.
R4 makes that a reproducible artifact: exec the ORIGINAL and each MUTANT max_dd source in
isolated namespaces, run both over a fixed adversarial fixture battery (leading/trailing/
alternating/all-NaN/single-row/NaN-adjacent-to-trough + seeded randomized panels), and
require BIT-IDENTICAL outputs (== on floats, both-NaN as equal). A single differing panel
refutes equivalence and the mutant must then be killed by a test instead.

Exit code 0 = all claimed-equivalent mutants verified equivalent.
"""
import numpy as np
import pandas as pd

SHIPPED = """def max_dd(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(r) else float('nan')
"""

MUTANTS = {
    "M22a_literal_nanwrite": """def max_dd(r):
    eq = (1 + r).cumprod()
    eq[r.isna()] = float('nan')
    return float((eq / eq.cummax() - 1).min()) if len(r) else float('nan')
""",
    "M22b_dropna_compress": """def max_dd(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(r) else float('nan')
""",
    "M22c_dd_output_poison": """def max_dd(r):
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1)
    dd[r.isna()] = float('nan')
    return float(dd.min()) if len(r) else float('nan')
""",
}


def battery(n_rand=300, seed=20260908):
    """Adversarial deterministic fixtures + seeded randomized NaN panels."""
    idx = pd.date_range("2020-01-01", periods=8, freq="B")
    fx = [
        pd.Series([0.01, 0.01, -0.10, 0.02], index=pd.date_range("2020-01-01", periods=4, freq="B")),
        pd.Series(np.nan, index=pd.date_range("2020-01-01", periods=252, freq="B")),          # all-NaN
        pd.Series([np.nan, 0.05, -0.10], index=idx[:3]),                                       # leading hole
        pd.Series([0.05, -0.10, np.nan], index=idx[:3]),                                       # trailing hole
        pd.Series([0.05, np.nan, -0.10], index=idx[:3]),                                       # hole before trough
        pd.Series([np.nan], index=idx[:1]),                                                    # single NaN row
        pd.Series([0.05], index=idx[:1]),                                                      # single real row
        pd.Series([0.01, np.nan, -0.05, np.nan, -0.10, np.nan, 0.02], index=idx[:7]),          # alternating
        pd.Series([0.0, 0.0, 0.0], index=idx[:3]),                                             # all-zero
    ]
    rng = np.random.default_rng(seed)
    for _ in range(n_rand):
        n = int(rng.integers(1, 60))
        vals = rng.normal(0, 0.02, n)
        vals[rng.random(n) < rng.uniform(0.05, 0.5)] = np.nan
        fx.append(pd.Series(vals, index=pd.date_range("2020-01-01", periods=n, freq="B")))
    return fx


def load(src):
    ns = {}
    exec(compile(src, "<mutant>", "exec"), {"np": np, "pd": pd}, ns)
    return ns["max_dd"]


def eq_float(a, b):
    if np.isnan(a) and np.isnan(b):
        return True
    return a == b  # bit-identical requirement, no tolerance


def main():
    panels = battery()
    orig = load(SHIPPED)
    print(f"panels: {len(panels)} (9 adversarial + {len(panels)-9} seeded random)")
    all_equiv = True
    for name, src in MUTANTS.items():
        f = load(src)
        diffs = []
        for i, p in enumerate(panels):
            try:
                a, b = orig(p), f(p)
            except Exception as e:  # mutant raises where original doesn't = distinguishable
                diffs.append((i, f"RAISED {type(e).__name__}: {e}"))
                continue
            if not eq_float(a, b):
                diffs.append((i, f"{a!r} vs {b!r}"))
        if diffs:
            all_equiv = False
            print(f"{name:24s} DISTINGUISHABLE on {len(diffs)} panels, e.g. {diffs[:3]}")
        else:
            print(f"{name:24s} EQUIVALENT on all {len(panels)} panels")
    print("RESULT:", "ALL-CLAIMED-EQUIVALENT-VERIFIED" if all_equiv else "EQUIVALENCE-REFUTED")
    return 0 if all_equiv else 1


if __name__ == "__main__":
    raise SystemExit(main())
