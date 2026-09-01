"""C6 Idea 5: Regime-ML meta-allocation. Trailing sleeve-pool stats (corr of each sleeve to EW,
own vol, mom) -> GBM predict next-21d sleeve underperformance vs EW -> monthly over/underweights.
Must beat EW of pool OOS (2017+) to save."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr
from sklearn.ensemble import GradientBoostingRegressor
import glob, warnings; warnings.filterwarnings('ignore')

files = glob.glob('/Users/daxu/software/world-trader/campaign/results/sleeve_library/*.csv')
files += glob.glob('/Users/daxu/software/world-trader/campaign/agents/*/sleeves/*.csv')
files = [f for f in files if not f.endswith('.meta')]
R = {}
for f in files:
    try:
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        if 'ret' in df and len(df) > 1500:
            R[f.split('/')[-1][:-4]] = df['ret']
    except Exception: pass
R = pd.DataFrame(R).sort_index()
R = R.loc['2008-09-01':]
R = R[R.columns[R.notna().mean() > 0.9]]
R = R.fillna(0.0)
print('pool', R.shape, R.index.min().date(), R.index.max().date())
ew = R.mean(axis=1)

# daily features per sleeve (all trailing)
W = 126
feats = {}
roll = R.rolling(W)
for c in R.columns:
    r = R[c]
    f = pd.DataFrame(index=R.index)
    f['vol'] = r.rolling(W).std()*np.sqrt(252)
    f['mom'] = (1+r).rolling(W).apply(np.prod, raw=True)-1
    f['dd'] = r.rolling(W).apply(lambda x: np.min(np.cumprod(1+x)/np.maximum.accumulate(np.cumprod(1+x))-1), raw=True)
    ewm = ew.rolling(W).mean()
    f['excess_mom'] = f['mom'] - (1+ew).rolling(W).apply(np.prod, raw=True)-1
    feats[c] = f
F = pd.concat(feats, axis=1)  # (date, sleeve, feat)
# target: next-21d sleeve excess return vs EW
tgt_mom = R.apply(lambda x: (1+x).rolling(21).apply(np.prod, raw=True)-1)
ew21 = (1+ew).rolling(21).apply(np.prod, raw=True)-1
TGT = tgt_mom.sub(ew21, axis=0).shift(-21)

mends = pd.date_range('2011-01-01', R.index.max() - pd.Timedelta(days=30), freq='ME')
Wdf = pd.DataFrame(index=R.index, columns=R.columns, dtype=float)
for me in mends:
    te_dates = R.index[(R.index > me) & (R.index <= me + pd.offsets.MonthEnd(1))]
    if len(te_dates) == 0: continue
    tr_end = me - pd.Timedelta(days=22)
    rows, ys, meta = [], [], []
    for c in R.columns:
        f = feats[c].loc[:tr_end].iloc[-1]
        if f.isna().any(): continue
        rows.append(f.values); meta.append(c)
        # training target: that sleeve's 21d excess fwd from past dates (use panel of trailing 750 rows)
        pass
    # build training set: for each of last 750 dates <= tr_end, each sleeve's features & fwd excess
    tr_dates = R.index[(R.index <= tr_end)][-750:]
    Xtr, ytr = [], []
    for dt in tr_dates:
        i = R.index.get_loc(dt)
        for c in R.columns:
            fv = feats[c].loc[dt]
            tv = TGT.loc[dt, c] if dt in TGT.index else np.nan
            if fv.notna().all() and not np.isnan(tv):
                Xtr.append(fv.values); ytr.append(tv)
    if len(Xtr) < 3000: continue
    m = GradientBoostingRegressor(n_estimators=60, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)
    m.fit(np.array(Xtr), np.array(ytr))
    Xte = np.array([feats[c].loc[te_dates[0]].values for c in R.columns])
    pr = m.predict(Xte)
    # weight: tilt from EW by rank of prediction (long-underweight shorts-of-sleeves predicted to outperform)
    rk = pd.Series(pr, index=R.columns).rank()
    wt = (rk - rk.mean())/rk.std() * 0.25 + 1.0   # mild tilt, ~0.5-1.5x
    wt = wt/wt.sum()
    Wdf.loc[te_dates, :] = np.nan
    for c in R.columns: Wdf.loc[te_dates, c] = wt[c]
Wdf = Wdf.fillna(1.0/len(R.columns))
strat = (Wdf.shift(1)*R).sum(axis=1)     # T+1
turn = Wdf.shift(1).diff().abs().sum(axis=1).fillna(0)
strat = strat - 6e-4*turn
ewb = ew - 6e-4*(Wdf.shift(1).diff().abs().sum(axis=1)*0)  # EW baseline w/o extra cost
print('--- EW pool baseline ---')
ewn,_ = vol_target(ewb, 0.10)
print({k:(round(v,2) if isinstance(v,float) else v) for k,v in full_stats(ewn).items() if k!='yearly'})
print('--- ML-tilt ---')
ns,_ = vol_target(strat, 0.10)
st = full_stats(ns); h1,h2 = halves_sr(ns)
print('FULL',{k:(round(v,2) if isinstance(v,float) else v) for k,v in st.items() if k!='yearly'})
print('halves',round(h1,2),round(h2,2))
oos_s = ns[ns.index>='2017-01-01']; oos_e = ewn[ewn.index>='2017-01-01']
print('OOS ML ',{k:(round(v,2) if isinstance(v,float) else v) for k,v in full_stats(oos_s).items() if k!='yearly'})
print('OOS EW ',{k:(round(v,2) if isinstance(v,float) else v) for k,v in full_stats(oos_e).items() if k!='yearly'})
ns.to_frame('ret').to_csv('/tmp/c6_meta_ml.csv')
print('yearly',st['yearly'])
