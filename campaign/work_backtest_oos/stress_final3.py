"""Financing stress-test DECISION champion vs champion of record (RAWEW15).
Uses campaign bt/financing_stress.stress_table: same gross 1.6x, common 2009+ window.
Correct keys: gross_check.ok, base{ann,sr_d,mdd,neg_years,worst_year}, rungs[{rate,...}]."""
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
netd=pd.DataFrame({c:load(c) for c in w.index}).fillna(0).dot(w)
champ=load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv')
common=netd.index.intersection(champ.index)
netd=netd.reindex(common); champ=champ.reindex(common)
gross=pd.Series(np.full(len(netd),1.6),index=netd.index)
gross_c=pd.Series(np.full(len(champ),1.6),index=champ.index)

print(f"window {common.min().date()}..{common.max().date()}, gross 1.6x both")
for name,net,gr in [("DECISION-CHAMPION",netd,gross),("CHAMPION-RAWEW15",champ,gross_c)]:
    print(f"\n===== {name} =====")
    for rate in [0.045,0.055,0.065,0.08]:
        t=fs.stress_table(net,gr,rate)
        go=t['gross_check']['ok']; b=t['base']
        # find this rate's rung row (base row always present at 4.5%)
        rt=[r for r in t['rungs'] if abs(r['rate']-rate)<1e-9]
        rw=rt[0] if rt else {}
        print(f"  rate {rate*100:4.1f}%: gross_ok={go} ann={b['ann']*100:6.2f}% sr_d={b['sr_d']:5.3f} "
              f"mdd={b['mdd']*100:6.2f}% negYr={b['neg_years']} worst={b['worst_year']*100:5.2f}% "
              f"| margin_drag={rw.get('margin_drag_ann_pct','-')}%/yr")
    # borrow tier summary (short_notional 0.5)
    t=fs.stress_table(net,gr,0.045,short_notional=0.5)
    print("  borrow_tiers:", [round(x.get('cost_ann_pct',x.get('drag',0)),3) if isinstance(x,dict) else x for x in t['borrow_tiers']] if t['borrow_tiers'] else "n/a (no short notional model)")

for name,net,gr in [("DECISION-CHAMPION",netd,gross),("CHAMPION-RAWEW15",champ,gross_c)]:
    # base (4.5% margin) daily SR ratio for a like-for-like comparison
    t45=fs.stress_table(net,gr,0.045); t80=fs.stress_table(net,gr,0.08)
    print(f"{name}: SR@4.5%={t45['base']['sr_d']:.3f}  SR@8.0%={t80['base']['sr_d']:.3f}")
