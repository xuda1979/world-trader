"""AGENT 04: Blotter & Trade Record Audit
Verify trade blotter integrity, cost accounting, and turnover."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; OD = D['OD']
report = {"agent": "04_blotter_trades", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

print("=== AGENT 04: Blotter & Trade Record Audit ===")

# Load blotter
blotter_path = os.path.join(OD, "OPT_20V5_honest_blotter.csv")
check("Blotter file exists", os.path.exists(blotter_path), "")

if os.path.exists(blotter_path):
    bl = pd.read_csv(blotter_path, parse_dates=['date'])
    
    # 1. Record count
    check("Blotter has > 1000 records", len(bl) > 1000, f"records={len(bl)}")
    check("Blotter has 20 unique sleeves", bl['sleeve'].nunique() == 20, f"sleeves={bl['sleeve'].nunique()}")
    
    # 2. Required columns
    required = ['date','sleeve','instrument','side','price','price_source',
                'qty_notional','weight_from','weight_to','cost_bps']
    check("All required columns present", all(c in bl.columns for c in required), f"missing={set(required)-set(bl.columns)}")
    
    # 3. Weight transitions: weight_to[i] = weight_from[i+1] for same sleeve
    mismatches = 0
    for s in bl['sleeve'].unique():
        sb = bl[bl['sleeve']==s].sort_values('date')
        for i in range(len(sb)-1):
            if abs(sb.iloc[i]['weight_to'] - sb.iloc[i+1]['weight_from']) > 1e-8:
                mismatches += 1
    check("Weight transitions consistent", mismatches == 0, f"mismatches={mismatches}")
    
    # 4. |weight_to| = allocation weight for each sleeve
    w_dict = {os.path.basename(s): w[s] for s in sleeves}
    pos_ok = True
    for s_name in bl['sleeve'].unique():
        expected = w_dict.get(s_name, 0)
        actual_max = bl[bl['sleeve']==s_name]['weight_to'].abs().max()
        if abs(actual_max - expected) > 1e-6:
            pos_ok = False
    check("|weight_to| matches allocation", pos_ok, "")
    
    # 5. Cost accounting
    total_cost_bp = (bl['qty_notional'] * bl['cost_bps']).sum()
    n_years = (bl['date'].max() - bl['date'].min()).days / 365.25
    cost_per_year = total_cost_bp / n_years / 100  # percent per year
    check("Cost per year < 2%", cost_per_year < 2.0, f"cost={cost_per_year:.4f}%/yr")
    check("Cost per year > 0.1%", cost_per_year > 0.1, f"cost={cost_per_year:.4f}%/yr")
    check("Cost bps = 6.4 for all trades", (bl['cost_bps'] == 6.4).all(), f"unique bps={bl['cost_bps'].unique()}")
    
    # 6. Turnover reasonableness
    total_qty = bl['qty_notional'].sum()
    check("Total qty > 100", total_qty > 100, f"qty={total_qty:.1f}")
    check("Total qty < 10000", total_qty < 10000, f"qty={total_qty:.1f}")
    
    # 7. Date range
    check("Blotter starts 2009", bl['date'].min().year == 2009, f"start={bl['date'].min().date()}")
    check("Blotter ends 2026", bl['date'].max().year == 2026, f"end={bl['date'].max().date()}")
    
    # 8. Side balance
    buys = (bl['side']=='BUY').sum()
    sells = (bl['side']=='SELL').sum()
    check("BUY/SELL roughly balanced", abs(buys-sells)/len(bl) < 0.1, f"BUY={buys} SELL={sells}")
    
    # 9. Price source
    check("All SYNTH price", (bl['price_source']=='SYNTH').all(), f"sources={bl['price_source'].unique()}")
    
    # 10. Per-sleeve trade count
    trades_per_sleeve = bl.groupby('sleeve').size()
    check("All sleeves have trades", (trades_per_sleeve > 0).all(), f"min trades={trades_per_sleeve.min()}")
    check("Max trades per sleeve < 5000", trades_per_sleeve.max() < 5000, f"max={trades_per_sleeve.max()}")
    
    # 11. No trades on weekends (sanity)
    weekend_trades = bl[bl['date'].dt.dayofweek >= 5]
    check("No weekend trades (or minimal)", len(weekend_trades) < 100, f"weekend={len(weekend_trades)}")
else:
    check("Blotter file exists", False, "FILE MISSING")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent04_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
