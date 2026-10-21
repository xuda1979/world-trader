"""A5 idea 6: contango carry + VIX-level cap. Long SPY only when term
structure in contango (hysteresis) AND VIX level below threshold
(enter <lo, exit >hi hysteresis). Targets grinding bears 2018/2022."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D
from a5_idea1_contango import run as run_idea1  # for reference

vd = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv', parse_dates=['DATE']).set_index('DATE')['vix']
v3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv', parse_dates=['DATE']).set_index('DATE')['vix3m']
ts = pd.concat([vd,v3],axis=1).dropna()
spy = D.closes()["SPY"]; r1 = spy.pct_change(); r1.index = r1.index.tz_localize(None)

def run(th=1.0, hyst=0.10, vlo=22, vhi=28, vt=0.10, lev_cap=2.0):
    ratio = ts["vix"]/ts["vix3m"]; v = ts["vix"]
    st=0.0; out=[]
    cont=0.0; lvl=0.0
    for i in range(len(ts)):
        rr = ratio.iloc[i]; vv = v.iloc[i]
        if rr < th: cont=1.0
        elif rr > th+hyst: cont=0.0
        if vv < vlo: lvl=1.0
        elif vv > vhi: lvl=0.0
        out.append(cont*lvl)
    pos = pd.Series(out, index=ts.index).shift(1).reindex(r1.index).fillna(0.0)
    gross = pos*r1.reindex(pos.index).fillna(0.0)
    to = pos.diff().abs().fillna(pos.abs())
    net = gross - to*D.COST/1e4
    sv = net.rolling(60).std()
    sc = (vt/np.sqrt(252)/sv).clip(0,lev_cap).shift(1).fillna(0.0)
    pos2 = pos*sc
    net = net*sc - pos2.diff().abs().fillna(pos2.abs())*D.COST/1e4
    return net.dropna(), pos2.dropna()

if __name__ == "__main__":
    print("=== idea6 scan: contango x VIX-level gate ===")
    for vlo,vhi in [(18,24),(22,28),(25,32),(28,100)]:
        for th,hy in [(1.0,0.10),(1.02,0.05)]:
            net,pos = run(th,hy,vlo,vhi)
            s = stats(net); h1,h2 = halves(net)
            sp = scramble_pval_sig(pos, r1, n=200)
            ok = s['sr']>=0.6 and h1>=0.3 and h2>=0.3 and s['neg_yr']<=2 and s['worst']>-5.0 and sp<=0.05
            print(f"vlo={vlo} vhi={vhi} th={th} hy={hy}: SR={s['sr']:.2f} H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% scram={sp:.3f} ALL={'PASS' if ok else 'FAIL'}")
            print("   negyrs:", {k:vv for k,vv in s['yearly'].items() if vv<0})
