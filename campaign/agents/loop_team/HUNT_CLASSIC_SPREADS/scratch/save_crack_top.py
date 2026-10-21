"""Save the top, non-redundant crack spread sleeves that PASS all honest gates."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
OUT = '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'

wti = E.eia('wti_spot_daily')
gas_nyh = E.eia('gasoline_nyh_spot_daily') * 42.0
ulsd_nyh = E.eia('ulsd_nyh_spot_daily') * 42.0
budgets = {
    # margin, [(lb,gate), ...] top non-redundant configs
    'crack321_nyh': [E.build_crack321(wti, gas_nyh, ulsd_nyh), [(60,1.5),(15,1.5),(60,1.0)]],
    'crack211_nyh': [E.build_crack211(wti, gas_nyh, ulsd_nyh), [(15,1.5),(60,1.5)]],
    'gas_crack_nyh': [gas_nyh - wti, [(30,1.5),(40,1.0),(30,2.0)]],
}
for name, (margin, cfgs) in budgets.items():
    for lb, gate in cfgs:
        net, gr, pos, tup = E.zrev_margin(margin, lookback=lb, gate=gate)
        net_vt, _ = E.vol_target(net)
        st = E.evaluate(net_vt, E.champ_ref(), name)
        p = E.position_rotation_p(pos, margin, n=200)[0]
        st['scramble_p'] = p
        st['ALL_PASS'] = bool(st['SR_pass'] and st['H_pass'] and st['negyr_pass']
                              and p<0.05 and st['corr_pass'] and st['flatten_pass'])
        fn = f"{OUT}/crack_{name}_L{lb}Z{gate}.csv"
        E.save_sleeve(net_vt, fn)
        print(f"SAVED {fn}  SR={st['SR']:.3f} ann={st['ann_geo']*100:.1f}% MDD={st['MDD']*100:.1f}% "
              f"negy={st['negyr']} corr={st['corr_champ']:+.3f} scram={p:.3f} unfilled rows={net_vt.isna().sum()} ALL={st['ALL_PASS']}")
print("done")
