import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
ROOT="/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES"; DATA=ROOT+"/data"
champ=E.champ_ref()
def load(s):
    df=pd.read_csv(f"{DATA}/{s}.csv",index_col=0,parse_dates=True); return df['close'].astype(float)
def save(a,b,lb,gate):
    A,B=load(a),load(b); sp=(np.log(A)-np.log(B)).dropna(); sp=sp[sp.index>='2009']
    net,gr,pos,tup=E.zrev_margin(sp,lookback=lb,gate=gate); nv,_=E.vol_target(net)
    p=E.position_rotation_p(pos,sp,n=200)[0]
    st=E.evaluate(nv,champ,f'{a}-{b}')
    st['scramble_p']=p
    ok=st['SR_pass'] and st['H_pass'] and st['negyr_pass'] and p<0.05 and st['corr_pass'] and st['flatten_pass']
    print(f"\n[{a}-{b} L{lb}Z{gate}] SR={st['SR']:.3f} ann={st['ann_geo']*100:.1f}% MDD={st['MDD']*100:.1f}% "
          f"negy={st['negyr']} worst={st['worst']*100:.1f}% H=({st['H1_H2'][0]:.2f},{st['H1_H2'][1]:.2f}) "
          f"scram={p:.3f} corr={st['corr_champ']:+.3f} ac1={st['ac1']:.3f} uniq={st['uniqR']:.2f} => PASS={ok}")
    if ok:
        E.save_sleeve(nv, f"{ROOT}/sleeves/cnpair_{a}_{b}_L{lb}Z{gate}.csv")
        print("   SAVED")
for (a,b,lb,gate) in [('M0','RM0',60,1.5),('RB0','HC0',90,1.0),('SC0','FU0',90,2.0)]:
    try: save(a,b,lb,gate)
    except Exception as e: print(f"{a}-{b} ERR {e}")
