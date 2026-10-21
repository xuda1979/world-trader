"""FAMILY 3: CREDIT momentum on REAL HYG/LQD prices (NOT paper-synth). Signal: HYG/LQD ratio mom,
baa-aaa z/mom as timing signal on HYG vs LQD. T10YIE as sector/inflation signal on XLE."""
import sys; sys.path.insert(0,'.')
from lib import *
blend=load_blend()
H=load_csv(f'{ROOT}/tools/quant/data/twelvedata/HYG.csv'); L=load_csv(f'{ROOT}/tools/quant/data/twelvedata/LQD.csv')
IEF=load_csv(f'{ROOT}/tools/quant/data/twelvedata/IEF.csv'); TLT=load_csv(f'{ROOT}/tools/quant/data/twelvedata/TLT.csv')
XLE=load_csv(f'{ROOT}/tools/quant/data/twelvedata/XLE.csv')
R=pd.DataFrame({'H':H.pct_change(),'L':L.pct_change(),'I':IEF.pct_change(),'T':TLT.pct_change(),'E':XLE.pct_change()}).loc['2007-06':]
baa,aaa=fred('baa'),fred('aaa'); oas=(baa-aaa)
rows=[]
books={'H-L':R.H-R.L,'H-I':R.H-R.I,'H-T':R.H-R.T,'L-T':R.L-R.T,'H':R.H,'L':R.L}
for nm,br in books.items():
    br08=br.dropna(); br08=br08[br08.index>='2008-01-01']
    if len(br08)<3000: continue
    ratio=(H/L if '-' in nm else H if nm=='H' else L).reindex(br.index).ffill()
    for lb in [10,21,42,63,126,252]:
        for mode in ['mom','rev']:
            sig=np.sign(ratio-ratio.shift(lb)); pos=sig if mode=='mom' else -sig
            r,_=net_of(pos,br)
            r2=r[r.index>='2008-01-01']
            if len(r2)<2500: continue
            st=full_stats(r2)
            j=pd.concat([r2.rename('s'),blend.rename('c')],axis=1,join='inner').dropna()
            rows.append(dict(book=nm,src='ratio',mode=mode,lb=lb,sr=st['sr'],ann=st['ann_geo'],mdd=st['mdd'],
                             negy=st['negy'],worst=st['worst'],corr=j.s.corr(j.c)))
# OAS signal (baa-aaa) timing on real books: pos = -sign(oas - oas.shift(lb)) (tightening -> risk-on long H)
common=R.H.dropna().index
oc=oas.reindex(common).ffill()
for nm,br in books.items():
    br=br.reindex(common)
    br=br.dropna()
    if len(br)<3000: continue
    for lb in [10,21,42,63,126,252]:
        for mode in ['mom','rev']:
            sig=np.sign(oc-oc.shift(lb)); pos=-sig if mode=='mom' else sig
            r,_=net_of(pos,br)
            r2=r[r.index>='2008-01-01']
            if len(r2)<2500: continue
            st=full_stats(r2)
            j=pd.concat([r2.rename('s'),blend.rename('c')],axis=1,join='inner').dropna()
            rows.append(dict(book=nm,src='baaaaaa',mode=mode,lb=lb,sr=st['sr'],ann=st['ann_geo'],mdd=st['mdd'],
                             negy=st['negy'],worst=st['worst'],corr=j.s.corr(j.c)))
# T10YIE signal on XLE
be=fred('T10YIE').reindex(R.E.dropna().index).ffill()
for lb in [21,42,63,126,252]:
    for mode in ['mom','rev']:
        sig=np.sign(be-be.shift(lb)); pos=sig if mode=='mom' else -sig
        r,_=net_of(pos,R.E)
        r2=r[r.index>='2008-01-01']
        st=full_stats(r2)
        j=pd.concat([r2.rename('s'),blend.rename('c')],axis=1,join='inner').dropna()
        rows.append(dict(book='XLE',src='T10YIE',mode=mode,lb=lb,sr=st['sr'],ann=st['ann_geo'],mdd=st['mdd'],
                         negy=st['negy'],worst=st['worst'],corr=j.s.corr(j.c)))
res=pd.DataFrame(rows).sort_values('sr',ascending=False)
res.to_csv('s12_credit_results.csv',index=False)
print(res.head(40).to_string())
print('total',len(res))
