#!/usr/bin/env python3
"""CAMP_COST R6 session-3 independent re-verification (fresh runs, this session).

1. sha-pin all 18 round inputs vs work_r6/input_shas_round.json
2. champion-of-record guard: bt/verify_champion.py 13-sleeve  -> ..._SESSION3.json
3. candidate: bt/verify_champion.py 14-sleeve                 -> ..._SESSION3.json
4. rawew14_candidate.py --verify (no writes)
5. determinism: fresh in-memory net vs on-disk candidate CSV bytes
"""
import hashlib, json, subprocess, sys
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
W6 = ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6/"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")

def sha16(p):
    return hashlib.sha256(open(ROOT + "/" + p, "rb").read()).hexdigest()[:16]

# ---- 1. sha pin
start = json.load(open(W6 + "input_shas_round.json"))
mism = [(k, start[k], sha16(k)) for k in start if sha16(k) != start[k]]
print(f"[1] sha-pin: {len(start)-len(mism)}/{len(start)} MATCH round-start shas")
for k, a, b in mism:
    print(f"    MISMATCH {k}: round-start {a} now {b}")

# ---- 2/3. verify_champion.py runs
def run_verify(inputs, params, out_json, label):
    cmd = [sys.executable, ROOT + "/campaign/bt/verify_champion.py",
           "--champion", inputs["champion"], "--weights", inputs["weights"]]
    for n, p in inputs["sleeves"].items():
        cmd += ["--sleeve", f"{n}={p}"]
    for k, v in params.items():
        if k in ("gear", "rate", "bps", "p"):
            cmd += [f"--{k}", str(v)]
        elif k == "start":
            cmd += ["--start", v]
    cmd += ["--json", out_json]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    print(f"[{label}] rc={r.returncode} tail: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip().splitlines()[-1:]}")
    j = json.load(open(out_json))
    n_ok = sum(1 for c in j["checks"].values() if c.get("ok"))
    print(f"[{label}] ok={j['ok']} checks {n_ok}/{len(j['checks'])} errors={j['errors']}")
    return j

inp_c = json.load(open(W6 + "verify_champion_r6_champ_guard_SESSION2.json"))
j_guard = run_verify(inp_c["inputs"], inp_c["params"], W6 + "verify_champion_r6_champ_guard_SESSION3.json", "2-guard")
inp_k = json.load(open(W6 + "verify_champion_r6_candidate_SESSION2.json"))
j_cand = run_verify(inp_k["inputs"], inp_k["params"], W6 + "verify_champion_r6_candidate_SESSION3.json", "3-cand")

s13, s14 = j_guard["stats"], j_cand["stats"]
print(f"[cmp] c13 ann {s13['ann_cagr_pct']:.4f} sr {s13['sr']:.4f} mdd {s13['mdd_pct']:.4f} neg {s13['neg_years']} n {s13['n_days']}")
print(f"[cmp] c14 ann {s14['ann_cagr_pct']:.4f} sr {s14['sr']:.4f} mdd {s14['mdd_pct']:.4f} neg {s14['neg_years']} n {s14['n_days']}")
print(f"[cmp] dAnn {s14['ann_cagr_pct']-s13['ann_cagr_pct']:+.4f}pp dSR {s14['sr']-s13['sr']:+.4f} dMDD {s14['mdd_pct']-s13['mdd_pct']:+.4f}pp")
print(f"[cmp] charged bp/yr: c13 {j_guard['checks']['cost_reconciliation']['bp_per_year']:.4f} c14 {j_cand['checks']['cost_reconciliation']['bp_per_year']:.4f}")
print(f"[cmp] gross max: c13 {j_guard['checks']['gross']['max']:.13f} c14 {j_cand['checks']['gross']['max']:.13f} n_over {j_cand['checks']['gross']['n_over']}")

# ---- 4/5. builder verify + determinism (in-memory vs on-disk bytes)
import rawew14_candidate as C
net, relw, gross, to, df = C.build()
disk = pd.read_csv(ROOT + "/campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv",
                   index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([net.rename("m"), disk.rename("f")], axis=1, join="inner").dropna()
dev = float((j.m - j.f).abs().max())
print(f"[5] determinism fresh-vs-disk: inner={len(j)} maxdev={dev:.3e} "
      f"{'BYTE-DETERMINISTIC' if dev < 1e-12 else 'DRIFT'}")
wr = pd.read_csv(ROOT + "/campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv", index_col=0, parse_dates=True).iloc[:, 0]
wdev = float((relw - wr.reindex(relw.index)).abs().max())
print(f"[5] weights file vs fresh re-solve: maxdev={wdev:.3e}")
share = C.hobr_nav_share()
print(f"[4] HOBR NAV share min {share.min():.5f} mean {share.mean():.5f} max {share.max():.5f} (cap .15: {'OK' if share.max()<=.15 else 'BREACH'})")
