# m11: is champion PnL folded across its 89 holes? test vs sibling files row-by-row
import pandas as pd, numpy as np, datetime as dt
B="/Users/daxu/software/world-trader"
ch=pd.read_csv(f"{B}/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']
ib=pd.read_csv(f"{B}/campaign/results/GOAL100_IBKR_STRICT_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']
ft=pd.read_csv(f"{B}/campaign/results/GOAL100_FINAL_TRUTH_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']
print(f"grids: champ={len(ch)} ibkr={len(ib)} ftruth={len(ft)}")
print(f"champ window {ch.index[0].date()}..{ch.index[-1].date()}")
inw=lambda s:{d for d in s.index if ch.index[0]<=d<=ch.index[-1]}
ci, cf = inw(ib), inw(ft)
cset=set(ch.index)
print(f"in window: ibkr={len(ci)} ftruth={len(cf)} champ={len(cset)}")
print(f"ibkr has, champ missing: {len(ci-cset)}; ftruth has, champ missing: {len(cf-cset)}")
print(f"champ has, ibkr missing: {len(cset-ci)}; champ has, ftruth missing: {len(cset-cf)}")

# where does the IBKR/FTRUTH grid come from? check a few of champ's missing days
for d in ["2020-08-31","2018-12-24","2018-12-26","2011-04-29","2017-11-10","2008-10-13"]:
    d=pd.Timestamp(d)
    print(f"\n{d.date()} ({d.day_name()}): champ={'YES' if d in cset else 'no'} ibkr={'YES' if d in ci else 'no'} ftruth={'YES' if d in cf else 'no'}")
    for nm,s in [('ibkr',ib),('ftruth',ft)]:
        if d in s.index: print(f"    {nm} ret that day: {s.loc[d]*100:+.3f}%")
    nxt = ch.index[ch.index.searchsorted(d)] if ch.index.searchsorted(d)<len(ch) else None
    if nxt is not None and nxt>d:
        print(f"    champ next row {nxt.date()}: {ch.loc[nxt]*100:+.3f}%")
        for nm,s in [('ibkr',ib),('ftruth',ft)]:
            if d in s.index and nxt in s.index:
                prod=(1+s.loc[d])*(1+s.loc[nxt])-1
                print(f"    {nm}: missing-day {s.loc[d]*100:+.3f}% x next {s.loc[nxt]*100:+.3f}% = folded {prod*100:+.3f}%  vs champ next {ch.loc[nxt]*100:+.3f}%")

# systematic test: for every champ-hole d with sibling rows, regression champ_next vs sib folded / not folded
import numpy as np
def test(sib, name):
    xs_fold, xs_not, ys = [],[],[]
    for d in sorted((inw(sib)-cset)):
        i = ch.index.searchsorted(d)
        if i>=len(ch.index): continue
        nxt = ch.index[i]
        if nxt<=d or nxt not in sib.index or d not in sib.index: continue
        ys.append(ch.loc[nxt]); xs_fold.append((1+sib.loc[d])*(1+sib.loc[nxt])-1); xs_not.append(sib.loc[nxt])
    ys=np.array(ys); xf=np.array(xs_fold); xn=np.array(xs_not)
    if len(ys)<5: print(f"{name}: insufficient overlap ({len(ys)})"); return
    print(f"\n{name}: n={len(ys)} champ-next vs sibling-NOT-folded: corr={np.corrcoef(ys,xn)[0,1]:.4f} maxabsdiff={np.abs(ys-xn).max()*1e4:.1f}bp meanabsdiff={np.abs(ys-xn).mean()*1e4:.1f}bp")
    print(f"{name}: n={len(ys)} champ-next vs sibling-FOLDED:    corr={np.corrcoef(ys,xf)[0,1]:.4f} maxabsdiff={np.abs(ys-xf).max()*1e4:.1f}bp meanabsdiff={np.abs(ys-xf).mean()*1e4:.1f}bp")
test(ib,'IBKR'); test(ft,'FTRUTH')
