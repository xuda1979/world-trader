"""A1 r2 Mission 2: sector momentum on 298-name panel.
Sectors: average-linkage correlation clustering on 126d returns (K=12, min size 5).
Signal at month-end t: 126d momentum per member; sector mom = EW mean; hold top-3 sectors
as ETF-like books (EW all members), monthly rebalance, T+1, 6bps x turnover,
book vol-target 10% ann expanding (min 60d, shift 1).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import closes, COST
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

def build_sectors(K=12, minsz=5, cwin=126):
    px = closes()
    ret = px.pct_change()
    use = [c for c in px.columns if px[c].notna().sum() > 1500]
    ret = ret[use].loc["2010":"2023"]
    ok = ret.columns[ret.notna().sum() > int(0.8*len(ret))]
    ret = ret[ok].fillna(0.0)
    mkt = ret.mean(axis=1)
    ret = ret.sub(mkt, axis=0)  # residualize out market before clustering
    c = ret.corr().values
    d = np.sqrt(np.clip((1-c)/2.0, 0, 1))
    np.fill_diagonal(d, 0.0)
    Z = linkage(squareform(d, checks=False), method="average")
    lab = fcluster(Z, t=K, criterion="maxclust")
    from collections import Counter
    cnt = Counter(lab)
    keep = {k for k, v in cnt.items() if v >= minsz}
    sec = {col: int(l) for col, l in zip(ok, lab) if l in keep}
    return px, sec

def run(px, sec, L=126, topk=3, vt=0.10, vwin=126, minsz=5, start="2007-05-01"):
    ret = px.pct_change()
    sect_names = sorted(set(sec.values()))
    # member columns per sector
    members = {s: [c for c in px.columns if sec.get(c) == s] for s in sect_names}
    month_ends = px.resample("ME").last().index
    mes = [t for t in month_ends if t in px.index]
    dates = px.index
    W = pd.DataFrame(0.0, index=dates, columns=px.columns)
    pick_log = []
    for t in mes:
        i = dates.get_loc(t)
        if i < L + 5: continue
        mom = px.iloc[i] / px.iloc[i-L] - 1.0
        # sector momentum = EW of members' momentum with valid data
        smom = {}
        for s in sect_names:
            vals = [mom[c] for c in members[s] if pd.notna(mom[c])]
            if len(vals) >= minsz: smom[s] = np.mean(vals)
        if len(smom) < topk + 1: continue
        top = sorted(smom, key=smom.get, reverse=True)[:topk]
        pick_log.append((t.date(), [f"{s}:{smom[s]:+.1%}" for s in top]))
        cols = [c for s in top for c in members[s] if pd.notna(px[c].iloc[i])]
        if not cols: continue
        w = 1.0/len(cols)
        W.loc[t, cols] = w
    # daily: weights constant between month-ends (ffill), applied next day (T+1)
    Wd = W.replace(0.0, np.nan).ffill().fillna(0.0)
    gross = (Wd.shift(1)*ret).sum(axis=1)
    to = Wd.diff().abs().sum(axis=1).fillna(0.0)
    net = gross - to*COST/1e4
    rv = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    net = net*(vt/rv).clip(upper=3.0).fillna(1.0)
    return net[net.index >= start], Wd, pick_log

def stats(r):
    r = r.dropna(); mu, sd = r.mean(), r.std()
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    h1 = r[r.index<=r.index[len(r)//2]]; h2 = r[r.index>r.index[len(r)//2]]
    return dict(n=len(r), sr=mu/sd*np.sqrt(252) if sd>0 else 0,
                h1=h1.mean()/h1.std()*np.sqrt(252), h2=h2.mean()/h2.std()*np.sqrt(252),
                neg=int((yr<0).sum()), worst=yr.min()*100, years=len(yr),
                ann=mu*252*100, vol=sd*np.sqrt(252)*100,
                yr={int(k): round(v*100,1) for k,v in yr.items()})

if __name__ == "__main__":
    px, sec = build_sectors()
    from collections import Counter
    print("sector sizes:", sorted(Counter(sec.values()).values()), "n_names:", len(sec))
    for L in [63, 126, 189]:
        for topk in [2, 3, 4]:
            r, Wd, _ = run(px, sec, L=L, topk=topk)
            s = stats(r)
            print(f"L={L} top{topk}: SR={s['sr']:.2f} H1={s['h1']:.2f} H2={s['h2']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% negyr={s['neg']}/{s['years']} worst={s['worst']:.1f}%")
