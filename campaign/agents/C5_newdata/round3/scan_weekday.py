"""C5 Round-3 charter item 4+7: weekday t-scan across ALL daily spot/DEX series on disk.
Windows: all-year and report-season (Apr-Oct). Legs: Mon..Fri close->next, both directions.
Multiple-testing control (charter): report ONLY |t|>=3.5 as candidates; full gates after.
"""
import pandas as pd, numpy as np
NEW='/Users/daxu/software/world-trader/tools/quant/data/newdata/'
FRD='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred/'
NAMES_N=['DCOILWTICO','DCOILBRENTEU','DHOILNYH','DHHNGSP','DPROPANEMTXCF','DJFUELUSGULF',
         'DPUFUEUS2M','GASREGW','DTWEXBGS','DEXBZUS','DEXDNUS','DEXINUS','DEXJPUS','DEXKOUS',
         'DEXMXUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXSIUS','DEXUSAL','DEXUSEU','DEXUSUK']
NAMES_F=['xau','slv','spx','dow','copx','vix','cad','eur','gbp','jpy','cny']
def load(p):
    df=pd.read_csv(p,index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce'); s=s[s>0].dropna().sort_index()
    return s
rows=[]
for nm in NAMES_N:
    try: s=load(NEW+nm+'.csv')
    except Exception as e: print('skip',nm,e); continue
    lr=np.log(s).diff()
    for win,mset in [('all',set(range(1,13))),('summer',set(range(4,11)))]:
        for d in (1,-1):
            for dow in range(5):
                m=(lr.index.dayofweek==dow)&lr.index.month.isin(mset)
                pnl=(d*lr.shift(-1))[m].dropna()
                if len(pnl)<60: continue
                t=pnl.mean()/pnl.std()*np.sqrt(len(pnl))
                rows.append((nm,win,dow,d,round(t,2),len(pnl),round(pnl.mean()*1e4,1)))
for nm in NAMES_F:
    try: s=load(FRD+nm+'.csv')
    except Exception as e: print('skip',nm,e); continue
    lr=np.log(s).diff()
    for win,mset in [('all',set(range(1,13))),('summer',set(range(4,11)))]:
        for d in (1,-1):
            for dow in range(5):
                m=(lr.index.dayofweek==dow)&lr.index.month.isin(mset)
                pnl=(d*lr.shift(-1))[m].dropna()
                if len(pnl)<60: continue
                t=pnl.mean()/pnl.std()*np.sqrt(len(pnl))
                rows.append((nm,win,dow,d,round(t,2),len(pnl),round(pnl.mean()*1e4,1)))
R=pd.DataFrame(rows,columns=['series','win','dow','dir','t','n','mean_bp'])
R=R.sort_values('t',key=abs,ascending=False)
print('total tests:',len(R))
print('--- TOP 25 by |t| ---')
print(R.head(25).to_string(index=False))
print('--- SURVIVORS |t|>=3.5 ---')
print(R[R['t'].abs()>=3.5].to_string(index=False))
print('--- natgas reference rows ---')
print(R[R['series']=='DHHNGSP'].to_string(index=False))
print('--- WTI/Brent summer rows (charter item 4) ---')
print(R[(R['series'].isin(['DCOILWTICO','DCOILBRENTEU']))&(R['win']=='summer')].to_string(index=False))
