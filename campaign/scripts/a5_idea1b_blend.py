"""A5 idea 1 fallback (charter): contango gate as OVERLAY on LIB:L_S_130_30.
Blend = gated L/S sleeve. T+1, apply own costs on gate switches (L/S sleeve
CSV already net of ITS costs; we add gate switching cost 6bps x turnover)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

vd = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv', parse_dates=['DATE']).set_index('DATE')['vix']
v3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv', parse_dates=['DATE']).set_index('DATE')['vix3m']
ts = pd.concat([vd,v3],axis=1).dropna()
lib = load_lib("L_S_130_30")

def gated(th=1.0, hyst=0.10, partial=0.5, vt=0.10):
    ratio = ts["vix"]/ts["vix3m"]
    st=0.0; out=[]
    for v in ratio.values:
        if v < th: st=1.0
        elif v > th+hyst: st=partial
        out.append(st)
    g = pd.Series(out, index=ratio.index)
    # align: gate known at t close applies to t+1 lib return
    g1 = g.shift(1).reindex(lib.index).fillna(0.0)
    raw = lib * g1   # gate multiplies NET lib returns (lib costs already in)
    to = g1.diff().abs().fillna(0.0)  # only switch cost extra
    net = raw - to*D.COST/1e4
    # vol target using trailing strategy vol only
    sv = net.rolling(60).std()
    sc = (vt/np.sqrt(252)/sv).clip(0,2).shift(1).fillna(0.0)
    net = net*sc - (g1*sc).diff().abs().fillna((g1*sc).abs())*D.COST/1e4
    return net.dropna(), g1

def report(name, net, g1):
    s = stats(net); h1,h2 = halves(net)
    sp = scramble_pval_base(net, n=200)  # block perm of net; sig-level too
    ok = s['sr']>=0.6 and h1>=0.3 and h2>=0.3 and s['neg_yr']<=2 and s['worst']>-5.0 and sp<=0.05
    print(f"{name}: SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% scram={sp:.3f} ALL={'PASS' if ok else 'FAIL'}")
    print("   negyrs:", {k:v for k,v in s['yearly'].items() if v<0})
    return ok, net

if __name__ == "__main__":
    for th,hy,part in [(1.0,0.10,0.5),(1.02,0.05,0.5),(1.0,0.05,0.5),(1.02,0.10,0.5),(1.0,0.10,0.0),(1.02,0.05,0.0)]:
        net, g1 = gated(th,hy,part)
        report(f"gatedLS th={th} hyst={hy} partial={part}", net, g1)
    # correlation of best blend vs lib components
    net,_ = gated(1.02,0.05,0.5)
    print("corr to lib:", corr_to_lib(net))
