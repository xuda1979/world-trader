"""GOAL100 coordinator blend: ingests all sleeves, gates, blends, reports frontier honestly.
Usage: python3 campaign/scripts/coord_goal100_blend.py [--vt 0.075] [--oos]
"""
import os, sys, glob, json
import numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader')
from campaign.harness.data import save_sleeve

ROOT='/Users/daxu/software/world-trader'
COST=6e-4

def load_sleeves(min_obs=1200, end='2026-08-29'):
    files = sorted(glob.glob(f'{ROOT}/campaign/results/sleeve_library/*.csv'))
    for a in glob.glob(f'{ROOT}/campaign/agents/*/sleeves/*.csv'):
        files.append(a)
    out={}
    for f in files:
        if f.endswith('.meta'): continue
        name=os.path.basename(f)[:-4]
        try:
            df=pd.read_csv(f, parse_dates=[0], index_col=0)
        except Exception:
            continue
        if 'ret' not in df.columns: continue
        r=df['ret'].replace([np.inf,-np.inf],np.nan).fillna(0)
        r=r[~r.index.duplicated(keep='last')].sort_index()
        r=r[r.index<=end]
        if len(r)>=min_obs:
            out[name]=r
    return out

def stats(r):
    r=r.dropna(); mu,sd=r.mean(),r.std()
    sr=mu/sd*np.sqrt(252) if sd>0 else 0
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(ann=mu*252, sr=sr, mdd=dd, negy=int((yr<0).sum()), worst=yr.min(),
                n=len(r), yearly={int(k):round(v*100,1) for k,v in yr.items()})

def vt_scale(r, vt=0.075, min_days=60, clip=3.0):
    rc=r.expanding(min_days).std()*np.sqrt(252)
    return (vt/rc).clip(upper=clip)

def build_blend(pool, names, vt=0.075, throttle_dd=-0.05, throttle_w=0.35):
    """EW of vol-normalized sleeves + optional trailing-126d drawdown throttle. Trailing-only."""
    df=pd.DataFrame({n:pool[n] for n in names}).dropna(how='all').fillna(0)
    # vol-normalize each with trailing expanding vol, target 10% each
    scales={}
    for n in names:
        rc=df[n].expanding(60).std()*np.sqrt(252)
        scales[n]=(0.10/rc).clip(upper=3.0)
    norm=pd.DataFrame({n:df[n]*scales[n] for n in names})
    blend=norm.mean(axis=1)
    # global vol target
    g=vt_scale(blend, vt=vt)
    out=blend*g
    # trailing 126d drawdown throttle on the blended curve (trailing only)
    eq=(1+out).cumprod()
    # trailing dd computed on past only (shift(1))
    peak=eq.cummax()
    dd=(eq/peak-1)
    sig=(dd.shift(1)>throttle_dd).astype(float)
    w=throttle_w+(1-throttle_w)*sig
    out=out*w
    return out.drop(out.index[:61])  # drop warmup

def main():
    pool=load_sleeves()
    print(f"loaded {len(pool)} sleeves")
    # quality screen: full SR>=0.6, then pick set
    qual={}
    for n,r in pool.items():
        s=stats(r[r.index>='2008-01-01'])
        if s['sr']>=0.6 and s['n']>=1500:
            qual[n]=s
    print(f"{len(qual)} pass SR>=0.6 screen (2008+)")
    for n,s in sorted(qual.items(), key=lambda kv:-kv[1]['sr']):
        print(f"  {n:40s} SR={s['sr']:.2f} ann={s['ann']*100:6.1f}% mdd={s['mdd']*100:6.1f}% negy={s['negy']}")
    # correlation matrix
    df=pd.DataFrame({n:pool[n] for n in qual}).dropna(how='all').fillna(0)
    corr=df.corr()
    # greedy decorrelated pick: sort by SR, add if avg |corr| to selected < 0.25
    order=sorted(qual, key=lambda n:-qual[n]['sr'])
    sel=[]
    for n in order:
        if not sel: sel.append(n); continue
        c=corr.loc[n, sel].abs().mean()
        if c<0.25: sel.append(n)
    print(f"\ngreedy decorrelated selection: {len(sel)} sleeves")
    # blend
    for vt in [0.07, 0.075, 0.08]:
        b=build_blend(pool, sel, vt=vt)
        st=stats(b[b.index>='2008-01-01'])
        oos=stats(b[b.index>='2017-01-01'])
        print(f"vt={vt}: FULL ann {st['ann']*100:.1f}% SR {st['sr']:.2f} mdd {st['mdd']*100:.1f}% negy {st['negy']} | OOS17+ ann {oos['ann']*100:.1f}% SR {oos['sr']:.2f} mdd {oos['mdd']*100:.1f}%")
    # save headline at vt 0.075
    b=build_blend(pool, sel, vt=0.075)
    st=stats(b[b.index>='2008-01-01'])
    save_sleeve(b, f'{ROOT}/campaign/results/GOAL100_blend_daily.csv',
                json.dumps({'sleeves':sel,'vt':0.075,'stats':{k:v for k,v in st.items() if k!='yearly'}}, indent=1))
    print("\nsaved GOAL100_blend_daily.csv with", len(sel), "sleeves")

if __name__=='__main__':
    main()
