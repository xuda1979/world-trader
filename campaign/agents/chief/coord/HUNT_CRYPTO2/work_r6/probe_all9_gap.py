import sys
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import importlib.util
spec=importlib.util.spec_from_file_location("fx5c", f"{ROOT}/campaign/scripts/HUNT_FXCARRY2_round5.py")
fx5=importlib.util.module_from_spec(spec); spec.loader.exec_module(fx5)
px=fx5.load_frankfurter(); rates=fx5.load_rates()
R_total=fx5.fx_total_returns(px,rates); R_spot=fx5.returns_from_px(px)
print(f"{'config':<18}{'ndiff':>6}{'SR_net':>9}{'SR_reff':>9}{'neg_net':>8}{'neg_reff':>9}  mech")
for fam,params in [("carry",dict(top=2,k=252)),("carry",dict(top=3,k=252)),("carry",dict(top=4,k=252))]:
    W=fx5.carry_book_weights(px,rates,**params)
    R=R_total; name=f"CARRY_EWtop{params['top']}_12m"
    net,We,sig,r_pu=fx5.net_of(W,R); net_t=fx5.trim_warmup(net,sig); idx=net_t.index
    r_eff=pd.Series(np.asarray(sig.reindex(idx).fillna(0.0),float)*r_pu.reindex(idx).fillna(0.0).values,index=idx)
    d=(r_eff-net_t).abs()
    print(f"{name:<18}{int((d>1e-12).sum()):>6}{fx5.M.sharpe_d(net_t):>9.4f}{fx5.M.sharpe_d(r_eff):>9.4f}"
          f"{fx5.M.neg_years(net_t.dropna())[0]:>8}{fx5.M.neg_years(r_eff)[0]:>9}  ")
for lb in (63,126,252):
    for mode in ("LS","LF"):
        W=fx5.trend_book_weights(px,lb=lb,mode=mode)
        net,We,sig,r_pu=fx5.net_of(W,R_spot); net_t=fx5.trim_warmup(net,sig); idx=net_t.index
        r_eff=pd.Series(np.asarray(sig.reindex(idx).fillna(0.0),float)*r_pu.reindex(idx).fillna(0.0).values,index=idx)
        d=(r_eff-net_t).abs()
        nd=int((d>1e-12).sum())
        mech=""
        if nd:
            bad=(d>1e-12)
            sigd=sig.reindex(idx).fillna(0.0)
            mech=f"sig==0 on {int((sigd[bad]==0).sum())}/{nd} diff-days"
        print(f"TREND_mom{lb}_{mode:<4} {nd:>6}{fx5.M.sharpe_d(net_t):>9.4f}{fx5.M.sharpe_d(r_eff):>9.4f}"
              f"{fx5.M.neg_years(net_t.dropna())[0]:>8}{fx5.M.neg_years(r_eff)[0]:>9}  {mech}")
