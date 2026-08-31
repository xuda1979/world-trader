"""Volume-shock reversal: signal on volume z-score (anomalous volume -> price reverses)."""
import numpy as np, pandas as pd
from campaign.harness.data import closes, volumes
from campaign.agents.B2_highfreq.bt import load_px
COST=6.0/1e4

def run_vol_reversal(window=20, k_long=20, k_short=20, min_vol=1e5, L=3):
    px = load_px()
    vol = volumes()
    vol = vol.reindex(px.index).reindex(px.columns, axis=1)
    # volume z-score relative to trailing window (uses data <= t)
    mp = min(30, window)
    vmean = vol.rolling(window, min_periods=mp).mean()
    vstd = vol.rolling(window, min_periods=mp).std()
    vz = (vol - vmean)/vstd.replace(0, np.nan)
    # past L-day price return
    past = px.pct_change(L)
    # signal: high volume shock (vz>2) + past return -> expect reversal next day
    # combine: short names with high vol shock that rallied, long names with high vol shock that dropped
    # rank the interaction
    fwd = px.pct_change(1).shift(-1)
    # score = vz * past; reversal: more negative past with high vz => buy
    # Simpler: only trade names with vol shock (|vz|>2), then cross-sectionally long most-negative past ret, short most-positive
    shocked = vz.abs() > 1.5
    # restrict
    score = past.where(shocked)
    rank = score.rank(axis=1, na_option='keep')
    n = px.shape[1]
    long_mask = (rank <= k_long) & shocked
    short_mask = (rank > (n - k_short)) & shocked
    pos = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    pos[long_mask] = 1.0/k_long
    pos[short_mask] = -1.0/k_short
    valid = past.notna() & fwd.notna() & px.notna()
    pos = pos.where(valid, 0.0)
    contrib = pos*fwd
    active=(pos!=0).sum(axis=1)
    gr = contrib.sum(axis=1)/active.replace(0,np.nan)
    gr=gr.fillna(0)
    frac=(k_long+k_short)/n
    net = gr - frac*COST
    return net, gr

if __name__=='__main__':
    for w in [20,40,60]:
        for L in [2,3,5]:
            net,gr=run_vol_reversal(window=w, L=L)
            mu,sd=net.mean(),net.std(); sr=mu/sd*np.sqrt(252) if sd>0 else 0
            eq=(1+net).cumprod(); dd=(eq/eq.cummax()-1).min()
            gmu,gsd=gr.mean(),gr.std(); gsr=gmu/gsd*np.sqrt(252) if gsd>0 else 0
            print(f"w={w} L={L}: SR={sr:.2f} ann={mu*252*100:.1f}% GrossSR={gsr:.2f} MaxDD={dd*100:.1f}%")
