"""IDEA 4: IG-vs-rates divergence. DV01-hedged: long BAA synth (dur7) / short 10y synth
(dur 8.5, 1 unit notional) sized so rate beta ~0 -> net dur 7-8.5 per unit... use w=7/8.5
notional on the short leg to DV01-match: short notional = 7/8.5 = 0.824 x10y.
Signal: (TR_baa - TR_hedged_leg) trailing Ld momentum > 0 -> long pair; < 0 -> flip.
Weekly decision (step 5). T+1, 6bps, VT10."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *

DB=7.0; D10=8.5
baa=yld('baa'); y10=yld('DGS10')
df=pd.concat([baa.rename('baa'),y10.rename('y10')],axis=1,sort=True).dropna()
df=df[df.index>='1986-06-01']
tr_baa=rfn(df['baa'],DB)
tr10=rfn(df['y10'],D10)
w=DB/D10   # 0.824 units of 10y per 1 unit BAA => DV01 neutral
pair_ret=tr_baa-w*tr10    # long credit / short rates (dur-hedged)
pair_ret=pair_ret-0.5*(tr_baa-w*tr10)*0  # keep raw; rf accrual handled by book below
rfc=rf_daily().reindex(df.index).fillna(0)
mom=pair_ret.rolling(63).sum()
out={}
for step in (5,10,21):
    z=mom.iloc[::step]
    sig=(z>0).astype(float)*2-1     # +1 long credit/short rates; -1 reverse
    sig=sig.reindex(df.index).ffill().shift(1).fillna(0)
    to=sig.diff().abs().fillna(0)*(1+w)
    net=vt(sig*pair_ret-to*COST+rfc*(1-sig.abs()))
    out[step]=(net,sig)
for step,(net,sig) in out.items():
    s=stats(net); h=halves(net); cb=corr_to(net,CHAMP); ca=corr_to(net,A1CR)
    print(f"div-mom L63 step{step}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}% H1={h[0]:.2f} H2={h[1]:.2f} corr_champ={cb:.3f} corr_A1={ca:.3f} to/d={sig.diff().abs().mean():.4f}")
    print("  negyrs:", {k:v for k,v in s['yearly'].items() if v<0})
# grid over momentum window for chosen step
print("\nmomentum window grid (step5):")
for L in (21,42,63,126,252):
    mom=pair_ret.rolling(L).sum()
    z=mom.iloc[::5]; sig=(z>0).astype(float)*2-1
    sig=sig.reindex(df.index).ffill().shift(1).fillna(0)
    to=sig.diff().abs().fillna(0)*(1+w)
    net=vt(sig*pair_ret-to*COST+rfc*(1-sig.abs()))
    s=stats(net)
    print(f"  L={L}: SR={s['sr']:.2f} negy={s['negy']} worst={s['worst']:.1f}% H1={halves(net)[0]:.2f} H2={halves(net)[1]:.2f}")
