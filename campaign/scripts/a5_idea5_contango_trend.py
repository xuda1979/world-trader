"""A5 idea 5: contango carry AND price-trend filter. Long SPY when
(vix<vix3m+hyst hysteresis) AND SPY>200d MA. T+1, 6bps, vol-tgt 10%."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

vd = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv', parse_dates=['DATE']).set_index('DATE')['vix']
v3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv', parse_dates=['DATE']).set_index('DATE')['vix3m']
ts = pd.concat([vd,v3],axis=1).dropna()
spy = D.closes()["SPY"]; r1 = spy.pct_change(); r1.index = r1.index.tz_localize(None)

def run(th=1.0, hyst=0.10, mawin=200, vt=0.10):
    ratio = ts["vix"]/ts["vix3m"]
    st=0.0; out=[]
    for v in ratio.values:
        if v < th: st=1.0
        elif v > th+hyst: st=0.0
        out.append(st)
    gate_v = pd.Series(out, index=ratio.index)
    ma = spy.rolling(mawin).mean()
    trend = (spy > ma).astype(float)
    trend.index = trend.index.tz_localize(None)
    trend = trend.reindex(gate_v.index).ffill().fillna(0.0)
    pos = (gate_v*trend).shift(1)
    pos = pos.reindex(r1.index).fillna(0.0)
    gross = pos*r1.reindex(pos.index).fillna(0.0)
    to = pos.diff().abs().fillna(pos.abs())
    net = gross - to*D.COST/1e4
    sv = net.rolling(60).std()
    sc = (vt/np.sqrt(252)/sv).clip(0,2).shift(1).fillna(0.0)
    pos2 = pos*sc
    net = net*sc - pos2.diff().abs().fillna(pos2.abs())*D.COST/1e4
    return net.dropna(), pos2.dropna()

def gate_full(name, net, pos):
    s = stats(net); h1,h2 = halves(net)
    sp = scramble_pval_sig(pos, r1, n=200)
    ok_a, ok_c = s['sr']>=0.6, (h1>=0.3 and h2>=0.3)
    ok_d = s['neg_yr']<=2 and s['worst']>-5.0
    ok_e = sp<=0.05
    ok = ok_a and ok_c and ok_d and ok_e
    print(f"{name}: SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% scram={sp:.3f} gates[a={ok_a},c={ok_c},d={ok_d},e={ok_e}] ALL={'PASS' if ok else 'FAIL'}")
    print("   negyrs:", {k:v for k,v in s['yearly'].items() if v<0})
    return ok, net

if __name__ == "__main__":
    for th,hy in [(1.0,0.10),(1.02,0.05),(1.0,0.05),(1.02,0.10)]:
        for mawin in [100, 200]:
            net,pos = run(th,hy,mawin)
            gate_full(f"th={th} hyst={hy} ma={mawin}", net, pos)
