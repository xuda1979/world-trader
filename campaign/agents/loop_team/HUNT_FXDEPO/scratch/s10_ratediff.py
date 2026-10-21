"""IDEA 3 final honest build: TRUE FX carry needs foreign DEPOSIT rates — absent on disk.
Only US DGS3MO daily exists. WITHOUT foreign rates, a long-high-carry book is NOT constructible
(PIT). The only PIT-usable foreign rates are MONTHLY 10y (2018+), already PROVEN DEAD by
FXMICRO G3 (SR 0.23) and CARRYFX §6 (tilt +0.004 SR). Attempt the one novel variant not yet
tried: 10y-diff CARRY SIGN on the DEX 10-cross panel with vol-inv weights, 2018+ window
(short) — expected fail; document as BLOCKED/dead instead of iterating.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

FR2=f'{ROOT}/tools/quant/hedge_fund_strats/data_fred'
def pit(s):
    """monthly value m usable from 1st bday of m+1, then ffill to bdays (CARRYFX §2 convention)."""
    m=s.resample('ME').last().dropna()
    sh=pd.Series(m.values,index=m.index+pd.offsets.BMonthEnd(1))
    return sh.reindex(pd.bdate_range(sh.index[0],s.index[-1])).ffill()

codes={'DEXJPUS':'jp10y','DEXNOUS':'no? none','DEXSDUS':'none','DEXSFUS':'ch10y','DEXDNUS':'none',
       'DEXUSEU':'ez10y','DEXUSUK':'gb10y'}
avail={'JPY':'jp10y','CHF':'ch10y','EUR':'ez10y','GBP':'gb10y'}
print('foreign 10y PIT coverage: 2018+ only. Books: JPY,CHF,EUR,GBP vs USD (DGS3MO for US?')
print('mixing 3mo US vs 10y foreign is NOT a carry measure — use same-maturity US 10y).')
us10=pd.to_numeric(pd.read_csv(f'{FR2}/us10y.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna()
px=pd.DataFrame({n:dex(n) for n in ['DEXJPUS','DEXSFUS','DEXUSEU','DEXUSUK']})
rloc=-px.pct_change()
tot=0; cnt=0
for c,code in avail.items():
    f=pit(pd.to_numeric(pd.read_csv(f'{FR2}/{code}.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna())
    diff=(f-us10.reindex(f.index)).dropna()          # foreign - US 10y
    carry=diff.diff(21)                              # carry-improvement proxy... actually LEVEL is carry
    sig=np.sign(carry.shift(1)).fillna(0.0)          # long ccy when its yield advantage RISING
    n=f'DEX{"JPUS" if c=="JPY" else "SFUS" if c=="CHF" else "USEU" if c=="EUR" else "USUK"}'
    r=net_of_book(pd.DataFrame({n:sig}),pd.DataFrame({n:rloc[n]}))
    tot=tot+r.fillna(0); cnt+=1
r=(tot/cnt).dropna()
r8=r[r.index>='2008-01-01']
st=full_stats(r8); h1,h2=halves_sr(r8)
print(f'10y-diff-rising carry sign EW (JPY,CHF,EUR,GBP): SR {st["sr"]:+.3f} H1 {h1:+.2f} H2 {h2:+.2f} ann {st["ann_geo"]*100:+.2f}% negy {st["negy"]} n={len(r8)} {st["first"]}..{st["last"]}')
# always-on carry (level sign)
tot=0
for c,code in avail.items():
    f=pit(pd.to_numeric(pd.read_csv(f'{FR2}/{code}.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna())
    diff=(f-us10.reindex(f.index)).dropna()
    sig=np.sign(diff.shift(1)).fillna(0.0)
    n=f'DEX{"JPUS" if c=="JPY" else "SFUS" if c=="CHF" else "USEU" if c=="EUR" else "USUK"}'
    r=net_of_book(pd.DataFrame({n:sig}),pd.DataFrame({n:rloc[n]}))
    tot=tot+r.fillna(0)
r=(tot/len(avail)).dropna(); r8=r[r.index>='2008-01-01']
st=full_stats(r8)
print(f'10y-diff LEVEL carry sign EW: SR {st["sr"]:+.3f} ann {st["ann_geo"]*100:+.2f}% negy {st["negy"]} n={len(r8)}')
