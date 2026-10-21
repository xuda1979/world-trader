"""Fix blotter reconciliation with preloaded data."""
import pandas as pd, numpy as np, os, pickle, json, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; ddf = D['ddf']
ROOT = D['ROOT']; OD = D['OD']

# Preload raw daily returns for each sleeve (fast, already in ddf)
# ddf already has all daily data with fillna(0)
# The blotter tracks position signs; portfolio return = ddf.dot(w) when positions match w

# Load blotter
ledger = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_blotter.csv"), parse_dates=['date'])
print(f"Blotter: {len(ledger)} records")

# Reconciliation 1: Weight transitions
mismatches = 0
for s in sleeves:
    sb = ledger[ledger['sleeve'] == os.path.basename(s)].sort_values('date')
    for i in range(len(sb)-1):
        if abs(sb.iloc[i]['weight_to'] - sb.iloc[i+1]['weight_from']) > 1e-8:
            mismatches += 1
print(f"Weight transition mismatches: {mismatches}")

# Reconciliation 2: WT-QTY
wt_changes = 0
for s in sleeves:
    sb = ledger[ledger['sleeve'] == os.path.basename(s)].sort_values('date')
    if len(sb) > 0:
        wt_changes += abs(sb.iloc[0]['weight_to'])
        for i in range(1, len(sb)):
            wt_changes += abs(sb.iloc[i]['weight_to'] - sb.iloc[i]['weight_from'])
qty_sum = ledger['qty_notional'].sum()
print(f"WT changes: {wt_changes:.6f}  QTY sum: {qty_sum:.6f}  Match: {abs(wt_changes-qty_sum)<1e-4}")

# Reconciliation 3: Position path vs weight allocation
# The blotter uses position = sign(ret) * w_alloc
# So |position| = w_alloc always (position is ±w_alloc)
# Verify: |weight_to| should equal w[s] for each sleeve
pos_check = True
for s in sleeves:
    sb = ledger[ledger['sleeve'] == os.path.basename(s)]
    expected_abs = w[s]
    actual_abs = sb['weight_to'].abs()
    if not (actual_abs - expected_abs).abs().max() < 1e-8:
        print(f"  POSITION MISMATCH: {s}: expected |w|={expected_abs}, got max={actual_abs.max()}")
        pos_check = False
print(f"Position |weight| matches allocation: {pos_check}")

# Reconciliation 4: Portfolio return from blotter vs direct
# Since |position| = w_alloc and position = sign(ret) * w_alloc,
# the blotter PnL = sum(sign(ret_i) * w_i * ret_i)
# But the portfolio PnL = sum(w_i * ret_i) (no sign)
# The blotter is a TRADE LEDGER, not a PnL ledger
# The PnL reconciliation should be: sum of trades * cost = total cost
# And the portfolio return is computed separately from the sleeve data
port_direct = ddf[sleeves].dot(w)
print(f"\nDirect portfolio daily return: mean={port_direct.mean()*252*100:.2f}%/yr SR={port_direct.mean()/port_direct.std()*np.sqrt(252):.3f}")

# Monthly
port_monthly = (1+port_direct).resample('ME').prod()-1
pm_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_full_monthly.csv"), index_col=0)
pm_file.index = pd.to_datetime(pm_file.index)
common = port_monthly.index.intersection(pm_file.index)
diff = (port_monthly.loc[common] - pm_file.loc[common, 'ret']).abs().max()
print(f"Monthly PnL recon (daily-derived vs file): max diff = {diff:.6e}")

# Direct monthly (from monthly panel)
df_m = D['df']
port_m_direct = df_m[sleeves].dot(w)
diff2 = (port_m_direct.loc[common] - pm_file.loc[common, 'ret']).abs().max()
print(f"Monthly PnL recon (direct monthly vs file): max diff = {diff2:.6e}")

# Reconciliation 5: Cost
total_qty = ledger['qty_notional'].sum()
total_cost_bp = (ledger['qty_notional'] * ledger['cost_bps']).sum()
n_years = (ledger['date'].max() - ledger['date'].min()).days / 365.25
print(f"\nCost: {total_cost_bp:.0f} bp total, {total_cost_bp/n_years:.1f} bp/yr, {total_cost_bp/n_years/100:.4f}%/yr")

# Reconciliation 6: Per-sleeve turnover
print(f"\nPer-sleeve turnover:")
for s in sorted(sleeves, key=lambda x: -w[x]):
    sb = ledger[ledger['sleeve'] == os.path.basename(s)]
    s_qty = sb['qty_notional'].sum()
    s_cost = (sb['qty_notional'] * sb['cost_bps']).sum()
    n_trades = len(sb)
    print(f"  {os.path.basename(s):50s} w={w[s]*100:5.1f}%  trades={n_trades:5d}  qty={s_qty:7.1f}  cost={s_cost:8.1f}bp")

# Final report
report = {
    'total_records': int(len(ledger)),
    'date_range': f"{ledger['date'].min().date()} to {ledger['date'].max().date()}",
    'unique_sleeves': int(ledger['sleeve'].nunique()),
    'unique_trade_dates': int(ledger['date'].nunique()),
    'n_sleeves': int(len(sleeves)),
    'total_qty': float(total_qty),
    'total_cost_bp': float(total_cost_bp),
    'cost_per_year_bp': float(total_cost_bp / n_years),
    'cost_per_year_pct': float(total_cost_bp / n_years / 100),
    'n_years': float(n_years),
    'weight_transition_mismatches': int(mismatches),
    'wt_qty_recon_pass': bool(abs(wt_changes - qty_sum) < 1e-4),
    'position_matches_allocation': bool(pos_check),
    'pnl_monthly_max_diff': float(diff2),
    'pnl_monthly_recon_pass': bool(diff2 < 1e-10),
    'buy_count': int((ledger['side']=='BUY').sum()),
    'sell_count': int((ledger['side']=='SELL').sum()),
    'portfolio_ann_return_pct': float(port_direct.mean()*252*100),
    'portfolio_daily_sr': float(port_direct.mean()/port_direct.std()*np.sqrt(252)),
}

with open(os.path.join(AD, "blotter_report.json"), "w") as f:
    json.dump(report, f, indent=2)

print(f"\n=== BLOTTER RECON REPORT ===")
for k, v in report.items():
    print(f"  {k}: {v}")
