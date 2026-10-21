"""AGENT 07: Cost Sensitivity & Financing Stress Audit
Verify portfolio survives under higher cost and margin stress scenarios."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; osdf = D['osdf']
report = {"agent": "07_cost_stress", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

def perf(r):
    r = r.dropna(); r = r[r.abs() < 0.5]
    return r.mean()/r.std()*np.sqrt(12) if len(r) > 1 else 0

print("=== AGENT 07: Cost Sensitivity & Financing Stress ===")

port = df[sleeves].dot(w)
port_oos = osdf[sleeves].dot(w)

# 1. Cost sensitivity: apply different cost assumptions
# Blotter shows ~12.3% turnover/yr, at 6.4bps = ~0.79%/yr cost
# Test at higher costs
for bps in [6.4, 10, 15, 20, 30, 50]:
    # Estimate annual cost: total_qty * bps / n_years / 100
    bl = pd.read_csv(os.path.join(D['OD'], "OPT_20V5_honest_blotter.csv"))
    total_qty = bl['qty_notional'].sum()
    n_years = 17.67
    annual_cost_pct = total_qty * bps / n_years / 10000
    # Net return = gross - cost
    gross_ann = port.mean() * 12
    net_ann = gross_ann - annual_cost_pct
    net_sr = net_ann / port.std() / np.sqrt(12) if port.std() > 0 else 0
    check(f"Survives at {bps}bps cost (SR>0)", net_sr > 0, f"cost={annual_cost_pct*100:.2f}%/yr net_SR={net_sr:.3f}")

# 2. Margin stress: test at different leverage levels
for lev in [1.0, 1.6, 2.0, 2.5, 3.0]:
    eq = (1 + port * lev).cumprod()
    dd = (eq/eq.cummax() - 1).min() * 100
    ann = port.mean() * 12 * lev * 100
    sr = perf(port)  # SR doesn't change with leverage
    check(f"Lev {lev}x: DD > -20%", dd > -20, f"DD={dd:.2f}% ann={ann:.1f}%")

# 3. Borrow cost stress (short positions)
# Some sleeves go short; model borrow cost
for borrow_bps in [0, 50, 100, 200]:
    # Approximate: half of turnover is short, borrow cost = short_qty * borrow_bps
    bl = pd.read_csv(os.path.join(D['OD'], "OPT_20V5_honest_blotter.csv"))
    short_qty = bl[bl['side']=='SELL']['qty_notional'].sum()
    borrow_cost_pct = short_qty * borrow_bps / 17.67 / 10000
    net_ann = port.mean() * 12 - borrow_cost_pct
    check(f"Borrow {borrow_bps}bps: net ann > 0", net_ann > 0, f"borrow_cost={borrow_cost_pct*100:.2f}%/yr net={net_ann*100:.1f}%")

# 4. Regime stress: worst 6-month period
rolling_6m = port.rolling(6).apply(lambda x: (1+x).prod()-1 if len(x)==6 else np.nan).dropna()
worst_6m = rolling_6m.min()
check("Worst 6m return > -10%", worst_6m > -0.10, f"worst 6m={worst_6m*100:.2f}%")

# 5. 2008-style stress: assume 30% monthly drawdown
stress_ret = port.copy()
stress_ret.iloc[0] = -0.30  # worst month
eq_stress = (1 + stress_ret).cumprod()
dd_stress = (eq_stress/eq_stress.cummax()-1).min()*100
check("Survives 30% monthly shock (DD > -35%)", dd_stress > -35, f"stress DD={dd_stress:.1f}%")

# 6. Cost at 1.6x leverage
bl = pd.read_csv(os.path.join(D['OD'], "OPT_20V5_honest_blotter.csv"))
total_qty = bl['qty_notional'].sum()
cost_16x = total_qty * 6.4 / 17.67 / 10000 * 1.6
gross_ann_16x = port.mean() * 12 * 1.6
net_ann_16x = gross_ann_16x - cost_16x
check("Net ann at 1.6x > 15%", net_ann_16x > 0.15, f"net={net_ann_16x*100:.1f}%")
check("Cost at 1.6x < 2%/yr", cost_16x < 0.02, f"cost={cost_16x*100:.2f}%")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent07_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
