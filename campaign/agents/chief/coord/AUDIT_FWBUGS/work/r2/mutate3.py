"""AUDIT_FWBUGS R2(b) mutation harness v3.

v1 bug: pytest prepend-import resolved `import bt` to the LIVE tree -> every verdict fake.
v2 fix: sandbox validated (selfcheck proves mutated tree is imported), but
  - crashed on M16 (sandbox had no scripts/ tree) and
  - M9 mutated an unreachable line (sn.clip when sn<0 already raises -> survives trivially).
v3 = v2's validated sandbox + FULL mutation registry (v1's) + per-mutation SANDBOX BASELINE
(unmutated copy of the test file must PASS in the sandbox first; else verdict is
 BASELINE-FAIL, not a vacuity claim) + fixed M16 (sandbox gets builder+sleeves+frozen
 champion emitted at sandbox build time) + M9 rewritten to clip the OUTPUT credit (the
 real bug class the test must catch).

Usage: python3 mutate3.py            # all
       python3 mutate3.py <ID>       # one, verbose
"""
import os, shutil, subprocess, sys, tempfile

ROOT = "/Users/daxu/software/world-trader/campaign"
WROOT = "/Users/daxu/software/world-trader"

TESTS = {
    "test_fwbugs_audit.py":       ["M1_cap_scaleup", "M2_cost_drop_day1", "M3_negyears_failopen", "M4_recon_drop_day1"],
    "test_shortability.py":       ["M5_gate_drops_longs", "M6_flat_borrow"],
    "test_shortability_r2.py":    ["M7_pregate_no_relever", "M10_pregate_borrow_pre_scale"],
    "test_shortability_r2b_ladder.py": ["M9_delta_clip_credit"],
    "test_gates_audit.py":        ["M11_plateau_half", "M12_corr_failopen"],
    "test_gates_audit_r2.py":     ["M13_scr_raw_sr", "M14_scr_failopen", "M15_scr_nan_ok"],
    "test_engine.py":             ["M17_margin_full_gross", "M18_borrow_on_longs", "M19_caplev_scaleup"],
    "test_metrics.py":            ["M20_sharpe_const_nan", "M21_halfsplit_offby1", "M22_maxdd_nanpoison"],
    "test_gates.py":              ["M23_uniq_no_round", "M24_zeroruns_drop", "M25_scramble_raw_sr"],
    "test_reconcile.py":          ["M26_recon_day1_drop", "M27_maxabsdiff_nanopen"],
    "test_backtest.py":           ["M28_book_nolag", "M29_sleeve_nolag"],
    "test_align.py":              ["M30_align_after_false", "M31_align_keep_first"],
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
# M5 v2: 'clip(lower=0, upper=0)' DID kill the TINYCO test (shorts->0 both ways) but the
# mutated code ALSO zeroes positive weights of a NONE name -- untested. Stronger mutation:
# keep the short drop, ALSO drop the long leg (asymmetric wrongness).
"M5_gate_drops_longs": ("bt/shortability.py", lambda s: s.replace(
    "        w[c] = w[c].clip(lower=0.0)   # drop the short leg only",
    "        w[c] = w[c].clip(lower=0.0)\n        w[c] = w[c].clip(upper=0.0)  # MUTATED: longs die too")),
# M9 v2 clipped the INPUT, unreachable behind the sn<0 raise. Real bug class: clipping the
# OUTPUT so a cheaper tier (credit) is charged as zero instead of negative.
"M9_delta_clip_credit": ("bt/shortability.py", lambda s: s.replace(
    "    return sn * (tier_rate - base_rate) / ANN",
    "    return (sn * (tier_rate - base_rate) / ANN).clip(lower=0.0)  # MUTATED")),
"M6_flat_borrow": ("bt/shortability.py", lambda s: s.replace(
    "        borrow = borrow + shorts * TIERS[t] / ANN",
    "        borrow = borrow + shorts * 0.005 / ANN  # MUTATED flat")),
"M7_pregate_no_relever": ("bt/shortability.py", lambda s: s.replace(
    "if not dropped or not preserve_gross:", "if True:")),
"M10_pregate_borrow_pre_scale": ("bt/shortability.py", lambda s: s.replace(
    "borrow = borrow + (-w[c].clip(upper=0.0)) * TIERS[t] / ANN\n    info.update",
    "borrow = borrow0\n    info.update")),
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
# --- new v3 mutations against the ORIGINAL round-1 (iter10-era) test files ---
"M17_margin_full_gross": ("bt/engine.py", lambda s: s.replace(
    "lev = (gross - 1.0).clip(lower=0.0)", "lev = pd.Series(gross).fillna(0.0)")),
"M18_borrow_on_longs": ("bt/engine.py", lambda s: s.replace(
    "shorts = -weights.clip(upper=0.0)", "shorts = weights.abs()")),
"M19_caplev_scaleup": ("bt/engine.py", lambda s: s.replace(
    "kappa = np.minimum(1.0, max_lev * (1.0 - 1e-12) / g).fillna(1.0)",
    "kappa = (max_lev * (1.0 - 1e-12) / g).fillna(1.0)")),
"M20_sharpe_const_nan": ("bt/metrics.py", lambda s: s.replace(
    "if not s or not np.isfinite(s) or s < 1e-12:\n        return 0.0", "pass  # MUTATED")),
"M21_halfsplit_offby1": ("bt/metrics.py", lambda s: s.replace(
    "k = len(r) // 2", "k = (len(r) + 1) // 2")),
"M22_maxdd_nanpoison": ("bt/metrics.py", lambda s: s.replace(
    "eq = (1 + r).cumprod()", "eq = (1 + r).cumprod()\n    eq[r.isna()] = np.nan")),
"M23_uniq_no_round": ("bt/gates.py", lambda s: s.replace(
    "r = r.round(10)", "pass  # MUTATED: no rounding, float noise counts as unique")),
"M24_zeroruns_drop": ("bt/gates.py", lambda s: s.replace(
    "if v >= min_run:", "if v > 10**9:  # MUTATED: never fires")),
"M25_scramble_raw_sr": ("bt/gates.py", lambda s: s.replace(
    "real_sr = sharpe_d(pd.Series(sig * r))",
    "real_sr = sharpe_d(pd.Series(pd.Series(r).fillna(0.0)))  # MUTATED")),
"M26_recon_day1_drop": ("bt/reconcile.py", lambda s: s.replace(
    "prev = pos_path.shift(1)\n    prev.iloc[0] = 0.0", "prev = pos_path.shift(1)")),
"M27_maxabsdiff_nanopen": ("bt/reconcile.py", lambda s: s.replace(
    "if j.isna().any().any():\n        return np.inf", "pass  # MUTATED fail-open")),
"M28_book_nolag": ("bt/backtest.py", lambda s: s.replace(
    "w = weights.reindex(returns.index).fillna(0.0).shift(1).fillna(0.0)",
    "w = weights.reindex(returns.index).fillna(0.0)")),
"M29_sleeve_nolag": ("bt/backtest.py", lambda s: s.replace(
    "pos = lag_signal(sig)", "pos = sig")),
"M30_align_after_false": ("bt/align.py", lambda s: s.replace(
    'side = "right" if after else "left"', 'side = "right"')),
"M31_align_keep_first": ("bt/align.py", lambda s: s.replace(
    'live = live[~live.index.duplicated(keep="last")]',
    'live = live[~live.index.duplicated(keep="first")]')),
}


