import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
import engine as E
champ=E.champ_ref()
gas_nyh=E.eia('gasoline_nyh_spot_daily'); gas_gulf=E.eia('gasoline_gulf_spot_daily')
sp=np.log(gas_nyh)-np.log(gas_gulf)
lb,gate=30,1.0
net,gr,pos,tup=E.zrev_margin(sp,lookback=lb,gate=gate)
net_vt,_=E.vol_target(net)
st=E.evaluate(net_vt,champ,'gasreg')
p=E.position_rotation_p(pos,sp,n=300)[0]
st['scramble_p']=p; st['scramble_pass']=p<0.05
st['ALL_PASS']=bool(st['SR_pass'] and st['H_pass'] and st['negyr_pass'] and st['scramble_pass'] and st['corr_pass'] and st['flatten_pass'])
print("=== gasreg_nyh_gulf L30Z1.0 FULL GATE VERIFICATION ===")
for k,v in st.items():
    if k in ('negyr_map',): print(f"  {k} = {v}")
    else: print(f"  {k:16s} = {v}")
print("\n ALL_PASS =", st['ALL_PASS'])
