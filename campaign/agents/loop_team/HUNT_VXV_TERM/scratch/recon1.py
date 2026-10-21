"""recon1: data prep + predictive screen (corr, quintiles) of term-structure signals
vs champion daily returns. All signals trailing (level at t uses only data<=t)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
from bt.metrics import sharpe_d

BASE = '/Users/daxu/software/world-trader'
CHAMP_F = BASE + '/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv'
GROSS = 3.367  # STATS_REVIEW §8 BAL capital-real all-in mean 2008+ (HUNT_VOLOVERLAY charge basis)


def load():
    ch = pd.read_csv(CHAMP_F, index_col=0, parse_dates=True)['ret']
    vix = pd.read_csv(BASE + '/tools/quant/hedge_fund_strats/data_fred_new/VIXCLS.csv',
                      index_col=0, parse_dates=True).iloc[:, 0].rename('vix')
    vxv = pd.read_csv(BASE + '/tools/quant/data/more_fred/VXVCLS.csv',
                      index_col=0, parse_dates=True).iloc[:, 0].rename('vxv')
    gvz = pd.read_csv(BASE + '/tools/quant/data/more_fred/GVZCLS.csv',
                      index_col=0, parse_dates=True).iloc[:, 0].rename('gvz')
    ovx = pd.read_csv(BASE + '/tools/quant/data/more_fred/OVXCLS.csv',
                      index_col=0, parse_dates=True).iloc[:, 0].rename('ovx')
    df = pd.concat([ch.rename('champ'), vix, vxv, gvz, ovx], axis=1)
    # term structure joins on common dates; missing idx values -> NaN then ffill<=3d (lint: gaps<=2)
    df[['vix', 'vxv', 'gvz', 'ovx']] = df[['vix', 'vxv', 'gvz', 'ovx']].ffill(limit=3)
    return df


def signals(df):
    s = pd.DataFrame(index=df.index)
    s['slope'] = df.vxv - df.vix                                    # (a) raw slope
    s['slope_z'] = (df.vxv / df.vix - 1.0)                          # (a') pct slope
    s['ratio_z'] = ((df.vxv / df.vix)
                    - (df.vxv / df.vix).rolling(252, min_periods=126).mean()) \
        / (df.vxv / df.vix).rolling(252, min_periods=126).std()      # (a) z of ratio
    s['dvxv'] = df.vxv.pct_change()                                 # (b) VXV 1d chg
    s['dvxv21'] = df.vxv / df.vxv.shift(21) - 1.0                   # (b') VXV 21d chg
    s['contango'] = (df.vxv > df.vix).astype(float)                 # (c) contango sign
    s['gvzovx_z'] = ((df.gvz / df.ovx)
                     - (df.gvz / df.ovx).rolling(63, min_periods=42).mean()) \
        / (df.gvz / df.ovx).rolling(63, min_periods=42).std()        # (d) GVZ/OVX 63d z
    s['combo'] = s['ratio_z'].fillna(0) - s['gvzovx_z'].fillna(0)   # (e) combined
    return s


if __name__ == '__main__':
    df = load()
    s = signals(df)
    post2008 = df.index >= '2008-01-01'
    print('champ n full=%d, 2008+ n=%d' % (len(df), post2008.sum()))
    j = pd.concat([df.champ.rename('champ'), s], axis=1).loc[post2008].dropna()
    print('joint-NA screen n=%d, span %s..%s' % (len(j), j.index.min().date(), j.index.max().date()))
    print('%-10s corr_sig_vs_R   mean_q1..q5(bp/day)   SR_q1..q5' % 'signal')
    for c in s.columns:
        x = j[c]
        corr = x.corr(j.champ)
        q = pd.qcut(x.rank(method='first'), 5, labels=False)
        mns = [j.champ[q == k].mean() * 1e4 for k in range(5)]
        srs = [sharpe_d(j.champ[q == k]) for k in range(5)]
        print('%-10s %+0.4f        %s   %s' % (c, corr,
              '/'.join('%+0.1f' % v for v in mns), '/'.join('%0.2f' % v for v in srs)))


def predictive():
    """HONEST screen: signal at t-1 (known at close t-1) vs champion return at t.
    corr_p = corr(s_{t-1}, r_t)  -- this is what a T+1 overlay can harvest."""
    df = load(); s = signals(df)
    post2008 = df.index >= '2008-01-01'
    j = pd.concat([df.champ.rename('champ'), s], axis=1).loc[post2008]
    print('== PREDICTIVE (s_{t-1} vs r_t), n=%d span %s..%s' % (len(j.dropna()), j.index.min().date(), j.index.max().date()))
    for c in s.columns:
        x = s[c].shift(1)
        jj = pd.concat([j.champ, x.rename('x')], axis=1).dropna()
        corr = jj.x.corr(jj.champ)
        q = pd.qcut(jj.x.rank(method='first'), 5, labels=False)
        mns = [jj.champ[q == k].mean() * 1e4 for k in range(5)]
        srs = [sharpe_d(jj.champ[q == k]) for k in range(5)]
        on = jj[jj.x.notna()]
        print('%-10s corr %+0.4f | mean_q1..q5(bp) %s | SR %s' % (c, corr,
              '/'.join('%+0.1f' % v for v in mns), '/'.join('%0.2f' % v for v in srs)))
