"""HUNT_CLASSIC_SPREADS — INTER-COMMODITY SPREAD (跨品种套利) research.
Pairs: Brent-WTI, gold-silver, gold-platinum, gold-palladium, gasoline regional (NYH-Gulf),
diesel-jet, crude marketing margins. Uses LOG-RATIO z-rev (validated brwt/diescrack engine).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
OUT = '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'
champ = E.champ_ref()

# ---- log spread series (like brwt: log(priceA) - log(priceB))
wti = E.eia('wti_spot_daily'); brent = E.eia('brent_spot_daily')
gold = E.newdata2('gold_am'); silver = E.newdata2('silver')
plat = E.newdata2('platinum_pm'); pall = E.newdata2('palladium_pm')
gas_nyh = E.eia('gasoline_nyh_spot_daily'); gas_gulf = E.eia('gasoline_gulf_spot_daily')
ulsd_nyh = E.eia('ulsd_nyh_spot_daily'); jet = E.eia('jet_gulf_spot_daily')

import numpy as np
pairs = {
    'brwt':  np.log(brent) - np.log(wti),
    'ausi':  np.log(gold) - np.log(silver),
    'aupl':  np.log(gold) - np.log(plat),
    'aupd':  np.log(gold) - np.log(pall),
    'plpd':  np.log(plat) - np.log(pall),
    'gasreg_nyh_gulf': np.log(gas_nyh) - np.log(gas_gulf),   # regional refining basis
    'dieseljet': np.log(ulsd_nyh) - np.log(jet),             # product slate
    'diesel_gas': np.log(ulsd_nyh) - np.log(gas_nyh),        # distillate-gasoline ratio
}

print("=== INTER-COMMODITY log-spread series ===")
for k, s in pairs.items():
    v = s.dropna()
    print(f"{k:18s} n={len(v):5d} span {v.index.min().date()}..{v.index.max().date()}")

def build_zrev(sp, lb, gate):
    # adapt: use zrev on the log spread (like brwt/diescrack)
    net, gr, pos, tup = E.zrev_margin(sp, lookback=lb, gate=gate)
    net_vt, _ = E.vol_target(net)
    return net_vt, net, pos

print("\n=== GRID (log-ratio z-rev, vt0.08, borrow, 6.4bps) ===")
rows = []
for pname, sp in pairs.items():
    for lb in [15, 30, 40, 60, 90]:
        for gate in [1.0, 1.5, 2.0, 2.5]:
            try:
                net, gr, pos, tup = E.zrev_margin(sp, lookback=lb, gate=gate)
                net_vt, _ = E.vol_target(net)
                p = E.position_rotation_p(pos, sp, n=100)[0]
                st = E.evaluate(net_vt, champ, pname)
                rows.append(dict(name=pname, lb=lb, gate=gate, SR=st['SR'], ann=st['ann_geo']*100,
                                 mdd=st['MDD']*100, negy=st['negyr'], corr=st['corr_champ'],
                                 H1=st['H1_H2'][0], H2=st['H1_H2'][1], scramble_p=p,
                                 uniqR=st['uniqR'], ac1=st['ac1'],
                                 ALL=(st['SR_pass'] and st['H_pass'] and st['negyr_pass']
                                      and p<0.05 and st['corr_pass'] and st['flatten_pass'])))
            except Exception as e:
                pass
df = pd.DataFrame(rows)
pd.set_option('display.width',200)
print(df.sort_values('SR',ascending=False).to_string(index=False))
df.to_csv('/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/reports/inter_grid.csv', index=False)
print("\n=== PASSING configs ===")
print(df[df['ALL']==True].to_string(index=False))
print("count passing:", (df['ALL']==True).sum())
