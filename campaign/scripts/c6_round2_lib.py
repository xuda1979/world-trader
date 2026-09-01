"""Shared round-2 helpers for C6_mlmulti: data loaders, ML walk-forward, gates, blend corr."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader')
from campaign.harness.data import fred, apply_cost
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr, vol_target, scramble_pval, plateau

FRED = '/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
COST = 6.0/1e4
BLEND_PATH = '/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv'

def blend():
    b = pd.read_csv(BLEND_PATH, parse_dates=['date'], index_col='date')['ret']
    return b

def corr_blend(r, min_n=250):
    b = blend()
    j = pd.concat([r, b], axis=1).dropna()
    j.columns = ['r', 'b']
    if len(j) < min_n: return np.nan
    return j['r'].corr(j['b'])

def robust_fred(name, root=None):
    root = root or FRED
    try:
        df = pd.read_csv(f"{root}/{name}.csv")
    except Exception:
        return pd.Series(dtype=float)
    c0 = df.columns[0]
    df[c0] = pd.to_datetime(df[c0], errors='coerce')
    df = df.dropna(subset=[c0]).set_index(c0)
    val = df['value'] if 'value' in df.columns else df.iloc[:, 0]
    return pd.to_numeric(val, errors='coerce').dropna()

def load_tenors(names):
    """wide df of FRED yield series, daily, %"""
    out = {}
    for n in names:
        s = robust_fred(n)
        out[n] = s
    return pd.DataFrame(out).sort_index()

def kenfrench_vw(path='/Users/daxu/software/world-trader/tools/quant/data/kenfrench/48_Industry_Portfolios_Daily.csv'):
    lines = open(path).read().splitlines()
    hdr_i = None
    for i, l in enumerate(lines):
        if 'Average Value Weighted Returns -- Daily' in l:
            hdr_i = i + 1; break
    hdr = [h.strip() for h in lines[hdr_i].split(',')][1:]
    rows = []
    for l in lines[hdr_i+1:]:
        parts = l.split(',')
        if not parts[0].strip().isdigit(): break
        rows.append([float(x) if x.strip() else np.nan for x in parts])
    df = pd.DataFrame(rows, columns=['date'] + hdr).set_index('date')
    df.index = pd.to_datetime(df.index, format='%Y%m%d')
    return (df.replace(-99.99, np.nan) / 100.0)

def vt_scale(r, vt_ann=0.10, min_days=60, cap=3.0):
    rc = r.expanding(min_days).std() * np.sqrt(252)
    return (vt_ann / rc).clip(upper=cap)

def gates_report(r, name=''):
    """Full gate battery on net vt-scaled returns r (daily)."""
    s = full_stats(r)
    h1, h2 = halves_sr(r)
    pv, real = scramble_pval(r, 200, seed=0)
    cb = corr_blend(r)
    yr = s['yearly']
    res = dict(name=name, n=int(r.notna().sum()), start=str(r.index[0].date()), end=str(r.index[-1].date()),
               ann=round(s['ann'],1), vol=round(s['vol'],1), sr=round(s['sr'],2), mdd=round(s['mdd'],1),
               H1=round(h1,2), H2=round(h2,2), negy=s['negy'], worst=round(s['worst'],1),
               scr_p=round(pv,3), scr_p95=None, corr_blend=None if cb!=cb else round(cb,3))
    g = {'a_sr>=1.0': s['sr']>=1.0, 'c_halves': h1>=0.5 and h2>=0.5,
         'd_yearly': s['negy']<=2 and s['worst']>-5, 'e_scramble': pv<=0.05,
         'f_corr<0.15': (cb!=cb) or abs(cb)<0.15}
    res['gates'] = g; res['all_pass'] = all(g.values())
    return res

def oos_is_split(r, split='2017-01-01'):
    isr = r[r.index < split]; oos = r[r.index >= split]
    return full_stats(isr)['sr'], full_stats(oos)['sr']

def pr(res):
    g = ' '.join(f"{k}:{'P' if v else 'F'}" for k,v in res['gates'].items())
    print(f"{res['name']}: SR {res['sr']} ann {res['ann']}% mdd {res['mdd']}% H1 {res['H1']} H2 {res['H2']} "
          f"negy {res['negy']} worst {res['worst']}% scr {res['scr_p']} corrB {res['corr_blend']} OOS-IS {res.get('oos_is','')} | {g} => {'ALL PASS' if res['all_pass'] else 'FAIL'}")
