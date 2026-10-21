#!/usr/bin/env python3
"""Self-contained candidate champion with the Brent-WTI spread-filter, reading sleeve paths
directly (no shared-module mutation). Same IS weight-fit + net logic as the canonical builder."""
import os, sys, pandas as pd, numpy as np
ROOT="/Users/daxu/software/world-trader"; sys.path.insert(0, ROOT+"/campaign")
from scripts import rawew13v2_build as B

# sleeve paths: 8 unchanged + 3 filtered brwt
PATHS = dict(B.PATHS)
for name, path in list(PATHS.items()):
    b = os.path.basename(path)
    if b.startswith("brwt") and b.endswith("costfix.csv"):
        PATHS[name] = f"{ROOT}/campaign/results/brwt_filtered/{b}"

def load(p):
    df = pd.read_csv(p, index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

NAMES = [n for n in B.NAMES]
df = pd.DataFrame({n: load(PATHS[n]) for n in NAMES})
df = df[df.index >= "2008-03-31"]
# same IS weight fit
isr = df[df.index < pd.Timestamp("2017-01-01")]
rw = B.fit_relw(isr, shrink_d=B.SHRINK_D)
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(rw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
Wg = d2 * (B.GEAR / len(NAMES))
port = (df.fillna(0).values * Wg.values).sum(axis=1)
to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
net = pd.Series(port, index=df.index) - to*B.BPS/1e4 - np.maximum(B.GEAR-1,0)*B.RATE/252

def stats(x):
    x = x.dropna(); eq=(1+x).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=x.resample("YE").apply(lambda v:(1+v).prod()-1)
    return (x.mean()*252, x.mean()/x.std(ddof=1)*np.sqrt(252) if x.std(ddof=1)>0 else 0, float(dd), int((yr<0).sum()))

a,sr,dd,neg=stats(net)
print("=== CANDIDATE CHAMPION (filtered brwt) ===")
print(f"ann {a*100:.2f}%  SR {sr:.3f}  MaxDD {dd*100:.2f}%  neg {neg}  gross {Wg.abs().sum(axis=1).mean():.3f}")
print(f"IS ann {stats(net[net.index<'2017-01-01'])[0]*100:.1f}% / OOS ann {stats(net[net.index>='2017-01-01'])[0]*100:.1f}%")
# turnover of champion
print(f"turnover {to.mean()*252*6.4:.2f} bp/yr  margin {max(B.GEAR-1,0)*4.5:.2f}%/yr")

champ=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
ac,src,ddc,negc=stats(champ)
print("=== OF-RECORD champion (reference) ===")
print(f"ann {ac*100:.2f}%  SR {src:.3f}  MaxDD {ddc*100:.2f}%  neg {negc}")

net.to_frame("ret").to_csv(f"{ROOT}/campaign/results/BRWT_FILTER_CANDIDATE_daily.csv")
print("saved candidate -> campaign/results/BRWT_FILTER_CANDIDATE_daily.csv")
