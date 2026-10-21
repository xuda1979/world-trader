# m13: hole-day PnL materiality via FTRUTH proxy; top-day attribution; effective N
import pandas as pd, numpy as np
B="/Users/daxu/software/world-trader"
ch=pd.read_csv(f"{B}/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']
ft=pd.read_csv(f"{B}/campaign/results/GOAL100_FINAL_TRUTH_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']
cset=set(ch.index)
holes_ft=[d for d in ft.index if ch.index[0]<=d<=ch.index[-1] and d not in cset]
h=pd.Series({d:ft.loc[d] for d in holes_ft})
print(f"FTRUTH rows on champion-hole days: n={len(h)}  sum={h.sum()*100:+.2f}pp  mean/day={h.mean()*100:+.3f}%  win/loss={int((h>0).sum())}/{int((h<0).sum())}")
print(f"if ADDED back (approx, 12/14 scale): total PnL change = {h.sum()*100*(12/14):+.2f}pp over 18.3y")
print(f"champion total (sum of daily) = {ch.sum()*100:.1f}pp -> would become {ch.sum()*100 + h.sum()*100*(12/14):.1f}pp; ann {(ch.mean()*252 + h.mean()*(89/18.33)*252/252*252/252)*100:.2f}% approx")
# more precisely: recompute ann on combined series
comb = pd.concat([ch, h*(12/14)]).sort_index()
print(f"combined-series ann = {comb.mean()*252*100:.2f}%  (champion as-is 49.36%)")

# top-day attribution
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
P={k:pd.to_numeric(pd.read_csv(p,parse_dates=['date']).set_index('date')['ret'],errors='coerce') for k,p in SLEEVES.items()}
print("\ntop-8 champion days: which sleeves drive (|ret|>1% on that day)?")
for t in ch.abs().nlargest(8).index:
    row=[f"{k}:{P[k].get(t,np.nan)*100:+.2f}" for k in SLEEVES if abs(P[k].get(t,0) or 0)>0.01]
    print(f"  {t.date()} champ {ch.loc[t]*100:+.2f}% -> {row}")

# effective N: vt-normalized pairwise corr on common window
def vt10(r,target=0.10,minobs=60,cap=8.0):
    vol=r.rolling(minobs,min_periods=minobs).std().shift(1)*np.sqrt(252)
    return (r*(target/vol.replace(0,np.nan)).clip(upper=cap)).fillna(0.0)
V=pd.DataFrame({k:vt10(P[k]) for k in SLEEVES})
V=V[(V.index>=ch.index[0])&(V.index<=ch.index[-1])]
C=V.corr()
mask=np.triu(np.ones_like(C,dtype=bool),1)
rhos=C.values[mask]
print(f"\nvt-normalized pairwise sleeve corr: mean={rhos.mean():+.3f} median={np.median(rhos):+.3f} max={rhos.max():+.3f}")
br=C.loc[[k for k in SLEEVES if k.startswith('brwt')],[k for k in SLEEVES if k.startswith('brwt')]].values
brm=br[np.triu(np.ones_like(br,dtype=bool),1)]
print(f"brwt-family (4 slots, same Brent-WTI pair) internal corr: mean={brm.mean():.3f}")
c5=C.loc['C5ng','C5ngsum']; print(f"C5ng vs C5ngsum corr: {c5:.3f}")
n=len(SLEEVES); eff=n/(1+(n-1)*rhos.mean())
print(f"effective independent engines N* = n/(1+(n-1)rho) = {eff:.1f} (of 12 advertised; brwt counted as 4)")
# dedup brwt->1: recompute with 9 distinct families
Vd=V.copy(); Vd['brwt']=V[[k for k in V if k.startswith('brwt')]].mean(axis=1)
Vd=Vd[[k for k in Vd if not k.startswith('brwt') or k=='brwt']]
Cd=Vd.corr(); rhod=Cd.values[np.triu(np.ones_like(Cd,dtype=bool),1)]
effd=9/(1+8*rhod.mean())
print(f"9-family version: mean corr={rhod.mean():+.3f}, N*={effd:.1f}")
# share of vt portfolio in commodity family
fam = V.assign(com=V[['brwt15','brwt10','brwt7','brwt5','C5ng','C5ngsum']].abs().sum(axis=1)/V.abs().sum(axis=1))
print(f"mean |weight| share of 6 commodity slots (4brwt+2ng): {fam['com'].mean()*100:.1f}%")
