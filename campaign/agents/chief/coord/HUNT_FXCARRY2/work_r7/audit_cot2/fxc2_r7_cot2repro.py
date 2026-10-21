"""HUNT_FXCARRY2 R7 charter-(a) audit: independent re-execution of HUNT_COT2-R6's
r6/credit2_rerun_battery.json pipeline. My own wrapper (not a copy of theirs):
imports HUNT_CREDIT2_round5 as a module, no-ops save_sleeve + patches SLEEVES to my
own dir (belt+braces fail-safe so nothing can be written into HUNT_CREDIT2), runs
main() offline, captures the FULL v2 battery dict per config (incl. scr_p, leak dict,
beats_passive detail), and cross-checks vs COT2's published JSON cell-by-cell."""
import sys, json, os

ROOT = "/Users/daxu/software/world-trader"
MYOUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r7/audit_cot2"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")

import HUNT_CREDIT2_round5 as M

# fail-safes: never write into HUNT_CREDIT2
M.save_sleeve = lambda *a, **k: None
M.SLEEVES = MYOUT

res = M.main()

out = {}
for k, v in res.items():
    g = v.get('v2', {})
    lp = g.get('leak') or {}
    bp = g.get('beats_passive') or {}
    out[k] = dict(
        local_sr=v.get('sr'), local_h1=v.get('h1'), local_h2=v.get('h2'),
        local_neg=v.get('neg'), local_worst=v.get('worst'), local_corr=v.get('corr'),
        n=v.get('n'), start=str(v.get('start')), end=str(v.get('end')),
        v2_sr=g.get('sr'), v2_corr=g.get('corr'), scr_p=g.get('scr_p'),
        leak_ok=g.get('leak_ok'), leak_corr=lp.get('same_period_corr'),
        leak_p=lp.get('same_period_p'), bp_ok=g.get('beats_passive_ok'),
        bp_best=(bp.get('best_passive_name'), bp.get('best_passive_sr')),
        mtrx_p=g.get('mtrx_p'), plateau_ok=g.get('plateau_ok'),
        pass_=g.get('pass'))

json.dump(out, open(f"{MYOUT}/fxc2_r7_credit2_rerun_battery.json", 'w'), indent=1, default=str)

# cross-check vs COT2-R6's published battery
theirs = json.load(open(f"{ROOT}/campaign/agents/chief/coord/HUNT_COT2/r6/credit2_rerun_battery.json"))
assert set(theirs) == set(out), (set(theirs) ^ set(out))
rows = []
mismatch = 0
for k in sorted(out):
    t, m = theirs[k], out[k]
    for fld_t, fld_m in (('local_sr', 'local_sr'), ('v2_sr', 'v2_sr'),
                         ('scr_p', 'scr_p'), ('leak_ok', 'leak_ok'),
                         ('bp_ok', 'bp_ok'), ('pass_', 'pass_')):
        tv, mv = t.get(fld_t), m.get(fld_m)
        if fld_t == 'pass_':
            tv, mv = bool(t.get('pass_')), bool(m.get('pass_'))
            same = tv == mv
        else:
            same = (tv == mv) or (tv is not None and mv is not None and
                                  abs(float(tv) - float(mv)) <= 1e-9)
        if not same:
            mismatch += 1
            rows.append((k, fld_t, tv, mv))
print(f"\nFXC2-R7 RERUN: n={len(out)} configs; COT2-R6 cross-check fields={6*len(out)}, "
      f"mismatches={mismatch}")
for r in rows[:20]:
    print("  MISMATCH", r)
best = max(out.items(), key=lambda kv: kv[1]['v2_sr'] or -9)
print(f"BEST v2_sr: {best[0]} v2_sr={best[1]['v2_sr']:.4f} scr_p={best[1]['scr_p']} "
      f"leak_ok={best[1]['leak_ok']} bp_ok={best[1]['bp_ok']} pass={best[1]['pass_']}")
