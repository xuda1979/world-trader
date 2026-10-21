"""AGENT 03: PnL Reconstruction Audit
Verify that portfolio returns from weights match saved monthly files."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; isdf = D['isdf']; osdf = D['osdf']
OD = D['OD']
report = {"agent": "03_pnl_reconstruction", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

print("=== AGENT 03: PnL Reconstruction Audit ===")

# 1. Full monthly file
port_full = df[sleeves].dot(w)
pm_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_full_monthly.csv"), index_col=0)
pm_file.index = pd.to_datetime(pm_file.index)
common = port_full.index.intersection(pm_file.index)
diff = (port_full.loc[common] - pm_file.loc[common, 'ret']).abs()
check("Full monthly matches file", diff.max() < 1e-10, f"max diff={diff.max():.2e}")

# 2. OOS monthly file
port_oos = osdf[sleeves].dot(w)
po_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_oos_monthly.csv"), index_col=0)
po_file.index = pd.to_datetime(po_file.index)
common_o = port_oos.index.intersection(po_file.index)
diff_o = (port_oos.loc[common_o] - po_file.loc[common_o, 'ret']).abs()
check("OOS monthly matches file", diff_o.max() < 1e-10, f"max diff={diff_o.max():.2e}")

# 3. SR computation from monthly
def perf(r):
    r = r.dropna(); r = r[r.abs() < 0.5]
    return r.mean()/r.std()*np.sqrt(12) if len(r) > 1 else 0

is_sr = perf(isdf[sleeves].dot(w))
oos_sr = perf(osdf[sleeves].dot(w))
full_sr = perf(df[sleeves].dot(w))
bj = json.load(open(os.path.join(OD, "OPT_20V5_honest_best.json")))
check("IS SR matches json", abs(is_sr - bj['is_sr']) < 0.001, f"computed={is_sr:.4f} json={bj['is_sr']:.4f}")
check("OOS SR matches json", abs(oos_sr - bj['oos_sr']) < 0.001, f"computed={oos_sr:.4f} json={bj['oos_sr']:.4f}")
check("Full SR matches json", abs(full_sr - bj.get('full_sr', 0)) < 0.001, f"computed={full_sr:.4f} json={bj.get('full_sr',0):.4f}")

# 4. Ann return computation
oos_ann = osdf[sleeves].dot(w).mean() * 12 * 100 * 1.6
check("OOS ann (1.6x) matches json", abs(oos_ann - bj['oos_ann']) < 0.01, f"computed={oos_ann:.4f} json={bj['oos_ann']:.4f}")

# 5. DD computation
eq = (1 + osdf[sleeves].dot(w)).cumprod()
oos_dd = (eq/eq.cummax() - 1).min() * 100
check("OOS DD matches json", abs(oos_dd - bj['oos_dd']) < 0.01, f"computed={oos_dd:.4f} json={bj['oos_dd']:.4f}")

# 6. Verify monthly returns are reasonable (no extreme values)
port_ret = df[sleeves].dot(w)
check("No monthly return > 50%", port_ret.abs().max() < 0.50, f"max={port_ret.abs().max():.4f}")
check("No monthly return > 20%", port_ret.abs().max() < 0.20, f"max={port_ret.abs().max():.4f}")

# 7. Cumulative return check
cum_ret = (1 + port_full).prod() - 1
check("Cumulative return positive", cum_ret > 0, f"cum={cum_ret*100:.1f}%")
check("Cumulative return > 100% over 18yr", cum_ret > 1.0, f"cum={cum_ret*100:.1f}%")

# 8. Monthly return distribution
check("Mean monthly return > 0", port_full.mean() > 0, f"mean={port_full.mean()*100:.3f}%")
check("Median monthly return > 0", port_full.median() > 0, f"median={port_full.median()*100:.3f}%")
check("Positive months > 60%", (port_full > 0).mean() > 0.60, f"pos%={(port_full>0).mean()*100:.1f}%")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent03_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
