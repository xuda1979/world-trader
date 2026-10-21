import pandas as pd, numpy as np
# Verify the paper-credit claim independently: synth BAA TR vs real LQD/HYG (twelvedata)
import glob
lqds = glob.glob('/Users/daxu/software/world-trader/tools/quant/data/**/LQD*', recursive=True) + glob.glob('/Users/daxu/software/world-trader/tools/quant/data/**/lqd*', recursive=True)
hygs = glob.glob('/Users/daxu/software/world-trader/tools/quant/data/**/HYG*', recursive=True)
baas = glob.glob('/Users/daxu/software/world-trader/tools/quant/**/BAA*', recursive=True)
print("LQD:", lqds[:2], "HYG:", hygs[:2], "BAA:", baas[:2])
if lqds and baas:
    lqd = pd.read_csv(lqds[0],index_col=0,parse_dates=True)['close'].astype(float).sort_index()
    r_lqd = lqd.pct_change().dropna()
    baa = pd.read_csv(baas[0],index_col=0,parse_dates=True).iloc[:,0]
    baa = pd.to_numeric(baa,errors='coerce').dropna().sort_index()/100.0
    # synth BAA TR per A5r7 convention: ~ -7*d(spread?)... A5r7 uses DBAA index; use -dur*d(baa yield)+carry
    tr = (-7.0*baa.diff()+baa/252.0).dropna()
    j = pd.concat([tr.rename('synth'), r_lqd.rename('lqd')],axis=1,sort=True).dropna()
    print(f"synth BAA TR vs LQD daily corr: n={len(j)} corr={j['synth'].corr(j['lqd']):.3f}")
