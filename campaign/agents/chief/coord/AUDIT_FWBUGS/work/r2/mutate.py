"""Charter (b) mutation harness v2 (validated).

v1 BUG (logged in FINDINGS): pytest prepend-import resolved `import bt` to the LIVE campaign
tree (test files sit in campaign/bt/tests package), so v1 mutated a tree that was never
imported and reported everything VACUOUS. v2 copies the test file + conftest into the sandbox
WITHOUT package __init__.py so the sandbox conftest's sys.path.insert(0, sandbox) makes the
MUTATED bt the one imported. Self-check below proves the sandbox is actually exercised.
"""
import os, shutil, subprocess, sys, tempfile

ROOT = "/Users/daxu/software/world-trader/campaign"

TESTS = {
    "test_fwbugs_audit.py":       ["M1_cap_scaleup", "M2_cost_drop_day1", "M3_negyears_failopen", "M4_recon_drop_day1"],
    "test_shortability.py":       ["M5_gate_drops_longs", "M6_flat_borrow"],
    "test_shortability_r2.py":    ["M7_pregate_no_relever", "M10_pregate_borrow_pre_scale"],
    "test_shortability_r2b_ladder.py": ["M9_delta_clip_neg"],
    "test_gates_audit.py":        ["M11_plateau_half", "M12_corr_failopen"],
    "test_gates_audit_r2.py":     ["M13_scr_raw_sr", "M14_scr_failopen", "M15_scr_nan_ok"],
    "test_camp_cost_full_dw.py":  ["M16_builder_halfturn"],
}

MUT = {
"M1_cap_scaleup": ("bt/engine.py", lambda s: s.replace(
    "kappa = np.minimum(1.0, max_lev * (1.0 - 1e-12) / g).fillna(1.0)",
    "kappa = (max_lev * (1.0 - 1e-12) / g).fillna(1.0)")),
"M2_cost_drop_day1": ("bt/engine.py", lambda s: s.replace(
    "prev = w.shift(1)\n    prev.iloc[0] = 0.0", "prev = w.shift(1)")),
"M3_negyears_failopen": ("bt/metrics.py", lambda s: s.replace(
    "yr = yr.where(np.isfinite(yr), -1.0)", "pass  # MUTATED")),
"M4_recon_drop_day1": ("bt/reconcile.py", lambda s: s.replace(
    "prev = pos_path.shift(1)\n    prev.iloc[0] = 0.0", "prev = pos_path.shift(1)")),
"M5_gate_drops_longs": ("bt/shortability.py", lambda s: s.replace(
    "w[c] = w[c].clip(lower=0.0)   # drop the short leg only",
    "w[c] = w[c].clip(lower=0.0, upper=0.0)  # MUTATED: drops longs too")),
"M6_flat_borrow": ("bt/shortability.py", lambda s: s.replace(
    "borrow = borrow + shorts * TIERS[t] / ANN",
    "borrow = borrow + shorts * 0.005 / ANN  # MUTATED flat")),
"M7_pregate_no_relever": ("bt/shortability.py", lambda s: s.replace(
    "if not dropped or not preserve_gross:", "if True:")),
"M10_pregate_borrow_pre_scale": ("bt/shortability.py", lambda s: s.replace(
    "borrow = borrow + (-w[c].clip(upper=0.0)) * TIERS[t] / ANN\n    info.update",
    "borrow = borrow0\n    info.update")),
"M9_delta_clip_neg": ("bt/shortability.py", lambda s: s.replace(
    "return sn * (tier_rate - base_rate) / ANN",
    "return sn.clip(lower=0.0) * (tier_rate - base_rate) / ANN  # MUTATED")),
"M11_plateau_half": ("bt/gates.py", lambda s: s.replace(
    "ok = bool(nb) and len(good) == len(nb)",
    "ok = bool(nb) and len(good) >= 0.5 * len(nb)  # MUTATED neighbor_frac=0.5")),
"M12_corr_failopen": ("bt/gates.py", lambda s: s.replace(
    "corr_ok=(bool(abs(corr_to(ref, r_eff)) < p['corr_max']) if ref is not None else False),",
    "corr_ok=(bool(abs(corr_to(ref, r_eff)) < p['corr_max']) if ref is not None else True),")),
"M13_scr_raw_sr": ("bt/gates.py", lambda s: s.replace(
    "real_sr = sharpe_d(pd.Series(sig * r))",
    "real_sr = sharpe_d(pd.Series(r))  # MUTATED: raw-return baseline")),
"M14_scr_failopen": ("bt/gates.py", lambda s: s.replace(
    "scr_ok=(bool(np.isfinite(scr_p)) and scr_p < p['p_max']),",
    "scr_ok=(bool(np.isnan(scr_p)) or scr_p < p['p_max']),")),
"M15_scr_nan_ok": ("bt/gates.py", lambda s: s.replace(
    "if not np.isfinite(sig).all() or not np.isfinite(r).all():\n        return (np.nan, np.nan)",
    "pass  # MUTATED: compute on NaN")),
"M16_builder_halfturn": ("scripts/rawew13v2_build.py", lambda s: s.replace(
    "to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)",
    "to = (Wg.diff().abs().sum(axis=1) * 0.5).fillna(0.0)", 1)),
}

