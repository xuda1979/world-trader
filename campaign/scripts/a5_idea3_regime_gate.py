"""A5 idea 3: Long SPY gated by dollar trend (dxy below/above MA) + credit
regime (baa-aaa spread trend). Risk-on when dxy falling/below MA AND credit
spread falling/below MA. T+1, 6bps/side, expanding vol-target 10%.
hy_oas starts 2023 only -> use baa-aaa proxy (long history)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

spy = D.closes()["SPY"]
r1 = spy.pct_change(); r1.index = r1.index.tz_localize(None)
dxy = D.fred("dxy")
baa, aaa = D.fred("baa"), D.fred("aaa")
spr = (baa-aaa).dropna()
# daily-reindex: forward-fill macro series (monthly/daily mix) onto SPY calendar
cal = r1.index
dxy_d = dxy.reindex(cal).ffill()
spr_d = spr.reindex(cal).ffill()

def positions(dma=100, sma=100, dmode="below", smode="below", th=None):
    ok_d = dxy_d < dxy_d.rolling(dma).mean() if dmode=="below" else dxy_d.diff(sma) < 0
    ok_s = spr_d < spr_d.rolling(sma).mean() if smode=="below" else spr_d.diff(sma) < 0
    p = (ok_d & ok_s).astype(float)
    p.iloc[:max(dma,sma)+1] = 0.0
    return p

def net_of(pos):
    pos = pos.shift(1)
    gross = pos*r1.reindex(pos.index).fillna(0.0)
    to = pos.diff().abs().fillna(pos.abs())
    net = gross - to*D.COST/1e4
    sv = net.rolling(60).std()
    sc = (0.10/np.sqrt(252)/sv).clip(0,2).shift(1).fillna(0.0)
    pos2 = pos*sc
    net = net*sc - pos2.diff().abs().fillna(pos2.abs())*D.COST/1e4
    return net.dropna(), pos2.dropna()

def full(name, net, pos, quiet=False):
    s = stats(net); h1,h2 = halves(net)
    sp = scramble_pval_sig(pos, r1, n=200)
    ok = s['sr']>=0.6 and h1>=0.3 and h2>=0.3 and s['neg_yr']<=2 and s['worst']>-5.0 and sp<=0.05
    if not quiet:
        print(f"{name}: SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']} worst={s['worst']:.1f}% scram={sp:.3f} ALL={'PASS' if ok else 'FAIL'}")
        if ok or True: print("   negyrs:", {k:v for k,v in s['yearly'].items() if v<0})
    return ok, net, s

if __name__ == "__main__":
    print("=== idea3 scan: dxy gate x credit gate ===")
    for dmode in ["below","slope"]:
        for smode in ["below","slope"]:
            for dma, sma in [(50,50),(100,100),(200,100)]:
                p = positions(dma, sma, dmode, smode)
                net, pos2 = net_of(p)
                full(f"dxy:{dmode}{dma} spr:{smode}{sma}", net, pos2)
