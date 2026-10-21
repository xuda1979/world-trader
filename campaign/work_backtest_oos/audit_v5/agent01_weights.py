"""AGENT 01: Weight Integrity Audit
Verify weight constraints, normalization, and boundary conditions."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; OD = D['OD']
report = {"agent": "01_weight_integrity", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

print("=== AGENT 01: Weight Integrity Audit ===")

# 1. Sum to 1.0
check("Weight sum = 1.0", abs(w.sum() - 1.0) < 1e-10, f"sum={w.sum():.15f}")

# 2. All weights positive
check("All weights positive", (w > 0).all(), f"min={w.min():.6f}")

# 3. Max weight constraint
check("Max weight ≤ 10%", w.max() <= 0.10 + 1e-8, f"max={w.max():.6f}")

# 4. Min weight constraint  
check("Min weight ≥ 2%", w.min() >= 0.02 - 1e-8, f"min={w.min():.6f}")

# 5. No NaN or Inf
check("No NaN", not w.isna().any(), f"NaN count={w.isna().sum()}")
check("No Inf", not np.isinf(w.values).any(), "")

# 6. Weights match saved file
w_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_weights.csv"), index_col=0)['w']
check("Weights match file", (w - w_file).abs().max() < 1e-10, f"max diff={(w-w_file).abs().max():.2e}")

# 7. Energy exposure
ENP = __import__('re').compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|brent|wti|\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)", __import__('re').I)
en_flags = [bool(ENP.search(os.path.basename(s))) for s in sleeves]
en_exp = sum(w.values[i] * en_flags[i] for i in range(len(sleeves)))
check("Energy ≤ 30%", en_exp <= 0.30, f"energy={en_exp*100:.1f}%")
check("Energy > 0%", en_exp > 0, f"energy={en_exp*100:.1f}%")

# 8. No single sleeve dominates
check("No sleeve > 50%", w.max() < 0.50, f"max={w.max()*100:.1f}%")
check("Top 3 < 50%", w.nlargest(3).sum() < 0.50, f"top3={w.nlargest(3).sum()*100:.1f}%")

# 9. Weight distribution
check("Weight std < 3%", w.std() < 0.03, f"std={w.std()*100:.2f}%")

# 10. N sleeves correct
check("N sleeves = 20", len(sleeves) == 20, f"n={len(sleeves)}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent01_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
