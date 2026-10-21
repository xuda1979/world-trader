"""E4_globalidx shared lib: data loaders + gates for global index sleeves."""
import sys, os
sys.path.insert(0, '/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.harness.data import apply_cost, save_sleeve, COST
ND = '/Users/daxu/software/world-trader/tools/quant/data/newdata'
BFRED = '/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'

def _fred_csv(path, valcol=None):
    df = pd.read_csv(path)
    dcol = df.columns[0]
    df[dcol] = pd.to_datetime(df[dcol])
    df = df.set_index(dcol).sort_index()
    s = df[valcol if valcol else df.columns[-1]].astype(float)
    s = s[s > 0]  # drop missing markers '.' handled by astype->NaN, and nonpositive
    s = s.dropna()
    s.name = path.split('/')[-1].replace('.csv','')
    return s

def nikkei():
    return _fred_csv(f'{ND}/NIKKEI225.csv')

def nasdaq():
    return _fred_csv(f'{ND}/NASDAQCOM.csv')

def djia():
    return _fred_csv(f'{ND}/DJIA.csv')

def spx():  # SP500 from FRED (2016+) preferred if longer local spx.csv exists? use longest
    a = _fred_csv(f'{ND}/SP500.csv')
    return a

def spx_long():
    return _fred_csv(f'{BFRED}/spx.csv')

def vix():
    return _fred_csv(f'{BFRED}/VIXCLS.csv')

def dxy():
    return _fred_csv(f'{BFRED}/dxy.csv')

def _rets(px):
    return px.dropna().pct_change().dropna()

def _z(x, w):
    m = x.rolling(w).mean(); s = x.rolling(w).std()
    return (x - m) / s

def vol_scale_signal(sig_ret, vt_ann=0.10, min_days=60, clip=3.0):
    """scale = vt / expanding realized vol (trailing only); clip <= clip."""
    rcum = sig_ret.expanding(min_days).std() * np.sqrt(252)
    scale = (vt_ann / rcum).clip(upper=clip)
    return scale

def apply_vt(net, vt_ann=0.10, min_days=60, clip=3.0):
    scale = vol_scale_signal(net, vt_ann, min_days, clip)
    return net * scale

def stats(r):
    r = r.dropna()
    mu, sd = r.mean(), r.std()
    sr = mu/sd*np.sqrt(252) if sd>0 else 0
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    return dict(ann=mu*252*100, vol=sd*np.sqrt(252)*100, sr=sr, mdd=dd*100,
                negy=int((yr<0).sum()), worst=yr.min()*100, years=len(yr),
                yearly={int(k): round(v*100,1) for k,v in yr.items()})

def halves(r):
    r = r.dropna(); mid = r.index[len(r)//2]
    return stats(r[r.index<=mid])['sr'], stats(r[r.index>mid])['sr']

def scramble_pval(r, n=200, seed=0):
    rng = np.random.default_rng(seed)
    r = r.dropna().values
    real = r.mean()/r.std()*np.sqrt(252)
    cnt = 0
    for _ in range(n):
        rc = rng.permutation(r)
        s = rc.mean()/rc.std()*np.sqrt(252)
        if s >= real: cnt += 1
    return cnt/n, real

def blend_corr(r, blend_path='/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv'):
    b = pd.read_csv(blend_path, index_col=0, parse_dates=True)['ret']
    df = pd.concat([r, b], axis=1, join='inner').dropna()
    if len(df) < 100: return np.nan
    return df.corr().iloc[0,1]

def full_gates(net, name, min_sr=1.0):
    s = stats(net)
    h1, h2 = halves(net)
    pv, real = scramble_pval(net)
    corr = blend_corr(net)
    g = {
      'full_sr>=1.0': s['sr']>=min_sr,
      'H1>=0.5': h1>=0.5, 'H2>=0.5': h2>=0.5,
      'negy<=2': s['negy']<=2, 'worst>-5': s['worst']>-5,
      'scramble_p<0.05': pv<0.05,
      'corr<0.15': (abs(corr)<0.15) if corr==corr else False,
      'corr_ok_secondary': (abs(corr)<0.35) if corr==corr else False,
    }
    res = dict(name=name, ann=round(s['ann'],1), vol=round(s['vol'],1), sr=round(s['sr'],2),
               mdd=round(s['mdd'],1), negy=s['negy'], worst=round(s['worst'],1),
               years=s['years'], H1=round(h1,2), H2=round(h2,2),
               scramble_p=round(pv,4), corr_blend=round(corr,3) if corr==corr else None,
               gates=g, all_pass=all(g.values()))
    return res

def pp(res):
    gates_s = ', '.join(f"{k}:{'Y' if v else 'N'}" for k,v in res['gates'].items())
    print(f"{res['name']}: ann={res['ann']}% vol={res['vol']}% SR={res['sr']} MDD={res['mdd']}% "
          f"negy={res['negy']} worst={res['worst']}% yrs={res['years']} H1={res['H1']} H2={res['H2']} "
          f"scr_p={res['scramble_p']} corr={res['corr_blend']}")
    print(f"   gates: {gates_s} => ALL_PASS={res['all_pass']}")
