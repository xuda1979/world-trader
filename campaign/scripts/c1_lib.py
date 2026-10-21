"""C1 shared lib: Ken French daily portfolio loader + honest backtest + brief gates."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, '/Users/daxu/software/world-trader')
import os
KF = '/Users/daxu/software/world-trader/tools/quant/data/kenfrench'
COST = 6.0/1e4

def load_kf(path, section):
    lines = open(path).read().splitlines()
    idx = next(i for i,l in enumerate(lines) if section in l)
    hdr = lines[idx+1]
    cols = [c.strip() for c in hdr.split(',')][1:]
    rows=[]
    for l in lines[idx+2:]:
        p=[x.strip() for x in l.split(',')]
        if len(p)<len(cols)+1 or not (len(p[0])==8 and p[0].isdigit()): break
        rows.append([float(x) for x in p[:len(cols)+1]])
    df = pd.DataFrame(rows, columns=['date']+cols).set_index('date')
    df.index = pd.to_datetime(df.index, format='%Y%m%d')
    return df.replace(-99.99, np.nan).replace(-999.0, np.nan)/100.0

def kf48(section='Average Value Weighted Returns -- Daily'):
    return load_kf(f'{KF}/48_Industry_Portfolios_Daily.csv', section)

def kf49(section='Average Value Weighted Returns -- Daily'):
    return load_kf(f'{KF}/49_Industry_Portfolios_Daily.csv', section)

def bt(pos, rets, cost=COST):
    """pos: weights decided using data <= t. Earns ret t+1 (T+1). Cost 6bps x one-side turnover."""
    pl = pos.shift(1)
    gross = (pl*rets).sum(axis=1)
    to = (pl - pos.shift(2)).abs().sum(axis=1)   # one-side notional traded per $nav
    net = gross - to*cost
    return net, gross, to

def vt(net, vt_ann=0.10, min_days=60):
    """Trailing expanding-window vol target, scale clip 3.0 (gate g)."""
    rc = net.expanding(min_days).std()*np.sqrt(252)
    scale = (vt_ann/rc).clip(upper=3.0).fillna(0.0)
    return net*scale, scale

def stats(r):
    r = r.dropna()
    mu,sd = r.mean(), r.std()
    sr = mu/sd*np.sqrt(252) if sd>0 else 0.0
    eq = (1+r).cumprod(); dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(ann=mu*252*100, vol=sd*np.sqrt(252)*100, sr=sr, mdd=dd*100,
                negy=int((yr<0).sum()), worst=yr.min()*100, years=len(yr))

def scramble_pval(r, n=200, seed=0):
    rng = np.random.default_rng(seed)
    r = r.dropna().values
    real = r.mean()/r.std()*np.sqrt(252)
    cnt = sum(1 for _ in range(n)
              if (lambda rc: rc.mean()/rc.std()*np.sqrt(252))(rng.permutation(r)) >= real)
    return cnt/n

def blend():
    df = pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',
                     index_col=0, parse_dates=True)
    return df['ret']

def corr_blend(r):
    b = blend()
    df = pd.concat([r.rename('s'), b.rename('b')], axis=1).dropna()
    return df['s'].corr(df['b'])

def gates(net, min_sr=1.0):
    s = stats(net)
    idx = net.dropna().index
    mid = idx[len(idx)//2]
    h1 = stats(net[net.index<=mid])['sr']; h2 = stats(net[net.index>mid])['sr']
    pv = scramble_pval(net)
    cb = corr_blend(net)
    r_ = net.dropna()
    yr = r_.groupby(r_.index.year).apply(lambda x:(1+x).prod()-1)
    g = {
      'full_sr>=1.0': s['sr']>=min_sr,
      'H1>=0.5': h1>=0.5, 'H2>=0.5': h2>=0.5,
      'negy<=2': s['negy']<=2, 'worst>-5pct': s['worst']>-5.0,
      'scramble_p>0.05': pv>0.05,
      '|corr|<0.15': abs(cb)<0.15}
    return dict(stats=s, H1=h1, H2=h2, scramble_p=pv, corr_blend=cb,
                worst=yr.min()*100, gates=g, all_pass=all(g.values()))

def save(ret, name, meta):
    d = f'/Users/daxu/software/world-trader/campaign/agents/C1_kfindustry/sleeves'
    os.makedirs(d, exist_ok=True)
    r = ret.replace([np.inf,-np.inf], np.nan).fillna(0.0)
    r = r[~r.index.duplicated(keep='last')].sort_index()
    pd.DataFrame({'ret': r.values}, index=r.index).rename_axis('date').to_csv(f'{d}/{name}.csv')
    open(f'{d}/{name}.csv.meta','w').write(meta)
    return f'{d}/{name}.csv'
