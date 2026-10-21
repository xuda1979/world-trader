import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
books=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD")]
print("=== baseline dual-timeframe grid (no carry, no wday) ===")
rows=[]
for lb in (21,42,63):
    for div in (2.0,):
        nets={}
        for k,(a,b) in enumerate(books):
            n,_=book_pnl(C,a,b,lb=lb,div=div)
            nets[f"b{k}"]=n
        ew=pd.concat(nets,axis=1).mean(axis=1).dropna()
        st=stats(ew)
        st.update(lb=lb,div=div)
        rows.append(st)
        print(f"lb={lb}: SR={st['SR']} H1={st['SR_H1']} H2={st['SR_H2']} MDD={st['MDD']} neg={st['negyrs']} top20={st['top20']}% top50={st['top50']}%")
# dual-timeframe: average of lb21+lb63 books (2 frames x 3 pairs)
def blend_dtf(lbs=(21,63),div=2.0):
    nets=[]
    for lb in lbs:
        for (a,b) in books:
            n,_=book_pnl(C,a,b,lb=lb,div=div)
            nets.append(n)
    return pd.concat(nets,axis=1).mean(axis=1).dropna()
print("\n=== dual-timeframe (6 sub-books: 3 pairs x lb in {21,63}) ===")
for lbs in [(21,63),(21,42,63)]:
    ew=blend_dtf(lbs)
    st=stats(ew)
    print(f"lbs={lbs}: n={st['n']} SR={st['SR']} H1={st['SR_H1']} H2={st['SR_H2']} MDD={st['MDD']} neg={st['negyrs']}({st['worst_yr']}%) top20={st['top20']}% top50={st['top50']}% ac1={st['ac1']} uq={st['uniqR']}")
