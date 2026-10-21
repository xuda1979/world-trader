"""E4_globalidx ROUND 1 scan repro. All variants; none passed gates (see FINDINGS.md).
Run: python3 scan_round1.py"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/E4_globalidx')
import E4_lib as L
import pandas as pd, numpy as np

def weekly_pos(sig, idx):
    iso = idx.isocalendar(); wkkey=(iso.year*100+iso.week).values
    dfw = pd.DataFrame({'sig':sig,'wk':wkkey},index=idx)
    last = dfw.groupby('wk').tail(1)
    pos = pd.Series(np.nan,index=idx); pos.loc[last.index]=last['sig']
    return pos.shift(1).ffill()

def evalnet(net, tag):
    st=L.stats(net); h1,h2=L.halves(net); pv,_=L.scramble_pval(net)
    print(f"{tag}: SR={st['sr']:.2f} ann={st['ann']:.1f}% MDD={st['mdd']:.1f}% negy={st['negy']} H1={h1:.2f} H2={h2:.2f} scr_p={pv:.3f} corr={L.blend_corr(net):.3f}")

nk=L.nikkei(); ndq=L.nasdaq(); dj=L.djia(); dxy=L.dxy()
r=nk.pct_change()
# Idea1: Nikkei TSMOM weekly LS
for w in [21,63,126,252]:
    evalnet(weekly_pos(np.sign(nk/nk.shift(w)-1), nk.index)*r - weekly_pos(np.sign(nk/nk.shift(w)-1), nk.index).diff().abs().fillna(0)*L.COST/1e4, f"I1 NKY TSMOM w={w}")
# Idea2: Nikkei->SPY day-session
spy = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/SPY.csv', index_col=0, parse_dates=True)
df = pd.DataFrame({'day':spy['close']/spy['open']-1,'nk':nk.pct_change()}).dropna()
evalnet(np.sign(df['nk'])*df['day'] - 2*L.COST/1e4, "I2 NKY->SPY day-session")
# Idea3: NASDAQ vs DJIA rel-mom
rel = np.log(ndq)-np.log(dj)
ls = ndq.pct_change()-dj.pct_change()
for w in [21,63,126,252]:
    pos = weekly_pos(np.sign(rel-rel.shift(w)), rel.index)
    evalnet(pos*ls - 2*pos.diff().abs().fillna(0)*L.COST/1e4, f"I3 NDQ/DJI relmom w={w}")
# Idea4: NKY+NDQ vol-norm weekly TSMOM basket
px = pd.DataFrame({'nky':nk,'ndq':ndq}).dropna(); rets=px.pct_change()
vol = rets.rolling(63).std()*np.sqrt(252)
for w in [63,126,252]:
    sig=np.sign(px/px.shift(w)-1); wts=(sig/vol); wts=wts.div(wts.abs().sum(axis=1),axis=0)
    iso=px.index.isocalendar(); wkkey=(iso.year*100+iso.week).values
    dfw=pd.concat([wts,pd.Series(wkkey,index=px.index,name='wk')],axis=1)
    last=dfw.groupby('wk').tail(1)
    pos=pd.DataFrame(np.nan,index=px.index,columns=wts.columns)
    pos.loc[last.index,wts.columns]=last[wts.columns]; pos=pos.shift(1).ffill()
    evalnet((pos*rets).sum(axis=1)-pos.diff().abs().sum(axis=1).fillna(0)*L.COST/1e4, f"I4 basket2 w={w}")
# Idea5: Nikkei z-reversion both signs
lp=np.log(nk)
for w in [21,63,126,252]:
    z=(lp-lp.rolling(w).mean())/lp.rolling(w).std()
    for sgn,lab in [(1,'fade'),(-1,'trend')]:
        pos = weekly_pos(sgn*np.sign(-z), nk.index)
        evalnet(pos*r-pos.diff().abs().fillna(0)*L.COST/1e4, f"I5 z{w} {lab}")
# Extensions: DXY TSMOM, NASDAQ LF, NKY LF, baskets — see FINDINGS.md numbers