def run_one(mut, test_file):
    src_name, fn = MUT[mut]
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(f"{ROOT}/bt", f"{td}/bt", ignore=shutil.ignore_patterns('__pycache__'))
        for junk in os.listdir(f"{td}/bt/tests"):
            if junk != "__init__.py" and (junk.startswith("test_") ):
                os.remove(f"{td}/bt/tests/{junk}")     # only the file under test stays
        # mutate
        s = open(f"{ROOT}/{src_name}").read()
        s2 = fn(s)
        if s2 == s:
            return "MUTATION_DID_NOT_APPLY", ""
        open(f"{td}/{src_name}", "w").write(s2)
        # test file + conftest into sandbox tests dir (no __init__.py on the copy path)
        open(f"{td}/bt/tests/__init__.py", "w").write("")
        shutil.copy(f"{ROOT}/bt/tests/{test_file}", f"{td}/bt/tests/{test_file}")
        if test_file == "test_camp_cost_full_dw.py":
            # repoint ROOT at the sandbox so the MUTATED builder is the one imported
            t = open(f"{td}/bt/tests/{test_file}").read().replace(
                f'ROOT = "{ROOT}"', f'ROOT = "{td}"')
            open(f"{td}/bt/tests/{test_file}", "w").write(t)
        r = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q",
                            f"{td}/bt/tests/{test_file}"],
                           capture_output=True, text=True, cwd=td, timeout=900)
        out = r.stdout + r.stderr
        lines = [l for l in out.strip().splitlines() if l.strip()]
        tail = lines[-1] if lines else ""
        vacuous = (r.returncode == 0)
        return ("VACUOUS" if vacuous else "CAUGHT"), tail

def selfcheck():
    """Prove the sandbox actually imports the mutated tree (v1's failure mode)."""
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(f"{ROOT}/bt", f"{td}/bt", ignore=shutil.ignore_patterns('__pycache__'))
        open(f"{td}/bt/tests/__init__.py", "w").write("")
        for junk in os.listdir(f"{td}/bt/tests"):
            if junk.startswith("test_"):
                os.remove(f"{td}/bt/tests/{junk}")
        open(f"{td}/bt/engine.py", "w").write("raise RuntimeError('SANDBOX ACTIVE')\n")
        shutil.copy(f"{ROOT}/bt/tests/test_shortability.py", f"{td}/bt/tests/")
        r = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q",
                            f"{td}/bt/tests/test_shortability.py"],
                           capture_output=True, text=True, cwd=td)
        out = r.stdout + r.stderr
        return ("SANDBOX ACTIVE" in out), out.strip().splitlines()[-1]

if __name__ == "__main__":
    ok, tail = selfcheck()
    print(f"SELFCHECK sandbox-mutation-is-imported: {ok} | {tail}", flush=True)
    if not ok:
        print("HARNESS BROKEN — aborting (v1 lesson)")
        sys.exit(2)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    n_vac = 0
    for tf, muts in TESTS.items():
        for m in muts:
            if only and only not in m:
                continue
            verdict, t = run_one(m, tf)
            if verdict in ("VACUOUS", "MUTATION_DID_NOT_APPLY"):
                n_vac += 1
            print(f"{verdict:26s} {m:28s} vs {tf:32s} | {t}", flush=True)
    print(f"\nVACUOUS+DID_NOT_APPLY count: {n_vac}")
