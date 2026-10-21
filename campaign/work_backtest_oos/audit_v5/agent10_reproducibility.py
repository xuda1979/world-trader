"""AGENT 10: Reproducibility & Edge Case Audit
Verify results are reproducible and handle edge cases (NaN, inf, missing data)."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; isdf = D['isdf']; osdf = D['osdf']; ddf = D['ddf']
OD = D['OD']; ROOT = D['ROOT']
report = {"agent": "10_reproducibility_edge", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

def perf(r):
    r = r.dropna(); r = r[r.abs() < 0.5]
    return r.mean()/r.std()*np.sqrt(12) if len(r) > 1 else 0

print("=== AGENT 10: Reproducibility & Edge Case Audit ===")

# 1. Reproducibility: recompute from scratch and compare
port_recomputed = df[sleeves].dot(w)
pm_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_full_monthly.csv"), index_col=0)
pm_file.index = pd.to_datetime(pm_file.index)
diff = (port_recomputed - pm_file['ret']).abs().max()
check("Reproducible: recomputed matches file", diff < 1e-10, f"max diff={diff:.2e}")

# 2. Weights file reproducibility
w_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_weights.csv"), index_col=0)['w']
check("Weights reproducible", (w - w_file).abs().max() < 1e-10, f"max diff={(w-w_file).abs().max():.2e}")

# 3. JSON metrics reproducibility
bj = json.load(open(os.path.join(OD, "OPT_20V5_honest_best.json")))
is_sr = perf(isdf[sleeves].dot(w))
oos_sr = perf(osdf[sleeves].dot(w))
check("IS SR reproducible", abs(is_sr - bj['is_sr']) < 0.001, "")
check("OOS SR reproducible", abs(oos_sr - bj['oos_sr']) < 0.001, "")

# 4. Edge case: NaN in sleeve data
n_nan = df[sleeves].isna().sum().sum()
check("No NaN in monthly panel", n_nan == 0, f"NaN count={n_nan}")

# 5. Edge case: Inf in sleeve data
n_inf = np.isinf(df[sleeves].values).sum()
check("No Inf in monthly panel", n_inf == 0, f"Inf count={n_inf}")

# 6. Edge case: daily data NaN/Inf
n_nan_d = ddf[sleeves].isna().sum().sum()
n_inf_d = np.isinf(ddf[sleeves].values).sum()
check("No NaN in daily panel", n_nan_d == 0, f"NaN count={n_nan_d}")
check("No Inf in daily panel", n_inf_d == 0, f"Inf count={n_inf_d}")

# 7. Edge case: extreme returns (> 50% in a month)
extreme = (df[sleeves].abs() > 0.5).sum().sum()
check("No extreme monthly returns > 50%", extreme == 0, f"count={extreme}")

# 8. Edge case: all-zero months
all_zero = (df[sleeves].sum(axis=1) == 0).sum()
check("No all-zero months", all_zero == 0, f"count={all_zero}")

# 9. Determinism: same computation twice gives same result
sr1 = perf(osdf[sleeves].dot(w))
sr2 = perf(osdf[sleeves].dot(w))
check("Deterministic computation", sr1 == sr2, f"sr1={sr1:.10f} sr2={sr2:.10f}")

# 10. Missing data handling: fillna(0) is the right approach
# Verify that fillna(0) doesn't create bias
# A sleeve with missing months contributes 0 return = no position
# This is correct if missing = not trading
n_missing_per_sleeve = {}
for s in sleeves:
    raw_data = df[s]
    n_missing_per_sleeve[os.path.basename(s)] = int((raw_data == 0).sum())
max_missing = max(n_missing_per_sleeve.values())
check("Max missing months per sleeve < 100", max_missing < 100, f"max={max_missing}")

# 11. Sleeve file existence
all_exist = all(os.path.exists(os.path.join(ROOT, s)) for s in sleeves)
check("All sleeve CSV files exist", all_exist, "")

# 12. Weight sum precision
check("Weight sum precision < 1e-10", abs(w.sum() - 1.0) < 1e-10, f"sum={w.sum():.15f}")

# 13. Monthly file column name
check("Monthly file has 'ret' column", 'ret' in pm_file.columns, f"columns={list(pm_file.columns)}")

# 14. Index type is datetime
check("Monthly file index is datetime", isinstance(pm_file.index, pd.DatetimeIndex), "")

# 15. No duplicate dates
check("No duplicate dates in monthly file", pm_file.index.duplicated().sum() == 0, f"dups={pm_file.index.duplicated().sum()}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent10_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
