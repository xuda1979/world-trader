"""A5 idea 7: blend = 50/50 contango carry (idea1 best plateau) + LIB:Multi_Strategy_EW.
Contango sleeve: long SPY when vix/vix3m < 1.0 with 0.10 hysteresis exit,
T+1, 6bps/side, vol-target 10% trailing. Blend re-vol-targeted to 10%."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

vd = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv', parse_dates=['DATE']).set_index('DATE')['vix']
v3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv', parse_dates=['DATE']).set_index('DATE')['vix3m']
ts = pd.concat([vd,v3],axis=1).dropna()
spy = D.closes()["SPY"]; r1 = spy.pct_change(); r1.index = r1.index.tz_localize(None)

def contango_pos(th=1.0, hyst=0.10):
    ratio = ts["vix"]/ts["vix3m"]
    st=0.0; out=[]
    for v in ratio.values:
        if v < th: st=1.0
        elif v > th+hyst: st=0.0
        out.append(st)
    return pd.Series(out, index=ratio.index).shift(1)

def contango_sleeve(th=1.0, hyst=0.10, vt=0.10):
    pos = contango_pos(th,hyst).reindex(r1.index).fillna(0.0)
    gross = pos*r1.reindex(pos.index).fillna(0.0)
    to = pos.diff().abs().fillna(pos.abs())
    net = gross - to*D.COST/1e4
    sv = net.rolling(60).std()
    sc = (vt/np.sqrt(252)/sv).clip(0,2).shift(1).fillna(0.0)
    pos2 = pos*sc
    net = net*sc - pos2.diff().abs().fillna(pos2.abs())*D.COST/1e4
    return net.dropna(), pos2.dropna()

def blend(w=0.5, th=1.0, hyst=0.10, vt=0.10):
    c, cpos = contango_sleeve(th,hyst)
    m = load_lib("Multi_Strategy_EW")
    idx = c.index.intersection(m.index)
    b = w*c.reindex(idx).fillna(0.0) + (1-w)*m.reindex(idx).fillna(0.0)
    sv = b.rolling(60).std()
    sc = (vt/np.sqrt(252)/sv).clip(0,2).shift(1).fillna(0.0)
    b = b*sc
    return b.dropna(), (cpos*w*sc).dropna()

if __name__ == "__main__":
    print("=== idea7 blend scan ===")
    for w in [0.3,0.4,0.5,0.6]:
        for th,hy in [(1.0,0.10),(1.02,0.05)]:
            b, cpos = blend(w,th,hy)
            s = stats(b); h1,h2 = halves(b)
            sp = scramble_pval_sig(cpos, r1, n=200)  # scramble the active signal leg
            ok = s['sr']>=0.6 and h1>=0.3 and h2>=0.3 and s['neg_yr']<=2 and s['worst']>-5.0 and sp<=0.05
            print(f"w={w} th={th} hy={hy}: SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% scram={sp:.3f} ALL={'PASS' if ok else 'FAIL'}")
            print("   negyrs:", {k:vv for k,vv in s['yearly'].items() if vv<0})
    b,_ = blend(0.5,1.0,0.10)
    print("corr to lib:", corr_to_lib(b, names=("L_S_130_30","CTA_15vol","FactorMom_1963","Merger_Arb_PEAD","Multi_Strategy_EW")))
    cc,_ = contango_sleeve()
    j = pd.concat([cc, load_lib("Multi_Strategy_EW")],axis=1).dropna()
    print("contango-vs-MS_EW corr:", round(float(j.corr().iloc[0,1]),2))
