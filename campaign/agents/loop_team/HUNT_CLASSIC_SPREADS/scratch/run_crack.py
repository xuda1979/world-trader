"""HUNT_CLASSIC_SPREADS — CRACK SPREAD (裂解价差) research (v2, proper scramble).
Real 3:2:1 / 2:1:1 / gasoline-crack margins from EIA daily NYH/Gulf spots.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E

OUT = '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'
champ = E.champ_ref()

wti = E.eia('wti_spot_daily')
gas_nyh = E.eia('gasoline_nyh_spot_daily') * 42.0
ulsd_nyh = E.eia('ulsd_nyh_spot_daily') * 42.0
gas_gulf = E.eia('gasoline_gulf_spot_daily') * 42.0
ulsd_gulf = E.eia('ulsd_gulf_spot_daily') * 42.0
jet = E.eia('jet_gulf_spot_daily') * 42.0
brent = E.eia('brent_spot_daily')

frames = {
    'crack321_nyh': E.build_crack321(wti, gas_nyh, ulsd_nyh),
    'crack211_nyh': E.build_crack211(wti, gas_nyh, ulsd_nyh),
    'crack321_gulf': E.build_crack321(wti, gas_gulf, ulsd_gulf),
    'gas_crack_nyh': gas_nyh - wti,
    'diesel_crack_nyh': ulsd_nyh - wti,
}

def full_eval(margin, lb, gate, mname):
    net, gr, pos, tup = E.zrev_margin(margin, lookback=lb, gate=gate)
    net_vt, _ = E.vol_target(net)
    st = E.evaluate(net_vt, champ, mname)
    # PROPER scramble: position-rotation through full pipeline
    net_vt_real, _2 = E.vol_target(net)
    st['scramble_p'] = E.position_rotation_p(pos, margin, n=200)[0]
    st['scramble_pass'] = st['scramble_p'] < 0.05
    st['ALL_PASS'] = bool(st['SR_pass'] and st['H_pass'] and st['negyr_pass'] and
                          st['scramble_pass'] and st['corr_pass'] and st['flatten_pass'])
    return net_vt, st

print("=== CRACK SPREAD grid rescan with PROPER position-rotation scramble ===")
all_rows = []
for mname, margin in frames.items():
    for lb in [15, 30, 40, 60, 90]:
        for gate in [1.0, 1.5, 2.0, 2.5]:
            try:
                net, gr, pos, tup = E.zrev_margin(margin, lookback=lb, gate=gate)
                net_vt, _ = E.vol_target(net)
                p = E.position_rotation_p(pos, margin, n=100)[0]
                st = E.evaluate(net_vt, champ, mname)
                all_rows.append(dict(name=mname, lb=lb, gate=gate, SR=st['SR'],
                                     ann=st['ann_geo']*100, mdd=st['MDD']*100,
                                     negy=st['negyr'], corr=st['corr_champ'],
                                     H1=st['H1_H2'][0], H2=st['H1_H2'][1],
                                     scramble_p=p, uniqR=st['uniqR'], ac1=st['ac1'],
                                     ALL=(st['SR_pass'] and st['H_pass'] and st['negyr_pass']
                                          and p<0.05 and st['corr_pass'] and st['flatten_pass'])))
            except Exception as e:
                pass

df = pd.DataFrame(all_rows)
pd.set_option('display.width', 200)
print(df.sort_values('SR', ascending=False).to_string(index=False))
df.to_csv('/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/reports/crack_grid.csv', index=False)

print("\n=== PASSING configs (ALL_PASS with proper scramble <0.05) ===")
passing = df[df['ALL'] == True]
print(passing.to_string(index=False))
print(f"\nTotal passing configs: {len(passing)}")
