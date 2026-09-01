"""IDEA 2b: dispersion level book — long industries when dispersion low only (long/flat),
positive predictivity +0.103/0.136 suggests conditional EW long when z<median."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import kf48, bt
from c1r2_lib import evaluate

ind = kf48(); rets = ind.iloc[:, :48]
disp = rets.pow(2).rolling(21).mean().mean(axis=1).pow(0.5)
z = (disp - disp.expanding(252).mean())/disp.expanding(252).std()
w = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
on = (z < 0.0).values
w[on] = 1.0/48
net, _, _ = bt(w, rets)
evaluate(net, 'longEW when disp z<0 (21d), flat else')
# variant: z threshold -1, and long when z<0 with 2x when z<-1
w2 = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
w2[(z < 0).values] = 0.5/48; w2[(z < -1).values] = 1.0/48
net2, _, _ = bt(w2, rets)
evaluate(net2, 'longEW 0.5x z<0, 1x z<-1')
