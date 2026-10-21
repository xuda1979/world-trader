# m5: independent 12-sleeve reconstruction + outlier-day attribution + cost model test
import pandas as pd, numpy as np
B="/Users/daxu/software/world-trader/campaign"
SLEEVES = {
 'brwt15': f"{B}/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 'brwt10': f"{B}/agents/COORD/sleeves/brwt10_2000.csv",
 'brwt7':  f"{B}/agents/COORD/sleeves/brwt7.csv",
 'brwt5':  f"{B}/agents/COORD/sleeves/brwt5.csv",
 'C5ng':   f"{B}/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 'C5ngsum':f"{B}/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 'A5r2':   f"{B}/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 'a6r7':   f"{B}/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 'QAxasts':f"{B}/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 'carryv2':f"{B}/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 'dualmom':f"{B}/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 'XGB1y':  f"{B}/results/sleeve_library/XGB1y_deploy.csv",
}
P={}
for k,p in SLEEVES.items():
    s=pd.read_csv(p,parse_dates=['date']).set_index('date')['ret']
    P[k]=pd.to_numeric(s,errors='coerce')
    print(f"{k:9s} n={P[k].notna().sum():5d}  {P[k].dropna().index[0].date()}..{P[k].dropna().index[-1].date()}")

ch=pd.read_csv(f"{B}/results/GOAL100_STRICTTRADE_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']

print("\n== 2020-09-01 sleeve attribution ==")
for k in SLEEVES:
    v=P[k].get(pd.Timestamp('2020-09-01'),np.nan)
    print(f"  {k:9s} {v*100:+8.2f}%")
print(f"  champion {ch.get(pd.Timestamp('2020-09-01'),np.nan)*100:+8.2f}%  -> 1/12 EW of sleeves would be {np.mean([P[k].get(pd.Timestamp('2020-09-01'),0) for k in SLEEVES])*100:+.2f}%")

# reconstruct vt10 EW + throttle, compare
def vt10(r, target=0.10, minobs=60, cap=8.0):
    vol=r.rolling(minobs,min_periods=minobs).std().shift(1)*np.sqrt(252)
    return (r*(target/vol.replace(0,np.nan)).clip(upper=cap)).fillna(0.0)
V=pd.DataFrame({k:vt10(P[k]) for k in SLEEVES})
core=V.mean(axis=1)
vol_g=core.rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
sc_g=(0.10/vol_g.replace(0,np.nan)).clip(upper=8.0)
g=(core*sc_g).fillna(0.0)
eq=(1+g).cumprod(); peak=eq.rolling(126,min_periods=1).max().shift(1)
tdd=eq/peak-1
thr=pd.Series(np.where(tdd>-0.05,1.0,0.5),index=g.index)
f=g*thr
j=pd.concat([f.rename('mine'),ch.rename('comm')],axis=1,sort=True)
j=j[j['mine'].notna()&j['comm'].notna()]
corr=j['mine'].corr(j['comm']); md=(j['mine']-j['comm']).abs().max()
print(f"\nmy simple 12-sleeve vt10+throttle rebuild vs committed: n={len(j)} corr={corr:.6f} maxdiff={md*100:.3f}pp")
print(f"mine ann={j['mine'].mean()*252*100:.1f}% SR={j['mine'].mean()/j['mine'].std()*np.sqrt(252):.2f} | comm ann={j['comm'].mean()*252*100:.1f}% SR={j['comm'].mean()/j['comm'].std()*np.sqrt(252):.2f}")
