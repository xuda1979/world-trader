"""A1 r2 Mission 1: BREADTH CTA — 9-leg macro trend book (T+1, 6bps, expanding vol-target).
Legs: xau, wti, brent, copper(monthly ff), natgas, dxy, us10y synth TR (dur 7.5), us30y synth TR (dur 15), slv.
Signal: long if 252d return>0 AND 63d return>0 (confirm); variant long/flat or long/short.
Vol target 10% ann per leg, expanding (min 60d), weight cap 1.5. Costs 6bps x one-side turnover.
spx excluded: series starts 2016 only (insufficient history) — honest deviation from charter list.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import fred, COST

RNG = np.random.default_rng(7)

def tr_series(leg):
    if leg == "us10y": y = fred("us10y"); D = 7.5
    elif leg == "us30y": y = fred("us30y"); D = 15.0
    else:
        s = fred(leg).astype(float)
        # drop obvious gaps: reindex to business days ffill
        bidx = pd.bdate_range(s.index[0], s.index[-1])
        return s.reindex(bidx).ffill()
    y = y.astype(float)
    bidx = pd.bdate_range(y.index[0], y.index[-1])
    y = y.reindex(bidx).ffill()
    dy = y.diff()
    tr = y.shift(1)/100.0/252.0 - D*dy/100.0   # daily total return
    tr.iloc[0] = 0.0
    return (1+tr).cumprod()

LEGS = ["xau","wti","brent","copper_monthly","natgas","dxy","us10y","us30y","slv"]
PX = pd.DataFrame({l: tr_series(l) for l in LEGS}).sort_index()
RETS = PX.pct_change()

def leg_weights(L=252, C=63, variant="flat", vt=0.10, cap=1.5, minobs=60):
    W = {}
    for l in LEGS:
        p = PX[l]
        r = RETS[l]
        trend = p/p.shift(L)-1
        conf  = p/p.shift(C)-1
        sig = pd.Series(np.nan, index=p.index)
        sig[(trend>0)&(conf>0)] = 1.0
        if variant=="short":
            sig[(trend<0)&(conf<0)] = -1.0
        sig = sig.fillna(0.0)
        vol = r.expanding(min_periods=minobs).std()*np.sqrt(252)
        w = sig * (vt/vol).clip(upper=cap)
        w = w.replace([np.inf,-np.inf],0.0).fillna(0.0)
        W[l] = w
    return pd.DataFrame(W)

def portfolio(W, start="2009-01-02"):
    w1 = W.shift(1)                    # T+1: weights decided at t applied to t+1 returns
    gross = (w1*RETS).sum(axis=1)
    to = (W.diff().abs().sum(axis=1)).fillna(0.0)
    net = gross - to*COST/1e4
    net = net[net.index >= start]
    return net

def stats(r):
    r = r.dropna(); mu, sd = r.mean(), r.std()
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(n=len(r), sr=mu/sd*np.sqrt(252) if sd>0 else 0,
                h1=r[r.index<=r.index[len(r)//2]].mean()/r[r.index<=r.index[len(r)//2]].std()*np.sqrt(252),
                h2=r[r.index>r.index[len(r)//2]].mean()/r[r.index>r.index[len(r)//2]].std()*np.sqrt(252),
                neg=int((yr<0).sum()), worst=yr.min()*100, years=len(yr),
                ann=mu*252*100, vol=sd*np.sqrt(252)*100)

def scramble_pval(r, W, nperm=200):
    """shuffle weight rows vs return matrix; real SR vs scrambled distribution."""
    idx = r.index
    Rw = RETS.loc[idx][LEGS].values
    Wv = W.loc[idx][LEGS].values
    to = W.diff().abs().sum(axis=1).loc[idx].values*COST/1e4
    def sr_of(Wm):
        g = (Wm*Rw).sum(axis=1); return (g-to).mean()/max((g-to).std(),1e-12)*np.sqrt(252)
    real = sr_of(Wv)
    null = []
    for _ in range(nperm):
        P = RNG.permutation(Wv)
        null.append(sr_of(P))
    return real, (np.array(null) >= real).mean(), np.percentile(null, 95)

if __name__ == "__main__":
    print(f"panel {PX.index[0].date()}..{PX.index[-1].date()}")
    for variant in ["flat","short"]:
        print(f"\n===== variant {variant} =====")
        rows = {}
        for L in [189,252,315]:
            for C in [42,63,84]:
                W = leg_weights(L,C,variant)
                r = portfolio(W)
                s = stats(r)
                rows[(L,C)] = s["sr"]
                print(f"L={L} C={C}: SR={s['sr']:.2f} H1={s['h1']:.2f} H2={s['h2']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% negyr={s['neg']}/{s['years']} worst={s['worst']:.1f}% to/day={W.diff().abs().sum(axis=1).mean():.3f}")
        peak = max(rows.values())
        print(f"peak SR {peak:.2f}; grid ratio to peak: " + " ".join(f"{v/peak:.2f}" for v in rows.values()))