def _make_sandbox(td, test_file):
    """Copy bt/ + (for M16) the builder chain into a sandbox; leave only the test file."""
    shutil.copytree(f"{ROOT}/bt", f"{td}/bt", ignore=shutil.ignore_patterns('__pycache__'))
    for junk in os.listdir(f"{td}/bt/tests"):
        if junk != "__init__.py" and junk.startswith("test_"):
            os.remove(f"{td}/bt/tests/{junk}")
    open(f"{td}/bt/tests/__init__.py", "w").write("")
    shutil.copy(f"{ROOT}/bt/tests/{test_file}", f"{td}/bt/tests/{test_file}")
    if test_file == "test_camp_cost_full_dw.py":
        _setup_m16_sandbox(td)


def _setup_m16_sandbox(td, test_file):
    # frozen builder chain: builder + ALL sleeve CSVs it reads, plus a champion emitted
    # NOW (pre-mutation) inside the sandbox so --verify comparisons are self-consistent.
    # Layout mirrors live: <td>/campaign/scripts/rawew13v2_build.py (test's ROOT point).
    os.makedirs(f"{td}/campaign/scripts", exist_ok=True)
    os.makedirs(f"{td}/campaign/results", exist_ok=True)
    shutil.copy(f"{ROOT}/scripts/rawew13v2_build.py", f"{td}/campaign/scripts/")
    import re as _re
    src = open(f"{ROOT}/scripts/rawew13v2_build.py").read()
    for p in _re.findall(r'"campaign/[^"]+"', src):
        rp = p.strip('"')
        dst = f"{td}/{rp}"
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(f"{WROOT}/{rp}", dst)
    t = open(f"{td}/bt/tests/{test_file}").read()
    # replace BOTH the module-level ROOT and function-local `ROOT = "/Users/..."`
    t = t.replace(f'ROOT = "{WROOT}/campaign"', f'ROOT = "{td}/campaign"')
    t = t.replace(f'ROOT = "{WROOT}"', f'ROOT = "{td}"')
    open(f"{td}/bt/tests/{test_file}", "w").write(t)
    # repoint the builder's ROOT at the sandbox and emit a frozen champion there
    b = open(f"{td}/campaign/scripts/rawew13v2_build.py").read().replace(
        f'ROOT = "{WROOT}"', f'ROOT = "{td}"')
    open(f"{td}/campaign/scripts/rawew13v2_build.py", "w").write(b)
    r = subprocess.run([sys.executable, f"{td}/campaign/scripts/rawew13v2_build.py", "--emit"],
                       capture_output=True, text=True, cwd=td)
    assert r.returncode == 0, f"sandbox emit failed: {r.stderr[-400:]}"
    # the test's offender-pin greps QA_dualmom_band121.py for the 0.5x pattern; the LIVE
    # copy was just costfixed by the concurrent re-emit wave (pin stale in live tree),
    # so freeze the HEAD (committed) generator, which still carries it.
    import subprocess as _sp
    head = _sp.run(["git", "-C", WROOT, "show",
                    "HEAD:software/world-trader/campaign/scripts/QA_dualmom_band121.py"],
                   capture_output=True, text=True)
    if head.returncode == 0:
        open(f"{td}/campaign/scripts/QA_dualmom_band121.py", "w").write(head.stdout)


