"""Materiality check (my own scratch): the INTENDED monthly-held trend book
(non-decision rows NaN -> ffill) run through their COMMITTED net_of + bt metrics.
This is not a re-tune: it tests whether the finding is verdict-safe under the book
the docstring describes."""
import sys
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import importlib.util
spec=importlib.util.spec_from_file_location("fx5f", f"{ROOT}/campaign/scripts/HUNT_FXCARRY2_round5.py")
fx5=importlib.util.module_from_spec(spec); spec.loader.exec_module(fx5)
from bt import metrics as M
px=fx5.load_frankfurter(); R_spot=fx5.returns_from_px(px)
mes=set(fx5.month_ends(R_spot.index))
def held(W):
    H=W.copy().astype(float)
    H[[t not in mes for t in H.index]]=np.nan
    return H.ffill().fillna(0.0)
print(f"{'config':<18}{'SR_asbuilt':>11}{'SR_held':>9}{'neg_asbuilt':>12}{'neg_held':>9}{'live_held':>10}")
for lb in (63,126,252):
    for mode in ("LS","LF"):
        W=fx5.trend_book_weights(px,lb=lb,mode=mode)
        net,We,sig,r_pu=fx5.net_of(W,R_spot); net_t=fx5.trim_warmup(net,sig)
        Wh=held(W)
        neth,Weh,sigh,r_puh=fx5.net_of(Wh,R_spot); neth_t=fx5.trim_warmup(neth,sigh)
        print(f"TREND_mom{lb}_{mode:<4}{M.sharpe_d(net_t):>11.4f}{M.sharpe_d(neth_t):>9.4f}"
              f"{M.neg_years(net_t.dropna())[0]:>12}{M.neg_years(neth_t.dropna())[0]:>9}"
              f"{float((sigh>0).mean()):>10.3f}")
