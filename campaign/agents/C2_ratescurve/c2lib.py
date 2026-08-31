"""C2_ratescurve shared lib: yield-curve signal -> T+1 backtest -> ALL gates."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader')
from campaign.harness.data import fred, save_sleeve
import importlib.util
spec = importlib.util.spec_from_file_location("gates", "/Users/daxu/software/world-trader/campaign/agents/B2_highfreq/gates.py")
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

FRED = '/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
BLEND = '/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv'

def yld(name):
    """FRED yield series in pct -> clean float."""
    s = fred(name)
    s = pd.to_numeric(s, errors='coerce').replace([-99.99, -99.9], np.nan).dropna()
    s.index = pd.to_datetime(s.index)
    s = s[~s.index.duplicated(keep='last')].sort_index()
    return s

# approx modified durations at typical yield levels (documented approximation)
DUR = {'DGS1MO':0.08,'DGS3MO':0.25,'DGS6MO':0.5,'DGS1':0.95,'DGS2':1.9,'DGS3':2.8,
       'DGS5':4.4,'DGS7':6.1,'DGS10':8.5,'DGS20':15.0,'DGS30':17.5}

def bond_ret(name):
    """Approx daily bond total return: ret ~ -D*dy + y/252 (carry). Documented approximation."""
    y = yld(name)
    dy = y.diff()
    r = -DUR[name]*dy + y/252.0/100.0
    return r

def curve_ret(spread_def):
    """Duration-neutral curve position return (per unit gross, s=+1 flattener):
    returns series of the flattener portfolio (long short-leg via duration weights)."""
    (a, b) = split_spread(spread_def)
    Da, Db = DUR[a], DUR[b]
    ra, rb = bond_ret(a), bond_ret(b)
    df = pd.concat([ra.rename('ra'), rb.rename('rb')], axis=1).dropna()
    wa, wb = Db/(Da+Db), Da/(Da+Db)   # unit flattener: long short-mat (a), long-short...
    # flattener PnL = wa*ra + wb*(-rb) ; positive when spread (b-a) narrows
    flat = wa*df['ra'] - wb*df['rb']
    return flat, df

def split_spread(s):
    parts = s.split('-')
    return parts[0], parts[1]

def load_blend():
    b = pd.read_csv(BLEND, index_col=0, parse_dates=True)['ret']
    return b

def backtest(sig, gross_ret, cost_bps=6.0, vt=0.10, min_days=60, clip=3.0):
    """sig: position series (float, data<=t). gross_ret: per-unit-gross daily return.
    T+1: pos held on day t earns gross_ret[t] (sig already shifted by caller).
    Returns net vol-targeted daily returns."""
    pos = sig
    to = pos.diff().abs().fillna(pos.abs())  # one-side turnover per day
    gross = pos*gross_ret
    net = gross - to*cost_bps/1e4
    # vol target: expanding std of NET returns, shifted 1d (trailing only)
    rcum = net.expanding(min_days).std()*np.sqrt(252)
    scale = (vt/rcum).clip(upper=clip).shift(1)
    scaled = (net*scale).dropna()
    return scaled, dict(turnover=to.mean(), scale_med=float(scale.median()))

def run_all_gates(r, name, corr_vs=None, verbose=True):
    """ALL GOAL100 gates. r = net vol-targeted returns."""
    s = G.full_stats(r)
    h1, h2 = G.halves_sr(r)
    pv, real = G.scramble_pval(r, n=200, seed=0)
    out = dict(name=name, ann=round(s['ann'],1), vol=round(s['vol'],1), sr=round(s['sr'],2),
               mdd=round(s['mdd'],1), H1=round(h1,2), H2=round(h2,2), negy=s['negy'],
               worst=round(s['worst'],2), years=s['years'], scramble_p=round(pv,4))
    out['g_full_sr'] = s['sr'] >= 1.0
    out['g_halves'] = (h1 >= 0.5) and (h2 >= 0.5)
    out['g_yearly'] = (s['negy'] <= 2) and (s['worst'] > -5)
    out['g_scramble'] = pv < 0.05
    blend = load_blend()
    idx = r.index.intersection(blend.index)
    c = np.corrcoef(r[idx], blend[idx])[0,1]
    out['corr_blend'] = round(float(c),3)
    out['g_corr'] = abs(c) < 0.15
    out['all_pass'] = out['g_full_sr'] and out['g_halves'] and out['g_yearly'] and out['g_scramble'] and out['g_corr']
    if corr_vs is not None:
        cs = {}
        for nm, rr in corr_vs:
            i2 = r.index.intersection(rr.index)
            if len(i2) > 500:
                cs[nm] = round(float(np.corrcoef(r[i2], rr[i2])[0,1]),3)
        out['corr_lib'] = dict(sorted(cs.items(), key=lambda x: -abs(x[1]))[:5])
    if verbose:
        print(out)
    return out
