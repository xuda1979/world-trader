"""r4 idea1: 12-1 momentum LONG-ONLY top quintile at vt15, MA150 hysteresis gate.
Grid over {lookback, skip, frac, MA win} — pick by SR on plateau, then full gate battery."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from r4lib import *
from r2lib import wbacktest

G150=ma_gate(150,0.03)
def make_sig(lb,skip): return px.shift(skip)/px.shift(lb)-1.0

rows=[]
for lb in (189,252,315):
    for skip in (21,42):
        for frac in (0.15,0.20,0.30):
            for gw in (150,200):
                G=ma_gate(gw,0.03)
                sc=make_sig(lb,skip); W=long_top(sc,frac,G)
                e=evaluate(f"lb{lb} sk{skip} f{frac} ma{gw}",W,0.15,verbose=False)
                if e: rows.append((lb,skip,frac,gw,e["g"]["SR"],e["g"]["H1"],e["g"]["H2"],e["g"]["negYr"],e["g"]["worst"],e["g"]["ann"],e["g"]["corr_champ"]))
df=pd.DataFrame(rows,columns=["lb","skip","frac","gw","SR","H1","H2","negYr","worst","ann","corrC"])
pd.set_option("display.width",200)
print(df.sort_values("SR",ascending=False).head(15).to_string(index=False))
df.to_csv("/tmp/r4_idea1_grid.csv",index=False)
# plateau view for best cell: neighbors
b=df.sort_values("SR",ascending=False).iloc[0]
print("\nBEST:",dict(b))
sub=df[(df.lb==b.lb)]
print(sub.to_string(index=False))
