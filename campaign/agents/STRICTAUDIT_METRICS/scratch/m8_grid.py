# m8: is the champion grid the INTERSECTION of sleeve dates? Are after-gap days accumulation?
import pandas as pd, numpy as np
B="/Users/daxu/software/world-trader"
SLEEVES = {
 'brwt15': f"{B}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 'brwt10': f"{B}/campaign/agents/COORD/sleeves/brwt10_2000.csv",
 'brwt7':  f"{B}/campaign/agents/COORD/sleeves/brwt7.csv",
 'brwt5':  f"{B}/campaign/agents/COORD/sleeves/brwt5.csv",
 'C5ng':   f"{B}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 'C5ngsum':f"{B}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 'A5r2':   f"{B}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 'a6r7':   f"{B}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 'QAxasts':f"{B}/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 'carryv2':f"{B}/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 'dualmom':f"{B}/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 'XGB1y':  f"{B}/campaign/results/sleeve_library/XGB1y_deploy.csv",
}
P={}
for k,p in SLEEVES.items():
    s=pd.read_csv(p,parse_dates=['date']).set_index('date')['ret']
    P[k]=pd.to_numeric(s,errors='coerce')
ch=pd.read_csv(f"{B}/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']

win = ch.index
sets = {k:set(P[k].dropna().index) for k in P}
inter = set(win)
for k in sets: inter &= sets[k]
inter = pd.DatetimeIndex(sorted(inter))
print(f"champion rows={len(win)}  intersection of 12 sleeve date-sets within window={len(inter)}")
print(f"champion == intersection? {set(win)==set(inter)}")
champ_not_inter = sorted(set(win)-set(inter)); inter_not_champ = sorted(set(inter)-set(win))
print(f"in champion not in intersection: {len(champ_not_inter)}", [str(d.date()) for d in champ_not_inter[:10]])
print(f"in intersection not in champion: {len(inter_not_champ)}", [str(d.date()) for d in inter_not_champ[:10]])

# which sleeves are missing on each champion-missing day (union grid)?
miss = [d for d in win if all(d not in sets[k] for k in ['brwt7'])]  # placeholder
allgrid = set()
for k in sets: allgrid |= sets[k]
allgrid = pd.DatetimeIndex(sorted(d for d in allgrid if win[0]<=d<=win[-1]))
missing = [d for d in allgrid if d not in set(win)]
print(f"\nunion-grid missing days: {len(missing)}")
cnt = pd.Series({d: sum(d not in sets[k] for k in P) for d in missing[:0]} ) 
rows=[]
for d in missing:
    absent=[k for k in P if d not in sets[k]]
    rows.append((d, len(absent), ','.join(absent)))
cnts = pd.Series([n for _,n,_ in rows]).value_counts().sort_index()
print("distribution of #absent sleeves on missing days:")
print(cnts.to_string())
print("\nfirst 15 missing days with absent sleeves:")
for d,n,a in rows[:15]: print(f"  {d.date()}: {n} absent -> {a[:80]}")
# who is absent most?
ab = pd.Series([k for _,_,a in rows for k in a.split(',') if a]).value_counts()
print("\nabsence count by sleeve:")
print(ab.to_string())
