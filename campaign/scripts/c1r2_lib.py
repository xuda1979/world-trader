"""C1 Round-2 helpers: windowing + gate runner on top of c1_lib."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import bt, vt, stats, scramble_pval, corr_blend, save, COST

W0, W1 = '2008-09-01', '2026-08-31'   # campaign window (Round-1 comparability)

def evaluate(net_full, name='', verbose=True):
    """net_full: daily net return series (T+1, costs). Slice window, vol-target, run ALL gates."""
    r = net_full.reindex(net_full.index.sort_values())
    rw = r.loc[W0:W1].dropna()
    if len(rw) < 1000:
        return None
    scaled, scale = vt(rw)
    s = stats(scaled)
    idx = scaled.index
    mid = idx[len(idx)//2]
    h1 = stats(scaled[scaled.index<=mid])['sr']; h2 = stats(scaled[scaled.index>mid])['sr']
    pv = scramble_pval(scaled)
    cb = corr_blend(scaled)
    yr = scaled.groupby(scaled.index.year).apply(lambda x:(1+x).prod()-1)
    g = {'full_sr>=1.0': s['sr']>=1.0, 'H1>=0.5': h1>=0.5, 'H2>=0.5': h2>=0.5,
         'negy<=2': s['negy']<=2, 'worst>-5pct': yr.min()>-0.05,
         'scramble_p>0.05': pv>0.05, '|corr|<0.15': abs(cb)<0.15}
    out = dict(name=name, sr=round(s['sr'],2), ann=round(s['ann'],1), vol=round(s['vol'],1),
               mdd=round(s['mdd'],1), H1=round(h1,2), H2=round(h2,2), negy=s['negy'],
               worst=round(yr.min()*100,1), p_scr=round(pv,3), corrB=round(cb,3),
               gates=g, all_pass=all(g.values()), scaled=scaled, scale=scale)
    if verbose:
        print(f"{name}: SR={out['sr']} ann={out['ann']}% vol={out['vol']}% mdd={out['mdd']}% "
              f"H1={out['H1']} H2={out['H2']} negy={out['negy']} worst={out['worst']}% "
              f"p={out['p_scr']} corrB={out['corrB']} PASS={out['all_pass']} "
              f"{[k for k,v in g.items() if not v]}")
    return out

def weekly_positions(target_daily):
    """Hold positions constant within week: rebalance signal computed on last trading day of week,
    executed next day (bt shifts by 1)."""
    w = target_daily.copy()
    iso = w.index.isocalendar()
    eow = pd.Series((iso.year*100 + iso.week).values, index=w.index)
    newweek = eow != eow.shift(1)
    held = w.where(newweek).ffill().fillna(0.0)
    return held
