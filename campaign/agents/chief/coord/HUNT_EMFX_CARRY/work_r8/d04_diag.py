import os, sys
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign")
import emfx_lib as L
CH=L.champion(); PX=L.panel(); CARRY=L.carry_brl(CH.index)
PU=L.total_perunit(PX,CARRY).fillna(0.0)
print("PU NaN:", int(PU.isna().sum().sum()), " PX NaN:", int(PX.isna().sum().sum()))
sig=pd.DataFrame({"BRL":np.where(CARRY>0,1.0,0.0)},index=CH.index)
w=L.effective_weights(sig,PU,target=0.10)
print("\nBRL carry weight series:")
print("  min %.4f max %.4f mean %.4f std %.4f" % (w["BRL"].min(),w["BRL"].max(),w["BRL"].mean(),w["BRL"].std()))
print("  nunique %d" % w["BRL"].nunique())
print("  first 5:", [round(x,4) for x in w["BRL"].head(5)])
print("  around 2020-03:", [round(x,4) for x in w["BRL"].loc["2020-03-10":"2020-04-01"]][:8])
to=w.fillna(0).diff().abs().sum(axis=1); to.iloc[0]=abs(w.iloc[0]).sum()
print("  daily |dW| mean %.6f  -> ann cost %.3f bp/yr" % (to.mean(), to.mean()*1e4*252))
print("  ann |dW| mean %.2f" % (to.mean()*252))
# vol target scale directly
g=sig.abs().sum(axis=1).replace(0,np.nan)
unit=sig.div(g,axis=0).fillna(0.0)
port=(unit.shift(1)*PU).sum(axis=1)
print("\nport(vol input) stats: n=%d mean %.6f std %.6f" % (len(port),port.mean(),port.std()))
sc=L.vol_target_scale(port.to_frame("r"),target=0.10,window=60,cap=3.0)["r"]
print("scale: min %.4f max %.4f mean %.4f nunique %d" % (sc.min(),sc.max(),sc.mean(),sc.nunique()))
print("scale around 2020-03:", [round(x,3) for x in sc.loc["2020-03-10":"2020-04-01"]][:8])
