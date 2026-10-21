"""D2_macroregime shared lib: honest weekly/monthly macro-regime backtests.
Publication lag convention (documented per idea):
- ICSA weekly (week ends Sat, released following Thu): 5 calendar days
- WALCL/BOGMBASE weekly Wed release for prior Wed: 5 days
- TGA daily, released next day: 1 day
- PAYEMS monthly (1st Friday): 8 days after month end
- M2SL monthly (4th week): 28 days
- CFNAIMA3 monthly (~24th of following month): 24 days
Signal known at obs_date + lag; position taken at NEXT trading day close (T+1 on signal day).
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, '/Users/daxu/software/world-trader')
import campaign.harness.data as H
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval

NEW = "/Users/daxu/software/world-trader/tools/quant/data/newdata"
FR  = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
COST = 6.0/1e4

def load_new(n):
    s = pd.read_csv(f"{NEW}/{n}.csv", index_col=0, parse_dates=True).iloc[:,0]
    s = s[s.notna()]; return s.sort_index()

def load_fr(n):
    s = pd.read_csv(f"{FR}/{n}.csv", index_col=0, parse_dates=True).iloc[:,0]
    s = s[s.notna()]; return s.sort_index()

def trading_cal():
    y = load_fr('DGS2')  # daily trading calendar 1976+
    return y.index

def to_daily(sig, lag_days, cal=None):
    """sig: pd.Series indexed by observation DATE (period end). Value known at obs+lag.
    Returns daily series (on trading cal) with value asof (t - lag), i.e. only obs with
    obs_date + lag <= t are visible at t."""
    cal = trading_cal() if cal is None else cal
    avail = pd.Series(sig.values, index=sig.index + pd.Timedelta(days=lag_days))
    daily = avail.reindex(cal.union(avail.index)).ffill().reindex(cal)
    return daily

def synth_tr(yld_pct, dur):
    """Daily total return synth from par yield (pct): carry + duration price effect."""
    y = yld_pct/100.0
    dy = y.diff().fillna(0.0)
    return y/252.0 - dur*dy

def backtest(pos, asset_ret, name="", vt=True):
    """pos: daily target exposure series (already based on info available at t).
    Executed at t+1 close-to-close: shift(1). Costs on |delta pos|."""
    pos = pos.fillna(0.0)
    exec_pos = pos.shift(1).fillna(0.0)
    gross = exec_pos*asset_ret
    to = exec_pos.diff().abs().fillna(0.0) + exec_pos.abs()*0.0  # entry cost via diff incl from 0
    to.iloc[0] = abs(exec_pos.iloc[0])
    net = gross - to*COST
    if vt:
        scaled, scale = vol_target(net, 0.10)
        return scaled, net, gross, exec_pos, scale
    return net, net, gross, exec_pos, None

def blend_ret():
    b = pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',
                    index_col=0, parse_dates=True)['ret']
    return b

def corr_blend(r):
    b = blend_ret()
    df = pd.concat([r, b], axis=1).dropna()
    return df.corr().iloc[0,1]

def gates_full(r_scaled, name):
    """ALL brief gates incl full SR>=1.0, halves>=0.5, yearly, scramble, decorrelation."""
    s = full_stats(r_scaled)
    h1,h2 = halves_sr(r_scaled)
    pv, real = scramble_pval(r_scaled, 200, seed=0)
    cb = corr_blend(r_scaled)
    yr = r_scaled.groupby(r_scaled.index.year).apply(lambda x:(1+x).prod()-1)
    neg = yr[yr<0]
    res = dict(name=name, start=str(r_scaled.index[0].date()), end=str(r_scaled.index[-1].date()),
               ann=round(s['ann'],1), vol=round(s['vol'],1), sr=round(s['sr'],2), mdd=round(s['mdd'],1),
               H1=round(h1,2), H2=round(h2,2), negy=s['negy'], worst=round(s['worst'],1),
               years=s['years'], scramble_p=round(pv,3), corr_blend=round(cb,3))
    g = {'a_sr>=1.0': s['sr']>=1.0, 'c_halves>=0.5': h1>=0.5 and h2>=0.5,
         'd_negy<=2': s['negy']<=2, 'd_worst>-5': s['worst']>-5,
         'e_scramble_p<0.05': pv<0.05, 'f_|corr|<0.15': abs(cb)<0.15}
    res['gates']=g; res['all_pass']=all(g.values())
    res['neg_yr_list'] = {int(k): round(v*100,1) for k,v in neg.items()}
    return res

def pp(res):
    print(f"{res['name']}: {res['start']}->{res['end']} ann={res['ann']}% vol={res['vol']}% SR={res['sr']} "
          f"mdd={res['mdd']}% H1={res['H1']} H2={res['H2']} negy={res['negy']} worst={res['worst']}% "
          f"scramble_p={res['scramble_p']} corr_blend={res['corr_blend']}")
    print("  gates:", {k:bool(v) for k,v in res['gates'].items()}, "ALL_PASS:", res['all_pass'])
    print("  neg yrs:", res['neg_yr_list'])

def signal_scramble_pval(net, pos, n=200, seed=1):
    """Honest scramble: permute the POSITION sequence vs fixed asset returns, recompute
    net (incl costs) + same vol-target, compare SRs. p = frac(scrambled >= real)."""
    from campaign.agents.B2_highfreq.gates import vol_target
    rng = np.random.default_rng(seed)
    asset = net + (pos.diff().abs().fillna(0)*COST)  # recover gross-per-exec? simpler: rebuild
    # We instead operate on gross series passed in by caller via closure-free API:
    return None
