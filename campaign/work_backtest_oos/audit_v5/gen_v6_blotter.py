import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings("ignore")
with open("shared_data.pkl","rb") as f: D=pickle.load(f)
sleeves=D["sleeves"]; w=D["w"]; ddf=D["ddf"]
OD=D["OD"]

# Load V6 weights
v6=pd.read_csv(os.path.join(OD,"OPT_20V6_weights.csv"),index_col=0)
wt=v6["w"]

# Monthly rebalancing blotter (same as V5-honest fix)
all_dates=ddf.index
monthly_dates=pd.DatetimeIndex(pd.Series(all_dates).groupby(all_dates.to_period("M")).first().values)

ledger=[]
BPS=6.4
cur_w={s:0.0 for s in sleeves}

for i,dt in enumerate(monthly_dates):
    for s in sleeves:
        target=wt[s]; current=cur_w[s]
        delta=target-current
        if abs(delta)>1e-8:
            side="BUY" if delta>0 else "SELL"
            ledger.append({"date":dt,"sleeve":os.path.basename(s),
                "instrument":os.path.basename(s),"side":side,
                "price":100.0,"price_source":"SYNTH",
                "qty_notional":abs(delta),
                "weight_from":current,"weight_to":target,"cost_bps":BPS})
            cur_w[s]=target
    if i<len(monthly_dates)-1:
        nd=monthly_dates[i+1]
        md=ddf[(ddf.index>=dt)&(ddf.index<nd)]
        for s in sleeves:
            if s in md.columns and len(md)>0:
                mr=(1+md[s]).prod()-1
                cur_w[s]=cur_w[s]*(1+mr)

bl=pd.DataFrame(ledger).sort_values("date").reset_index(drop=True)
bl.to_csv(os.path.join(OD,"OPT_20V6_blotter.csv"),index=False)

n_yr=(bl["date"].max()-bl["date"].min()).days/365.25
tq=bl["qty_notional"].sum()
tc=tq*BPS
print(f"V6 Blotter: {len(bl)} records, {tq:.2f} total qty, {tc/n_yr/100:.4f}%/yr cost")

# PnL recon
pm=D["df"][sleeves].dot(wt)
pmf=pd.read_csv(os.path.join(OD,"OPT_20V6_full_monthly.csv"),index_col=0)
pmf.index=pd.to_datetime(pmf.index)
common=pm.index.intersection(pmf.index)
diff=(pm.loc[common]-pmf.loc[common,"ret"]).abs().max()
print(f"PnL recon: {diff:.2e} -> {"PASS" if diff<1e-10 else "FAIL"}")