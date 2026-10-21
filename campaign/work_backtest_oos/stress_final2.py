"""Financing stress-test the DECISION champion vs champion of record (RAWEW15).
Properly uses bt/financing_stress.rung_ladder output (call-rate ladder) + borrow tiers.
Same gross 1.6x, common window 2009+."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign")
from bt import financing_stress as fs

ROOT="/Users/daxu/software/world-trader/campaign"; OD=os.path.join(ROOT,"work_backtest_oos")
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
w=pd.read_csv(os.path.join(OD,"DECISION_CHAMPION_weights.csv"),index_col=0)['w']
frame=pd.DataFrame({c:load(c) for c in w.index})
netd=frame.fillna(0).dot(w)
champ=load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv')
common=netd.index.intersection(champ.index)
netd=netd.reindex(common); champ=champ.reindex(common)
gross=pd.Series(np.full(len(netd),1.6),index=netd.index)
gross_c=pd.Series(np.full(len(champ),1.6),index=champ.index)

def fmt(tbl):
    go=tbl['gross_ok']; b=tbl['base']
    rr=[ (r['rate'], r) for r in tbl['rungs'] ]
    return go, b, rr

for name,net,gr in [("DECISION-CHAMPION",netd,gross),("CHAMPION-RAWEW15",champ,gross_c)]:
    print(f"\n===== {name} (gross 1.6x, {net.index[0].date()}..{net.index[-1].date()}) =====")
    for rate in [0.045,0.055,0.065,0.08]:
        tbl=fs.stress_table(net, gr, rate)
        go,tb,rr=fmt(tbl)
        b=tb
        print(f"  call-rate {rate*100:.1f}%: gross_ok={go} ann(geo)={b['ann']*100:.2f}% "
              f"sr_d={b['sr_d']:.3f} mdd={b['mdd']*100:.2f}% negYr={b['neg_years']} worst={b['worst_year']*100:.2f}%")
    print("  --- borrow tier drag (short) @ base 4.5% ---")
    tbl=fs.stress_table(net, gr, 0.045, short_notional=0.5)
    bt=tbl['borrow_tiers']
    for tier in bt:
        pass
    # borrow_tiers structure
    short=[ t for t in fs.__dict__.get('borrow_tier_block',[])(net,0.5,0.005) ] if False else None
    print("  (borrow_tiers rows:", len(tbl['borrow_tiers']), ")")
    for t in tbl['borrow_tiers']:
        print("   ", json.dumps(t, default=str)[:160])
