"""E2 Ideas 4+5: turn-of-quarter flows and pre/post-holiday drift. SPY + EW panel."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import e2_lib as L, numpy as np, pandas as pd

def toq_masks(idx):
    s = idx.to_series(); m = s.dt.month
    nxt = s.shift(-1).dt.month; prv = s.shift(1).dt.month
    prv2 = s.shift(2).dt.month; prv3 = s.shift(3).dt.month
    l1 = (~nxt.eq(m)) & m.isin([3,6,9,12])
    l2 = l1 | (l1.shift(1,fill_value=False))
    l3 = l2 | (l1.shift(2,fill_value=False))
    f1 = m.isin([4,7,10,1]) & prv.isin([3,6,9,12])
    f2 = f1 | (m.isin([4,7,10,1]) & prv2.isin([3,6,9,12]))
    f3 = f2 | (m.isin([4,7,10,1]) & prv3.isin([3,6,9,12]))
    return l1,l2,l3,f1,f2,f3

def gap_masks(idx):
    s = idx.to_series(); g = s.diff().dt.days
    pre = (g>1)&(g<6)
    post = ((g.shift(-1)>1)&(g.shift(-1)<6)).fillna(False)
    return pre, post

ret = L.spy_ret()
print("=== IDEA 4: TOQ SPY long/cash ===")
rows=[]
for nl,nf in [(1,0),(1,1),(1,2),(1,3),(2,2),(2,3),(3,3),(0,3)]:
    l1,l2,l3,f1,f2,f3 = toq_masks(ret.index)
    lm = {0:pd.Series(False,index=ret.index),1:l1,2:l2,3:l3}[nl]
    fm = {0:pd.Series(False,index=ret.index),1:f1,2:f2,3:f3}[nf]
    msk = lm|fm
    net = L.book_net(msk.astype(float), ret)
    s = L.full_stats(net)
    rows.append((nl,nf,round(s['sr'],2),round(ret[msk].mean()*1e4,1),round(ret[~msk].mean()*1e4,1),s['negy']))
print(pd.DataFrame(rows,columns=['nl','nf','sr','in_bp','out_bp','negy']).to_string())

print("\npanel (EW 298) TOQ 2006+:")
px = L.D.closes(); panel_ret = px.pct_change().mean(axis=1).dropna()
l1,l2,l3,f1,f2,f3 = toq_masks(panel_ret.index)
for nl,nf in [(1,3),(2,3),(3,3),(0,3),(1,1)]:
    lm = {0:pd.Series(False,index=panel_ret.index),1:l1,2:l2,3:l3}[nl]
    fm = {0:pd.Series(False,index=panel_ret.index),1:f1,2:f2,3:f3}[nf]
    msk = lm|fm
    mi = panel_ret[msk].mean()*1e4; mo = panel_ret[~msk].mean()*1e4
    t = (mi-mo)/1e4/np.sqrt(panel_ret.var()/len(panel_ret))
    net = L.book_net(msk.astype(float), panel_ret)
    L.evaluate(net, f"panel_toq{nl}{nf}", start='2006-09-26', verbose=True)

print("\n=== IDEA 5: holidays ===")
pre, post = gap_masks(ret.index)
for lab, msk in [("pre",pre),("post",post),("pre|post",pre|post)]:
    m1 = ret[msk].mean()*1e4; m0 = ret[~msk].mean()*1e4
    t = (m1-m0)/1e4/np.sqrt(ret.var()/len(ret))
    print(f"SPY {lab}: in={m1:.1f}bp n={msk.sum()} out={m0:.1f}bp t={t:.2f}")
for lab, msk in [("pre",pre),("pre|post",pre|post)]:
    L.evaluate(L.book_net(msk.astype(float), ret), f"spy_{lab}")
print("panel pre/post 2006+:")
ppre, ppost = gap_masks(panel_ret.index)
for lab, msk in [("pre",ppre),("post",ppost),("pre|post",ppre|ppost)]:
    mi = panel_ret[msk].mean()*1e4; mo = panel_ret[~msk].mean()*1e4
    t = (mi-mo)/1e4/np.sqrt(panel_ret.var()/len(panel_ret))
    print(f"EW {lab}: in={mi:.1f}bp n={msk.sum()} out={mo:.1f}bp t={t:.2f}")
L.evaluate(L.book_net(ppre.astype(float), panel_ret), "panel_pre", start='2006-09-26')
