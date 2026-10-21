"""RECON 1: factor timing on daily FF factors (MKT/SMB/HML/MOM). All T+1, 6bps/side, borrow 0.5%/yr.
Engines: (a) TS-momentum sign (lookback lb), long/short and long/flat
         (b) Moreira-Muir inverse-vol scale on factor
         (c) VIX regime gate (long factor when VIX<its ma, flat else)
Evaluation window 2008+ (gate), vol-target trailing expanding 60d cap 3 applied AFTER costs.
"""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

ff=lib.load_ff3(); mom=lib.load_mom()
F={'MKT':ff['Mkt-RF'],'SMB':ff['SMB'],'HML':ff['HML'],'MOM':mom['MOM']}
vix=lib.load_vix()
champ=lib.load_champion()

def vt(r, vt0=0.10, min_days=60, cap=3.0):
    rv=r.expanding(min_days).std()*np.sqrt(252)
    s=(vt0/rv).clip(upper=cap).shift(1).fillna(1.0)
    return r*s

rows=[]
def ev(tag, pos, r):
    net,posa=lib.net_of(pos,r)
    net=vt(net)
    net=net[net.index>=pd.Timestamp('2008-01-01')]
    st=lib.full_stats(net)
    h1,h2=lib.halves_sr(net)
    okn,negyrs=lib.negyr_tol(net)
    fg=lib.flatten_gates(net)
    corr,ncorr=lib.corr_to(net,champ)
    rows.append(dict(tag=tag,sr=st['sr'],h1=h1,h2=h2,negy=st['negy'],worst=st['worst'],
                     ac1=fg['ac1'],uniq=fg['uniqR'],corr=corr,ann=st['ann_geo'],mdd=st['mdd'],n=st['n']))
    return net

W0=pd.Timestamp('2006-01-01')
for nm,s in F.items():
    s=s[s.index>=W0]
    # (a) TS momentum
    for lb in (21,63,126,252):
        sig=np.sign(s.rolling(lb).sum())
        ev(f'tsmom_{nm}_lb{lb}_LS',sig,s)
        lf=(s.rolling(lb).sum()>0).astype(float)
        ev(f'tsmom_{nm}_lb{lb}_LF',lf,s)
    # (b) Moreira-Muir inverse-vol (ex-ante, 63d)
    rv=s.rolling(63,min_periods=63).std()
    mm=(s/(rv**2))
    mm=mm/mm.rolling(252,min_periods=60).std()  # normalize to ~unit
    ev(f'moreiramuir_{nm}_63',mm.fillna(0),s)
    # (c) VIX gate
    v=vix.reindex(s.index).ffill()
    for ma in (126,252):
        g=(v<v.rolling(ma).mean()).astype(float)
        ev(f'vixgate_{nm}_ma{ma}_LF',g,s)

df=pd.DataFrame(rows).sort_values('sr',ascending=False)
pd.set_option('display.width',250)
print(df.head(25).to_string(index=False,
      formatters={'sr':'{:.2f}'.format,'h1':'{:.2f}'.format,'h2':'{:.2f}'.format,'worst':'{:.1%}'.format,
                  'ac1':'{:.2f}'.format,'uniq':'{:.2f}'.format,'corr':'{:+.3f}'.format,'ann':'{:.1%}'.format,'mdd':'{:.1%}'.format}))
df.to_csv('recon1_results.csv',index=False)
print('...total cells:',len(df))
