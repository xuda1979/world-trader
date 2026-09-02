import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import build, vt, sn, POOL, ROOT

def loadraw(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)
rawl = {n: loadraw(p) for n,p in POOL.items()}

# --- A. clean identity rerun ---
r_no,_  = build(0.07,0.04,REBAL=False,KEEP=True)
r_reb,s = build(0.07,0.04,REBAL=True, KEEP=True)
Sd, gs = s['Sd'], s['gs']
reb = (Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0)).reindex(r_reb.index).fillna(0)
ident = (r_no - r_reb - reb*6e-4).abs().max()
m08 = (reb[reb.index>='2008-01-01']).mean()*6e-4*252*100
print(f"A. identity max|resid| = {ident:.3e}; mean drag 2008+ = {m08:.3f}%/yr; reb charged days {(reb>0).sum()}, total rows {len(reb)}")

# --- B. 2006 decomposition ---
r06 = r_reb[r_reb.index<'2007-01-01']
b06 = s['b'].reindex(r06.index)
reb06 = reb.reindex(r06.index).fillna(0)
print(f"\nB. 2006 stub: n={len(r06)} sum {r06.sum()*100:.3f}% | b!=0 days {(b06!=0).sum()} | reb-cost sum {reb06.sum()*6e-4*100:.3f}%")
print("   5 largest negative days:", [(str(d.date()), round(float(r06[d])*1e4,1)) for d in r06.abs().idxmax(0) and [r06.nsmallest(5).index[0], r06.nsmallest(5).index[1], r06.nsmallest(5).index[2], r06.nsmallest(5).index[3], r06.nsmallest(5).index[4]]])
gs06 = s['gs'].reindex(r06.index).fillna(0)
turnon = gs06[gs06>0]
print(f"   gs first nonzero: {turnon.index[0].date() if len(turnon) else None}; reb on that day {reb06[turnon.index[0]]*6e-4*1e4 if len(turnon) else 0:.1f}bp")

# --- C. sleeve coverage per FIX row ---
cnt = pd.Series(0, index=r_reb.index)
for n,r in rawl.items():
    cnt = cnt + pd.Series(1, index=r_reb.index).where(pd.Series(r.reindex(r_reb.index).notna().values, index=r_reb.index), 0)
print(f"\nC. rows with all 11 sleeves: {(cnt==11).sum()}/{len(cnt)}; full-11 ends {cnt[cnt==11].index[-1].date()}")
print(f"   last 30 days sleeve counts: {cnt.tail(30).groupby(cnt.tail(30)).agg(['first','last']).to_dict()}")
print(f"   extension 2026-08-03..27 counts: {cnt['2026-08-01':].to_dict()}")
lowc = cnt[cnt<11]
print(f"   rows with <11 sleeves: {len(lowc)} ({len(lowc)/len(cnt)*100:.1f}%), earliest {lowc.index[0].date()}")
print(f"   rows with exactly 1 sleeve: {(cnt==1).sum()}, dates: {[str(d.date()) for d in cnt[cnt==1].index][:25]}")

# --- D. composition of 75 in-window recovered days ---
l16 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
added = r_reb.index.difference(l16.index)
inw = added[(added>=pd.Timestamp('2008-03-31'))&(added<=pd.Timestamp('2026-07-31'))]
from dateutil.easter import easter
gfs = set((pd.Timestamp(easter(y)) - pd.Timedelta(days=2)).date() for y in range(2008,2027))
special = {pd.Timestamp('2012-10-29').date(),pd.Timestamp('2012-10-30').date(),pd.Timestamp('2018-12-05').date(),pd.Timestamp('2025-01-09').date()}
cat = {'good_friday':0,'nyse_mourning_sandy':0,'other':0}
for d in inw:
    if d.date() in gfs: cat['good_friday']+=1
    elif d.date() in special: cat['nyse_mourning_sandy']+=1
    else: cat['other']+=1
print(f"\nD. 75 in-window recovered: {cat}")
print(f"   P&L on recovered days (BAL): mean {r_reb.reindex(inw).mean()*1e4:.2f}bp vs all rows {r_reb.mean()*1e4:.2f}bp")

# --- E. gross reconciliation ---
_, sa = build(0.07,0.04); _, sb = build(0.091,0.03)
def gross(s):
    return (s['Sd'].abs().sum(axis=1)/11 * s['gs']).dropna()
gA, gG = gross(sa), gross(sb)
print(f"\nE. gross full-span means: SAFE {gA.mean():.3f}x  AGGR {gG.mean():.3f}x  avg {(gA.mean()+gG.mean())/2:.3f}x | BAL-series mean {((gA+gG)/2).mean():.3f}x")
for lbl, g in [('SAFE',gA),('AGGR',gG)]:
    g08=g[g.index>='2008-01-01']
    print(f"   {lbl} 2008+: mean {g08.mean():.3f}x p95 {g08.quantile(.95):.3f}x max {g08.max():.3f}x")
