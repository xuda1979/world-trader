"""Save top passing inter-commodity spread sleeves."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
import engine as E
OUT = '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'
champ = E.champ_ref()
wti=E.eia('wti_spot_daily'); gas_nyh=E.eia('gasoline_nyh_spot_daily'); gas_gulf=E.eia('gasoline_gulf_spot_daily')
ulsd_nyh=E.eia('ulsd_nyh_spot_daily'); jet=E.eia('jet_gulf_spot_daily')
pairs = {
  'gasreg_nyh_gulf': np.log(gas_nyh)-np.log(gas_gulf),
  'dieseljet': np.log(ulsd_nyh)-np.log(jet),
}
cfgs = {
  'gasreg_nyh_gulf': [(30,1.0),(40,1.0),(60,1.0)],
  'dieseljet': [(60,1.5),(60,1.0)],
}
for name, sp in pairs.items():
    for lb, gate in cfgs[name]:
        net, gr, pos, tup = E.zrev_margin(sp, lookback=lb, gate=gate)
        net_vt, _ = E.vol_target(net)
        st = E.evaluate(net_vt, champ, name)
        p = E.position_rotation_p(pos, sp, n=200)[0]
        fn = f"{OUT}/inter_{name}_L{lb}Z{gate}.csv"
        E.save_sleeve(net_vt, fn)
        print(f"SAVED {fn}  SR={st['SR']:.3f} ann={st['ann_geo']*100:.1f}% MDD={st['MDD']*100:.1f}% "
              f"negy={st['negyr']} worst={st['worst']*100:.1f}% corr={st['corr_champ']:+.3f} scram={p:.3f} ALL_PASS={st['ALL_PASS']}")
