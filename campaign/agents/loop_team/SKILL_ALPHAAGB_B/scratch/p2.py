"""P2: (a) small-cap EXT-panel reversal lb5; (b) big-panel xs momentum 63/126/252 skip1."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb
exec(open('p1.py').read().split("if __name__")[0])

def run_panel(px, r, lb, skip, vwin=21, tercile=3, min_names=100, start='2008-01-01', long_side='lo'):
    mom=px.shift(skip)/px.shift(skip+lb)-1.0
    vol=r.rolling(vwin).std()*np.sqrt(vwin)
    sig=mom/(vol+1e-9)
    n=r.notna().sum(axis=1); ok=n>=min_names
    rnk=sig.rank(axis=1,pct=True); k=1.0/tercile
    if long_side=='lo': lm=(rnk<=k)&sig.notna(); sm=(rnk>1-k)&sig.notna()
    else:               lm=(rnk>1-k)&sig.notna(); sm=(rnk<=k)&sig.notna()
    pos=lm.div(lm.sum(axis=1),axis=0).fillna(0)-sm.div(sm.sum(axis=1),axis=0).fillna(0)
    pos[~ok]=0.0
    pos=pos[r.index>=start]; rr=r[r.index>=start]
    g0=book_net(pos,rr)
    s=F.vol_target_scale(g0,vt=0.10,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos.mul(s,axis=0)
    return book_net(posv,rr), posv

champ=F.load_champion()
# (a) EXT small caps: keep names with >=4900 rows (full-window coverage)
pxe=panel_closes('twelve_extend')
cov=pxe.notna().sum()
keep=cov[cov>=4900].index
pxe=pxe[keep]; re_=pxe.sort_index().pct_change()
print('EXT names full-cov:',len(keep))
net,posv=run_panel(pxe,re_,5,0)
st=F.full_stats(net); h1,h2=F.halves_sr(net); fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
pl,_=libb.book_position_lag_p(posv,re_[re_.index>=st['first']],n=200)
print(f"EXTrev_lb5: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")
# (b) big xs momentum L/S (long winners short losers = momentum direction)
for lb,skip in [(63,1),(126,1),(252,1)]:
    net,posv=run_panel(rets,rets,lb,skip,long_side='hi')
    st=F.full_stats(net); h1,h2=F.halves_sr(net); fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
    pl,_=libb.book_position_lag_p(posv,rets[rets.index>=st['first']],n=200)
    print(f"mom_lb{lb}: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")
