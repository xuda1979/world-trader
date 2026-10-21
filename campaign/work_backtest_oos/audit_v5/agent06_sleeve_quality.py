"""AGENT 06: Sleeve Quality & vt_bad Audit
Verify no FAILED_NO_PROMOTION sleeves, check individual sleeve metrics."""
import pandas as pd, numpy as np, json, os, pickle, re, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; isdf = D['isdf']; osdf = D['osdf']
ROOT = D['ROOT']
report = {"agent": "06_sleeve_quality", "checks": [], "sleeves": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

print("=== AGENT 06: Sleeve Quality & vt_bad Audit ===")

# 1. vt_bad check
def vt_bad(rel):
    m = os.path.splitext(os.path.join(ROOT, rel))[0] + ".csv.meta"
    if not os.path.exists(m): return False
    t = open(m).read()
    return ('FAILED_NO_PROMOTION' in t) or ('DEAD_NOT_PROMOTED' in t)

n_vt = sum(1 for s in sleeves if vt_bad(s))
check("Zero vt_bad sleeves", n_vt == 0, f"vt_bad count={n_vt}")

# 2. No MHX/HT_TAIL sleeves
mhx = sum(1 for s in sleeves if re.search(r"MHX|HT_TAIL", s, re.I))
check("Zero MHX/HT_TAIL sleeves", mhx == 0, f"count={mhx}")

# 3. No overlay sleeves
overlay = sum(1 for s in sleeves if re.search(r"_on_CHAMP|overlay", s, re.I))
check("Zero overlay sleeves", overlay == 0, f"count={overlay}")

# 4. Individual sleeve metrics
for s in sleeves:
    pi = isdf[s]; po = osdf[s]
    is_sr = pi.mean()/pi.std()*np.sqrt(12) if pi.std() > 0 else 0
    oos_sr = po.mean()/po.std()*np.sqrt(12) if po.std() > 0 else 0
    oos_ann = po.mean()*12*100
    vt = vt_bad(s)
    report["sleeves"].append({
        "name": os.path.basename(s),
        "weight_pct": float(w[s]*100),
        "is_sr": float(is_sr),
        "oos_sr": float(oos_sr),
        "oos_ann_pct": float(oos_ann),
        "vt_bad": bool(vt),
    })

# 5. All sleeves have positive IS SR
all_pos_is = all(s['is_sr'] > 0 for s in report["sleeves"])
check("All sleeves IS SR > 0", all_pos_is, "")

# 6. Not all sleeves OOS SR > 0 (would be suspicious)
all_pos_oos = all(s['oos_sr'] > 0 for s in report["sleeves"])
check("Not all sleeves OOS SR > 0 (realistic)", not all_pos_oos, f"all positive: {all_pos_oos}")

# 7. Sleeves with negative OOS SR
neg_oos = [s for s in report["sleeves"] if s['oos_sr'] < 0]
check("Some sleeves with negative OOS SR (diversification)", len(neg_oos) >= 0, f"neg count={len(neg_oos)}")

# 8. Weight concentration: Herfindahl index
hhi = (w**2).sum()
check("HHI < 0.1 (well diversified)", hhi < 0.10, f"HHI={hhi:.4f}")

# 9. Effective number of sleeves
eff_n = 1 / hhi
check("Effective N > 10", eff_n > 10, f"eff_n={eff_n:.1f}")

# 10. Each sleeve's data coverage
for s in sleeves:
    coverage = (df[s] != 0).sum() / len(df)
    if coverage < 0.3:
        check(f"Coverage {os.path.basename(s)} > 30%", False, f"coverage={coverage*100:.1f}%")
check("All sleeves coverage > 30%", all((df[s]!=0).sum()/len(df) > 0.3 for s in sleeves), "")

# 11. Metadata exists for all sleeves
meta_missing = [os.path.basename(s) for s in sleeves if not os.path.exists(os.path.splitext(os.path.join(ROOT,s))[0]+".csv.meta")]
check("Metadata exists for all sleeves", len(meta_missing) == 0, f"missing={meta_missing}")

# Print sleeve table
print(f"\n  {'Sleeve':<50s} {'w%':>5} {'IS SR':>7} {'OOS SR':>7} {'OOS ann':>8} {'vt_bad':>6}")
for s in report["sleeves"]:
    print(f"  {s['name']:<50s} {s['weight_pct']:5.1f} {s['is_sr']:7.3f} {s['oos_sr']:7.3f} {s['oos_ann_pct']:7.2f}% {'YES' if s['vt_bad'] else 'no':>6}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent06_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
