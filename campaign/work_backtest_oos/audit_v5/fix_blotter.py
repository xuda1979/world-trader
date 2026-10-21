"""Fix the V5-honest blotter to use monthly rebalancing model."""
import pandas as pd, numpy as np, os, pickle, json, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; ddf = D['ddf']
ROOT = D['ROOT']; OD = D['OD']

# Monthly rebalancing: first trading day of each month
all_dates = ddf.index
monthly_trade_dates = pd.DatetimeIndex(
    pd.Series(all_dates).groupby(all_dates.to_period('M')).first().values
)

print(f"Monthly trade dates: {len(monthly_trade_dates)}")

ledger_rows = []
BPS = 6.4
current_weights = {s: 0.0 for s in sleeves}

for i, dt in enumerate(monthly_trade_dates):
    for s in sleeves:
        target_w = w[s]
        current_w = current_weights[s]
        delta = target_w - current_w
        if abs(delta) > 1e-8:
            side = "BUY" if delta > 0 else "SELL"
            ledger_rows.append({
                'date': dt, 'sleeve': os.path.basename(s),
                'instrument': os.path.basename(s),
                'side': side, 'price': 100.0, 'price_source': 'SYNTH',
                'qty_notional': abs(delta),
                'weight_from': current_w, 'weight_to': target_w,
                'cost_bps': BPS,
            })
            current_weights[s] = target_w
    
    # Simulate drift
    if i < len(monthly_trade_dates) - 1:
        next_dt = monthly_trade_dates[i + 1]
        month_data = ddf[(ddf.index >= dt) & (ddf.index < next_dt)]
        for s in sleeves:
            if s in month_data.columns and len(month_data) > 0:
                month_ret = (1 + month_data[s]).prod() - 1
                current_weights[s] = current_weights[s] * (1 + month_ret)

ledger = pd.DataFrame(ledger_rows)
ledger = ledger.sort_values('date').reset_index(drop=True)

out_path = os.path.join(OD, "OPT_20V5_honest_blotter.csv")
ledger.to_csv(out_path, index=False)

total_qty = ledger['qty_notional'].sum()
total_cost_bp = (ledger['qty_notional'] * ledger['cost_bps']).sum()
n_years = (ledger['date'].max() - ledger['date'].min()).days / 365.25
annual_turnover = total_qty / n_years
annual_cost_pct = total_cost_bp / n_years / 100

print(f"\n=== FIXED BLOTTER (monthly rebalancing) ===")
print(f"Records: {len(ledger)}")
print(f"Total qty: {total_qty:.2f}")
print(f"Annual turnover: {annual_turnover:.2f}x")
print(f"Annual cost: {annual_cost_pct:.4f}%/yr")
print(f"Annual cost at 1.6x: {annual_cost_pct*1.6:.4f}%/yr")

# PnL recon
port_monthly = D['df'][sleeves].dot(w)
pm_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_full_monthly.csv"), index_col=0)
pm_file.index = pd.to_datetime(pm_file.index)
common = port_monthly.index.intersection(pm_file.index)
pnl_diff = (port_monthly.loc[common] - pm_file.loc[common, 'ret']).abs().max()
print(f"PnL recon: {pnl_diff:.2e} → {'PASS' if pnl_diff < 1e-10 else 'FAIL'}")

# Save report
report = {
    'total_records': int(len(ledger)),
    'date_range': f"{ledger['date'].min().date()} to {ledger['date'].max().date()}",
    'unique_sleeves': int(ledger['sleeve'].nunique()),
    'unique_trade_dates': int(ledger['date'].nunique()),
    'n_sleeves': int(len(sleeves)),
    'total_qty': float(total_qty),
    'total_cost_bp': float(total_cost_bp),
    'annual_turnover_x': float(annual_turnover),
    'annual_cost_pct': float(annual_cost_pct),
    'annual_cost_pct_16x': float(annual_cost_pct * 1.6),
    'n_years': float(n_years),
    'rebalance_frequency': 'monthly',
    'cost_bps': 6.4,
    'pnl_recon_max_diff': float(pnl_diff),
    'pnl_recon_pass': bool(pnl_diff < 1e-10),
    'buy_count': int((ledger['side']=='BUY').sum()),
    'sell_count': int((ledger['side']=='SELL').sum()),
}
with open(os.path.join(AD, "blotter_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"Report saved")
