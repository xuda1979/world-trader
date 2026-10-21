"""recon2: overlay battery. m_target built from signal at t, executed via bt.lag_signal.
Charged: |dm|*6.4bps*gross(=3.367). Reports dSR, MDD, neg-yrs, H1/H2 on 2008+."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VXV_TERM/scratch')
from bt.engine import lag_signal
from bt.metrics import sharpe_d, max_dd, neg_years, half_split, ann_geo
from overlay import overlay_ret
import recon1

GROSS = 3.367

def eval_m(m_target, df, label, results, gross=GROSS):
    r = df.champ
    post = r.index >= '2008-01-01'
    base = r[post].dropna()
    sr0 = sharpe_d(base)
    m_exec = lag_signal(m_target)
    out = overlay_ret(r, m_exec, gross=gross).loc[post].dropna()
    assert len(out) == len(base), (len(out), len(base))
    sr = sharpe_d(out)
    d = sr - sr0
    mdd0, mdd = max_dd(base), max_dd(out)
    n0, w0 = neg_years(base); n1, w1 = neg_years(out)
    h1, h2 = half_split(out)
    # money check: mean bp/day
    mb = out.mean() * 1e4
    results.append(dict(label=label, sr=sr, dsr=d, mdd=mdd, neg=n1, worst=w1,
                        h1=h1, h2=h2, mbpd=mb, mean_on=float(m_exec.loc[out.index].mean())))
    return out

if __name__ == '__main__':
    df = recon1.load(); s = recon1.signals(df)
    base = df.champ[df.champ.index >= '2008-01-01'].dropna()
    sr0 = sharpe_d(base)
    print('BASELINE 2008+: n=%d SR_d=%.4f ann_geo=%.4f MDD=%.4f neg=%d/19 worst=%.4f' % (
        len(base), sr0, ann_geo(base), max_dd(base), neg_years(base)[0], neg_years(base)[1]))
    res = []
    z = s.ratio_z
    for thr, nm in [(0.5, 'z>0.5'), (1.0, 'z>1.0'), (1.5, 'z>1.5'), (0.0, 'z>0')]:
        eval_m((z <= thr).astype(float), df, 'OFF ratio_z ' + nm, res)
        eval_m((z > thr).astype(float), df, 'ON  ratio_z ' + nm, res)
    sz = s.slope_z
    for thr in [0.0, -0.5]:
        eval_m((sz >= thr).astype(float), df, 'OFF slope_z>=%.1f' % thr, res)
        eval_m((sz < thr).astype(float), df, 'ON  slope_z<%.1f' % thr, res)
    d21 = s.dvxv21
    for q in [0.5, 0.8, 0.9]:
        thr = d21.quantile(q)
        eval_m((d21 <= thr).astype(float), df, 'OFF dvxv21>q%0.1f' % (q * 100), res)
        eval_m((d21 > thr).astype(float), df, 'ON  dvxv21>q%0.1f' % (q * 100), res)
    eval_m(s.contango, df, 'ON contango=1', res)
    eval_m(1 - s.contango, df, 'ON backwardation', res)
    go = s.gvzovx_z
    for thr in [0.5, 1.0, -0.5]:
        eval_m((go <= thr).astype(float), df, 'OFF gvzovx_z>%0.1f' % thr, res)
        eval_m((go > thr).astype(float), df, 'ON  gvzovx_z>%0.1f' % thr, res)
    co = s.combo
    for thr in [0.5, 1.0]:
        eval_m((co <= thr).astype(float), df, 'OFF combo>%0.1f' % thr, res)
        eval_m((co > thr).astype(float), df, 'ON  combo>%0.1f' % thr, res)
    # 2-sided tail-out: flat in BOTH extreme tails of ratio_z (whipsaw guard)
    q05, q95 = z.quantile(0.05), z.quantile(0.95)
    eval_m(((z >= q05) & (z <= q95)).astype(float), df, 'OFF ratio_z tails(5/95)', res)
    # 1x charge reference for best-family honesty
    R = pd.DataFrame(res).sort_values('dsr', ascending=False)
    print(R.to_string(index=False, float_format=lambda v: '%0.4f' % v))
    print('\nTop3 dSR charged@3.367x (bar +0.15); baseline SR %.4f' % sr0)