def run_one(mut, test_file, verbose=False):
    src_name, fn = MUT[mut]
    with tempfile.TemporaryDirectory() as td:
        _make_sandbox(td, test_file)
        # BASELINE: unmutated sandbox must pass the test file first
        r0 = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q",
                             f"{td}/bt/tests/{test_file}"],
                            capture_output=True, text=True, cwd=td, timeout=900)
        if r0.returncode != 0:
            return "BASELINE-FAIL", (r0.stdout + r0.stderr).strip().splitlines()[-1]
        # apply mutation INSIDE the sandbox (src_name is campaign-relative, e.g.
        # bt/engine.py or scripts/rawew13v2_build.py -> sandbox layout <td>/campaign/...)
        spath = f"{td}/{src_name}"           # bt/* copies live at <td>/bt/...
        if not os.path.exists(spath):
            spath = f"{td}/campaign/{src_name}"   # scripts/* live at <td>/campaign/scripts/...
        s = open(spath).read()
        s2 = fn(s)
        if s2 == s:
            return "MUTATION_DID_NOT_APPLY", ""
        open(spath, "w").write(s2)
        r = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q",
                            f"{td}/bt/tests/{test_file}"],
                           capture_output=True, text=True, cwd=td, timeout=900)
        out = (r.stdout + r.stderr).strip()
        tail = out.splitlines()[-1] if out else ""
        if verbose:
            print(out[-2000:])
        return ("VACUOUS" if r.returncode == 0 else "CAUGHT"), tail


