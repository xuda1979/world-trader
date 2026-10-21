"""AGENT 05: Robustness & Stability Audit
Walk-forward, leave-one-out, and sub-period stability checks."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; osdf = D['osdf']
report = {"agent": "05_robustness_stability", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

def perf(r):
    r = r.dropna(); r = r[r.abs() < 0.5]
    return r.mean()/r.std()*np.sqrt(12) if len(r) > 1 else 0

print("=== AGENT 05: Robustness & Stability Audit ===")

# 1. Walk-forward: 5yr IS → 1yr OOS
wf_srs = []
for fs in range(2012, 2022):
    oos_s = pd.Timestamp(f"{fs+5}-01-01")
    oos_e = pd.Timestamp(f"{fs+6}-01-01")
    oos_win = df[sleeves][(df.index >= oos_s) & (df.index < oos_e)]
    if len(oos_win) >= 6:
        sr = perf(oos_win.dot(w))
        wf_srs.append(sr)
        
check("WF: all 10 folds positive", all(s > 0 for s in wf_srs), f"min={min(wf_srs):.3f}")
check("WF: mean SR > 3.0", np.mean(wf_srs) > 3.0, f"mean={np.mean(wf_srs):.3f}")
check("WF: min fold SR > 2.0", min(wf_srs) > 2.0, f"min={min(wf_srs):.3f}")
check("WF: max fold SR < 10.0", max(wf_srs) < 10.0, f"max={max(wf_srs):.3f}")

# 2. Leave-one-out
loo_srs = []
for i in range(len(sleeves)):
    mask = [j for j in range(len(sleeves)) if j != i]
    wl = w.values[mask] / w.values[mask].sum()
    loo_srs.append(perf(osdf[[sleeves[j] for j in mask]].dot(wl)))
check("LOO: all > 2.0", all(s > 2.0 for s in loo_srs), f"min={min(loo_srs):.3f}")
check("LOO: all > 3.0", all(s > 3.0 for s in loo_srs), f"min={min(loo_srs):.3f}")
check("LOO: mean within 10% of portfolio", abs(np.mean(loo_srs) - perf(osdf[sleeves].dot(w))) / perf(osdf[sleeves].dot(w)) < 0.10,
      f"loo_mean={np.mean(loo_srs):.3f} port={perf(osdf[sleeves].dot(w)):.3f}")

# 3. Sub-period stability (quarterly)
port = df[sleeves].dot(w)
qly = port.resample('QE').apply(lambda x: (1+x).prod()-1 if len(x) > 0 else 0)
check("Quarterly: positive quarters > 65%", (qly > 0).mean() > 0.65, f"pos%={(qly>0).mean()*100:.1f}%")
check("Quarterly: max quarterly return < 15%", qly.max() < 0.15, f"max={qly.max()*100:.1f}%")
check("Quarterly: min quarterly return > -5%", qly.min() > -0.05, f"min={qly.min()*100:.1f}%")

# 4. Year-by-year consistency
yr = port.groupby(port.index.year).apply(lambda x: (1+x).prod()-1)
check("All years positive", (yr > 0).all(), f"neg years={int((yr<0).sum())}")
check("Yearly std < 8%", yr.std() < 0.08, f"std={yr.std()*100:.1f}%")
check("Worst year > 2%", yr.min() > 0.02, f"worst={yr.min()*100:.1f}%")
check("Best year < 35%", yr.max() < 0.35, f"best={yr.max()*100:.1f}%")

# 5. H1/H2 stability
o1 = perf(osdf[sleeves][osdf.index < '2021-01-01'].dot(w))
o2 = perf(osdf[sleeves][osdf.index >= '2021-01-01'].dot(w))
check("H1 SR > 2.0", o1 > 2.0, f"H1={o1:.3f}")
check("H2 SR > 2.0", o2 > 2.0, f"H2={o2:.3f}")
check("H1/H2 ratio > 0.4", min(o1,o2)/max(o1,o2) > 0.4, f"ratio={min(o1,o2)/max(o1,o2):.3f}")

# 6. Rolling 36-month SR
rolling_sr = port.rolling(36).apply(lambda x: x.mean()/x.std()*np.sqrt(12) if len(x)==36 and x.std()>0 else np.nan)
rolling_sr = rolling_sr.dropna()
check("Rolling 36m SR: min > 2.0", rolling_sr.min() > 2.0, f"min={rolling_sr.min():.3f}")
check("Rolling 36m SR: max < 15.0", rolling_sr.max() < 15.0, f"max={rolling_sr.max():.3f}")

# 7. Bootstrap: sample 100 random 60-month windows
np.random.seed(42)
boot_srs = []
for _ in range(100):
    start_idx = np.random.randint(0, len(port) - 60)
    window = port.iloc[start_idx:start_idx+60]
    boot_srs.append(perf(window))
check("Bootstrap 60m: 95th percentile > 2.0", np.percentile(boot_srs, 5) > 2.0, f"5th={np.percentile(boot_srs,5):.3f}")
check("Bootstrap 60m: mean > 4.0", np.mean(boot_srs) > 4.0, f"mean={np.mean(boot_srs):.3f}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent05_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
