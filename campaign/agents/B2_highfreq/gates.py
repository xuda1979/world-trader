"""Full gate evaluation for a sleeve return series (net, daily). Applies trailing vol target too."""
import numpy as np, pandas as pd
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')

COST=6.0/1e4

def vol_target(r_gross_or_net, vt_ann=0.10, min_days=60):
    """Apply trailing vol target using ONLY trailing data (expanding window, min 60d).
    Returns scaled daily returns + scale series."""
    # expanding window realized vol
    rv = r_gross_or_net.rolling(min_days, min_periods=min_days).std()*np.sqrt(252)
    # vol forecast = expanding realized vol (use expanding = full history up to t)
    rcum = r_gross_or_net.expanding(min_days).std()*np.sqrt(252)
    scale = (vt_ann/rcum).clip(upper=3.0)
    scaled = r_gross_or_net*scale
    return scaled, scale

def full_stats(r):
    r=r.dropna()
    mu,sd=r.mean(),r.std(); sr=mu/sd*np.sqrt(252) if sd>0 else 0
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(ann=mu*252*100, vol=sd*np.sqrt(252)*100, sr=sr, mdd=dd*100,
                negy=int((yr<0).sum()), worst=yr.min()*100, years=len(yr),
                yearly={int(k):round(v*100,1) for k,v in yr.items()})

def halves_sr(r):
    mid=r.index[len(r)//2]
    h1=full_stats(r[r.index<=mid])['sr']; h2=full_stats(r[r.index>mid])['sr']
    return h1,h2

def scramble_pval(r, n=200, seed=0):
    rng=np.random.default_rng(seed)
    r=r.dropna().values
    real = r.mean()/r.std()*np.sqrt(252)
    cnt=0
    for _ in range(n):
        rc=rng.permutation(r)
        if rc.std()>0:
            s=rc.mean()/rc.std()*np.sqrt(252)
            if s>=real: cnt+=1
    return cnt/n, real

def plateau(sr_grid, params, center_idx):
    """Check center is within 20% of max and neighbors not isolated. returns bool, peak_sr."""
    peak=max(sr_grid)
    ok = sr_grid[center_idx] >= 0.8*peak
    return ok, peak

def run_gates(net_scaled, meta, name, min_sr=0.6):
    s=full_stats(net_scaled)
    h1,h2=halves_sr(net_scaled)
    pv,real=scramble_pval(net_scaled)
    res={
      'name':name,'full_sr':round(s['sr'],2),'ann':round(s['ann'],1),'vol':round(s['vol'],1),
      'mdd':round(s['mdd'],1),'H1':round(h1,2),'H2':round(h2,2),
      'negy':s['negy'],'worst':round(s['worst'],2),'years':s['years'],
      'scramble_p':round(pv,4),'scramble_real_sr':round(real,2)}
    gates={
      'full_sr>=0.6': s['sr']>=min_sr,
      'H1>=0.3': h1>=0.3, 'H2>=0.3': h2>=0.3,
      'negy<=2': s['negy']<=2, 'worst>-5': s['worst']>-5,
      'scramble_p>0.05': pv>0.05}
    res['gates']=gates
    res['all_pass']=all(gates.values())
    return res

if __name__=='__main__':
    import sys, glob
    for p in sys.argv[1:]:
        df=pd.read_csv(p,index_col=0,parse_dates=True)
        r=df['ret']
        print(r.head())
        s=full_stats(r)
        print(s)