def selfcheck():
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




def crosscheck(mut):
    """Run the mutation against the WHOLE test suite in one sandbox; report only NEW
    failures vs the unmutated baseline run of the same sandbox (kills per-file isolation
    artifacts)."""
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(f"{ROOT}/bt", f"{td}/bt", ignore=shutil.ignore_patterns('__pycache__'))
        open(f"{td}/bt/tests/__init__.py", "w").write("")
        if mut == "M16_builder_halfturn":
            _setup_m16_sandbox(td, "test_camp_cost_full_dw.py")
        spath = f"{td}/{MUT[mut][0]}"
        if not os.path.exists(spath):
            spath = f"{td}/campaign/{MUT[mut][0]}"
        # drop test files that import agent-dir modules unavailable in the sandbox
        # (they error at collection and abort the whole run) — every framework test stays.
        SKIP = {"test_treasfut_r2.py", "test_auditrecon_r2_pin_mutations.py",
                "test_camp_short_r2b.py", "test_audit_champ2_round2.py",
                "test_audit_recon_lineage.py", "test_auditrecon_r2_lineage.py",
                "test_camp_borrow_round2.py", "test_camp_cost_r2.py"}
        for f in SKIP:
            pth = f"{td}/bt/tests/{f}"
            if os.path.exists(pth):
                os.remove(pth)
        def run():
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header",
                                "-rf", "-p", "no:cacheprovider", f"{td}/bt/tests/"],
                               capture_output=True, text=True, cwd=td, timeout=1800)
            if r.returncode not in (0, 1):
                raise RuntimeError(f"sandbox pytest rc={r.returncode}: "
                                   f"{(r.stdout + r.stderr)[-500:]}")
            fails = set()
            for ln in (r.stdout + r.stderr).splitlines():
                if ln.startswith("FAILED "):
                    t = ln.split("FAILED ", 1)[1].split()[0]
                    if "::" in t:
                        f, n = t.rsplit("::", 1)
                        fails.add(f.rsplit("/", 1)[-1] + "::" + n)
            return fails
        base = run()
        s = open(spath).read()
        s2 = MUT[mut][1](s)
        if s2 == s:
            return "MUTATION_DID_NOT_APPLY", []
        open(spath, "w").write(s2)
        after = run()
        new = sorted(after - base)
        return ("CAUGHT-SOMEWHERE" if new else "VACUOUS-EVERYWHERE"), new

if __name__ == "__main__":
    ok, tail = selfcheck()
    print(f"SELFCHECK sandbox-mutation-is-imported: {ok} | {tail}", flush=True)
    if not ok:
        print("HARNESS BROKEN — aborting")
        sys.exit(2)
    args = [a for a in sys.argv[1:] if a != "--cross"]
    only = args[0] if args else None
    verbose = only is not None
    if "--cross" in sys.argv:
        for m in MUT:
            if only and only != "--cross" and only not in m:
                continue
            v, nf = crosscheck(m)
            print(f"{v:20s} {m:26s} | {nf if nf else ''}", flush=True)
        sys.exit(0)
    n_vac = 0
    for tf, muts in TESTS.items():
        for m in muts:
            if only and only not in m:
                continue
            verdict, t = run_one(m, tf, verbose=verbose)
            if verdict in ("VACUOUS", "MUTATION_DID_NOT_APPLY", "BASELINE-FAIL"):
                n_vac += 1
            print(f"{verdict:24s} {m:26s} vs {tf:30s} | {t}", flush=True)
    print(f"\nPROBLEM count (VACUOUS+DID_NOT_APPLY+BASELINE-FAIL): {n_vac}")
